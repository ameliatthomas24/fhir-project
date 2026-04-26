# Integration tests for GET /observations
import pytest
from unittest.mock import AsyncMock

import routers.observations as obs_router
from tests.conftest import OBS_BUNDLE, EMPTY_BUNDLE


@pytest.fixture(autouse=True)
def mock_fhir(monkeypatch):
    monkeypatch.setattr(obs_router, "search_resource", AsyncMock(return_value=OBS_BUNDLE))

# GET /observations

def test_get_observations_clinician(clinician_client):
    resp = clinician_client.get("/observations/patient-abc")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_get_observations_maps_fields(clinician_client):
    obs = clinician_client.get("/observations/patient-abc").json()[0]
    assert obs["code"] == "2339-0"
    assert obs["display"] == "Glucose [Mass/volume] in Blood"
    assert obs["value"] == 118.0
    assert obs["unit"] == "mg/dL"
    assert obs["patient_id"] == "patient-abc"
    assert obs["status"] == "final"


def test_get_observations_patient_own(patient_client):
    resp = patient_client.get("/observations/patient-abc")
    assert resp.status_code == 200


def test_get_observations_patient_other_forbidden(patient_client):
    resp = patient_client.get("/observations/some-other-patient")
    assert resp.status_code == 403


def test_get_observations_empty_returns_list(clinician_client, monkeypatch):
    monkeypatch.setattr(obs_router, "search_resource", AsyncMock(return_value=EMPTY_BUNDLE))
    resp = clinician_client.get("/observations/patient-abc")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_glucose_passes_loinc_codes(clinician_client, monkeypatch):
    mock = AsyncMock(return_value=EMPTY_BUNDLE)
    monkeypatch.setattr(obs_router, "search_resource", mock)
    clinician_client.get("/observations/patient-abc/glucose")
    params = mock.call_args[0][1]
    assert "15074-8" in params["code"] or "2339-0" in params["code"]


def test_get_glucose_patient_own(patient_client):
    resp = patient_client.get("/observations/patient-abc/glucose")
    assert resp.status_code == 200


def test_get_glucose_patient_other_forbidden(patient_client):
    resp = patient_client.get("/observations/other-patient/glucose")
    assert resp.status_code == 403


def test_get_hba1c_returns_filtered_obs(clinician_client, monkeypatch):
    mock = AsyncMock(return_value=EMPTY_BUNDLE)
    monkeypatch.setattr(obs_router, "search_resource", mock)
    clinician_client.get("/observations/patient-abc/hba1c")
    params = mock.call_args[0][1]
    assert "4548-4" in params["code"] or "17856-6" in params["code"]


def test_get_hba1c_access_control(patient_client):
    resp = patient_client.get("/observations/other/hba1c")
    assert resp.status_code == 403


def test_get_blood_pressure_passes_loinc_codes(clinician_client, monkeypatch):
    mock = AsyncMock(return_value=EMPTY_BUNDLE)
    monkeypatch.setattr(obs_router, "search_resource", mock)
    clinician_client.get("/observations/patient-abc/blood-pressure")
    params = mock.call_args[0][1]
    bp_codes = {"55284-4", "8480-6", "8462-4"}
    sent_codes = set(params["code"].split(","))
    assert sent_codes & bp_codes


def test_get_blood_pressure_sorted_by_date(clinician_client, monkeypatch):
    mock = AsyncMock(return_value=EMPTY_BUNDLE)
    monkeypatch.setattr(obs_router, "search_resource", mock)
    clinician_client.get("/observations/patient-abc/blood-pressure")
    params = mock.call_args[0][1]
    assert params.get("_sort") == "-date"


def test_get_blood_pressure_access_control(patient_client):
    resp = patient_client.get("/observations/other/blood-pressure")
    assert resp.status_code == 403
