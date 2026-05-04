import { useEffect, useState } from "react";
import { searchPatients, getHighRiskPatients, getAllAppointments, getAllMessages, markMessageRead, replyToMessage } from "../api/client";
import type { AppointmentWithPatient, HighRiskPatient, PatientMessage, PatientSummary } from "../types";
import PatientRecord from "./PatientRecord";
import ClinicianInbox from "./ClinicianInbox";
import "./ClinicianDashboard.css";

type DashTab = "home" | "search" | "appointments" | "messages";

interface Props {
    onLogout: () => void;
    onSwitchPortal: () => void;
}

function formatDate(d: string) {
    if (!d) return "—";
    const [y, m, day] = d.split("-").map(Number);
    return new Date(y, m - 1, day).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function formatTime(t: string) {
    if (!t) return "—";
    const [h, min] = t.split(":");
    const hour = parseInt(h, 10);
    return `${hour % 12 || 12}:${min} ${hour >= 12 ? "PM" : "AM"}`;
}

function formatDOB(d?: string) {
    if (!d) return "—";
    const [y, m, day] = d.split("-");
    return `${m}/${day}/${y}`;
}

function todayLabel() {
    return new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
}

function formatMsgTime(iso: string) {
    const d = new Date(iso);
    const diffMins = Math.floor((Date.now() - d.getTime()) / 60000);
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function isUnread(m: PatientMessage) {
    return m.fromRole === "clinician" ? (!!m.reply && !m.patientRead) : !m.read;
}

export default function ClinicianDashboard({ onLogout, onSwitchPortal }: Props) {
    const [tab, setTab] = useState<DashTab>("home");
    const [selectedPatient, setSelectedPatient] = useState<PatientSummary | null>(null);
    const [highRisk, setHighRisk] = useState<HighRiskPatient[]>([]);
    const [allAppointments, setAllAppointments] = useState<AppointmentWithPatient[]>([]);
    const [allMessages, setAllMessages] = useState<PatientMessage[]>([]);
    const [allPatients, setAllPatients] = useState<PatientSummary[]>([]);
    const [searchFilter, setSearchFilter] = useState("");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            getHighRiskPatients().catch(() => [] as HighRiskPatient[]),
            getAllAppointments().catch(() => [] as AppointmentWithPatient[]),
            getAllMessages().catch(() => [] as PatientMessage[]),
            searchPatients(undefined, 100).catch(() => [] as PatientSummary[]),
        ]).then(([risk, appts, msgs, patients]) => {
            setHighRisk(risk);
            setAllAppointments(appts);
            setAllMessages(msgs);
            setAllPatients(patients);
            setLoading(false);
        });
    }, []);

    function handleMarkRead(id: string) {
        const msg = allMessages.find(m => m.id === id);
        if (msg) markMessageRead(msg.patientId, id).catch(() => {});
        setAllMessages(prev => prev.map(m => m.id === id ? { ...m, read: true } : m));
    }

    function handleReply(id: string, reply: string) {
        const msg = allMessages.find(m => m.id === id);
        if (!msg) return;
        replyToMessage(msg.patientId, id, reply)
            .then(updated => setAllMessages(prev => prev.map(m => m.id === id ? updated : m)))
            .catch(() => {});
    }

    const unreadCount = allMessages.filter(isUnread).length;
    const upcomingAppts = [...allAppointments]
        .sort((a, b) => a.date.localeCompare(b.date) || a.time.localeCompare(b.time))
        .slice(0, 5);
    const recentUnread = allMessages.filter(isUnread).slice(0, 5);

    const filteredPatients = searchFilter.trim()
        ? allPatients.filter(p => p.full_name.toLowerCase().includes(searchFilter.toLowerCase()))
        : allPatients;

    if (selectedPatient) {
        return <PatientRecord patient={selectedPatient} portal="clinician" onBack={() => setSelectedPatient(null)} />;
    }

    const navItems: { id: DashTab; icon: string; label: string }[] = [
        { id: "home", icon: "⌂", label: "Home" },
        { id: "search", icon: "⊙", label: "Patients" },
        { id: "appointments", icon: "▦", label: "Appointments" },
        { id: "messages", icon: "✉", label: "Messages" },
    ];

    return (
        <div className="cd-layout">
            {/* Sidebar */}
            <aside className="cd-sidebar">
                <div className="cd-sidebar-top">
                    <div className="cd-logo">
                        <div className="cd-logo-icon">♥</div>
                        <div className="cd-logo-text">Diabetes Management Portal</div>
                    </div>
                    <nav className="cd-nav">
                        {navItems.map(item => (
                            <button
                                key={item.id}
                                className={`cd-nav-item ${tab === item.id ? "active" : ""}`}
                                onClick={() => setTab(item.id)}
                            >
                                <span className="cd-nav-icon">{item.icon}</span>
                                <span className="cd-nav-label">{item.label}</span>
                                {item.id === "messages" && unreadCount > 0 && (
                                    <span className="cd-nav-badge">{unreadCount}</span>
                                )}
                            </button>
                        ))}
                    </nav>
                </div>
                <div className="cd-sidebar-bottom">
                    <button className="cd-switch-portal" onClick={onSwitchPortal}>
                        ⇄ View Patient Portal
                    </button>
                    <button className="cd-logout" onClick={onLogout}>
                        <span>⎋</span> Log out
                    </button>
                </div>
            </aside>

            {/* Main content */}
            <main className="cd-main">
                {/* ── HOME ── */}
                {tab === "home" && (
                    <div className="cd-home">
                        <div className="cd-grid">
                            {/* Top-left: Greeting */}
                            <div className="cd-card cd-greeting">
                                <div className="cd-greeting-badge">Clinician Portal</div>
                                <div className="cd-greeting-name">Welcome, Dr. Emily Chen</div>
                                <div className="cd-greeting-date">{todayLabel()}</div>
                                <div className="cd-greeting-divider" />
                                <div className="cd-greeting-office">
                                    <span className="cd-greeting-office-name">Main Clinic</span>
                                    <span className="cd-greeting-office-addr">450 Medical Dr, Suite 200</span>
                                </div>
                                <div className="cd-greeting-stats">
                                    <div className="cd-stat">
                                        <div className="cd-stat-val">{allPatients.length}</div>
                                        <div className="cd-stat-lbl">Patients</div>
                                    </div>
                                    <div className="cd-stat">
                                        <div className="cd-stat-val">{allAppointments.length}</div>
                                        <div className="cd-stat-lbl">Appointments</div>
                                    </div>
                                    <div className="cd-stat">
                                        <div className="cd-stat-val">{unreadCount}</div>
                                        <div className="cd-stat-lbl">Unread</div>
                                    </div>
                                </div>
                            </div>

                            {/* Top-right: Upcoming Appointments */}
                            <div className="cd-card">
                                <div className="cd-card-header">
                                    <span className="cd-card-title">📅 Upcoming Appointments</span>
                                    <button className="cd-card-link" onClick={() => setTab("appointments")}>View all</button>
                                </div>
                                {loading ? (
                                    <div className="cd-empty">Loading...</div>
                                ) : upcomingAppts.length === 0 ? (
                                    <div className="cd-empty">No upcoming appointments.</div>
                                ) : (
                                    <div className="cd-list">
                                        {upcomingAppts.map(a => (
                                            <div key={a.id} className="cd-list-item" onClick={() => setTab("appointments")}>
                                                <div className="cd-list-item-main">
                                                    <div className="cd-list-item-name">{a.patient_name ?? allPatients.find(p => p.id === a.patient_id)?.full_name ?? a.patient_id}</div>
                                                    <div className="cd-list-item-sub">{formatDate(a.date)} · {formatTime(a.time)}</div>
                                                </div>
                                                <span className={`cd-type-badge ${a.type === "virtual" ? "virtual" : ""}`}>
                                                    {a.type === "virtual" ? "Virtual" : "In-Person"}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Bottom-left: High-Risk Patients */}
                            <div className="cd-card">
                                <div className="cd-card-header">
                                    <span className="cd-card-title">⚠ High-Risk Patients</span>
                                    <span className="cd-card-sub">HbA1c &gt; 6.5%</span>
                                </div>
                                {loading ? (
                                    <div className="cd-empty">Loading...</div>
                                ) : highRisk.length === 0 ? (
                                    <div className="cd-empty">No high-risk patients found.</div>
                                ) : (
                                    <div className="cd-list">
                                        {highRisk.map(p => (
                                            <div
                                                key={p.id}
                                                className="cd-list-item clickable"
                                                onClick={() => {
                                                    const found = allPatients.find(ap => ap.id === p.id);
                                                    setSelectedPatient(found ?? { id: p.id, full_name: p.full_name });
                                                }}
                                            >
                                                <div className="cd-risk-avatar">
                                                    {p.full_name.split(" ").map(n => n[0]).slice(0, 2).join("").toUpperCase()}
                                                </div>
                                                <div className="cd-list-item-main">
                                                    <div className="cd-list-item-name">{p.full_name}</div>
                                                    <div className="cd-list-item-sub">HbA1c: {p.hba1c.toFixed(1)}%</div>
                                                </div>
                                                <span className="cd-risk-badge">High Risk</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Bottom-right: Inbox */}
                            <div className="cd-card">
                                <div className="cd-card-header">
                                    <span className="cd-card-title">
                                        ✉ Inbox{unreadCount > 0 && <span className="cd-inbox-count"> ({unreadCount})</span>}
                                    </span>
                                    <button className="cd-card-link" onClick={() => setTab("messages")}>View all</button>
                                </div>
                                {loading ? (
                                    <div className="cd-empty">Loading...</div>
                                ) : recentUnread.length === 0 ? (
                                    <div className="cd-empty">No unread messages.</div>
                                ) : (
                                    <div className="cd-list">
                                        {recentUnread.map(m => (
                                            <div key={m.id} className="cd-list-item clickable" onClick={() => setTab("messages")}>
                                                <div className="cd-risk-avatar">
                                                    {m.patientName.split(" ").map(n => n[0]).slice(0, 2).join("").toUpperCase()}
                                                </div>
                                                <div className="cd-list-item-main">
                                                    <div className="cd-list-item-name">{m.patientName}</div>
                                                    <div className="cd-list-item-sub">{m.subject}</div>
                                                </div>
                                                <span className="cd-msg-time">{formatMsgTime(m.sentAt)}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* ── SEARCH / PATIENTS ── */}
                {tab === "search" && (
                    <div className="cd-section">
                        <div className="cd-section-header">
                            <div>
                                <div className="cd-section-title">Patients</div>
                                <div className="cd-section-sub">{allPatients.length} patients on record</div>
                            </div>
                            <div className="cd-search-wrap">
                                <input
                                    className="cd-search-input"
                                    placeholder="Filter by name..."
                                    value={searchFilter}
                                    onChange={e => setSearchFilter(e.target.value)}
                                />
                            </div>
                        </div>
                        {loading ? (
                            <div className="cd-empty" style={{ marginTop: "2rem" }}>Loading patients...</div>
                        ) : (
                            <div className="cd-table-wrap">
                                <table className="cd-table">
                                    <thead>
                                        <tr>
                                            <th>Name</th>
                                            <th>Date of Birth</th>
                                            <th>Gender</th>
                                            <th>Phone</th>
                                            <th>Address</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filteredPatients.map(p => (
                                            <tr key={p.id} onClick={() => setSelectedPatient(p)} className="cd-table-row">
                                                <td>
                                                    <div className="cd-table-name">
                                                        <div className="cd-risk-avatar small">
                                                            {p.full_name.split(" ").map(n => n[0]).slice(0, 2).join("").toUpperCase()}
                                                        </div>
                                                        {p.full_name}
                                                    </div>
                                                </td>
                                                <td>{formatDOB(p.birth_date)}</td>
                                                <td>{p.gender ? p.gender.charAt(0).toUpperCase() + p.gender.slice(1) : "—"}</td>
                                                <td>{p.phone ?? "—"}</td>
                                                <td>{p.address ?? "—"}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                                {filteredPatients.length === 0 && (
                                    <div className="cd-empty" style={{ padding: "2rem" }}>No patients match that name.</div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* ── APPOINTMENTS ── */}
                {tab === "appointments" && (
                    <div className="cd-section">
                        <div className="cd-section-header">
                            <div>
                                <div className="cd-section-title">Appointments</div>
                                <div className="cd-section-sub">{allAppointments.length} total</div>
                            </div>
                        </div>
                        {loading ? (
                            <div className="cd-empty" style={{ marginTop: "2rem" }}>Loading...</div>
                        ) : allAppointments.length === 0 ? (
                            <div className="cd-empty" style={{ marginTop: "2rem" }}>No appointments scheduled yet.</div>
                        ) : (
                            <div className="cd-table-wrap">
                                <table className="cd-table">
                                    <thead>
                                        <tr>
                                            <th>Patient</th>
                                            <th>Date</th>
                                            <th>Time</th>
                                            <th>Type</th>
                                            <th>Reason</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {[...allAppointments]
                                            .sort((a, b) => a.date.localeCompare(b.date) || a.time.localeCompare(b.time))
                                            .map(a => (
                                                <tr key={a.id} className="cd-table-row-plain">
                                                    <td>{a.patient_name ?? allPatients.find(p => p.id === a.patient_id)?.full_name ?? a.patient_id}</td>
                                                    <td>{formatDate(a.date)}</td>
                                                    <td>{formatTime(a.time)}</td>
                                                    <td>
                                                        <span className={`cd-type-badge ${a.type === "virtual" ? "virtual" : ""}`}>
                                                            {a.type === "virtual" ? "Virtual" : "In-Person"}
                                                        </span>
                                                    </td>
                                                    <td>{a.reason}</td>
                                                </tr>
                                            ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )}

                {/* ── MESSAGES ── */}
                {tab === "messages" && (
                    <div className="cd-section cd-section-inbox">
                        <div className="cd-section-header">
                            <div>
                                <div className="cd-section-title">Messages</div>
                                <div className="cd-section-sub">{unreadCount} unread</div>
                            </div>
                        </div>
                        <ClinicianInbox
                            messages={allMessages}
                            onMarkRead={handleMarkRead}
                            onReply={handleReply}
                        />
                    </div>
                )}
            </main>
        </div>
    );
}
