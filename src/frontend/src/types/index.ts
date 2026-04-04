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
