import { useEffect, useState } from "react";
import { getRecommendations } from "../api/client";
import type { RecommendationResponse } from "../types";
import "./CareRecommendations.css";

interface Props {
  patientId: string;
}

const CATEGORY_ICONS: Record<string, string> = {
  Diet: "🥗",
  Exercise: "🏃",
  Medication: "💊",
  Monitoring: "📊",
  Lifestyle: "🌿",
};

const PRIORITY_ORDER: Record<string, number> = { High: 0, Medium: 1, Low: 2 };

export default function CareRecommendations({ patientId }: Props) {
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setData(null);
    getRecommendations(patientId)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load recommendations"))
      .finally(() => setLoading(false));
  }, [patientId]);

  if (loading) {
    return (
      <div className="cr-loading">
        <div className="cr-spinner" />
        <p>Generating personalized recommendations…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="cr-error">
        <span>⚠</span>
        <p>{error}</p>
      </div>
    );
  }

  if (!data) return null;

  const sorted = [...data.recommendations].sort(
    (a, b) => (PRIORITY_ORDER[a.priority] ?? 9) - (PRIORITY_ORDER[b.priority] ?? 9)
  );

  return (
    <div className="cr-root">
      <div className="cr-summary-card">
        <div className="cr-summary-label">✦ AI Assessment</div>
        <p className="cr-summary-text">{data.summary}</p>
      </div>

      <div className="cr-list">
        {sorted.map((rec, i) => (
          <div key={i} className={`cr-card cr-priority-${rec.priority.toLowerCase()}`}>
            <div className="cr-card-left">
              <span className="cr-icon">{CATEGORY_ICONS[rec.category] ?? "📋"}</span>
            </div>
            <div className="cr-card-body">
              <div className="cr-card-top">
                <span className="cr-category">{rec.category}</span>
                <span className={`cr-badge cr-badge-${rec.priority.toLowerCase()}`}>
                  {rec.priority}
                </span>
              </div>
              <div className="cr-title">{rec.title}</div>
              <div className="cr-detail">{rec.detail}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="cr-disclaimer">
        These recommendations are AI-generated based on available clinical data and are intended
        to support, not replace, clinical judgment. Always consult your healthcare provider.
      </div>
    </div>
  );
}
