from fastapi import APIRouter, Query
from typing import Optional

from fhir_client import search_resource, extract_bundle_entries
from models import ObservationPoint

router = APIRouter()

LOINC = {
    "glucose":         ["15074-8", "2339-0"],   # Glucose 
    "hba1c":           ["4548-4", "17856-6"],   # Hgb 
    "blood_pressure":  ["55284-4", "8480-6", "8462-4"],  # BP panel, systolic, diastolic
}

# Helpers 

def _simplify_observation(raw: dict) -> ObservationPoint:
    # Map a raw FHIR Observation 
    coding = raw.get("code", {}).get("coding", [{}])[0]
    code = coding.get("code", "")
    display = coding.get("display") or raw.get("code", {}).get("text", "Unknown")
    value_qty = raw.get("valueQuantity", {})
    value = value_qty.get("value")
    unit = value_qty.get("unit") or value_qty.get("code")
    effective = raw.get("effectiveDateTime") or raw.get("effectivePeriod", {}).get("start")

    # Patient reference 
    subject_ref = raw.get("subject", {}).get("reference", "")
    patient_id = subject_ref.split("/")[-1] if "/" in subject_ref else subject_ref

    return ObservationPoint(
        id=raw.get("id", ""),
        patient_id=patient_id,
        code=code,
        display=display,
        value=value,
        unit=unit,
        effective_date=effective,
        status=raw.get("status", "unknown"),
    )


async def _fetch_observations(
    patient_id: str,
    codes: Optional[list[str]] = None,
    count: int = 50,
) -> list[ObservationPoint]:
    params: dict = {
        "subject": patient_id,
        "_count": count,
        "_sort": "-date",
    }
    if codes:
        params["code"] = ",".join(codes)

    bundle = await search_resource("Observation", params)
    entries = extract_bundle_entries(bundle)
    return [_simplify_observation(o) for o in entries]


# Routes 

@router.get("/{patient_id}", response_model=list[ObservationPoint])
async def get_observations(
    patient_id: str,
    count: int = Query(50, alias="_count", ge=1, le=200),
):
    #Return all observations for a patient
    return await _fetch_observations(patient_id, count=count)


@router.get("/{patient_id}/glucose", response_model=list[ObservationPoint])
async def get_glucose(
    patient_id: str,
    count: int = Query(50, alias="_count", ge=1, le=200),
):
    # Return blood glucose 
    return await _fetch_observations(patient_id, codes=LOINC["glucose"], count=count)


@router.get("/{patient_id}/hba1c", response_model=list[ObservationPoint])
async def get_hba1c(
    patient_id: str,
    count: int = Query(50, alias="_count", ge=1, le=200),
):
    # Return HbA1c readings 
    return await _fetch_observations(patient_id, codes=LOINC["hba1c"], count=count)


@router.get("/{patient_id}/blood-pressure", response_model=list[ObservationPoint])
async def get_blood_pressure(
    patient_id: str,
    count: int = Query(50, alias="_count", ge=1, le=200),
):
    # Return blood pressure 
    return await _fetch_observations(patient_id, codes=LOINC["blood_pressure"], count=count)
