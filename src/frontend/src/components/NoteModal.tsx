import { useState, useRef, useEffect } from "react";
import "./NoteModal.css";

interface Props {
    open: boolean;
    onClose: () => void;
    onSave: (content: string) => void;
}

export default function NoteModal({ open, onClose, onSave }: Props) {
    const [content, setContent] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (open) textareaRef.current?.focus();
    }, [open]);

    if (!open) return null;

    function handleSave() {
        const trimmed = content.trim();
        if (!trimmed) return;
        onSave(trimmed);
        setContent("");
        onClose();
    }

    function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
        if (e.key === "Escape") onClose();
    }

    return (
        <div className="nm-backdrop" onClick={onClose}>
            <div className="nm-modal" onClick={e => e.stopPropagation()}>
                <div className="nm-header">
                    <span className="nm-title">📝 Add Note</span>
                    <button className="nm-close" onClick={onClose} aria-label="Close">✕</button>
                </div>

                <div className="nm-body">
                    <textarea
                        ref={textareaRef}
                        className="nm-textarea"
                        placeholder="Write your private notes here — observations, reminders, follow-up questions for your care team..."
                        value={content}
                        onChange={e => setContent(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                </div>

                <div className="nm-footer">
                    <button className="nm-cancel" onClick={onClose}>Cancel</button>
                    <button
                        className="nm-save"
                        onClick={handleSave}
                        disabled={!content.trim()}
                    >
                        Save Note
                    </button>
                </div>
            </div>
        </div>
    );
}
