# Low-level wrapper around the HAPI FHIR R4 REST AP

import os
from typing import Optional

import httpx
from fastapi import HTTPException

_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=os.getenv("FHIR_BASE_URL", "http://localhost:8080/fhir"),
            headers={"Accept": "application/fhir+json"},
            timeout=15.0,
        )
    return _client

# Get a single FHIR resource by type + id
async def get_resource(resource_type: str, resource_id: str) -> dict:
    response = await _get_client().get(f"/{resource_type}/{resource_id}")
    _raise_for_fhir_error(response)
    return response.json()

# Search for FHIR resources with query parameters
async def search_resource(resource_type: str, params: dict) -> dict:
    response = await _get_client().get(f"/{resource_type}", params=params)
    _raise_for_fhir_error(response)
    return response.json()

# Raise an HTTPException for FHIR errors
def _raise_for_fhir_error(response: httpx.Response) -> None:
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Resource not found on FHIR server.")
    if response.status_code >= 400:
        try:
            issue = response.json().get("issue", [{}])[0].get("diagnostics", response.text)
        except Exception:
            issue = response.text
        raise HTTPException(status_code=response.status_code, detail=f"FHIR error: {issue}")

# Extract resource dicts out of a FHIR Bundle searchset
def extract_bundle_entries(bundle: dict) -> list[dict]:
    return [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]
