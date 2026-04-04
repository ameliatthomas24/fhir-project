from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
 
from routers import patients, observations, medications, predict, recommendations
 
app = FastAPI(
    title="Diabetes Management Portal - FHIR Backend",
    description="Fetches and simplifies Patient, Observation, and MedicationRequest resources from HAPI FHIR.",
    version="0.1.0",
)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
app.include_router(patients.router, prefix="/patients", tags=["Patients"])
app.include_router(observations.router, prefix="/observations", tags=["Observations"])
app.include_router(medications.router, prefix="/medications", tags=["Medications"])
app.include_router(predict.router, prefix="/predict", tags=["Predict"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
 
 
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}