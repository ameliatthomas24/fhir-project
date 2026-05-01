# ntegration tests for authentication
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from tests.conftest import PATIENT_BUNDLE


# Health
def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# Login Checks
def test_login_success_clinician(client, mock_pool):
    from auth import hash_password
    mock_pool.fetchrow.return_value = {
        "id": 1,
        "hashed_password": hash_password("clinician123"),
        "role": "clinician",
        "fhir_patient_id": None,
    }
    resp = client.post("/auth/login", json={"email": "clinician@demo.com", "password": "clinician123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["role"] == "clinician"
    assert body["token_type"] == "bearer"


def test_login_success_patient(client, mock_pool):
    from auth import hash_password
    mock_pool.fetchrow.return_value = {
        "id": 2,
        "hashed_password": hash_password("patient123"),
        "role": "patient",
        "fhir_patient_id": "patient-abc",
    }
    resp = client.post("/auth/login", json={"email": "patient1@demo.com", "password": "patient123"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "patient"


def test_login_wrong_password(client, mock_pool):
    from auth import hash_password
    mock_pool.fetchrow.return_value = {
        "id": 1,
        "hashed_password": hash_password("correct-password"),
        "role": "clinician",
        "fhir_patient_id": None,
    }
    resp = client.post("/auth/login", json={"email": "clinician@demo.com", "password": "wrong-password"})
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


def test_login_unknown_email(client, mock_pool):
    mock_pool.fetchrow.return_value = None  # user not found
    resp = client.post("/auth/login", json={"email": "nobody@demo.com", "password": "any"})
    assert resp.status_code == 401


def test_no_token_returns_4xx(client):
    resp = client.get("/patients")
    assert resp.status_code in (401, 403)


def test_malformed_token_returns_401(client):
    resp = client.get("/patients", headers={"Authorization": "Bearer not.a.real.jwt"})
    assert resp.status_code == 401


def test_valid_token_clinician_can_reach_patients(clinician_client, monkeypatch):
    import routers.patients as p
    monkeypatch.setattr(p, "search_resource", AsyncMock(return_value={"resourceType": "Bundle", "entry": []}))
    resp = clinician_client.get("/patients")
    assert resp.status_code == 200


def test_patient_token_cannot_list_all_patients(patient_client, monkeypatch):
    resp = patient_client.get("/patients")
    assert resp.status_code == 403

def test_token_round_trip(client, monkeypatch):
    from auth import hash_password
    client.app.state.db_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = {
        "id": 1,
        "hashed_password": hash_password("clinician123"),
        "role": "clinician",
        "fhir_patient_id": None,
    }
    login_resp = client.post("/auth/login", json={"email": "clinician@demo.com", "password": "clinician123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    import routers.patients as p
    monkeypatch.setattr(p, "search_resource", AsyncMock(return_value={"resourceType": "Bundle", "entry": []}))
    patients_resp = client.get("/patients", headers={"Authorization": f"Bearer {token}"})
    assert patients_resp.status_code == 200
