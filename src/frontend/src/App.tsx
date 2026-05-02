import { useState } from "react";
import PatientSearch from "./components/PatientSearch";
import PatientRecord from "./components/PatientRecord";
import Login from "./components/Login";
import { getToken, setToken, clearToken } from "./api/client";
import type { LoginResponse } from "./api/client";
import type { PatientSummary } from "./types";
import "./App.css";

type Portal = "clinician" | "patient";

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(!!getToken());
  const [portal, setPortal] = useState<Portal>("clinician");
  const [selectedPatient, setSelectedPatient] = useState<PatientSummary | null>(null);

  const handleLogin = (data: LoginResponse) => {
    setToken(data.access_token);
    setPortal(data.role === "patient" ? "patient" : "clinician");
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    clearToken();
    setIsLoggedIn(false);
    setSelectedPatient(null);
  };

  if (!isLoggedIn) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className={`app ${portal === "patient" ? "patient-portal" : ""}`}>
      <header className="app-header">
        <span className="app-title">Diabetes Management Portal</span>
        <div className="portal-toggle">
          <button className={`toggle-btn ${portal === "clinician" ? "active" : ""}`} onClick={() => setPortal("clinician")}>
            Clinician Portal
          </button>
          <button className={`toggle-btn ${portal === "patient" ? "active" : ""}`} onClick={() => setPortal("patient")}>
            Patient Portal
          </button>
          <button onClick={handleLogout} style={{ marginLeft: "1rem", fontSize: "13px", color: "#64748b", background: "none", border: "none", cursor: "pointer" }}>
            Log out
          </button>
        </div>
      </header>
      <main className="app-main">
        {!selectedPatient ? (
          <div className="search-page">
            <PatientSearch onSelect={setSelectedPatient} portal={portal} />
          </div>
        ) : (
          <PatientRecord patient={selectedPatient} portal={portal} onBack={() => setSelectedPatient(null)} />
        )}
      </main>
    </div>
  );
}
