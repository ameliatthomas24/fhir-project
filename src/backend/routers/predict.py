from fastapi import APIRouter, Depends, HTTPException
import os
import joblib
import requests
import logging
from ml.ml_predict import generate_risk_assessment, PatientProfile
from auth import get_current_user, require_patient_access

router = APIRouter()
logger = logging.getLogger(__name__)

FHIR_URL = os.getenv("FHIR_BASE_URL", "http://hapi-fhir-server:8080/fhir")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "model.pkl")

try:
    model_pipeline = joblib.load(MODEL_PATH)
    logger.info(f" Model loaded from {MODEL_PATH}")
except Exception as e:
    logger.error(f" Model load failed: {e}")
    model_pipeline = None



@router.get("/{patient_id}")
async def get_prediction(patient_id: str):
    
    try:
        p_resp = requests.get(f"{FHIR_URL}/Patient/{patient_id}", timeout=5)
        if p_resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Patient not found in HAPI")
        patient = p_resp.json()

        o_resp = requests.get(f"{FHIR_URL}/Observation?subject=Patient/{patient_id}", timeout=5)
        entries = o_resp.json().get("entry", [])

        def find_val(code):
            for e in entries:
                resource = e.get("resource", {})
                codings = resource.get("code", {}).get("coding", [])
                if any(c.get("code") == code for c in codings):
                    return resource.get("valueQuantity", {}).get("value", 0)
            return 0

        profile = PatientProfile(
            gender=patient.get("gender", "male").capitalize(),
            age=45.0,
            bmi=float(find_val("39156-5") or 25.0),
            HbA1c_level=float(find_val("4548-4") or 5.5),
            blood_glucose_level=float(find_val("2339-0") or 100.0),
            smoking_history="never",
            hypertension=0,
            heart_disease=0,
        )

        return generate_risk_assessment(profile)

    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail=f"Cannot reach HAPI server at {FHIR_URL}")
    except Exception as e:
        logger.error(f"Prediction Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
