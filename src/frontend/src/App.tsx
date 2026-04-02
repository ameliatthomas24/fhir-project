import { useState } from "react";
import PatientSearch from "./components/PatientSearch";
import PatientHeader from "./components/PatientHeader";
import type { PatientSummary } from "./types";
import "./App.css";

export default function App() {
  const [selectedPatient, setSelectedPatient] = useState<PatientSummary | null>(null);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Diabetes Management Portal</h1>
      </header>

      <main className="app-main">
        <div className="search-panel">
          <PatientSearch onSelect={setSelectedPatient} />
        </div>

        <div className="detail-panel">
          {selectedPatient ? (
            <PatientHeader patient={selectedPatient} />
          ) : (
            <div className="detail-empty">
              <p>Select a patient to view their clinical summary.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
