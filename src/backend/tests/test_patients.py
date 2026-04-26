# Integration tests for GET /patients 
import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException

import routers.patients as patients_router
from tests.conftest import PATIENT_BUNDLE, PATIENT_RESOURCE, EMPTY_BUNDLE


@pytest.fixture(autouse=True)
def mock_fhir(monkeypatch):
    monkeypatch.setattr(patients_router, "search_resource", AsyncMock(return_value=PATIENT_BUNDLE))
    monkeypatch.setattr(patients_router, "get_resource", AsyncMock(return_value=PATIENT_RESOURCE))

# GET /patients  

def test_list_patients_returns_results(clinician_client):
    resp = clinician_client.get("/patients")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "patient-abc"
    assert data[0]["full_name"] == "Jane Doe"


def test_list_patients_gender_and_dob(clinician_client):
    resp = clinician_client.get("/patients")
    assert resp.status_code == 200
    p = resp.json()[0]
    assert p["gender"] == "female"
    assert p["birth_date"] == "1990-05-15"


def test_list_patients_address_mapping(clinician_client):
    resp = clinician_client.get("/patients")
    assert resp.json()[0]["address"] == "123 Main St, Atlanta, GA"


def test_list_patients_empty_bundle(clinician_client, monkeypatch):
    monkeypatch.setattr(patients_router, "search_resource", AsyncMock(return_value=EMPTY_BUNDLE))
    resp = clinician_client.get("/patients")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_patients_name_param_forwarded(clinician_client, monkeypatch):
    mock = AsyncMock(return_value=EMPTY_BUNDLE)
    monkeypatch.setattr(patients_router, "search_resource", mock)
    clinician_client.get("/patients?name=Doe")
    call_params = mock.call_args[0][1]
    assert call_params.get("name") == "Doe"


def test_list_patients_elements_param_always_set(clinician_client, monkeypatch):
    mock = AsyncMock(return_value=EMPTY_BUNDLE)
    monkeypatch.setattr(patients_router, "search_resource", mock)
    clinician_client.get("/patients")
    call_params = mock.call_args[0][1]
    assert "_elements" in call_params


def test_list_patients_patient_role_forbidden(patient_client):
    resp = patient_client.get("/patients")
    assert resp.status_code == 403


def test_get_patient_clinician(clinician_client):
    resp = clinician_client.get("/patients/patient-abc")
    assert resp.status_code == 200
    assert resp.json()["id"] == "patient-abc"


def test_get_patient_phone(clinician_client):
    resp = clinician_client.get("/patients/patient-abc")
    assert resp.json()["phone"] == "555-1234"


def test_get_patient_own_data_allowed(patient_client):
    resp = patient_client.get("/patients/patient-abc")
    assert resp.status_code == 200


def test_get_patient_other_patient_forbidden(patient_client):
    resp = patient_client.get("/patients/some-other-patient")
    assert resp.status_code == 403


def test_get_patient_not_found(clinician_client, monkeypatch):
    monkeypatch.setattr(
        patients_router, "get_resource",
        AsyncMock(side_effect=HTTPException(status_code=404, detail="Resource not found"))
    )
    resp = clinician_client.get("/patients/nonexistent")
    assert resp.status_code == 404


def test_get_patient_name_fallback(clinician_client, monkeypatch):
    minimal = {"resourceType": "Patient", "id": "x", "name": [], "gender": "unknown"}
    monkeypatch.setattr(patients_router, "get_resource", AsyncMock(return_value=minimal))
    resp = clinician_client.get("/patients/x")
    assert resp.json()["full_name"] == "Unknown"
