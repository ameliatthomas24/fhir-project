export interface PatientSummary {
  id: string;
  full_name: string;
  birth_date?: string;
  gender?: string;
  phone?: string;
  address?: string;
}

export interface ObservationPoint {
  id: string;
  patient_id: string;
  code: string;
  display: string;
  value?: number;
  unit?: string;
  effective_date?: string;
  status: string;
  category?: string;
}

export interface MedicationSummary {
  id: string;
  patient_id: string;
  medication_name: string;
  status: string;
  authored_on?: string;
  dosage_instruction?: string;
  prescriber_id?: string;
}

export interface Recommendation {
  category: string;
  title: string;
  detail: string;
  priority: "High" | "Medium" | "Low";
}

export interface RecommendationResponse {
  summary: string;
  recommendations: Recommendation[];
}

export interface ConditionSummary {
  id: string;
  patient_id: string;
  display: string;
  onset_date?: string;
  clinical_status?: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface Note {
  id: string;
  content: string;
  createdAt: string;
  author: "clinician" | "patient";
}

export interface ScheduledAppointment {
  id: string;
  date: string;
  time: string;
  type: "in-person" | "virtual";
  reason: string;
  status: "upcoming";
  patient_name?: string;
}

export interface AppointmentWithPatient {
  id: string;
  patient_id: string;
  patient_name?: string;
  date: string;
  time: string;
  type: "in-person" | "virtual";
  reason: string;
  status: string;
}

export interface HighRiskPatient {
  id: string;
  full_name: string;
  hba1c: number;
  date?: string;
}

export interface PatientMessage {
  id: string;
  patientId: string;
  patientName: string;
  subject: string;
  body: string;
  sentAt: string;
  read: boolean;
  reply?: string;
  patientRead?: boolean;
  fromRole?: string;
}
