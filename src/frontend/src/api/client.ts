import type { ChatMessage, ConditionSummary, MedicationSummary, ObservationPoint, PatientSummary, RecommendationResponse } from "../types";

const TOKEN_KEY = "auth_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(path, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Session expired. Please log in again.");
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: string;
  user_id: number;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Login failed: ${text}`);
  }
  const data: LoginResponse = await res.json();
  setToken(data.access_token);
  return data;
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

export function getConditions(patientId: string): Promise<ConditionSummary[]> {
  return apiFetch<ConditionSummary[]>(`/conditions/${patientId}`);
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
