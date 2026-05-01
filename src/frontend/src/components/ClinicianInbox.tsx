import { useState } from "react";
import type { PatientMessage } from "../types";
import "./ClinicianInbox.css";

export type { PatientMessage };

interface Props {
    messages: PatientMessage[];
    onMarkRead: (id: string) => void;
    onReply: (id: string, reply: string) => void;
}

export default function ClinicianInbox({ messages, onMarkRead, onReply }: Props) {
    const [selected, setSelected] = useState<PatientMessage | null>(null);
    const [replyText, setReplyText] = useState("");
    const [replySent, setReplySent] = useState(false);

    function handleSelect(msg: PatientMessage) {
        setSelected(msg);
        setReplyText("");
        setReplySent(false); // reset so "Reply sent" doesn't bleed across messages
        if (msg.fromRole === "clinician" && msg.reply && !msg.patientRead) {
            onMarkRead(msg.id);
        } else if (msg.fromRole !== "clinician" && !msg.read) {
            onMarkRead(msg.id);
        }
    }

    function handleReply() {
        if (!selected || !replyText.trim()) return;
        onReply(selected.id, replyText.trim());
        setReplySent(true);
        setReplyText("");
    }

    function formatTime(iso: string) {
        const d = new Date(iso);
        const now = new Date();
        const diffMs = now.getTime() - d.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
        return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }

    function isUnread(m: PatientMessage): boolean {
        return m.fromRole === "clinician" ? (!!m.reply && !m.patientRead) : !m.read;
    }

    const unreadCount = messages.filter(isUnread).length;

    const visibleMessages = messages.filter(m => m.fromRole !== "clinician" || !!m.reply);

    if (visibleMessages.length === 0) {
        return (
            <div className="inbox-empty">
                <div className="inbox-empty-icon">📭</div>
                <div className="inbox-empty-title">No messages yet</div>
                <div className="inbox-empty-sub">Patient messages will appear here.</div>
            </div>
        );
    }

    return (
        <div className="inbox-layout">
            {/* Message list */}
            <div className="inbox-list">
                <div className="inbox-list-header">
                    <span className="inbox-list-title">Inbox</span>
                    {unreadCount > 0 && (
                        <span className="inbox-unread-badge">{unreadCount} new</span>
                    )}
                </div>
                {[...visibleMessages]
                    .sort((a, b) => new Date(b.sentAt).getTime() - new Date(a.sentAt).getTime())
                    .map(msg => {
                        const unread = isUnread(msg);
                        const fromClinician = msg.fromRole === "clinician";
                        return (
                            <div
                                key={msg.id}
                                className={`inbox-item ${selected?.id === msg.id ? "selected" : ""} ${unread ? "unread" : ""}`}
                                onClick={() => handleSelect(msg)}
                            >
                                <div className="inbox-item-avatar">
                                    {msg.patientName.split(" ").map(n => n[0]).slice(0, 2).join("").toUpperCase()}
                                </div>
                                <div className="inbox-item-content">
                                    <div className="inbox-item-top">
                                        <span className="inbox-item-name">{msg.patientName}</span>
                                        <span className="inbox-item-time">{formatTime(msg.sentAt)}</span>
                                    </div>
                                    <div className="inbox-item-subject">
                                        {fromClinician ? `↩ ${msg.subject}` : msg.subject}
                                    </div>
                                    <div className="inbox-item-preview">
                                        {fromClinician
                                            ? `Patient replied: ${(msg.reply ?? "").slice(0, 50)}...`
                                            : `${msg.body.slice(0, 60)}...`}
                                    </div>
                                </div>
                                {unread && <div className="inbox-item-dot" />}
                            </div>
                        );
                    })}
            </div>

            {/* Thread view */}
            <div className="inbox-thread">
                {!selected ? (
                    <div className="inbox-thread-empty">
                        <div style={{ fontSize: "32px" }}>💬</div>
                        <div style={{ fontSize: "15px", fontWeight: 600, color: "#1e293b", marginTop: "12px" }}>Select a message</div>
                        <div style={{ fontSize: "13px", color: "#94a3b8", marginTop: "4px" }}>Choose a conversation from the left</div>
                    </div>
                ) : (
                    <>
                        <div className="inbox-thread-header">
                            <div className="inbox-thread-avatar">
                                {selected.patientName.split(" ").map(n => n[0]).slice(0, 2).join("").toUpperCase()}
                            </div>
                            <div>
                                <div className="inbox-thread-name">{selected.patientName}</div>
                                <div className="inbox-thread-time">{new Date(selected.sentAt).toLocaleString("en-US", { month: "long", day: "numeric", hour: "numeric", minute: "2-digit" })}</div>
                            </div>
                        </div>

                        <div className="inbox-thread-body">
                            <div className="inbox-thread-subject">{selected.subject}</div>

                            {selected.fromRole === "clinician" ? (
                                <>
                                    {/* Clinician sent this — show their message on right, patient reply on left */}
                                    <div className="inbox-bubble inbox-bubble-clinician">
                                        <div className="inbox-bubble-label">You (Dr. Emily Chen)</div>
                                        <div className="inbox-bubble-text">{selected.body}</div>
                                    </div>
                                    {selected.reply && (
                                        <div className="inbox-bubble inbox-bubble-patient">
                                            <div className="inbox-bubble-label">Patient</div>
                                            <div className="inbox-bubble-text">{selected.reply}</div>
                                        </div>
                                    )}
                                </>
                            ) : (
                                <>
                                    {/* Patient sent this — show their message on left, clinician reply on right */}
                                    <div className="inbox-bubble inbox-bubble-patient">
                                        <div className="inbox-bubble-label">Patient</div>
                                        <div className="inbox-bubble-text">{selected.body}</div>
                                    </div>
                                    {selected.reply && (
                                        <div className="inbox-bubble inbox-bubble-clinician">
                                            <div className="inbox-bubble-label">You (Dr. Emily Chen)</div>
                                            <div className="inbox-bubble-text">{selected.reply}</div>
                                        </div>
                                    )}
                                    {replySent && !selected.reply && (
                                        <div className="inbox-reply-sent">✓ Reply sent successfully</div>
                                    )}
                                </>
                            )}
                        </div>

                        {selected.fromRole !== "clinician" && !selected.reply && !replySent && (
                            <div className="inbox-reply-box">
                                <textarea
                                    className="inbox-reply-input"
                                    placeholder="Type your reply to the patient..."
                                    value={replyText}
                                    onChange={e => setReplyText(e.target.value)}
                                    rows={3}
                                />
                                <div className="inbox-reply-footer">
                                    <span style={{ fontSize: "12px", color: "#94a3b8" }}>
                                        Patient will see this reply in their portal
                                    </span>
                                    <button
                                        className="inbox-reply-btn"
                                        onClick={handleReply}
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