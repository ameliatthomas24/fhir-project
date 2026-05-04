from dotenv import load_dotenv
load_dotenv()
import os
import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from routers import patients, observations, medications, recommendations, predict, chat, conditions, portal_data
from routers import auth as auth_router
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id         SERIAL PRIMARY KEY,
    email      TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role       TEXT NOT NULL CHECK (role IN ('clinician', 'patient')),
    fhir_patient_id TEXT
)
"""
CREATE_NOTES_TABLE = """
CREATE TABLE IF NOT EXISTS notes (
    id         TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    author     TEXT NOT NULL CHECK (author IN ('clinician', 'patient'))
)
"""
CREATE_APPOINTMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS appointments (
    id         TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    date       TEXT NOT NULL,
    time       TEXT NOT NULL,
    type       TEXT NOT NULL CHECK (type IN ('in-person', 'virtual')),
    reason     TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'upcoming'
)
"""
CREATE_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id           TEXT PRIMARY KEY,
    patient_id   TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    subject      TEXT NOT NULL,
    body         TEXT NOT NULL,
    sent_at      TIMESTAMPTZ NOT NULL,
    read         BOOLEAN NOT NULL DEFAULT FALSE,
    reply        TEXT,
    patient_read BOOLEAN NOT NULL DEFAULT FALSE,
    from_role    TEXT NOT NULL DEFAULT 'patient'
)
"""
MIGRATE_MESSAGES_FROM_ROLE = """
ALTER TABLE messages ADD COLUMN IF NOT EXISTS from_role TEXT NOT NULL DEFAULT 'patient'
"""
MIGRATE_APPOINTMENTS_PATIENT_NAME = """
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS patient_name TEXT
"""
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = os.getenv("DATABASE_URL")
    app.state.db_pool = await asyncpg.create_pool(db_url)
    async with app.state.db_pool.acquire() as conn:
        await conn.execute(CREATE_USERS_TABLE)
        await conn.execute(CREATE_NOTES_TABLE)
        await conn.execute(CREATE_APPOINTMENTS_TABLE)
        await conn.execute(CREATE_MESSAGES_TABLE)
        await conn.execute(MIGRATE_MESSAGES_FROM_ROLE)
        await conn.execute(MIGRATE_APPOINTMENTS_PATIENT_NAME)
    yield
    await app.state.db_pool.close()
app = FastAPI(
    title="Diabetes Management Portal - FHIR Backend",
    description="Fetches and simplifies Patient, Observation, and MedicationRequest resources from HAPI FHIR.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
app.include_router(patients.router, prefix="/patients", tags=["Patients"])
app.include_router(observations.router, prefix="/observations", tags=["Observations"])
app.include_router(medications.router, prefix="/medications", tags=["Medications"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
app.include_router(predict.router, prefix="/predict", tags=["ML"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(conditions.router, prefix="/conditions", tags=["Conditions"])
app.include_router(portal_data.router, tags=["Portal Data"])
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
