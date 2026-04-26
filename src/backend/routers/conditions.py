from fastapi import APIRouter, Depends, Query

from auth import get_current_user, require_patient_access
from fhir_client import search_resource, extract_bundle_entries
from models import ConditionSummary

router = APIRouter()

# These are not clinical diagnoses and should not appear in the problem list
_SOCIAL_DETERMINANT_CODES = {
    "160903007", "160904001", "73438004",   # employment status
    "741062008", "160968000",               # not in labour force / risk activity
    "224663009", "160498000", "473137001",  # education level
    "224362006", "105539002", "473461003",  # education
    "713458007", "415510000", "266934004",  # transportation / access
    "422587007", "32911000", "422650009", "423315002",  # social isolation
    "445281000124101", "428361000124107",   # medication review
    "706893006", "248591000",               # IPV / abuse
    "228273003",                            # unhealthy alcohol
    "736236007", "73595000",               # stress
    "446654005",                            # refugee
}


_HIDE_SNOMED_TYPES = ("(person)", "(situation)", "(observable entity)", "(regime/therapy)")
# LLM was used to narrow down the list of keywords
_SOCIAL_KEYWORDS = (
    "employed", "employment", "labor force", "labour force",
    "school level", "education (", "educated to",
    "transport", "housing unsatisfactory", "housing problem",
    "criminal record", "legal",
    "social isolation", "social contact", "limited social",
    "medication review due",
    "received higher education", "received primary", "received secondary",
    "refugee", "risk activity",
    "stress (finding)", "homeless",
    "unhealthy alcohol", "alcohol misuse",
    "not in labor", "not in labour",
    "intimate partner",
)


def _is_clinical(raw: dict) -> bool:
    """Return False for social-determinant, administrative, or demographic conditions."""
    for coding in raw.get("code", {}).get("coding", []):
        if coding.get("code") in _SOCIAL_DETERMINANT_CODES:
            return False

    display = (
        raw.get("code", {}).get("text") or
        raw.get("code", {}).get("coding", [{}])[0].get("display", "")
    ).lower()

    # Hide by SNOMED semantic type suffix — catches (person), (situation), etc.
    if any(display.endswith(t) for t in _HIDE_SNOMED_TYPES):
        return False

    return not any(kw in display for kw in _SOCIAL_KEYWORDS)


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
