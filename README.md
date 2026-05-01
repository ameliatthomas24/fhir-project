# Diabetes Management Portal

A web-based health portal for diabetes management built for the Georgia Tech CS-6440 (Intro Health Informatics) practicum group project. The platform supports both clinicians and patients through role-specific dashboards, integrating real clinical data via HL7 FHIR with predictive analytics and AI-generated preventative care recommendations.

**Team:** Yovindu Don, Wei Dou, Bryanna Lawton, Reshmasai Malleedi, Amelia Thomas

---

## Deployment
Our application is deployed at: www.healthybean.me
To log in, use the following credentials:
Username: clinician@demo.com
Password: clinician123

## Features

### Portal Overview
- Multi-patient search and selection
- Patient demographics and clinical history (vitals, active medications)
- Blood glucose and HbA1c timeline charts with target range visualization
- Labs panel: HbA1c, LDL, HDL, Triglycerides with threshold indicators and progress bars
- Risk forecast panels: Cardiovascular, Neuropathy, Retinopathy
- Full lab results table and active medications list
- Active conditions list (clinical conditions only — social determinants filtered out)
- ML-based diabetes risk score with top contributing factors (built using XGBoost)
- AI-generated preventative care recommendations by category and priority (built using Gemini)
- AI health assistant chat with patient context
- Appointment scheduling with date, time, type (in-person/virtual), and reason
- Clinical notes with timestamped author attribution
- Bidirectional inbox: receive patient messages, reply, and send proactive messages to patients
- Appointment scheduling triggers automatic inbox notification to the patient

---

## Project Checklist

### Infrastructure
- [x] PPT-5: Deploy HAPI FHIR server and PostgreSQL via Docker
- [x] PPT-6: Generate 200+ synthetic diabetic patient records with Synthea
- [x] PPT-7: Repository setup with branching workflow
- [x] PPT-3: CI/CD pipeline (GitHub Actions)
- [x] PPT-12: Integration testing
- [x] PPT-13: Final deployment

### Backend
- [x] PPT-1: FastAPI FHIR data service (Patient, Observation, MedicationRequest, Condition)
- [x] PPT-9: Diabetes risk prediction engine (XGBoost ML model)
- [x] PPT-10: Preventative care recommendation engine (Gemini LLM)
- [x] PPT-11: Appointment scheduling and Clinical notes
- [x] PPT-14: AI-powered Chatbot
- [x] PPT-15: Bidirectional patient–clinician messaging system

### Frontend
- [x] PPT-8: UI/UX wireframes (Figma)
- [x] PPT-2: React frontend — patient search, patient header with clinical summary
- [x] PPT-4: Clinical data visualization (blood glucose and HbA1c timeline charts)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI, asyncpg |
| ML | XGBoost, Scikit-learn, Pandas |
| LLM | Google Gemini API (`gemini-2.5-flash`) |
| FHIR Server | HAPI FHIR R4 |
| Database | PostgreSQL |
| Containerization | Docker, Docker Compose |
| Synthetic Data | Synthea |

---

## Project Structure

```
fhir-project/
├── data/
│   └── output/fhir/            # Synthea-generated patient bundles
├── src/
│   ├── backend/
│   │   ├── routers/
│   │   │   ├── auth.py         # JWT login
│   │   │   ├── patients.py
│   │   │   ├── observations.py
│   │   │   ├── medications.py
│   │   │   ├── conditions.py
│   │   │   ├── predict.py
│   │   │   ├── recommendations.py
│   │   │   ├── chat.py
│   │   │   └── portal_data.py  # Notes, appointments, messages
│   │   ├── ml/                 # XGBoost model and training scripts
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── fhir_client.py
│   │   ├── seed_users.py
│   │   ├── upload_patients.py
│   │   └── requirements.txt
│   ├── frontend/
│   │   └── src/
│   │       ├── components/     # PatientSearch, PatientRecord, Inbox, Chat, Modals
│   │       ├── api/            # API client
│   │       ├── types/          # TypeScript interfaces
│   │       └── utils.ts
│   └── infra/
│       ├── docker-compose.yaml         # Production
│       └── docker-compose.local.yaml   # Local development
└── README.md
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/login` | Authenticate and receive JWT token |

### Patients
| Method | Endpoint | Description |
|---|---|---|
| GET | `/patients` | Search patients by name (clinician only) |
| GET | `/patients/{id}` | Get patient demographics |

### Observations
| Method | Endpoint | Description |
|---|---|---|
| GET | `/observations/{patient_id}` | All observations |
| GET | `/observations/{patient_id}/glucose` | Glucose readings |
| GET | `/observations/{patient_id}/hba1c` | HbA1c readings |
| GET | `/observations/{patient_id}/blood-pressure` | Blood pressure readings |

### Medications & Conditions
| Method | Endpoint | Description |
|---|---|---|
| GET | `/medications/{patient_id}` | All medications |
| GET | `/medications/{patient_id}/active` | Active medications only |
| GET | `/conditions/{patient_id}` | Active clinical conditions |

### AI & ML
| Method | Endpoint | Description |
|---|---|---|
| GET | `/predict/{patient_id}` | ML diabetes risk score (XGBoost) |
| GET | `/recommendations/{patient_id}` | AI care recommendations (Gemini) |
| POST | `/chat/{patient_id}` | AI health assistant chat (Gemini) |

### Portal Data
| Method | Endpoint | Description |
|---|---|---|
| GET | `/notes/{patient_id}` | Get clinical notes |
| POST | `/notes/{patient_id}` | Create note |
| GET | `/appointments/{patient_id}` | Get appointments |
| POST | `/appointments/{patient_id}` | Schedule appointment |
| GET | `/messages/{patient_id}` | Get messages |
| POST | `/messages/{patient_id}` | Send message |
| PATCH | `/messages/{patient_id}/{id}/read` | Mark message read |
| PATCH | `/messages/{patient_id}/{id}/reply` | Reply to message |
| PATCH | `/messages/{patient_id}/{id}/patient-read` | Mark reply read by patient |

---

## Local Setup (Docker)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop)

### 1. Clone the repository

```bash
git clone https://github.com/ameliatthomas24/fhir-project.git
cd fhir-project
```

### 2. Configure environment variables

```bash
cp src/backend/.env.example src/backend/.env
```

Open `src/backend/.env` and fill in your Gemini API key:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

To get a Gemini API key, visit [Google AI Studio](https://aistudio.google.com/app/apikey).

### 3. Start all services

Run from the **repo root**:

```bash
docker compose -f src/infra/docker-compose.local.yaml up --build
```

This starts PostgreSQL, HAPI FHIR, the FastAPI backend, and the React frontend. Wait ~30–60 seconds for HAPI FHIR to fully initialize.

### 4. Seed demo users

```bash
docker exec -it hapi-backend python seed_users.py
```

### 5. Load patient data

```bash
docker cp data/output/fhir/. hapi-backend:/app/data_files/
docker exec -it hapi-backend python upload_patients.py
```

This uploads all Synthea-generated patient bundles into the FHIR server (takes a few minutes).

### 6. Open the app

Visit `http://localhost:3000`

**Demo credentials:**

| Role | Email | Password |
|---|---|---|
| Clinician | `clinician@demo.com` | `clinician123` |
| Patient 1 | `patient1@demo.com` | `patient123` |
| Patient 2 | `patient2@demo.com` | `patient456` |
| Patient 3 | `patient3@demo.com` | `patient789` |

---

## Manual Setup (without Docker)

### Prerequisites
- Python 3.11+
- Node.js 18+
- A running HAPI FHIR R4 server and PostgreSQL instance

### Backend

```bash
cd src/backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs on `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd src/frontend
npm install
npm run dev
```

The app runs on `http://localhost:3000`.
