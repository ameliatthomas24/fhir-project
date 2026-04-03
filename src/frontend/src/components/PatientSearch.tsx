import { useState } from "react"; /*amelia*/
import { searchPatients } from "../api/client";
import type { PatientSummary } from "../types";
import "./PatientSearch.css";

interface Props {
    onSelect: (patient: PatientSummary) => void;
    portal: "clinician" | "patient";
}

function formatDOB(dateStr?: string): string {
    if (!dateStr) return "—";
    const [year, month, day] = dateStr.split("-");
    return `${month}/${day}/${year}`;
}

function getInitials(name: string): string {
    return name.split(" ").map(n => n[0]).slice(0, 2).join("").toUpperCase();
}

export default function PatientSearch({ onSelect, portal }: Props) {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<PatientSummary[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searched, setSearched] = useState(false);

    async function handleSearch(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSearched(true);
        try {
            const patients = await searchPatients(query.trim() || undefined);
            setResults(patients);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Search failed");
            setResults([]);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="search-container">
            <div className="search-header">
                <h1 className="search-title">
                    {portal === "clinician" ? "Clinician Portal" : "Patient Portal"}
                </h1>
                <p className="search-subtitle">
                    {portal === "clinician"
                        ? "Search and manage patient records"
                        : "View your health information"}
                </p>
            </div>

            <div className="search-card">
                <h2 className="search-card-title">Patient Search</h2>
                <form onSubmit={handleSearch} className="search-form">
                    <div className="search-input-wrap">
                        <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
                        </svg>
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search by name..."
                            className="search-input"
                        />
                    </div>
                    <button type="submit" className="search-btn" disabled={loading}>
                        {loading ? "Searching..." : "Search"}
                    </button>
                </form>

                {error && <p className="search-error">{error}</p>}
                {searched && !loading && results.length === 0 && !error && (
                    <p className="search-empty">No patients found.</p>
                )}

                {results.length > 0 && (
                    <ul className="results-list">
                        {results.map((p) => (
                            <li key={p.id} className="result-item" onClick={() => onSelect(p)}>
                                <div className="result-avatar">{getInitials(p.full_name)}</div>
                                <div className="result-info">
                                    <span className="result-name">{p.full_name}</span>
                                    <span className="result-meta">
                                        DOB: {formatDOB(p.birth_date)}
                                        {p.gender && <> &nbsp;·&nbsp; {p.gender.charAt(0).toUpperCase() + p.gender.slice(1)}</>}
                                    </span>
                                </div>
                                <svg className="result-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="m9 18 6-6-6-6" />
                                </svg>
                            </li>
                        ))}
                    </ul>
                )}

                {!searched && (
                    <div className="search-empty-state">
                        <p>Select a patient to view their clinical summary.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
