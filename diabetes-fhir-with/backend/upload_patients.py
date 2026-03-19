import os
import requests
import json

FHIR_URL = "http://localhost:8080/fhir"
DATA_PATH = r"C:\Users\ameli\Downloads\diabetes-fhir-project\data\output\fhir"

def upload_bundle(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            bundle = json.load(f)
            headers = {
                'Content-Type': 'application/fhir+json',
                'Accept': 'application/fhir+json',
            }
            response = requests.post(FHIR_URL, json=bundle, headers=headers, timeout=60)

            if response.status_code in [200, 201]:
                print(f"Success: {os.path.basename(file_path)}")
            elif response.status_code == 400:
                print(f"400 Bad Request: {os.path.basename(file_path)}")
                print(f"   {response.text[:300]}")
            else:
                print(f"Failed {os.path.basename(file_path)}: {response.status_code}")
                print(f"   {response.text[:150]}")
        except json.JSONDecodeError as e:
            print(f"JSON parse error in {os.path.basename(file_path)}: {e}")
        except requests.exceptions.ConnectionError:
            print("Could not connect — is Docker running?")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    if not os.path.exists(DATA_PATH):
        print(f"Folder not found at: {DATA_PATH}")
    else:
        files = [f for f in os.listdir(DATA_PATH) if f.endswith(".json")]
        files.sort(key=lambda x: ("hospital" not in x and "practitioner" not in x))
        print(f"Found {len(files)} files. Starting upload...")
        for filename in files:
            upload_bundle(os.path.join(DATA_PATH, filename))