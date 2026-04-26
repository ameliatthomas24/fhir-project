import { useEffect, useState, useRef } from "react";
import { getActiveMedications, getConditions, getObservations } from "../api/client";
import type { ConditionSummary, MedicationSummary, Note, ObservationPoint, PatientSummary, ScheduledAppointment } from "../types";
import CareRecommendations from "./CareRecommendations";
import ChatWidget from "./ChatWidget";
import AppointmentModal from "./AppointmentModal";
import NoteModal from "./NoteModal";
import "./PatientRecord.css";

interface Props {
    patient: PatientSummary;
    portal: "clinician" | "patient";
    onBack: () => void;
}

type Tab = "overview" | "labs" | "medications" | "visits" | "notes" | "ml-risk" | "care-plan";

const GLUCOSE_CODES = new Set(["15074-8", "2339-0"]);
const HBA1C_CODES = new Set(["4548-4", "17856-6"]);
const BP_CODES = new Set(["55284-4", "8462-4", "8480-6"]);
const HR_CODES = new Set(["8867-4"]);
const WEIGHT_CODES = new Set(["29463-7", "3141-9"]);
const LDL_CODES = new Set(["2089-1", "18262-6"]);
const HDL_CODES = new Set(["2085-9"]);
const TRIGLYCERIDE_CODES = new Set(["2571-8"]);

function latestByCode(obs: ObservationPoint[], codes: Set<string>) {
    return obs.filter(o => codes.has(o.code) && o.value != null)
        .sort((a, b) => (b.effective_date ?? "").localeCompare(a.effective_date ?? ""))[0];
}

function byCode(obs: ObservationPoint[], codes: Set<string>) {
    return obs.filter(o => codes.has(o.code) && o.value != null)
        .sort((a, b) => (a.effective_date ?? "").localeCompare(b.effective_date ?? ""));
}

function formatDate(d?: string) {
    if (!d) return "—";
    const datePart = d.split("T")[0];
    const [year, month, day] = datePart.split("-").map(Number);
    if (!year || !month || !day) return "—";
    return new Date(year, month - 1, day).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
}

function formatTime(t: string) {
    if (!t) return "—";
    const [h, m] = t.split(":");
    const hour = parseInt(h, 10);
    const ampm = hour >= 12 ? "PM" : "AM";
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${m} ${ampm}`;
}

function formatDOB(bd?: string) {
    if (!bd) return "—";
    const [y, m, d] = bd.split("-");
    return `${m}.${d}.${y}`;
}

function getInitials(name: string) {
    return name.split(" ").map(n => n[0]).slice(0, 2).join("").toUpperCase();
}

function CircleRisk({ pct, color }: { pct: number; color: string }) {
    const r = 28;
    const circ = 2 * Math.PI * r;
    const dash = (pct / 100) * circ;
    return (
        <svg width="72" height="72" viewBox="0 0 72 72" style={{ flexShrink: 0 }}>
            <circle cx="36" cy="36" r={r} fill="none" stroke="#f1f5f9" strokeWidth="7" />
            <circle cx="36" cy="36" r={r} fill="none" stroke={color} strokeWidth="7"
                strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" transform="rotate(-90 36 36)" />
            <text x="36" y="41" textAnchor="middle" fontSize="13" fontWeight="600" fill={color}>{pct}%</text>
        </svg>
    );
}

function CircleRiskLarge({ pct, color, label }: { pct: number; color: string; label: string }) {
    const r = 54;
    const circ = 2 * Math.PI * r;
    const dash = (pct / 100) * circ;
    return (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px" }}>
            <svg width="130" height="130" viewBox="0 0 130 130">
                <circle cx="65" cy="65" r={r} fill="none" stroke="#f1f5f9" strokeWidth="10" />
                <circle cx="65" cy="65" r={r} fill="none" stroke={color} strokeWidth="10"
                    strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" transform="rotate(-90 65 65)" />
                <text x="65" y="60" textAnchor="middle" fontSize="22" fontWeight="700" fill={color}>{pct}%</text>
                <text x="65" y="78" textAnchor="middle" fontSize="11" fill="#94a3b8">risk score</text>
            </svg>
            <span style={{ fontSize: "13px", fontWeight: 600, color: "#1e293b" }}>{label}</span>
        </div>
    );
}

function LabBar({ label, value, max, unit }: { label: string; value: number; max: number; unit: string }) {
    const pct = Math.min(100, (value / max) * 100);
    const over = value > max;
    return (
        <div className="pr-lab-bar">
            <div className="pr-lab-bar-header">
                <span className="pr-lab-bar-label">{label}</span>
                <span className="pr-lab-bar-val" style={{ color: over ? "#ef4444" : "#64748b" }}>
                    {value} / {max} {unit}
                </span>
            </div>
            <div className="pr-lab-bar-bg">
                <div className="pr-lab-bar-fill" style={{ width: `${pct}%`, background: over ? "#ef4444" : "#3b82f6" }} />
            </div>
        </div>
    );
}

function GlucoseChart({ data }: { data: ObservationPoint[] }) { 
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const wrapRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!canvasRef.current || !wrapRef.current || data.length === 0) return;
        const canvas = canvasRef.current;
        const wrap = wrapRef.current;
        const dpr = window.devicePixelRatio || 1;
        const w = wrap.offsetWidth;
        const h = 220;
        canvas.width = w * dpr;
        canvas.height = h * dpr;
        canvas.style.width = w + "px";
        canvas.style.height = h + "px";
        const ctx = canvas.getContext("2d")!;
        ctx.scale(dpr, dpr);

        const pad = { top: 16, right: 16, bottom: 36, left: 44 };
        const cw = w - pad.left - pad.right;
        const ch = h - pad.top - pad.bottom;
        const vals = data.map(d => d.value ?? 0);
        const minV = Math.max(0, Math.min(...vals) - 20);
        const maxV = Math.max(...vals) + 20;
        const xS = (i: number) => pad.left + (i / Math.max(data.length - 1, 1)) * cw;
        const yS = (v: number) => pad.top + ch - ((v - minV) / (maxV - minV)) * ch;

        ctx.fillStyle = "rgba(16,185,129,0.05)";
        const y180 = yS(Math.min(180, maxV));
        const y70 = yS(Math.max(70, minV));
        ctx.fillRect(pad.left, y180, cw, y70 - y180);

        ctx.beginPath(); ctx.setLineDash([5, 4]); ctx.strokeStyle = "#cbd5e1"; ctx.lineWidth = 1;
        ctx.moveTo(pad.left, yS(135)); ctx.lineTo(pad.left + cw, yS(135)); ctx.stroke();
        ctx.setLineDash([]);

        [45, 90, 135, 180].forEach(v => {
            if (v < minV || v > maxV) return;
            ctx.beginPath(); ctx.strokeStyle = "#f8fafc"; ctx.lineWidth = 1;
            ctx.moveTo(pad.left, yS(v)); ctx.lineTo(pad.left + cw, yS(v)); ctx.stroke();
            ctx.fillStyle = "#94a3b8"; ctx.font = "11px Inter,sans-serif"; ctx.textAlign = "right";
            ctx.fillText(String(v), pad.left - 6, yS(v) + 4);
        });

        ctx.beginPath(); ctx.strokeStyle = "#10b981"; ctx.lineWidth = 2.5; ctx.lineJoin = "round";
        data.forEach((d, i) => i === 0 ? ctx.moveTo(xS(i), yS(d.value ?? 0)) : ctx.lineTo(xS(i), yS(d.value ?? 0)));
        ctx.stroke();

        data.forEach((d, i) => {
            ctx.beginPath(); ctx.arc(xS(i), yS(d.value ?? 0), 4.5, 0, Math.PI * 2);
            ctx.fillStyle = "#10b981"; ctx.fill();
            ctx.strokeStyle = "white"; ctx.lineWidth = 2; ctx.stroke();
        });

        const seen = new Set<string>();
        ctx.fillStyle = "#94a3b8"; ctx.font = "11px Inter,sans-serif"; ctx.textAlign = "center";
        data.forEach((d, i) => {
            const yr = d.effective_date ? new Date(d.effective_date).getFullYear().toString() : "";
            if (yr && !seen.has(yr)) { seen.add(yr); ctx.fillText(yr, xS(i), h - pad.bottom + 16); }
        });
    }, [data]);

    if (data.length === 0) return <div className="pr-chart-empty">No glucose data available</div>;
    return <div ref={wrapRef} style={{ width: "100%" }}><canvas ref={canvasRef} /></div>;
}

type MlRisk = { insufficient_data?: boolean; risk_score: number; risk_label: string; top_factors: { feature: string; importance: number }[]; inputs?: Record<string, number | string> };

export default function PatientRecord({ patient, portal, onBack }: Props) {
    const [tab, setTab] = useState<Tab>("overview");
    const [observations, setObservations] = useState<ObservationPoint[]>([]);
    const [medications, setMedications] = useState<MedicationSummary[]>([]);
    const [conditions, setConditions] = useState<ConditionSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [mlRisk, setMlRisk] = useState<MlRisk | null>(null);
    const [chatOpen, setChatOpen] = useState(false);
    const [scheduleOpen, setScheduleOpen] = useState(false);
    const [noteOpen, setNoteOpen] = useState(false);
    const [appointments, setAppointments] = useState<ScheduledAppointment[]>([]);
    const [notes, setNotes] = useState<Note[]>([]);
    const [toastMsg, setToastMsg] = useState<string | null>(null);

    useEffect(() => {
        if (!toastMsg) return;
        const t = setTimeout(() => setToastMsg(null), 3500);
        return () => clearTimeout(t);
    }, [toastMsg]);

    function handleSaveNote(content: string) {
        setNotes(prev => [{
            id: crypto.randomUUID(),
            content,
            createdAt: new Date().toISOString(),
            author: portal,
        }, ...prev]);
        setToastMsg("Note saved.");
        setTab("notes");
    }

    function handleSchedule(appt: ScheduledAppointment) {
        setAppointments(prev => [appt, ...prev]);
        setToastMsg(`Appointment confirmed for ${formatDate(appt.date)} at ${formatTime(appt.time)}`);
        setTab("visits");
    }

    useEffect(() => {
        setLoading(true);
        Promise.all([getObservations(patient.id), getActiveMedications(patient.id), getConditions(patient.id)])
            .then(([obs, meds, conds]) => { setObservations(obs); setMedications(meds); setConditions(conds); })
            .catch(err => setError(err instanceof Error ? err.message : "Failed to load"))
            .finally(() => setLoading(false));
    }, [patient.id]);

    useEffect(() => {
        setMlRisk(null);
        const token = localStorage.getItem("auth_token");
        fetch(`/predict/${patient.id}`, {
            headers: token ? { "Authorization": `Bearer ${token}` } : {}
        })
            .then(r => {
                if (!r.ok) throw new Error("Backend Error");
                return r.json();
            })
            .then(data => setMlRisk(data))
            .catch((err) => console.error("Prediction fetch failed:", err));
    }, [patient.id]);

    const latestGlucose = latestByCode(observations, GLUCOSE_CODES);
    const latestBP = latestByCode(observations, BP_CODES);
    const latestHR = latestByCode(observations, HR_CODES);
    const latestWeight = latestByCode(observations, WEIGHT_CODES);
    const latestHba1c = latestByCode(observations, HBA1C_CODES);
    const latestLDL = latestByCode(observations, LDL_CODES);
    const latestHDL = latestByCode(observations, HDL_CODES);
    const latestTrig = latestByCode(observations, TRIGLYCERIDE_CODES);
    const glucoseHistory = byCode(observations, GLUCOSE_CODES);

    const hba1cVal = latestHba1c?.value ?? 6.5;
    const cvRisk = Math.min(99, Math.round(hba1cVal * 4 + 10));
    const neuroRisk = Math.min(99, Math.round(hba1cVal * 2 + 3));
    const retinoRisk = Math.min(99, Math.round(hba1cVal * 5 + 5));

    // Compute % change between two most recent readings for a code set, null if insufficient data
    function trendBadge(codes: Set<string>): { text: string; pos: boolean } | null {
        const sorted = observations
            .filter(o => codes.has(o.code) && o.value != null)
            .sort((a, b) => (b.effective_date ?? "").localeCompare(a.effective_date ?? ""));
        if (sorted.length < 2 || sorted[1].value === 0) return null;
        const pct = ((sorted[0].value! - sorted[1].value!) / sorted[1].value!) * 100;
        return { text: `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`, pos: pct >= 0 };
    }

    function riskLevel(pct: number): string {
        return pct < 30 ? "Low" : pct < 60 ? "Moderate" : "High";
    }

    function hba1cSummary(): string {
        if (!latestHba1c || latestHba1c.value == null)
            return "No lab data available yet. Check back after upcoming results.";
        const v = latestHba1c.value;
        if (v < 5.7) return `HbA1c ${v.toFixed(1)}% — within normal range, well-controlled.`;
        if (v < 6.5) return `HbA1c ${v.toFixed(1)}% — pre-diabetes range. Close monitoring recommended.`;
        if (v <= 7.0) return `HbA1c ${v.toFixed(1)}% — diabetes, reasonably controlled. Maintain current regimen.`;
        return `HbA1c ${v.toFixed(1)}% — above target. Review glycemic management plan.`;
    }

    const riskColor = mlRisk?.risk_label === "High" ? "#ef4444" : mlRisk?.risk_label === "Moderate" ? "#f59e0b" : "#10b981";
    const riskBg = mlRisk?.risk_label === "High" ? "#fee2e2" : mlRisk?.risk_label === "Moderate" ? "#fef3c7" : "#dcfce7";
    const riskText = mlRisk?.risk_label === "High" ? "#991b1b" : mlRisk?.risk_label === "Moderate" ? "#92400e" : "#166534";

    const tabs: { id: Tab; label: string }[] = [
        { id: "overview", label: "Overview" },
        { id: "labs", label: "Labs & Analytics" },
        { id: "medications", label: "Medications" },
        { id: "visits", label: "Visits & Appointments" },
        { id: "notes", label: "Clinical Notes" },
        { id: "ml-risk", label: "ML Risk Analysis" },
        { id: "care-plan", label: "✦ Care Plan" },
    ];

    return (
        <div className="pr-page">
            <div className="pr-topbar">
                <button className="pr-back" onClick={onBack}>← Back to Search Results</button>
                <span className="pr-portal-label">{portal === "clinician" ? "Clinician Portal" : "Patient Portal"}</span>
            </div>

            <div className="pr-tabs-bar">
                <div className="pr-tabs">
                    {tabs.map(t => (
                        <button key={t.id} className={`pr-tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
                            {t.label}
                        </button>
                    ))}
                </div>
                <div className="pr-actions">
                    {portal === "clinician" && (
                        <button className="pr-btn pr-btn-primary">✉ Message Patient</button>
                    )}
                    <button className="pr-btn" onClick={() => setNoteOpen(true)}>+ Add Note</button>
                    <button className="pr-btn" onClick={() => setScheduleOpen(true)}>📅 Schedule Appointment</button>
                </div>
            </div>

            {loading && <div className="pr-loading">Loading clinical data...</div>}
            {error && <div className="pr-error">{error}</div>}

            {!loading && !error && (
                <div className="pr-layout">
                    {/* SIDEBAR */}
                    <div className="pr-sidebar">
                        <div className="pr-avatar-wrap">
                            <div className="pr-avatar">{getInitials(patient.full_name)}</div>
                            <div className="pr-id-info">
                                <div className="pr-name">{patient.full_name}</div>
                                <div className="pr-demo">
                                    {patient.gender ? patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1) : ""}
                                    {patient.birth_date ? `, ${formatDOB(patient.birth_date)}` : ""}
                                </div>
                                <span className="pr-dx-badge">Type 2 Diabetes</span>
                            </div>
                        </div>

                        <hr className="pr-hr" />

                        <div className="pr-info-block">
                            <div className="pr-info-row">
                                <div className="pr-info-label">Primary Physician</div>
                                <div className="pr-info-val">Dr. Emily Chen</div>
                            </div>
                            <div className="pr-info-row">
                                <div className="pr-info-label">Insurance</div>
                                <div className="pr-info-val">Blue Cross PPO</div>
                            </div>
                            <div className="pr-info-row">
                                <div className="pr-info-label">Insurance ID</div>
                                <div className="pr-info-val">#BC{patient.id.slice(-10).toUpperCase()}</div>
                            </div>
                        </div>

                        <hr className="pr-hr" />

                        <div className="pr-section-title">Allergies</div>
                        <div className="pr-allergies">
                            <span className="pr-allergy">💊 Penicillin</span>
                            <span className="pr-allergy">💊 Sulfa Drugs</span>
                        </div>

                        <hr className="pr-hr" />

                        <div className="pr-problems-hdr">
                            <span className="pr-section-title">Latest Problems</span>
                            <button className="pr-view-all">View All</button>
                        </div>
                        <div className="pr-problems">
                            {conditions.length === 0 ? (
                                <div style={{ fontSize: "13px", color: "#94a3b8", padding: "4px 0" }}>No active conditions on record</div>
                            ) : (
                                conditions.slice(0, 4).map(c => (
                                    <div key={c.id} className="pr-problem">
                                        <span className="pr-problem-icon">⚠</span>
                                        <span>{c.display}</span>
                                        <span className="pr-problem-chev">›</span>
                                    </div>
                                ))
                            )}
                        </div>

                        <hr className="pr-hr" />

                        <button className="pr-ask-ai" onClick={() => setChatOpen(true)}>✦ Ask AI</button>

                        {/* ML Risk Preview in Sidebar */}
                        {mlRisk && !mlRisk.insufficient_data && (
                            <button
                                className="pr-ml-preview"
                                onClick={() => setTab("ml-risk")}
                            >
                                <div className="pr-ml-preview-header">
                                    <span>🤖 ML Diabetes Risk</span>
                                    <span style={{ fontSize: "11px", color: "#3b82f6" }}>View details ›</span>
                                </div>
                                <div className="pr-ml-preview-score">
                                    <span style={{ fontSize: "20px", fontWeight: 700, color: riskColor }}>
                                        {(mlRisk.risk_score * 100).toFixed(1)}%
                                    </span>
                                    <span style={{ fontSize: "11px", fontWeight: 600, padding: "2px 8px", borderRadius: "20px", background: riskBg, color: riskText }}>
                                        {mlRisk.risk_label} Risk
                                    </span>
                                </div>
                                <div className="pr-ml-bar-bg">
                                    <div className="pr-ml-bar-fill" style={{ width: `${mlRisk.risk_score * 100}%`, background: riskColor }} />
                                </div>
                            </button>
                        )}
                    </div>

                    {/* MAIN CONTENT */}
                    <div className="pr-main">
                        {tab === "overview" && (
                            <>
                                <div className="pr-vitals">
                                    {[
                                        { label: "Blood Glucose", value: latestGlucose?.value ?? "—", unit: "mg/dL", trend: trendBadge(GLUCOSE_CODES) },
                                        { label: "Blood Pressure", value: latestBP?.value ?? "—", unit: "mmHg", trend: trendBadge(BP_CODES) },
                                        { label: "Heart Rate", value: latestHR?.value ?? "—", unit: "bpm", trend: trendBadge(HR_CODES) },
                                        { label: "Weight", value: latestWeight?.value ?? "—", unit: "lbs", trend: trendBadge(WEIGHT_CODES) },
                                    ].map(v => (
                                        <div key={v.label} className="pr-vital">
                                            <div className="pr-vital-label">{v.label}</div>
                                            <div className="pr-vital-val">{v.value}<span className="pr-vital-unit"> {v.unit}</span></div>
                                            {v.trend && <span className={`pr-vital-badge ${v.trend.pos ? "pos" : "neg"}`}>{v.trend.text}</span>}
                                        </div>
                                    ))}
                                </div>

                                <div className="pr-card">
                                    <div className="pr-card-hdr">
                                        <span className="pr-card-title">📈 Blood Glucose Timeline</span>
                                        <div className="pr-chart-pills">
                                            <span className="pr-chart-pill active">Blood Glucose</span>
                                            <span className="pr-chart-pill">Target Range</span>
                                            <span className="pr-chart-pill">HbA1c</span>
                                        </div>
                                    </div>
                                    <GlucoseChart data={glucoseHistory} />
                                </div>

                                <div className="pr-two-col">
                                    <div className="pr-card">
                                        <div className="pr-card-title" style={{ marginBottom: "1rem" }}>📊 Labs</div>
                                        {latestHba1c && <LabBar label="HbA1c" value={latestHba1c.value!} max={7} unit="%" />}
                                        {latestLDL && <LabBar label="LDL" value={latestLDL.value!} max={100} unit="mg/dL" />}
                                        {latestHDL && <LabBar label="HDL" value={latestHDL.value!} max={60} unit="mg/dL" />}
                                        {latestTrig && <LabBar label="Triglycerides" value={latestTrig.value!} max={150} unit="mg/dL" />}
                                        {!latestHba1c && !latestLDL && !latestHDL && !latestTrig && (
                                            <p className="pr-empty">No lab data available</p>
                                        )}
                                        <div className="pr-ai-strip">
                                            <span className="pr-ai-star">✦</span>
                                            <div>
                                                <div className="pr-ai-strip-title">AI Assistant Report</div>
                                                <div className="pr-ai-strip-text">{hba1cSummary()}</div>
                                            </div>
                                            <span style={{ color: "#94a3b8" }}>›</span>
                                        </div>
                                    </div>

                                    <div className="pr-card">
                                        <div className="pr-card-title" style={{ marginBottom: "1rem" }}>⚠ Risk Forecast</div>
                                        {latestHba1c ? [
                                            { name: "Cardiovascular Risk", pct: cvRisk, color: "#3b82f6" },
                                            { name: "Neuropathy Risk", pct: neuroRisk, color: "#10b981" },
                                            { name: "Retinopathy Risk", pct: retinoRisk, color: "#f59e0b" },
                                        ].map(r => (
                                            <div key={r.name} className="pr-risk">
                                                <div className="pr-risk-text">
                                                    <div className="pr-risk-name">{r.name}</div>
                                                    <div className="pr-risk-level">Level: {riskLevel(r.pct)}</div>
                                                    <div className="pr-risk-factors">Based on HbA1c {latestHba1c.value?.toFixed(1)}%</div>
                                                </div>
                                                <CircleRisk pct={r.pct} color={r.color} />
                                            </div>
                                        )) : <p className="pr-empty">No HbA1c data available for risk forecast.</p>}
                                    </div>
                                </div>
                            </>
                        )}

                        {tab === "labs" && (
                            <div className="pr-card">
                                <div className="pr-card-title" style={{ marginBottom: "1rem" }}>Lab Results</div>
                                {(() => {
                                    const clinicalObs = observations.filter(
                                        o => o.category === "laboratory" || o.category === "vital-signs"
                                    );
                                    return clinicalObs.length === 0 ? <p className="pr-empty">No lab results available</p> : (
                                        <table className="pr-table">
                                            <thead><tr><th>Test</th><th>Value</th><th>Unit</th><th>Date</th><th>Status</th></tr></thead>
                                            <tbody>
                                                {clinicalObs.slice(0, 60).map(o => (
                                                    <tr key={`${o.id}-${o.code}`}>
                                                        <td>{o.display}</td>
                                                        <td style={{ fontWeight: 600 }}>{o.value ?? "—"}</td>
                                                        <td style={{ color: "#64748b" }}>{o.unit ?? "—"}</td>
                                                        <td>{formatDate(o.effective_date)}</td>
                                                        <td><span className="pr-status">{o.status}</span></td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    );
                                })()}
                            </div>
                        )}

                        {tab === "medications" && (
                            <div className="pr-card">
                                <div className="pr-card-title" style={{ marginBottom: "1rem" }}>Medications</div>
                                {medications.length === 0 ? <p className="pr-empty">No medications on record</p> : (
                                    <table className="pr-table">
                                        <thead><tr><th>Medication</th><th>Dosage</th><th>Status</th><th>Prescribed</th></tr></thead>
                                        <tbody>
                                            {medications.map(m => (
                                                <tr key={m.id}>
                                                    <td style={{ fontWeight: 500 }}>{m.medication_name}</td>
                                                    <td>{m.dosage_instruction ?? "—"}</td>
                                                    <td><span className={`pr-status ${m.status === "active" ? "active" : ""}`}>{m.status}</span></td>
                                                    <td>{formatDate(m.authored_on)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        )}

                        {tab === "visits" && (
                            <div className="pr-card">
                                <div className="pr-card-title" style={{ marginBottom: "1rem" }}>Visits &amp; Appointments</div>
                                {appointments.length === 0 ? (
                                    <p className="pr-empty" style={{ marginTop: "1rem" }}>No upcoming appointments. Use the Schedule button to book one.</p>
                                ) : (
                                    <div className="pr-appt-list">
                                        {appointments.map(appt => (
                                            <div key={appt.id} className="pr-appt-card">
                                                <div className="pr-appt-header">
                                                    <div>
                                                        <div className="pr-appt-date">
                                                            {formatDate(appt.date)} &nbsp;·&nbsp; {formatTime(appt.time)}
                                                        </div>
                                                        <div className="pr-appt-doctor">Dr. Emily Chen &mdash; Primary Care</div>
                                                    </div>
                                                    <div className="pr-appt-badges">
                                                        <span className={`pr-appt-type ${appt.type}`}>
                                                            {appt.type === "virtual" ? "💻 Virtual" : "🏥 In-Person"}
                                                        </span>
                                                        <span className="pr-appt-status">Upcoming</span>
                                                    </div>
                                                </div>
                                                <div className="pr-appt-detail">
                                                    <span className="pr-appt-reason">{appt.reason}</span>
                                                    <span className="pr-appt-location">
                                                        {appt.type === "in-person"
                                                            ? "📍 Main Clinic — 450 Medical Dr, Suite 200"
                                                            : "🔗 Video call link will be sent to your email"}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {tab === "notes" && (
                            <div className="pr-card">
                                <div className="pr-card-title" style={{ marginBottom: "1rem" }}>Clinical Notes</div>
                                {notes.length === 0 ? (
                                    <p className="pr-empty" style={{ marginTop: "1rem" }}>No notes yet. Use the Add Note button to create one.</p>
                                ) : (
                                    <div className="pr-note-list">
                                        {notes.map(note => (
                                            <div key={note.id} className="pr-note-card">
                                                <div className="pr-note-meta">
                                                    <span className={`pr-note-author ${note.author}`}>
                                                        {note.author === "clinician" ? "🩺 Clinician Note" : "👤 Patient Note"}
                                                    </span>
                                                    <span className="pr-note-ts">
                                                        {new Date(note.createdAt).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                                                        {" "}·{" "}
                                                        {new Date(note.createdAt).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}
                                                    </span>
                                                </div>
                                                <p className="pr-note-content">{note.content}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {tab === "care-plan" && (
                            <div className="pr-card">
                                <div className="pr-card-title" style={{ marginBottom: "1.25rem" }}>✦ Preventative Care Recommendations</div>
                                <CareRecommendations patientId={patient.id} />
                            </div>
                        )}

                        {tab === "ml-risk" && (
                            <div>
                                <div className="pr-card" style={{ marginBottom: "1.25rem" }}>
                                    <div className="pr-card-title" style={{ marginBottom: "1.5rem" }}>🤖 ML Diabetes Risk Analysis</div>
                                    {!mlRisk ? (
                                        <p className="pr-empty">Loading ML prediction...</p>
                                    ) : mlRisk.insufficient_data ? (
                                        <p className="pr-empty">No HbA1c observations found in this patient's record. ML risk scoring requires at least one HbA1c lab result.</p>
                                    ) : (
                                        <>
                                            {/* Big score display */}
                                            <div className="pr-ml-hero">
                                                <CircleRiskLarge
                                                    pct={Math.round(mlRisk.risk_score * 100)}
                                                    color={riskColor}
                                                    label={`${mlRisk.risk_label} Risk`}
                                                />
                                                <div className="pr-ml-hero-info">
                                                    <div style={{ fontSize: "13px", color: "#64748b", marginBottom: "1rem" }}>
                                                        This score is generated by an XGBoost machine learning model trained on clinical diabetes data.
                                                        It uses the patient's current vitals and lab values to estimate diabetes risk.
                                                    </div>
                                                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                                                        {mlRisk.inputs && Object.entries(mlRisk.inputs).map(([k, v]) => (
                                                            <div key={k} style={{ background: "#f8fafc", borderRadius: "8px", padding: "10px 12px", border: "1px solid #f1f5f9" }}>
                                                                <div style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                                                                    {k.replace(/_/g, " ")}
                                                                </div>
                                                                <div style={{ fontSize: "15px", fontWeight: 600, color: "#1e293b", marginTop: "2px" }}>
                                                                    {typeof v === "number" ? v.toFixed(1) : v}
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </div>

                                {mlRisk && !mlRisk.insufficient_data && (
                                    <div className="pr-card">
                                        <div className="pr-card-title" style={{ marginBottom: "1.25rem" }}>Top Risk Factors</div>
                                        <div style={{ fontSize: "13px", color: "#64748b", marginBottom: "1rem" }}>
                                            Features ranked by their influence on this patient's risk score.
                                        </div>
                                        {mlRisk.top_factors.map((f, i) => (
                                            <div key={f.feature} style={{ marginBottom: "14px" }}>
                                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "5px" }}>
                                                    <span style={{ fontSize: "13px", fontWeight: 500, color: "#1e293b" }}>
                                                        {i + 1}. {f.feature.replace(/_/g, " ")}
                                                    </span>
                                                    <span style={{ fontSize: "13px", fontWeight: 600, color: riskColor }}>
                                                        {(f.importance * 100).toFixed(1)}%
                                                    </span>
                                                </div>
                                                <div style={{ height: "8px", background: "#f1f5f9", borderRadius: "4px", overflow: "hidden" }}>
                                                    <div style={{
                                                        height: "100%", borderRadius: "4px",
                                                        width: `${(f.importance / mlRisk.top_factors[0].importance) * 100}%`,
                                                        background: i === 0 ? riskColor : i === 1 ? "#3b82f6" : "#94a3b8"
                                                    }} />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}

            <ChatWidget
                open={chatOpen}
                onClose={() => setChatOpen(false)}
                patientId={patient.id}
            />

            <AppointmentModal
                open={scheduleOpen}
                onClose={() => setScheduleOpen(false)}
                onSchedule={handleSchedule}
            />

            <NoteModal
                open={noteOpen}
                onClose={() => setNoteOpen(false)}
                onSave={handleSaveNote}
            />

            {toastMsg && (
                <div className="pr-toast">
                    <span className="pr-toast-icon">✅</span>
                    {toastMsg}
                </div>
            )}
        </div>
    );
}
