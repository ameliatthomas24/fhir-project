from fastapi import APIRouter, Depends, Query

from auth import get_current_user, require_patient_access
from fhir_client import search_resource, extract_bundle_entries
from models import ConditionSummary

router = APIRouter()

# Social determinant / administrative SNOMED codes Synthea adds as conditions.
# These are not clinical diagnoses and should not appear in the problem list.
_SOCIAL_DETERMINANT_CODES = {
    "160903007", "160904001", "73438004",   # employment status
    "224663009", "160498000", "473137001",  # education level
    "224362006", "105539002",               # education
    "713458007", "415510000",               # transportation / access
    "422587007", "32911000",                # social isolation / homelessness
    "445281000124101", "428361000124107",   # medication review
    "706893006", "248591000",               # IPV / abuse
    "228273003",                            # unhealthy alcohol
    "736236007",                            # mental stress (general)
}


def _is_clinical(raw: dict) -> bool:
    """Return False for pure social-determinant or administrative conditions."""
    for coding in raw.get("code", {}).get("coding", []):
        if coding.get("code") in _SOCIAL_DETERMINANT_CODES:
            return False
    display = (
        raw.get("code", {}).get("text") or
        raw.get("code", {}).get("coding", [{}])[0].get("display", "")
    ).lower()
    # Exclude purely administrative findings Synthea creates
    social_keywords = (
        "employed", "employment", "school level", "education (", "educated to",
        "transportation", "social isolation", "social contact", "medication review due",
        "received higher education", "received primary", "received secondary",
        "limited social",
    )
    return not any(kw in display for kw in social_keywords)


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
    return [_simplify_condition(c) for c in entries if _is_clinical(c)]
