import os
import json
import requests

DATA_PATH = os.getenv("DATA_PATH", "/app/data_files")
FHIR_URL = os.getenv("FHIR_BASE_URL", "http://hapi-fhir-server:8080/fhir")

# Only upload resource types the portal actually uses.
# Skipping financial/admin types that cause validation errors and aren't needed.
_KEEP_TYPES = {
    "Patient", "Observation", "Condition", "MedicationRequest",
    "Encounter", "Procedure", "Immunization",
}


def _strip_conditional_refs(obj):
    """Recursively remove any reference fields that use conditional lookup syntax.
    e.g. 'Practitioner?identifier=...' — these 404 because practitioners aren't loaded."""
    if isinstance(obj, dict):
        return {
            k: _strip_conditional_refs(v)
            for k, v in obj.items()
            if not (k == "reference" and isinstance(v, str) and "?" in v)
        }
    if isinstance(obj, list):
        return [_strip_conditional_refs(item) for item in obj]
    return obj


def _prepare_transaction(bundle: dict) -> dict:
    """
    Build a clean transaction bundle from a Synthea bundle.
    - Preserves fullUrl so internal urn:uuid references resolve correctly.
    - Converts Patient to PUT (preserves the original patient ID).
    - All other resources stay as POST (Synthea's default).
    - Drops resource types not used by the portal.
    """
    kept = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        rt = resource.get("resourceType", "")
        if rt not in _KEEP_TYPES:
            continue

        rid = resource.get("id")
        if rt == "Patient" and rid:
            request = {"method": "PUT", "url": f"Patient/{rid}"}
        else:
            request = entry.get("request", {"method": "POST", "url": rt})

        kept.append({
            "fullUrl": entry.get("fullUrl"),
            "resource": _strip_conditional_refs(resource),
            "request": request,
        })

    return {"resourceType": "Bundle", "type": "transaction", "entry": kept}


def start_upload():
    if not os.path.exists(DATA_PATH):
        print(f"Folder not found: {DATA_PATH}")
        return

    json_files = sorted(f for f in os.listdir(DATA_PATH) if f.endswith(".json"))
    total = len(json_files)
    print(f"Found {total} bundles. Uploading clinical resources...")

    success, fail = 0, 0

    for i, filename in enumerate(json_files, 1):
        filepath = os.path.join(DATA_PATH, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_bundle = json.load(f)

            tx = _prepare_transaction(raw_bundle)
            if not tx["entry"]:
                continue

            resp = requests.post(
                FHIR_URL,
                json=tx,
                headers={"Content-Type": "application/fhir+json"},
                timeout=30,
            )

            if resp.status_code in (200, 201):
                success += 1
                patient_id = next(
                    (e["resource"]["id"] for e in tx["entry"]
                     if e["resource"]["resourceType"] == "Patient"),
                    "unknown",
                )
                counts = {}
                for e in tx["entry"]:
                    counts[e["resource"]["resourceType"]] = counts.get(e["resource"]["resourceType"], 0) + 1
                summary = ", ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
                print(f"[{i}/{total}] OK  {patient_id}  ({summary})")
            else:
                fail += 1
                try:
                    diag = resp.json()["issue"][0].get("diagnostics", resp.text)
                except Exception:
                    diag = resp.text
                print(f"[{i}/{total}] FAIL {filename}: HTTP {resp.status_code} — {diag[:200]}")

        except Exception as e:
            fail += 1
            print(f"[{i}/{total}] ERROR {filename}: {e}")

    print(f"\nDone. Success: {success}  Failed: {fail}")


if __name__ == "__main__":
    start_upload()
