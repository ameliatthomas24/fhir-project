import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional

from auth import get_current_user, require_patient_access
from fhir_client import get_resource, search_resource, extract_bundle_entries
from models import PatientSummary

router = APIRouter()


def _simplify_patient(raw: dict) -> PatientSummary:
    name_list = raw.get("name", [])
    official = next((n for n in name_list if n.get("use") == "official"), None)
    name_entry = official or (name_list[0] if name_list else {})
    family = re.sub(r"\d+", "", name_entry.get("family", ""))
    given = " ".join(re.sub(r"\d+", "", g) for g in name_entry.get("given", []))
    full_name = re.sub(r"\s+", " ", f"{given} {family}").strip() or "Unknown"

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


@router.get("", response_model=list[PatientSummary])
async def list_patients(
    name: Optional[str] = Query(None, description="Partial name search"),
    count: int = Query(20, alias="_count", ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "clinician":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinician access required")

    params: dict = {
        "_count": count,
        "_elements": "id,name,birthDate,gender,telecom,address",
        "_has:Observation:patient:code": "39156-5",
    }
    if name:
        params["name"] = name

    bundle = await search_resource("Patient", params)
    entries = extract_bundle_entries(bundle)
    return [_simplify_patient(p) for p in entries]


@router.get("/high-risk")
async def get_high_risk_patients(
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "clinician":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinician access required")

    bundle = await search_resource("Observation", {
        "code": "4548-4,17856-6",
        "_sort": "-date",
        "_count": "200",
        "_include": "Observation:patient",
    })

    entries = bundle.get("entry", [])
    patients_by_id: dict = {}
    latest_obs_by_patient: dict = {}

    for entry in entries:
        resource = entry.get("resource", {})
        rt = resource.get("resourceType")
        if rt == "Patient":
            patients_by_id[resource["id"]] = resource
        elif rt == "Observation":
            value = resource.get("valueQuantity", {}).get("value")
            if value is None:
                continue
            patient_id = resource.get("subject", {}).get("reference", "").split("/")[-1]
            if patient_id not in latest_obs_by_patient:
                latest_obs_by_patient[patient_id] = {
                    "value": value,
                    "date": resource.get("effectiveDateTime", ""),
                }

    results = []
    for patient_id, obs in latest_obs_by_patient.items():
        if obs["value"] > 6.5:
            patient = patients_by_id.get(patient_id, {})
            name_list = patient.get("name", [])
            official = next((n for n in name_list if n.get("use") == "official"), None)
            name_entry = official or (name_list[0] if name_list else {})
            family = name_entry.get("family", "")
            given = " ".join(name_entry.get("given", []))
            full_name = f"{given} {family}".strip() or "Unknown"
            results.append({"id": patient_id, "full_name": full_name, "hba1c": obs["value"], "date": obs["date"]})

    results.sort(key=lambda x: x["hba1c"], reverse=True)
    return results[:5]


@router.get("/{patient_id}", response_model=PatientSummary)
async def get_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
):
    require_patient_access(patient_id, current_user)
    raw = await get_resource("Patient", patient_id)
    return _simplify_patient(raw)
