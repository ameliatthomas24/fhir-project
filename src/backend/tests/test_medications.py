# Integration tests for GET /medications
import pytest
from unittest.mock import AsyncMock

import routers.medications as med_router
from tests.conftest import MED_BUNDLE, EMPTY_BUNDLE


@pytest.fixture(autouse=True)
def mock_fhir(monkeypatch):
    monkeypatch.setattr(med_router, "search_resource", AsyncMock(return_value=MED_BUNDLE))


def test_get_medications_returns_results(clinician_client):
    resp = clinician_client.get("/medications/patient-abc")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["medication_name"] == "Metformin 500mg"


def test_get_medications_maps_fields(clinician_client):
    med = clinician_client.get("/medications/patient-abc").json()[0]
    assert med["id"] == "med-1"
    assert med["status"] == "active"
    assert med["patient_id"] == "patient-abc"
    assert med["authored_on"] == "2024-01-10"
    assert med["dosage_instruction"] == "1 tablet twice daily"


def test_get_medications_patient_own(patient_client):
    resp = patient_client.get("/medications/patient-abc")
    assert resp.status_code == 200


def test_get_medications_patient_other_forbidden(patient_client):
    resp = patient_client.get("/medications/some-other-patient")
    assert resp.status_code == 403


def test_get_medications_empty_returns_list(clinician_client, monkeypatch):
    monkeypatch.setattr(med_router, "search_resource", AsyncMock(return_value=EMPTY_BUNDLE))
    resp = clinician_client.get("/medications/patient-abc")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_medications_sorted_by_date(clinician_client, monkeypatch):
    mock = AsyncMock(return_value=EMPTY_BUNDLE)
    monkeypatch.setattr(med_router, "search_resource", mock)
    clinician_client.get("/medications/patient-abc")
    params = mock.call_args[0][1]
    assert params.get("_sort") == "-authoredon"



# GET /medications

def test_get_active_medications_sends_status_filter(clinician_client, monkeypatch):
    mock = AsyncMock(return_value=EMPTY_BUNDLE)
    monkeypatch.setattr(med_router, "search_resource", mock)
    clinician_client.get("/medications/patient-abc/active")
    params = mock.call_args[0][1]
    assert params.get("status") == "active"


def test_get_active_medications_returns_results(clinician_client):
    resp = clinician_client.get("/medications/patient-abc/active")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_active_medications_patient_own(patient_client):
    resp = patient_client.get("/medications/patient-abc/active")
    assert resp.status_code == 200


def test_get_active_medications_patient_other_forbidden(patient_client):
    resp = patient_client.get("/medications/other-patient/active")
    assert resp.status_code == 403

# Medication name 

def test_medication_name_from_reference(clinician_client, monkeypatch):
    bundle = {
        "resourceType": "Bundle",
        "entry": [{"resource": {
            "resourceType": "MedicationRequest",
            "id": "med-ref",
            "status": "active",
            "subject": {"reference": "Patient/patient-abc"},
            "medicationReference": {"display": "Insulin glargine"},
        }}],
    }
    monkeypatch.setattr(med_router, "search_resource", AsyncMock(return_value=bundle))
    resp = clinician_client.get("/medications/patient-abc")
    assert resp.json()[0]["medication_name"] == "Insulin glargine"


def test_medication_name_unknown_fallback(clinician_client, monkeypatch):
    bundle = {
        "resourceType": "Bundle",
        "entry": [{"resource": {
            "resourceType": "MedicationRequest",
            "id": "med-x",
            "status": "active",
            "subject": {"reference": "Patient/patient-abc"},
        }}],
    }
    monkeypatch.setattr(med_router, "search_resource", AsyncMock(return_value=bundle))
    resp = clinician_client.get("/medications/patient-abc")
    assert resp.json()[0]["medication_name"] == "Unknown"
