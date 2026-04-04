# Diabetes Management Portal

A web-based health portal for diabetes management built for the Georgia Tech CS-6440 (Intro Health Informatics) practicum group project. The platform supports both clinicians and patients through role-specific dashboards, integrating real clinical data via HL7 FHIR with predictive analytics and AI-generated preventative care recommendations.

**Team:** Yovindu Don, Wei Dou, Bryanna Lawton, Reshmasai Malleedi, Amelia Thomas

---

## Features

### Clinician Portal
- Multi-patient search and selection
- Patient demographics and clinical summary header
- Blood glucose timeline chart with target range visualization
- Labs panel: HbA1c, LDL, HDL, Triglycerides with threshold indicators
- Risk forecast: Cardiovascular, Neuropathy, Retinopathy
- Full lab results table and active medications list
- ML-based diabetes risk score with contributing factors (XGBoost)
- Appointment scheduling
- Inbox and messaging capabilities with care providers
- AI-generated preventative care recommendations (Gemini)

### Patient Portal
- Personal health overview with key vitals
- Medication history
- Appointment scheduling
- Inbox and messaging capabilities with care providers
- AI-generated personalized care plan (diet, exercise, monitoring, lifestyle)

---

## Project Checklist

### Infrastructure
- [x] PPT-5: Deploy HAPI FHIR server and PostgreSQL via Docker
- [x] PPT-6: Generate 200+ synthetic diabetic patient records with Synthea
- [x] PPT-7: Repository setup with branching workflow
- [x] PPT-3: CI/CD pipeline (GitHub Actions)

### Backend
- [x] PPT-1: FastAPI FHIR data service (Patient, Observation, MedicationRequest)
- [x] PPT-9: Diabetes risk prediction engine (XGBoost ML model)
- [x] PPT-10: Preventative care recommendation engine (Gemini LLM)

### Frontend
- [x] PPT-8: UI/UX wireframes (Figma)
- [x] PPT-2: React frontend — patient search and patient header with clinical summary
- [x] PPT-4: Clinical data visualization (blood glucose timeline chart)

### Remaining
- [ ] PPT-11: Appointment scheduling (FHIR Appointment resources)
- [ ] PPT-12: Integration testing
- [ ] PPT-13: Final deployment

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| ML | XGBoost, Scikit-learn, Pandas |
| LLM | Google Gemini API (`gemini-1.5-flash`) |
| FHIR Server | HAPI FHIR R4 |
| Database | PostgreSQL (via Supabase) |
| Containerization | Docker |
| Synthetic Data | Synthea |

---

## Setup

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- Python 3.11+
- Node.js 18+

### 1. Clone the repository

```bash
git clone https://github.com/ameliatthomas24/fhir-project.git
cd fhir-project
```

### 2. Start the HAPI FHIR server

```bash
cd src/infra
docker compose up
```

Wait for the server to fully start (30–60 seconds) — it's ready when you see `Started Application` in the logs. The FHIR server runs on `http://localhost:8080/fhir`.

### 3. Load synthetic patient data

```bash
cd src/backend
python upload_patients.py
```

### 4. Configure environment variables

```bash
cp src/backend/.env.example src/backend/.env
```

Open `src/backend/.env` and fill in:

```
FHIR_BASE_URL=http://localhost:8080/fhir
GEMINI_API_KEY=your_gemini_api_key_here
```

To get a Gemini API key, visit [Google AI Studio](https://aistudio.google.com/app/apikey).

### 5. Start the backend

```bash
cd src/backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs on `http://localhost:8000`. Interactive docs available at `http://localhost:8000/docs`.

### 6. Start the frontend

```bash
cd src/frontend
npm install
npm run dev
```

The app runs on `http://localhost:3000`.

---

## Project Structure

```
fhir-project/
├── data/
│   └── output/fhir/        # Synthea-generated patient bundles
├── src/
│   ├── backend/
│   │   ├── routers/
│   │   │   ├── patients.py
│   │   │   ├── observations.py
│   │   │   ├── medications.py
│   │   │   ├── predict.py
│   │   │   └── recommendations.py
│   │   ├── ml/             # XGBoost model and training scripts
│   │   ├── main.py
│   │   ├── fhir_client.py
│   │   ├── models.py
│   │   └── requirements.txt
│   ├── frontend/
│   │   └── src/
│   │       ├── components/ # PatientSearch, PatientRecord, CareRecommendations
│   │       ├── api/        # FHIR API client
│   │       └── types/      # TypeScript interfaces
│   └── infra/
│       └── docker-compose.yaml
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/patients` | Search patients by name |
| GET | `/patients/{id}` | Get patient by ID |
| GET | `/observations/{patient_id}` | All observations for a patient |
| GET | `/observations/{patient_id}/glucose` | Glucose readings |
| GET | `/observations/{patient_id}/hba1c` | HbA1c readings |
| GET | `/observations/{patient_id}/blood-pressure` | Blood pressure readings |
| GET | `/medications/{patient_id}` | All medications |
| GET | `/medications/{patient_id}/active` | Active medications only |
| GET | `/predict/{patient_id}` | ML diabetes risk score |
| GET | `/recommendations/{patient_id}` | AI care recommendations |
