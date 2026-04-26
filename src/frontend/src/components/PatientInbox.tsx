import { useState } from "react";
import type { PatientMessage } from "../types";
import "./ClinicianInbox.css";

interface Props {
    messages: PatientMessage[];
    onPatientMarkRead: (id: string) => void;
    onMarkRead: (id: string) => void;
    onReply: (id: string, reply: string) => void;
}

export default function PatientInbox({ messages, onPatientMarkRead, onMarkRead, onReply }: Props) {
    const [selected, setSelected] = useState<string | null>(null);
    const [replyText, setReplyText] = useState("");

    function handleSelect(msg: PatientMessage) {
        setSelected(msg.id);
        setReplyText("");
        if (msg.fromRole === "clinician" && !msg.read) {
            onMarkRead(msg.id);
        } else if (msg.fromRole !== "clinician" && msg.reply && !msg.patientRead) {
            onPatientMarkRead(msg.id);
        }
    }

    function handleReply(id: string) {
        if (!replyText.trim()) return;
        onReply(id, replyText.trim());
        setReplyText("");
    }

    function isUnread(msg: PatientMessage): boolean {
        if (msg.fromRole === "clinician") return !msg.read;
        return !!msg.reply && !msg.patientRead;
    }

    function formatTime(iso: string) {
        const d = new Date(iso);
        const now = new Date();
        const diffMins = Math.floor((now.getTime() - d.getTime()) / 60000);
        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
        return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }

    const unreadCount = messages.filter(isUnread).length;
    const sorted = [...messages].sort((a, b) => new Date(b.sentAt).getTime() - new Date(a.sentAt).getTime());
    const currentMsg = sorted.find(m => m.id === selected) ?? null;

    if (messages.length === 0) {
        return (
            <div className="inbox-empty">
                <div className="inbox-empty-icon">📭</div>
                <div className="inbox-empty-title">No messages yet</div>
                <div className="inbox-empty-sub">Use "Message Clinician" to send a message to your care team.</div>
            </div>
        );
    }

    return (
        <div className="inbox-layout">
            <div className="inbox-list">
                <div className="inbox-list-header">
                    <span className="inbox-list-title">My Messages</span>
                    {unreadCount > 0 && <span className="inbox-unread-badge">{unreadCount} new</span>}
                </div>
                {sorted.map(msg => {
                    const unread = isUnread(msg);
                    const fromClinician = msg.fromRole === "clinician";
                    let preview: string;
                    if (fromClinician) {
                        preview = msg.reply
                            ? `You replied: ${msg.reply.slice(0, 45)}${msg.reply.length > 45 ? "..." : ""}`
                            : `${msg.body.slice(0, 55)}...`;
                    } else {
                        preview = msg.reply
                            ? `Replied: ${msg.reply.slice(0, 45)}${msg.reply.length > 45 ? "..." : ""}`
                            : "Awaiting reply...";
                    }
                    return (
                        <div
                            key={msg.id}
                            className={`inbox-item ${currentMsg?.id === msg.id ? "selected" : ""} ${unread ? "unread" : ""}`}
                            onClick={() => handleSelect(msg)}
                        >
                            <div className="inbox-item-avatar" style={{ background: "#dcfce7", color: "#166534" }}>DC</div>
                            <div className="inbox-item-content">
                                <div className="inbox-item-top">
                                    <span className="inbox-item-name">Dr. Emily Chen</span>
                                    <span className="inbox-item-time">{formatTime(msg.sentAt)}</span>
                                </div>
                                <div className="inbox-item-subject">{msg.subject}</div>
                                <div className="inbox-item-preview">{preview}</div>
                            </div>
                            {unread && <div className="inbox-item-dot" />}
                        </div>
                    );
                })}
            </div>

            <div className="inbox-thread">
                {!currentMsg ? (
                    <div className="inbox-thread-empty">
                        <div style={{ fontSize: "32px" }}>💬</div>
                        <div style={{ fontSize: "15px", fontWeight: 600, color: "#1e293b", marginTop: "12px" }}>Select a message</div>
                        <div style={{ fontSize: "13px", color: "#94a3b8", marginTop: "4px" }}>Choose a conversation from the left</div>
                    </div>
                ) : (
                    <>
                        <div className="inbox-thread-header">
                            <div className="inbox-thread-avatar" style={{ background: "#dcfce7", color: "#166534" }}>DC</div>
                            <div>
                                <div className="inbox-thread-name">Dr. Emily Chen</div>
                                <div className="inbox-thread-time">
                                    {new Date(currentMsg.sentAt).toLocaleString("en-US", { month: "long", day: "numeric", hour: "numeric", minute: "2-digit" })}
                                </div>
                            </div>
                        </div>

                        <div className="inbox-thread-body">
                            <div className="inbox-thread-subject">{currentMsg.subject}</div>

                            {currentMsg.fromRole === "clinician" ? (
                                <>
                                    {/* Clinician initiated: their message on left, patient reply on right */}
                                    <div className="inbox-bubble inbox-bubble-patient">
                                        <div className="inbox-bubble-label">Dr. Emily Chen</div>
                                        <div className="inbox-bubble-text">{currentMsg.body}</div>
                                    </div>
                                    {currentMsg.reply && (
                                        <div className="inbox-bubble inbox-bubble-clinician">
                                            <div className="inbox-bubble-label">You</div>
                                            <div className="inbox-bubble-text">{currentMsg.reply}</div>
                                        </div>
                                    )}
                                </>
                            ) : (
                                <>
                                    {/* Patient initiated: their message on right, clinician reply on left */}
                                    <div className="inbox-bubble inbox-bubble-clinician">
                                        <div className="inbox-bubble-label">You</div>
                                        <div className="inbox-bubble-text">{currentMsg.body}</div>
                                    </div>
                                    {currentMsg.reply ? (
                                        <div className="inbox-bubble inbox-bubble-patient">
                                            <div className="inbox-bubble-label">Dr. Emily Chen</div>
                                            <div className="inbox-bubble-text">{currentMsg.reply}</div>
                                        </div>
                                    ) : (
                                        <div className="inbox-reply-sent" style={{ color: "#94a3b8" }}>
                                            ⏳ Awaiting reply from your care team...
                                        </div>
                                    )}
                                </>
                            )}
                        </div>

                        {/* Reply box: only for clinician-initiated messages the patient hasn't replied to yet */}
                        {currentMsg.fromRole === "clinician" && !currentMsg.reply && (
                            <div className="inbox-reply-box">
                                <textarea
                                    className="inbox-reply-input"
                                    placeholder="Type your reply..."
                                    value={replyText}
                                    onChange={e => setReplyText(e.target.value)}
                                    rows={3}
                                />
                                <div className="inbox-reply-footer">
                                    <span style={{ fontSize: "12px", color: "#94a3b8" }}>Dr. Emily Chen will see this reply</span>
                                    <button
                                        className="inbox-reply-btn"
                                        onClick={() => handleReply(currentMsg.id)}
                                        disabled={!replyText.trim()}
                                    >
                                        Send Reply ↑
                                    </button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
