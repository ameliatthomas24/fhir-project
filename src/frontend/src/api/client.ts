import type { ChatMessage, MedicationSummary, ObservationPoint, PatientSummary, RecommendationResponse } from "../types";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

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

export function getRecommendations(patientId: string): Promise<RecommendationResponse> {
  return apiFetch<RecommendationResponse>(`/recommendations/${patientId}`);
}

export async function sendChatMessage(patientId: string, messages: ChatMessage[]): Promise<string> {
  const res = await fetch(`/chat/${patientId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  const data = await res.json() as { reply: string };
  return data.reply;
}
