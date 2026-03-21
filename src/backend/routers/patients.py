from fastapi import APIRouter, Query
from typing import Optional

from fhir_client import get_resource, search_resource, extract_bundle_entries
from models import PatientSummary

router = APIRouter()

# Helpers 

def _simplify_patient(raw: dict) -> PatientSummary:
    # Map a raw FHIR Patient resource 
    name_list = raw.get("name", [])
    official = next((n for n in name_list if n.get("use") == "official"), None)
    name_entry = official or (name_list[0] if name_list else {})
    family = name_entry.get("family", "")
    given = " ".join(name_entry.get("given", []))
    full_name = f"{given} {family}".strip() or "Unknown"

    telecoms = raw.get("telecom", [])
    phone_entry = next((t for t in telecoms if t.get("system") == "phone"), None)
    phone = phone_entry.get("value") if phone_entry else None

    addresses = raw.get("address", [])
    addr_str = None
    if addresses:
        a = addresses[0]
        parts = a.get("line", []) + [a.get("city", ""), a.get("state", "")]
        addr_str = ", ".join(p for p in parts if p)

    return PatientSummary(
        id=raw.get("id", ""),
        full_name=full_name,
        birth_date=raw.get("birthDate"),
        gender=raw.get("gender"),
        phone=phone,
        address=addr_str,
    )


# Routes

@router.get("", response_model=list[PatientSummary])
async def list_patients(
    name: Optional[str] = Query(None, description="Partial name search"),
    count: int = Query(20, alias="_count", ge=1, le=100),
):
    # Return a list of patients from the FHIR server
    params: dict = {"_count": count}
    if name:
        params["name"] = name

    bundle = await search_resource("Patient", params)
    entries = extract_bundle_entries(bundle)
    return [_simplify_patient(p) for p in entries]


@router.get("/{patient_id}", response_model=PatientSummary)
async def get_patient(patient_id: str):
    #Return a single patient by FHIR resource id
    raw = await get_resource("Patient", patient_id)
    return _simplify_patient(raw)
