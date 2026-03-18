import os
import requests
import json

FHIR_URL = "http://localhost:8080/fhir"
DATA_PATH = r"C:\Users\ameli\Downloads\diabetes-fhir-project\data\output\fhir"

def upload_bundle(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            bundle = json.load(f)
            headers = {'Content-Type': 'application/fhir+json'}
            
            response = requests.post(FHIR_URL, json=bundle, headers=headers, timeout=30)

            if response.status_code in [200, 201]:
                print(f"✅ Success: {os.path.basename(file_path)}")
            else:
                print(f"❌ Failed {os.path.basename(file_path)}: Status {response.status_code}")
                print(f"   Server says: {response.text[:100]}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if not os.path.exists(DATA_PATH):
        print(f"Folder not found at: {DATA_PATH}")
    else:
        files = [f for f in os.listdir(DATA_PATH) if f.endswith(".json")]
        print(f"Found {len(files)} files. Starting...")
        for filename in files:
            upload_bundle(os.path.join(DATA_PATH, filename))