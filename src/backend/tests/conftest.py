import asyncpg
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

PATIENT_RESOURCE = {
    "resourceType": "Patient",
    "id": "patient-abc",
    "name": [{"use": "official", "family": "Doe", "given": ["Jane"]}],
    "birthDate": "1990-05-15",
    "gender": "female",
    "telecom": [{"system": "phone", "value": "555-1234"}],
    "address": [{"line": ["123 Main St"], "city": "Atlanta", "state": "GA"}],
}

PATIENT_BUNDLE = {
    "resourceType": "Bundle",
    "type": "searchset",
    "total": 1,
    "entry": [{"resource": PATIENT_RESOURCE}],
}

OBS_BUNDLE = {
    "resourceType": "Bundle",
    "type": "searchset",
    "entry": [
        {"resource": {
            "resourceType": "Observation",
            "id": "obs-glucose",
            "status": "final",
            "code": {"coding": [{"code": "2339-0", "display": "Glucose [Mass/volume] in Blood"}]},
            "subject": {"reference": "Patient/patient-abc"},
            "effectiveDateTime": "2024-03-01T08:00:00Z",
            "valueQuantity": {"value": 118.0, "unit": "mg/dL"},
        }},
        {"resource": {
            "resourceType": "Observation",
            "id": "obs-hba1c",
            "status": "final",
            "code": {"coding": [{"code": "4548-4", "display": "Hemoglobin A1c"}]},
            "subject": {"reference": "Patient/patient-abc"},
            "effectiveDateTime": "2024-03-01T08:00:00Z",
            "valueQuantity": {"value": 7.2, "unit": "%"},
        }},
    ],
}

MED_BUNDLE = {
    "resourceType": "Bundle",
    "type": "searchset",
    "entry": [
        {"resource": {
            "resourceType": "MedicationRequest",
            "id": "med-1",
            "status": "active",
            "subject": {"reference": "Patient/patient-abc"},
            "medicationCodeableConcept": {
                "text": "Metformin 500mg",
                "coding": [{"display": "Metformin"}],
            },
            "authoredOn": "2024-01-10",
            "dosageInstruction": [{"text": "1 tablet twice daily"}],
        }},
    ],
}

EMPTY_BUNDLE = {"resourceType": "Bundle", "type": "searchset", "entry": []}

def _make_pool():
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=None)
    conn.fetchrow = AsyncMock(return_value=None)

    acquire_ctx = AsyncMock()
    acquire_ctx.__aenter__ = AsyncMock(return_value=conn)
    acquire_ctx.__aexit__ = AsyncMock(return_value=False)

    pool = MagicMock()
    pool.acquire.return_value = acquire_ctx
    pool.close = AsyncMock()
    return pool, conn

# Patch asyncpg.create_pool and return the mock DB connection
@pytest.fixture()
def mock_pool(monkeypatch):

    pool, conn = _make_pool()
    monkeypatch.setattr(asyncpg, "create_pool", AsyncMock(return_value=pool))
    return conn

# Unauthenticated TestClient
@pytest.fixture()
def client(mock_pool):
    from main import app
    with TestClient(app) as c:
        yield c

# TestClient with get_current_user overridden to a clinician
@pytest.fixture()
def clinician_client(mock_pool):
    from main import app
    from auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1, "role": "clinician", "fhir_patient_id": None
    }
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# TestClient with get_current_user overridden
@pytest.fixture()
def patient_client(mock_pool):
    from main import app
    from auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 2, "role": "patient", "fhir_patient_id": "patient-abc"
    }
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
