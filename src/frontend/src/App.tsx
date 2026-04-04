import { useState } from "react"; /*amelia*/
import PatientSearch from "./components/PatientSearch";
import PatientRecord from "./components/PatientRecord";
import type { PatientSummary } from "./types";
import "./App.css";

type Portal = "clinician" | "patient";

export default function App() {
    const [portal, setPortal] = useState<Portal>("clinician");
    const [selectedPatient, setSelectedPatient] = useState<PatientSummary | null>(null);

    return (
        <div className="app">
            <header className="app-header">
                <span className="app-title">Diabetes Management Portal</span>
                <div className="portal-toggle">
                    <button
                        className={`toggle-btn ${portal === "clinician" ? "active" : ""}`}
                        onClick={() => setPortal("clinician")}
                    >
                        Clinician Portal
                    </button>
                    <button
                        className={`toggle-btn ${portal === "patient" ? "active" : ""}`}
                        onClick={() => setPortal("patient")}
                    >
                        Patient Portal
                    </button>
                </div>
            </header>
            <main className="app-main">
                {!selectedPatient ? (
                    <div className="search-page">
                        <PatientSearch onSelect={setSelectedPatient} portal={portal} />
                    </div>
                ) : (
                    <PatientRecord
                        patient={selectedPatient}
                        portal={portal}
                        onBack={() => setSelectedPatient(null)}
                    />
                )}
            </main>
        </div>
    );
}