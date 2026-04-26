import { useState } from "react";
import "./MessageModal.css";

interface Props {
    open: boolean;
    onClose: () => void;
    onSend: (message: string, subject: string) => void;
    patientName: string;
    mode?: "patient" | "clinician";
}

const PATIENT_SUBJECTS = [
    "Question about my medication",
    "Request for appointment",
    "Lab results question",
    "Side effects concern",
    "Other",
];

const CLINICIAN_SUBJECTS = [
    "Lab results available",
    "Care plan update",
    "Appointment reminder",
    "Follow-up required",
    "Referral information",
];

export default function MessageModal({ open, onClose, onSend, patientName, mode = "patient" }: Props) {
    const [subject, setSubject] = useState("");
    const [body, setBody] = useState("");
    const [sent, setSent] = useState(false);

    if (!open) return null;

    function handleSend() {
        if (!body.trim()) return;
        onSend(body.trim(), subject || "General inquiry");
        setSent(true);
        setTimeout(() => {
            setSent(false);
            setBody("");
            setSubject("");
            onClose();
        }, 1800);
    }

    return (
        <div className="msg-overlay" onClick={onClose}>
            <div className="msg-modal" onClick={e => e.stopPropagation()}>
                <div className="msg-header">
                    <div className="msg-header-left">
                        <div className="msg-icon">✉</div>
                        <div>
                            <div className="msg-title">{mode === "clinician" ? `Message ${patientName}` : "Message Your Care Team"}</div>
                            <div className="msg-subtitle">{mode === "clinician" ? "Patient Portal · Secure Message" : "Dr. Emily Chen · Primary Care"}</div>
                        </div>
                    </div>
                    <button className="msg-close" onClick={onClose}>✕</button>
                </div>

                {sent ? (
                    <div className="msg-sent">
                        <div className="msg-sent-icon">✓</div>
                        <div className="msg-sent-title">Message Sent!</div>
                        <div className="msg-sent-sub">{mode === "clinician" ? `${patientName} will be notified in their portal.` : "Your care team will respond within 1-2 business days."}</div>
                    </div>
                ) : (
                    <>
                        <div className="msg-body">
                            <div className="msg-field">
                                <label className="msg-label">Subject</label>
                                <div className="msg-quick-subjects">
                                    {(mode === "clinician" ? CLINICIAN_SUBJECTS : PATIENT_SUBJECTS).map(s => (
                                        <button
                                            key={s}
                                            className={`msg-quick-btn ${subject === s ? "active" : ""}`}
                                            onClick={() => setSubject(s)}
                                        >
                                            {s}
                                        </button>
                                    ))}
                                </div>
                                <input
                                    className="msg-input"
                                    placeholder="Or type a custom subject..."
                                    value={subject}
                                    onChange={e => setSubject(e.target.value)}
                                />
                            </div>

                            <div className="msg-field">
                                <label className="msg-label">Message</label>
                                <textarea
                                    className="msg-textarea"
                                    placeholder="Describe your concern, question, or request in detail. Be as specific as possible so your care team can help you effectively..."
                                    value={body}
                                    onChange={e => setBody(e.target.value)}
                                    rows={6}
                                />
                                <div className="msg-char-count">{body.length} characters</div>
                            </div>

                            <div className="msg-notice">
                                🔒 This message is private and secure. For emergencies, call 911 or go to the nearest ER.
                            </div>
                        </div>

                        <div className="msg-footer">
                            <button className="msg-cancel" onClick={onClose}>Cancel</button>
                            <button
                                className="msg-send-btn"
                                onClick={handleSend}
                                disabled={!body.trim()}
                            >
                                Send Message ✉
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}