import { useEffect, useState } from "react";
import { getActiveMedications, getObservations } from "../api/client";
import type { MedicationSummary, ObservationPoint, PatientSummary } from "../types";
import "./PatientHeader.css";

interface Props {
  patient: PatientSummary;
}

// LOINC codes matching the backend
const GLUCOSE_CODES = new Set(["15074-8", "2339-0"]);
const HBA1C_CODES = new Set(["4548-4", "17856-6"]);

function latestByCode(obs: ObservationPoint[], codes: Set<string>): ObservationPoint | undefined {
  return obs
    .filter((o) => codes.has(o.code) && o.value != null)
    .sort((a, b) => (b.effective_date ?? "").localeCompare(a.effective_date ?? ""))[0];
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function calculateAge(birthDate?: string): string {
  if (!birthDate) return "—";
  const diff = Date.now() - new Date(birthDate).getTime();
  return `${Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25))} yrs`;
}

export default function PatientHeader({ patient }: Props) {
  const [observations, setObservations] = useState<ObservationPoint[]>([]);
  const [medications, setMedications] = useState<MedicationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      getObservations(patient.id),
      getActiveMedications(patient.id),
    ])
      .then(([obs, meds]) => {
        setObservations(obs);
        setMedications(meds);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load clinical data"))
      .finally(() => setLoading(false));
  }, [patient.id]);

  const latestGlucose = latestByCode(observations, GLUCOSE_CODES);
  const latestHba1c = latestByCode(observations, HBA1C_CODES);

  return (
    <div className="patient-header">
      <div className="header-top">
        <div className="patient-avatar">
          {patient.full_name.charAt(0).toUpperCase()}
        </div>
        <div className="patient-identity">
          <h2 className="patient-name">{patient.full_name}</h2>
          <div className="patient-demo">
            <span>{calculateAge(patient.birth_date)}</span>
            <span className="demo-sep">·</span>
            <span>{patient.gender ? patient.gender.charAt(0).toUpperCase() + patient.gender.slice(1) : "Unknown"}</span>
            <span className="demo-sep">·</span>
            <span>DOB: {formatDate(patient.birth_date)}</span>
          </div>
          <div className="patient-contact">
            {patient.phone && <span>📞 {patient.phone}</span>}
            {patient.address && <span>📍 {patient.address}</span>}
          </div>
        </div>
      </div>

      <div className="clinical-summary">
        <h3>Clinical Summary</h3>

        {loading && <p className="summary-loading">Loading clinical data…</p>}
        {error && <p className="summary-error">{error}</p>}

        {!loading && !error && (
          <div className="summary-grid">
            <div className="summary-card">
              <div className="summary-label">Latest Glucose</div>
              {latestGlucose ? (
                <>
                  <div className="summary-value">
                    {latestGlucose.value} <span className="summary-unit">{latestGlucose.unit}</span>
                  </div>
                  <div className="summary-date">{formatDate(latestGlucose.effective_date)}</div>
                </>
              ) : (
                <div className="summary-value summary-none">No data</div>
              )}
            </div>

            <div className="summary-card">
              <div className="summary-label">Latest HbA1c</div>
              {latestHba1c ? (
                <>
                  <div className="summary-value">
                    {latestHba1c.value} <span className="summary-unit">{latestHba1c.unit}</span>
                  </div>
                  <div className="summary-date">{formatDate(latestHba1c.effective_date)}</div>
                </>
              ) : (
                <div className="summary-value summary-none">No data</div>
              )}
            </div>

            <div className="summary-card">
              <div className="summary-label">Active Medications</div>
              {medications.length === 0 ? (
                <div className="summary-value summary-none">None</div>
              ) : (
                <ul className="med-list">
                  {medications.slice(0, 4).map((m) => (
                    <li key={m.id} className="med-item">
                      <span className="med-name">{m.medication_name}</span>
                      {m.dosage_instruction && (
                        <span className="med-dose">{m.dosage_instruction}</span>
                      )}
                    </li>
                  ))}
                  {medications.length > 4 && (
                    <li className="med-more">+{medications.length - 4} more</li>
                  )}
                </ul>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
