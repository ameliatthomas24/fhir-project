from fastapi import APIRouter, Depends, Query

from auth import get_current_user, require_patient_access
from fhir_client import search_resource, extract_bundle_entries
from models import ConditionSummary

router = APIRouter()


def _simplify_condition(raw: dict) -> ConditionSummary:
    code_block = raw.get("code", {})
    display = (
        code_block.get("text")
        or (code_block.get("coding", [{}])[0].get("display"))
        or "Unknown"
    )

    subject_ref = raw.get("subject", {}).get("reference", "")
    patient_id = subject_ref.split("/")[-1] if "/" in subject_ref else subject_ref

    clinical_status = (
        raw.get("clinicalStatus", {})
        .get("coding", [{}])[0]
        .get("code")
    )

    onset = raw.get("onsetDateTime") or raw.get("onsetPeriod", {}).get("start")

    return ConditionSummary(
        id=raw.get("id", ""),
        patient_id=patient_id,
        display=display,
        onset_date=onset,
        clinical_status=clinical_status,
    )


@router.get("/{patient_id}", response_model=list[ConditionSummary])
async def get_conditions(
    patient_id: str,
    count: int = Query(50, alias="_count", ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    require_patient_access(patient_id, current_user)
    bundle = await search_resource("Condition", {
        "patient": patient_id,
        "clinical-status": "active",
        "_count": count,
    })
    entries = extract_bundle_entries(bundle)
    return [_simplify_condition(c) for c in entries]
