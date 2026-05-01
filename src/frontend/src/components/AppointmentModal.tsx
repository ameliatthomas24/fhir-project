import { useState } from "react";
import type { ScheduledAppointment } from "../types";
import { uid } from "../utils";
import "./AppointmentModal.css";

interface Props {
    open: boolean;
    onClose: () => void;
    onSchedule: (appt: ScheduledAppointment) => void;
}

export default function AppointmentModal({ open, onClose, onSchedule }: Props) {
    const [date, setDate] = useState("");
    const [time, setTime] = useState("");
    const [apptType, setApptType] = useState<"in-person" | "virtual">("in-person");
    const [reason, setReason] = useState("");

    if (!open) return null;

    const today = new Date().toISOString().split("T")[0];

    function handleSubmit() {
        if (!date || !time) return;
        onSchedule({
            id: uid(),
            date,
            time,
            type: apptType,
            reason: reason.trim() || "General Check-up",
            status: "upcoming",
        });
        setDate("");
        setTime("");
        setApptType("in-person");
        setReason("");
        onClose();
    }

    return (
        <div className="am-backdrop" onClick={onClose}>
            <div className="am-modal" onClick={e => e.stopPropagation()}>
                <div className="am-header">
                    <span className="am-title">📅 Schedule Appointment</span>
                    <button className="am-close" onClick={onClose} aria-label="Close">✕</button>
                </div>

                <div className="am-body">
                    <div className="am-row">
                        <div className="am-field">
                            <label className="am-label">Date</label>
                            <input
                                type="date"
                                className="am-input"
                                value={date}
                                min={today}
                                onChange={e => setDate(e.target.value)}
                            />
                        </div>
                        <div className="am-field">
                            <label className="am-label">Time</label>
                            <input
                                type="time"
                                className="am-input"
                                value={time}
                                onChange={e => setTime(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="am-field">
                        <label className="am-label">Appointment Type</label>
                        <div className="am-type-toggle">
                            <button
                                className={`am-type-btn ${apptType === "in-person" ? "active" : ""}`}
                                onClick={() => setApptType("in-person")}
                            >
                                🏥 In-Person
                            </button>
                            <button
                                className={`am-type-btn ${apptType === "virtual" ? "active" : ""}`}
                                onClick={() => setApptType("virtual")}
                            >
                                💻 Virtual
                            </button>
                        </div>
                    </div>

                    <div className="am-field">
                        <label className="am-label">
                            Reason for Visit
                            <span className="am-optional"> (optional)</span>
                        </label>
                        <input
                            type="text"
                            className="am-input"
                            placeholder="e.g. Routine check-up, glucose review..."
                            value={reason}
                            maxLength={120}
                            onChange={e => setReason(e.target.value)}
                        />
                    </div>
                </div>

                <div className="am-footer">
                    <button className="am-cancel" onClick={onClose}>Cancel</button>
                    <button
                        className="am-submit"
                        onClick={handleSubmit}
                        disabled={!date || !time}
                    >
                        Confirm Appointment
                    </button>
                </div>
            </div>
        </div>
    );
}
