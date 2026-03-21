from fastapi import APIRouter, Query
from typing import Optional

from fhir_client import search_resource, extract_bundle_entries
from models import MedicationSummary

router = APIRouter()

# Helpers 

def _simplify_medication(raw: dict) -> MedicationSummary:
    #Map a raw FHIR MedicationRequest 

    med_name = "Unknown"
    if "medicationCodeableConcept" in raw:
        codings = raw["medicationCodeableConcept"].get("coding", [{}])
        med_name = (
            raw["medicationCodeableConcept"].get("text")
            or codings[0].get("display", "Unknown")
        )
    elif "medicationReference" in raw:
        med_name = raw["medicationReference"].get("display", "Unknown")

    subject_ref = raw.get("subject", {}).get("reference", "")
    patient_id = subject_ref.split("/")[-1] if "/" in subject_ref else subject_ref

    requester_ref = raw.get("requester", {}).get("reference", "")
    prescriber_id = requester_ref.split("/")[-1] if "/" in requester_ref else None

    dosage_instructions = raw.get("dosageInstruction", [])
    dosage_text = None
    if dosage_instructions:
        dosage_text = dosage_instructions[0].get("text")

    return MedicationSummary(
        id=raw.get("id", ""),
        patient_id=patient_id,
        medication_name=med_name,
        status=raw.get("status", "unknown"),
        authored_on=raw.get("authoredOn"),
        dosage_instruction=dosage_text,
        prescriber_id=prescriber_id,
    )


async def _fetch_medications(
    patient_id: str,
    status: Optional[str] = None,
    count: int = 50,
) -> list[MedicationSummary]:
    params: dict = {
        "patient": patient_id,
        "_count": count,
        "_sort": "-authoredon",
    }
    if status:
        params["status"] = status

    bundle = await search_resource("MedicationRequest", params)
    entries = extract_bundle_entries(bundle)
    return [_simplify_medication(m) for m in entries]


# Routes

@router.get("/{patient_id}", response_model=list[MedicationSummary])
async def get_medications(
    patient_id: str,
    count: int = Query(50, alias="_count", ge=1, le=200),
):
    """Return all medication requests for a patient."""
    return await _fetch_medications(patient_id, count=count)


@router.get("/{patient_id}/active", response_model=list[MedicationSummary])
async def get_active_medications(
    patient_id: str,
    count: int = Query(50, alias="_count", ge=1, le=200),
):
    #Return only active prescriptions 
    return await _fetch_medications(patient_id, status="active", count=count)
