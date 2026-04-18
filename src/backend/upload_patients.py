import os
import requests
import json

# --- CONFIG ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.getenv("DATA_PATH", "/app/data_files") 
FHIR_URL = os.getenv("FHIR_BASE_URL", "http://hapi-fhir-server:8080/fhir")

def start_upload():
    if not os.path.exists(DATA_PATH):
        print(f"❌ Folder not found: {DATA_PATH}")
        return

    json_files = [f for f in os.listdir(DATA_PATH) if f.endswith(".json")]
    print(f"📊 Found {len(json_files)} files. Starting local upload...")

    success, fail = 0, 0

    for i, filename in enumerate(json_files):
        with open(os.path.join(DATA_PATH, filename), 'r', encoding='utf-8') as f:
            try:
                bundle = json.load(f)
                # Find the Patient resource in the bundle
                entry = next((e for e in bundle.get('entry', []) 
                             if e.get('resource', {}).get('resourceType') == 'Patient'), None)
                
                if entry:
                    patient = entry['resource']
                    p_id = patient.get('id')
                    # Use PUT to ensure IDs match your local frontend expectations
                    resp = requests.put(f"{FHIR_URL}/Patient/{p_id}", json=patient, timeout=5)
                    
                    if resp.status_code in [200, 201]:
                        success += 1
                        print(f"[{i+1}] ✅ {p_id}")
                    else:
                        fail += 1
                        print(f"[{i+1}] ❌ {p_id}: {resp.status_code}")

            except Exception as e:
                fail += 1
                print(f"Error on {filename}: {e}")

    print(f"\nDONE. Success: {success}, Failed: {fail}")

if __name__ == "__main__":
    start_upload()