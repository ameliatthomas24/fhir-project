import asyncio
import json
import os
from datetime import date
from typing import Optional

import google.generativeai as genai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from fhir_client import extract_bundle_entries, get_resource, search_resource

router = APIRouter()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GLUCOSE_CODES = {"15074-8", "2339-0"}
HBA1C_CODES = {"4548-4", "17856-6"}
BP_CODES = {"55284-4", "8480-6", "8462-4"}
WEIGHT_CODES = {"29463-7", "3141-9"}


class Recommendation(BaseModel):
    category: str
    title: str
    detail: str
    priority: str


class RecommendationResponse(BaseModel):
    summary: str
    recommendations: list[Recommendation]


def _all_obs(entries: list[dict], codes: set[str]) -> list[dict]:
    """Return all observations matching the given codes, sorted oldest → newest."""
    matches = [
        e for e in entries
        if e.get("code", {}).get("coding", [{}])[0].get("code") in codes
        and e.get("valueQuantity")
    ]
    matches.sort(key=lambda e: e.get("effectiveDateTime", ""))
    return matches


def _latest_obs(entries: list[dict], codes: set[str]) -> Optional[dict]:
    matches = _all_obs(entries, codes)
    return matches[-1] if matches else None


def _fmt(obs: Optional[dict]) -> str:
    if not obs:
        return "not available"
    qty = obs.get("valueQuantity", {})
    return f"{qty.get('value', '?')} {qty.get('unit', '')}".strip()


def _age(birth_date: Optional[str]) -> Optional[int]:
    if not birth_date:
        return None
    today = date.today()
    bd = date.fromisoformat(birth_date)
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))


def _hba1c_trend(entries: list[dict]) -> str:
    """Summarise direction of HbA1c over the last few readings."""
    readings = _all_obs(entries, HBA1C_CODES)
    if len(readings) < 2:
        return "insufficient data for trend"

    recent = readings[-5:]  # up to last 5
    values = [r["valueQuantity"]["value"] for r in recent]
    dates = [r.get("effectiveDateTime", "")[:10] for r in recent]

    history = ", ".join(f"{v:.1f}% ({d})" for v, d in zip(values, dates))

    first, last = values[0], values[-1]
    diff = last - first
    if abs(diff) < 0.2:
        direction = "stable"
    elif diff < 0:
        direction = f"improving (↓ {abs(diff):.1f}%)"
    else:
        direction = f"worsening (↑ {diff:.1f}%)"

    return f"{direction} — readings: {history}"


def _extract_conditions(condition_entries: list[dict]) -> list[str]:
    names = []
    for c in condition_entries:
        text = c.get("code", {}).get("text")
        if not text:
            coding = c.get("code", {}).get("coding", [{}])[0]
            text = coding.get("display")
        if text:
            names.append(text)
    return names


def _extract_med_names(med_entries: list[dict]) -> list[str]:
    names = []
    for m in med_entries[:10]:
        if "medicationCodeableConcept" in m:
            name = (
                m["medicationCodeableConcept"].get("text")
                or m["medicationCodeableConcept"].get("coding", [{}])[0].get("display", "Unknown")
            )
        elif "medicationReference" in m:
            name = m["medicationReference"].get("display", "Unknown")
        else:
            name = "Unknown"
        names.append(name)
    return names


def _build_prompt(
    patient_raw: dict,
    obs_entries: list[dict],
    med_entries: list[dict],
    condition_names: list[str],
) -> str:
    gender = patient_raw.get("gender", "unknown")
    age = _age(patient_raw.get("birthDate"))
    med_names = _extract_med_names(med_entries)

    latest_glucose = _latest_obs(obs_entries, GLUCOSE_CODES)
    latest_bp = _latest_obs(obs_entries, BP_CODES)
    latest_weight = _latest_obs(obs_entries, WEIGHT_CODES)
    latest_hba1c = _latest_obs(obs_entries, HBA1C_CODES)
    hba1c_trend = _hba1c_trend(obs_entries)

    comorbidities = ", ".join(condition_names) if condition_names else "none recorded"

    return f"""You are a clinical decision support assistant for a diabetes management portal.
Generate personalized preventative care recommendations for this patient.

Patient:
- Age: {age if age is not None else "unknown"}
- Gender: {gender}
- Comorbidities / Active Conditions: {comorbidities}
- Active Medications: {", ".join(med_names) if med_names else "none on record"}

Lab Values:
- Latest Blood Glucose: {_fmt(latest_glucose)}
- Latest HbA1c: {_fmt(latest_hba1c)}
- HbA1c Trend: {hba1c_trend}
- Latest Blood Pressure: {_fmt(latest_bp)}
- Weight: {_fmt(latest_weight)}

Instructions:
- Use the HbA1c trend to assess whether glycemic control is improving or worsening and reflect this in recommendations.
- Factor in comorbidities (e.g. hypertension, neuropathy, CKD) when prioritizing recommendations.
- Be specific — reference actual values, not generic advice.
- Do not recommend medications; only lifestyle, monitoring, diet, and exercise guidance.

Return ONLY a valid JSON object with no markdown, no code fences, and no extra text:
{{
  "summary": "2-3 sentence overall assessment referencing the HbA1c trend and key comorbidities",
  "recommendations": [
    {{
      "category": "Diet",
      "title": "short title",
      "detail": "specific actionable recommendation referencing the patient's actual values",
      "priority": "High"
    }}
  ]
}}

Include 5-7 recommendations covering: Diet, Exercise, Medication Adherence, Monitoring, Lifestyle.
Priority must be exactly one of: High, Medium, Low."""


@router.get("/{patient_id}", response_model=RecommendationResponse)
async def get_recommendations(patient_id: str):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Gemini API key not configured. Set GEMINI_API_KEY in .env.")

    patient_raw, obs_bundle, med_bundle, condition_bundle = await asyncio.gather(
        get_resource("Patient", patient_id),
        search_resource("Observation", {"subject": patient_id, "_count": 100, "_sort": "date"}),
        search_resource("MedicationRequest", {"patient": patient_id, "status": "active", "_count": 20}),
        search_resource("Condition", {"patient": patient_id, "clinical-status": "active", "_count": 50}),
    )

    obs_entries = extract_bundle_entries(obs_bundle)
    med_entries = extract_bundle_entries(med_bundle)
    condition_names = _extract_conditions(extract_bundle_entries(condition_bundle))

    prompt = _build_prompt(patient_raw, obs_entries, med_entries, condition_names)

    def call_gemini() -> str:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model.generate_content(prompt).text

    loop = asyncio.get_event_loop()
    raw_text = await loop.run_in_executor(None, call_gemini)

    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        data = json.loads(text)
        return RecommendationResponse(**data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse Gemini response: {exc}")
