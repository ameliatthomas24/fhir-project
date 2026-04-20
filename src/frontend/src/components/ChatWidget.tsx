import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "../api/client";
import type { ChatMessage } from "../types";
import "./ChatWidget.css";

interface Props {
    open: boolean;
    onClose: () => void;
    patientId: string;
}

const DISCLAIMER =
    "I'm your personal health assistant, here to help you understand your health data and navigate this portal. For urgent concerns or emergencies, please contact your care team directly or call 911. Do not share sensitive personal information beyond what is already in your health record.";

export default function ChatWidget({ open, onClose, patientId }: Props) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [minimized, setMinimized] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (open && !minimized) inputRef.current?.focus();
    }, [open, minimized]);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    function handleClose() {
        setMessages([]);
        setInput("");
        setMinimized(false);
        onClose();
    }

    async function handleSend() {
        const text = input.trim();
        if (!text || loading) return;

        const userMsg: ChatMessage = { role: "user", content: text };
        const updated = [...messages, userMsg];
        setMessages(updated);
        setInput("");
        setLoading(true);

        try {
            const reply = await sendChatMessage(patientId, updated);
            setMessages([...updated, { role: "assistant", content: reply }]);
        } catch {
            setMessages([
                ...updated,
                { role: "assistant", content: "I'm having trouble connecting right now. Please try again in a moment." },
            ]);
        } finally {
            setLoading(false);
        }
    }

    function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    }

    if (!open) return null;

    if (minimized) {
        return (
            <div className="cw-minimized" onClick={() => setMinimized(false)}>
                <span className="cw-min-star">✦</span>
                <span className="cw-min-label">Health Assistant</span>
                {messages.length > 0 && (
                    <span className="cw-min-badge">{messages.length}</span>
                )}
            </div>
        );
    }

    return (
        <div className="cw-overlay">
            <div className="cw-window">
                <div className="cw-header">
                    <div className="cw-header-left">
                        <span className="cw-header-star">✦</span>
                        <span className="cw-header-title">Health Assistant</span>
                    </div>
                    <div className="cw-header-actions">
                        <button className="cw-minimize" onClick={() => setMinimized(true)} aria-label="Minimize chat">—</button>
                        <button className="cw-close" onClick={handleClose} aria-label="Close chat">✕</button>
                    </div>
                </div>

                <div className="cw-disclaimer">
                    <span className="cw-disclaimer-icon">ℹ</span>
                    <p>{DISCLAIMER}</p>
                </div>

                <div className="cw-messages">
                    {messages.length === 0 && (
                        <div className="cw-empty">
                            Ask me anything about your health data or how to use this portal.
                        </div>
                    )}
                    {messages.map((msg, i) => (
                        <div key={i} className={`cw-bubble-wrap ${msg.role}`}>
                            {msg.role === "assistant" && (
                                <div className="cw-bot-avatar">✦</div>
                            )}
                            <div className={`cw-bubble ${msg.role}`}>{msg.content}</div>
                        </div>
                    ))}
                    {loading && (
                        <div className="cw-bubble-wrap assistant">
                            <div className="cw-bot-avatar">✦</div>
                            <div className="cw-bubble assistant cw-typing">
                                <span /><span /><span />
                            </div>
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>

                <div className="cw-input-area">
                    <textarea
                        ref={inputRef}
                        className="cw-input"
                        placeholder="Ask about your health data..."
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        rows={1}
                        disabled={loading}
                    />
                    <button
                        className="cw-send"
                        onClick={handleSend}
                        disabled={!input.trim() || loading}
                        aria-label="Send message"
                    >
                        ↑
                    </button>
                </div>
            </div>
        </div>
    );
}
