import asyncio
import logging
import os
from datetime import date
from typing import Optional

import joblib
from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user, require_patient_access
from fhir_client import extract_bundle_entries, get_resource, search_resource
from ml.ml_predict import PatientProfile, generate_risk_assessment

router = APIRouter()
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "model.pkl")

# SNOMED / ICD-10 codes used to flag hypertension and heart disease from conditions
_HYPERTENSION_CODES = {"38341003", "59621000", "I10", "I11", "I12", "I13"}
_HEART_DISEASE_CODES = {"53741008", "414545008", "I25", "I25.10", "I21", "I22", "I50"}

try:
    model_pipeline = joblib.load(MODEL_PATH)
    logger.info(f"Model loaded from {MODEL_PATH}")
except Exception as e:
    logger.error(f"Model load failed: {e}")
    model_pipeline = None


def _age_from_birthdate(birth_date: Optional[str]) -> float:
    if not birth_date:
        return 45.0
    bd = date.fromisoformat(birth_date)
    today = date.today()
    return float(today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day)))


_ALT_CODES: dict[str, list[str]] = {
    "39156-5": ["39156-5"],                    # BMI
    "4548-4":  ["4548-4", "17856-6"],          # HbA1c
    "2339-0":  ["2339-0", "15074-8"],          # Glucose
}


def _find_val(entries: list[dict], code: str) -> float:
    targets = set(_ALT_CODES.get(code, [code]))
    for obs in entries:
        codings = obs.get("code", {}).get("coding", [])
        if any(c.get("code") in targets for c in codings):
            val = obs.get("valueQuantity", {}).get("value")
            if val is not None:
                return float(val)
    return 0


def _has_condition(condition_entries: list[dict], target_codes: set[str]) -> int:
    for c in condition_entries:
        for coding in c.get("code", {}).get("coding", []):
            code = coding.get("code", "")
            # match exact or ICD-10 prefix (e.g. "I25" matches "I25.10")
            if code in target_codes or any(code.startswith(t) for t in target_codes):
                return 1
    return 0


@router.get("/{patient_id}")
async def get_prediction(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
):
    require_patient_access(patient_id, current_user)

    if model_pipeline is None:
        raise HTTPException(status_code=503, detail="ML model not loaded.")

    try:
        patient, obs_bundle, condition_bundle = await asyncio.gather(
            get_resource("Patient", patient_id),
            search_resource("Observation", {
                "subject": patient_id,
                "_count": 100,
                "_sort": "-date",
            }),
            search_resource("Condition", {
                "patient": patient_id,
                "clinical-status": "active",
                "_count": 50,
            }),
        )

        entries = extract_bundle_entries(obs_bundle)
        condition_entries = extract_bundle_entries(condition_bundle)

        bmi_raw   = _find_val(entries, "39156-5")
        hba1c_raw = _find_val(entries, "4548-4")
        gluc_raw  = _find_val(entries, "2339-0")

        # If no HbA1c observation exists we have no meaningful clinical data
        # for this patient — return a sentinel instead of a misleading score.
        if not hba1c_raw:
            return {"insufficient_data": True}

        bmi     = float(bmi_raw) if bmi_raw else 25.0
        hba1c   = float(hba1c_raw)
        glucose = float(gluc_raw) if gluc_raw else max(70.0, round(28.7 * hba1c - 46.7, 1))
        hypertension = _has_condition(condition_entries, _HYPERTENSION_CODES)
        heart_disease = _has_condition(condition_entries, _HEART_DISEASE_CODES)

        profile = PatientProfile(
            gender=patient.get("gender", "male").capitalize(),
            age=_age_from_birthdate(patient.get("birthDate")),
            bmi=bmi,
            HbA1c_level=hba1c,
            blood_glucose_level=glucose,
            smoking_history="never",
            hypertension=hypertension,
            heart_disease=heart_disease,
        )

        result = generate_risk_assessment(profile, model_pipeline)

        return {
            **result.model_dump(),
            "inputs": {
                "age": profile.age,
                "gender": profile.gender,
                "bmi": profile.bmi,
                "HbA1c_level": profile.HbA1c_level,
                "blood_glucose_level": profile.blood_glucose_level,
                "hypertension": profile.hypertension,
                "heart_disease": profile.heart_disease,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
