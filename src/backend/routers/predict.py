from fastapi import APIRouter, HTTPException
from fhir_client import search_resource, extract_bundle_entries
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "ml"))
from ml_predict import generate_risk_assessment, PatientProfile, prediction_pipeline

router = APIRouter()

GLUCOSE_CODES = {"15074-8", "2339-0"}
HBA1C_CODES   = {"4548-4", "17856-6"}
BP_CODES      = {"55284-4", "8462-4", "8480-6"}
WEIGHT_CODES  = {"29463-7", "3141-9"}
HEIGHT_CODES  = {"8302-2"}

def latest(obs_list: list, codes: set):
    matches = [o for o in obs_list if o.get("code", {}).get("coding", [{}])[0].get("code") in codes]
    matches.sort(key=lambda o: o.get("effectiveDateTime", ""), reverse=True)
    if not matches:
        return None
    return matches[0].get("valueQuantity", {}).get("value")

@router.get("/{patient_id}")
async def predict_diabetes_risk(patient_id: str):
    if prediction_pipeline is None:
        raise HTTPException(status_code=503, detail="ML model not loaded")

    from fhir_client import get_resource
    raw_patient = await get_resource("Patient", patient_id)

    gender_raw = raw_patient.get("gender", "male")
    gender = "Female" if gender_raw == "female" else "Male"

    birth_date = raw_patient.get("birthDate", "")
    age = 0.0
    if birth_date:
        from datetime import date
        born = date.fromisoformat(birth_date)
        age = round((date.today() - born).days / 365.25, 1)

    bundle = await search_resource("Observation", {"patient": patient_id, "_count": 200})
    obs_list = extract_bundle_entries(bundle)

    hba1c         = latest(obs_list, HBA1C_CODES) or 6.5
    blood_glucose = latest(obs_list, GLUCOSE_CODES) or 100.0

    # BMI from weight/height or default
    weight_kg = latest(obs_list, WEIGHT_CODES)
    height_m  = latest(obs_list, HEIGHT_CODES)
    if weight_kg and height_m:
        bmi = round(weight_kg / (height_m ** 2), 1)
    else:
        bmi = 27.0  # population average fallback

    # Hypertension/heart disease from conditions
    cond_bundle = await search_resource("Condition", {"patient": patient_id, "_count": 100})
    conditions = extract_bundle_entries(cond_bundle)
    condition_texts = " ".join([
        c.get("code", {}).get("text", "") +
        " ".join([cd.get("display", "") for cd in c.get("code", {}).get("coding", [])])
        for c in conditions
    ]).lower()

    hypertension  = 1 if any(w in condition_texts for w in ["hypertension", "high blood pressure"]) else 0
    heart_disease = 1 if any(w in condition_texts for w in ["heart", "cardiac", "coronary", "myocardial"]) else 0

    profile = PatientProfile(
        gender=gender,
        smoking_history="never",   # FHIR social history not always coded — safe default
        age=age,
        bmi=bmi,
        HbA1c_level=float(hba1c),
        blood_glucose_level=float(blood_glucose),
        hypertension=hypertension,
        heart_disease=heart_disease,
    )

    result = generate_risk_assessment(profile)

    return {
        "patient_id": patient_id,
        "risk_score": result.risk_score,
        "risk_label": result.risk_label,
        "top_factors": result.top_factors,
        "inputs": {
            "age": age,
            "bmi": bmi,
            "HbA1c_level": hba1c,
            "blood_glucose_level": blood_glucose,
            "hypertension": hypertension,
            "heart_disease": heart_disease,
            "gender": gender,
        }
    }