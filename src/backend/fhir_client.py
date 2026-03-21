"""
Low-level wrapper around the HAPI FHIR R4 REST API. All routes import this to avoid repeating HTTP logic.
"""

import os
import httpx
from fastapi import HTTPException

FHIR_BASE_URL = os.getenv("FHIR_BASE_URL", "http://localhost:8080/fhir")

_client = httpx.AsyncClient(
    base_url=FHIR_BASE_URL,
    headers={"Accept": "application/fhir+json"},
    timeout=15.0,
)

async def get_resource(resource_type: str, resource_id: str) -> dict:
    """Fetch a single FHIR resource by type + id."""
    url = f"/{resource_type}/{resource_id}"
    response = await _client.get(url)
    _raise_for_fhir_error(response)
    return response.json()


async def search_resource(resource_type: str, params: dict) -> dict:
    """Search for FHIR resources with query parameters."""
    url = f"/{resource_type}"
    response = await _client.get(url, params=params)
    _raise_for_fhir_error(response)
    return response.json()


def _raise_for_fhir_error(response: httpx.Response) -> None:
    """Translate FHIR / HTTP errors into FastAPI HTTPExceptions."""
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Resource not found on FHIR server.")
    if response.status_code >= 400:
        try:
            issue = response.json().get("issue", [{}])[0].get("diagnostics", response.text)
        except Exception:
            issue = response.text
        raise HTTPException(status_code=response.status_code, detail=f"FHIR error: {issue}")


def extract_bundle_entries(bundle: dict) -> list[dict]:
    """Pull resource dicts out of a FHIR Bundle searchset."""
    return [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]