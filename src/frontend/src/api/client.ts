import type { AppointmentWithPatient, ChatMessage, ConditionSummary, HighRiskPatient, MedicationSummary, Note, ObservationPoint, PatientMessage, PatientSummary, RecommendationResponse, ScheduledAppointment } from "../types";

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

function cleanPatientName(name: string): string {
  return name.replace(/\d+/g, "").replace(/\s+/g, " ").trim();
}

export async function searchPatients(name?: string, count = 20): Promise<PatientSummary[]> {
  const params = new URLSearchParams({ _count: String(count) });
  if (name) params.set("name", name);
  const patients = await apiFetch<PatientSummary[]>(`/patients?${params.toString()}`);
  return patients.map((p) => ({ ...p, full_name: cleanPatientName(p.full_name) }));
}

export function getHighRiskPatients(): Promise<HighRiskPatient[]> {
  return apiFetch<HighRiskPatient[]>("/patients/high-risk")
    .then(patients => patients.map(p => ({ ...p, full_name: cleanPatientName(p.full_name) })));
}

export function getAllAppointments(): Promise<AppointmentWithPatient[]> {
  return apiFetch<AppointmentWithPatient[]>("/appointments");
}

export function getAllMessages(): Promise<PatientMessage[]> {
  return apiFetch<PatientMessage[]>("/messages");
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

// ── Notes ────────────────────────────────────────────────────────────────────

export function getNotes(patientId: string): Promise<Note[]> {
  return apiFetch<Note[]>(`/notes/${patientId}`);
}

export function createNote(patientId: string, note: { id: string; content: string; createdAt: string; author: string }): Promise<Note> {
  return apiFetch<Note>(`/notes/${patientId}`, { method: "POST", body: JSON.stringify(note) });
}

// ── Appointments ─────────────────────────────────────────────────────────────

export function getAppointments(patientId: string): Promise<ScheduledAppointment[]> {
  return apiFetch<ScheduledAppointment[]>(`/appointments/${patientId}`);
}

export function createAppointment(patientId: string, appt: ScheduledAppointment): Promise<ScheduledAppointment> {
  return apiFetch<ScheduledAppointment>(`/appointments/${patientId}`, { method: "POST", body: JSON.stringify(appt) });
}

// ── Messages ─────────────────────────────────────────────────────────────────

export function getMessages(patientId: string): Promise<PatientMessage[]> {
  return apiFetch<PatientMessage[]>(`/messages/${patientId}`);
}

export function sendMessage(patientId: string, msg: { id: string; patientName: string; subject: string; body: string; sentAt: string; fromRole?: string }): Promise<PatientMessage> {
  return apiFetch<PatientMessage>(`/messages/${patientId}`, { method: "POST", body: JSON.stringify(msg) });
}

export function markMessageRead(patientId: string, messageId: string): Promise<void> {
  return apiFetch<void>(`/messages/${patientId}/${messageId}/read`, { method: "PATCH" });
}

export function replyToMessage(patientId: string, messageId: string, reply: string): Promise<PatientMessage> {
  return apiFetch<PatientMessage>(`/messages/${patientId}/${messageId}/reply`, { method: "PATCH", body: JSON.stringify({ reply }) });
}

export function markMessagePatientRead(patientId: string, messageId: string): Promise<void> {
  return apiFetch<void>(`/messages/${patientId}/${messageId}/patient-read`, { method: "PATCH" });
}

// ── Chat ─────────────────────────────────────────────────────────────────────

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
