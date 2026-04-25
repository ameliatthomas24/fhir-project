from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
 
 
class PatientSummary(BaseModel):
    id: str
    full_name: str
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
 
class ObservationPoint(BaseModel):
    id: str
    patient_id: str
    code: str          
    display: str      
    value: Optional[float] = None
    unit: Optional[str] = None
    effective_date: Optional[str] = None
    status: str
 
class ConditionSummary(BaseModel):
    id: str
    patient_id: str
    display: str
    onset_date: Optional[str] = None
    clinical_status: Optional[str] = None

class MedicationSummary(BaseModel):
    id: str
    patient_id: str
    medication_name: str
    status: str                   
    authored_on: Optional[str] = None
    dosage_instruction: Optional[str] = None
    prescriber_id: Optional[str] = None