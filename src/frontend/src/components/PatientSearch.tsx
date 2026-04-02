import { useState } from "react";
import { searchPatients } from "../api/client";
import type { PatientSummary } from "../types";
import "./PatientSearch.css";

interface Props {
  onSelect: (patient: PatientSummary) => void;
}

function formatDOB(dateStr?: string): string {
  if (!dateStr) return "—";
  const [year, month, day] = dateStr.split("-");
  return `${month}/${day}/${year}`;
}

export default function PatientSearch({ onSelect }: Props) {
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
    <div className="patient-search">
      <h2>Patient Search</h2>
      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by name…"
          className="search-input"
        />
        <button type="submit" className="search-btn" disabled={loading}>
          {loading ? "Searching…" : "Search"}
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
              <span className="result-name">{p.full_name}</span>
              <span className="result-meta">
                DOB: {formatDOB(p.birth_date)} &nbsp;·&nbsp;
                {p.gender ? p.gender.charAt(0).toUpperCase() + p.gender.slice(1) : "Unknown"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
