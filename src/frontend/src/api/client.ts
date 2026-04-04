import type { MedicationSummary, ObservationPoint, PatientSummary } from "../types";

// 1. This tells the frontend WHERE the backend is living
const BASE_URL = "http://127.0.0.1:8000";

// 2. This is the "Engine" that actually goes and gets the data
async function apiFetch<T>(path: string): Promise<T> {
    // THIS IS THE FIX: It combines the URL + the path (like /patients)
    const res = await fetch(`${BASE_URL}${path}`);

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`API ${res.status}: ${text}`);
    }
    return res.json() as Promise<T>;
}

// 3. These are the "Buttons" your components will press
export function searchPatients(name?: string): Promise<PatientSummary[]> {
    const query = name ? `?name=${encodeURIComponent(name)}` : "";
    return apiFetch<PatientSummary[]>(`/patients${query}`);
}

export function getObservations(patientId: string): Promise<ObservationPoint[]> {
    return apiFetch<ObservationPoint[]>(`/observations/${patientId}`);
}

export function getActiveMedications(patientId: string): Promise<MedicationSummary[]> {
    return apiFetch<MedicationSummary[]>(`/medications/${patientId}/active`);
}