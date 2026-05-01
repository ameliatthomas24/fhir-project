import os
import json
import requests

DATA_PATH = os.getenv("DATA_PATH", "/app/data_files")
FHIR_URL = os.getenv("FHIR_BASE_URL", "http://hapi-fhir-server:8080/fhir")

_KEEP_TYPES = {
    "Patient", "Observation", "Condition", "MedicationRequest", "Medication",
    "Encounter", "Procedure", "Immunization"
}

_KEEP_OBS_CODES = {
    "4548-4", "17856-6",
    "2339-0", "15074-8",
    "39156-5",
    "85354-9", "55284-4",
    "8480-6", "8462-4",
    "8867-4",
    "29463-7", "3141-9",
    "8302-2",
    "2089-1", "18262-6",
    "2085-9",
    "2571-8",
    "2093-3",
    "718-7", "6690-2", "789-8",
    "20570-8", "4544-3",
    "777-3",
    "38483-4", "6299-2",
    "2947-0", "6298-4",
}

def _strip_conditional_refs(obj):
    if isinstance(obj, dict):
        return {
            k: _strip_conditional_refs(v)
            for k, v in obj.items()
            if not (k == "reference" and isinstance(v, str) and "?" in v)
        }
    if isinstance(obj, list):
        return [_strip_conditional_refs(item) for item in obj]
    return obj

def _obs_code(resource: dict) -> str:
    return resource.get("code", {}).get("coding", [{}])[0].get("code", "")

def _obs_date(resource: dict) -> str:
    return resource.get("effectiveDateTime") or resource.get("effectivePeriod", {}).get("start", "")

def _prepare_transaction(bundle: dict) -> dict:
    obs_by_code: dict[str, list] = {}
    other_entries = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        rt = resource.get("resourceType", "")
        if rt not in _KEEP_TYPES:
            continue

        if rt == "Observation":
            code = _obs_code(resource)
            if code not in _KEEP_OBS_CODES:
                continue
            obs_by_code.setdefault(code, []).append(entry)
        else:
            other_entries.append(entry)

    kept = []
    for entry in other_entries:
        resource = entry.get("resource", {})
        rt = resource.get("resourceType", "")
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

    for code, entries in obs_by_code.items():
        recent = sorted(entries, key=lambda e: _obs_date(e.get("resource", {})), reverse=True)[:15]
        for entry in recent:
            kept.append({
                "fullUrl": entry.get("fullUrl"),
                "resource": _strip_conditional_refs(entry.get("resource", {})),
                "request": entry.get("request", {"method": "POST", "url": "Observation"}),
            })

    return {"resourceType": "Bundle", "type": "transaction", "entry": kept}

def _upload_one(i, total, filename, counters):
    filepath = os.path.join(DATA_PATH, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw_bundle = json.load(f)

        tx = _prepare_transaction(raw_bundle)
        if not tx["entry"]:
            return

        resp = requests.post(
            FHIR_URL,
            json=tx,
            headers={"Content-Type": "application/fhir+json"},
            timeout=60,
        )

        if resp.status_code in (200, 201):
            counters["success"] += 1
            patient_id = next(
                (e["resource"]["id"] for e in tx["entry"]
                 if e["resource"]["resourceType"] == "Patient"),
                "unknown",
            )
            counts = {}
            for e in tx["entry"]:
                counts[e["resource"]["resourceType"]] = counts.get(e["resource"]["resourceType"], 0) + 1
            summary = " ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
            print(f"[{i}/{total}] OK  {patient_id}  ({summary})")
        else:
            counters["fail"] += 1
            try:
                diag = resp.json()["issue"][0].get("diagnostics", resp.text)
            except Exception:
                diag = resp.text
            print(f"[{i}/{total}] FAIL {filename}: HTTP {resp.status_code} {diag[:200]}")

    except Exception as e:
        counters["fail"] += 1
        print(f"[{i}/{total}] ERROR {filename}: {e}")

def start_upload():
    if not os.path.exists(DATA_PATH):
        print(f"Folder not found: {DATA_PATH}")
        return

    json_files = sorted(f for f in os.listdir(DATA_PATH) if f.endswith(".json"))
    total = len(json_files)
    print(f"Found {total} bundles. Uploading sequentially...")

    counters = {"success": 0, "fail": 0}

    for i, fn in enumerate(json_files, 1):
        _upload_one(i, total, fn, counters)

    print(f"\nDone. Success: {counters['success']}  Failed: {counters['fail']}")

if __name__ == "__main__":
    start_upload()