import asyncio
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


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


def _age(birth_date: Optional[str]) -> Optional[int]:
    if not birth_date:
        return None
    today = date.today()
    bd = date.fromisoformat(birth_date)
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))


def _latest_obs(entries: list[dict], codes: set[str]) -> Optional[dict]:
    matches = [
        e for e in entries
        if e.get("code", {}).get("coding", [{}])[0].get("code") in codes
        and e.get("valueQuantity")
    ]
    matches.sort(key=lambda e: e.get("effectiveDateTime", ""))
    return matches[-1] if matches else None


def _fmt(obs: Optional[dict]) -> str:
    if not obs:
        return "not available"
    qty = obs.get("valueQuantity", {})
    return f"{qty.get('value', '?')} {qty.get('unit', '')}".strip()


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


def _build_system_prompt(
    patient_raw: dict,
    obs_entries: list[dict],
    med_entries: list[dict],
    condition_names: list[str],
) -> str:
    name_block = (patient_raw.get("name") or [{}])[0]
    full_name = " ".join(filter(None, [
        " ".join(name_block.get("given", [])),
        name_block.get("family", ""),
    ])).strip() or "this patient"

    gender = patient_raw.get("gender", "unknown")
    age = _age(patient_raw.get("birthDate"))
    age_str = f"{age} years old" if age else "unknown age"

    latest_glucose = _latest_obs(obs_entries, GLUCOSE_CODES)
    latest_hba1c = _latest_obs(obs_entries, HBA1C_CODES)
    latest_bp = _latest_obs(obs_entries, BP_CODES)

    med_names = _extract_med_names(med_entries)
    conditions = ", ".join(condition_names) if condition_names else "none recorded"
    meds = ", ".join(med_names) if med_names else "none on record"

    return f"""You are a friendly personal health assistant embedded in a diabetes management patient portal. Your name is HealthBot.

You are speaking with {full_name}, a {age_str} {gender} patient managing Type 2 Diabetes.

Their current health snapshot:
- Latest Blood Glucose: {_fmt(latest_glucose)}
- Latest HbA1c: {_fmt(latest_hba1c)}
- Latest Blood Pressure: {_fmt(latest_bp)}
- Active Medications: {meds}
- Active Conditions: {conditions}

YOUR ROLE:
- Help this patient understand their health data, lab values, and portal features in plain, supportive language.
- Encourage healthy habits and positive engagement with their care team.
- Answer general questions about diabetes management, what their numbers mean, and how to navigate the portal.

STRICT BOUNDARIES — follow these without exception:
1. Never provide specific medical advice, diagnoses, or treatment recommendations.
2. Never suggest changing, skipping, or adjusting any medication — always defer to their prescribing clinician.
3. If the patient asks anything requiring a clinical decision, respond with something like: "That's a great question for your care team. I'd recommend scheduling an appointment with your clinician — they can give you personalized guidance based on your full history."
4. If the patient describes emergency symptoms (chest pain, severe shortness of breath, loss of consciousness, blood sugar below 54 mg/dL with symptoms, or anything life-threatening), immediately tell them to call 911 or go to the nearest emergency room. Do not attempt to help further.
5. Do not speculate about diagnoses or prognoses.
6. Do not discuss anything unrelated to the patient's health or portal navigation.

Keep your tone warm, encouraging, and easy to understand. Avoid medical jargon. Keep responses concise — 2–4 sentences unless more detail is genuinely helpful."""


@router.post("/{patient_id}", response_model=ChatResponse)
async def chat(patient_id: str, request: ChatRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Gemini API key not configured.")
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided.")

    patient_raw, obs_bundle, med_bundle, condition_bundle = await asyncio.gather(
        get_resource("Patient", patient_id),
        search_resource("Observation", {"subject": patient_id, "_count": 50, "_sort": "date"}),
        search_resource("MedicationRequest", {"patient": patient_id, "status": "active", "_count": 20}),
        search_resource("Condition", {"patient": patient_id, "clinical-status": "active", "_count": 50}),
    )

    obs_entries = extract_bundle_entries(obs_bundle)
    med_entries = extract_bundle_entries(med_bundle)
    condition_names = _extract_conditions(extract_bundle_entries(condition_bundle))

    system_prompt = _build_system_prompt(patient_raw, obs_entries, med_entries, condition_names)

    def call_gemini() -> str:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            system_instruction=system_prompt,
        )
        history = [
            {
                "role": msg.role if msg.role == "user" else "model",
                "parts": [msg.content],
            }
            for msg in request.messages[:-1]
        ]
        chat_session = model.start_chat(history=history)
        return chat_session.send_message(request.messages[-1].content).text

    loop = asyncio.get_running_loop()
    reply = await loop.run_in_executor(None, call_gemini)
    return ChatResponse(reply=reply.strip())
