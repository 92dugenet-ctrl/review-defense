import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { FeedbackMessage } from "@/components/layout/FeedbackMessage";
import { PageHeading } from "@/components/layout/PageHeading";
import { api } from "@/services/api/client";

type QueueItem = {
  case_id: string;
  priority?: string;
  priority_score?: number;
  status?: string;
  sla?: { status?: string };
};

type QueueResponse = {
  items?: QueueItem[];
};

type WorkloadResponse = {
  items?: Array<{ case_count?: number | string }>;
};

/** Presents the review queue, its priority counts and the current workload. */
export function AnalysisPage() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [workload, setWorkload] = useState<WorkloadResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api.get<QueueResponse>("/v1/review-queue"),
      api.get<WorkloadResponse>("/v1/review-queue/workload"),
    ])
      .then(([queueResponse, workloadResponse]) => {
        setQueue(queueResponse.items ?? []);
        setWorkload(workloadResponse);
      })
      .catch((caught) => {
        setError(
          caught instanceof Error
            ? caught.message
            : "Impossible de charger la file d’analyse.",
        );
      })
      .finally(() => setLoading(false));
  }, []);

  function countByPriority(priority: string) {
    return queue.filter(
      (item) => String(item.priority).toUpperCase() === priority,
    ).length;
  }

  const totalWorkload = (workload?.items ?? []).reduce(
    (total, row) => total + (Number(row.case_count) || 0),
    0,
  );

  return (
    <section className="workspace">
      <PageHeading
        as="header"
        className="module-heading"
        eyebrow="ANALYSE"
        title="La file de travail."
        description="Priorisez ce qui mérite une lecture humaine et gardez une vue claire de la charge."
        action={
          <Link className="module-refresh" to="/app/analysis">
            Actualiser
          </Link>
        }
      />

      {error && (
        <FeedbackMessage className="form-error" role="alert">
          {error}
        </FeedbackMessage>
      )}

      <div className="analysis-kpis">
        <div>
          <span>TOTAL</span>
          <strong>{loading ? "—" : queue.length}</strong>
        </div>
        <div>
          <span>CRITIQUES</span>
          <strong>{loading ? "—" : countByPriority("CRITICAL")}</strong>
        </div>
        <div>
          <span>ÉLEVÉS</span>
          <strong>{loading ? "—" : countByPriority("HIGH")}</strong>
        </div>
        <div>
          <span>CHARGE</span>
          <strong>{loading ? "—" : totalWorkload}</strong>
        </div>
      </div>

      <div className="module-table">
        <table>
          <thead>
            <tr>
              <th>Dossier</th>
              <th>Priorité</th>
              <th>Score</th>
              <th>SLA</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {queue.map((item) => (
              <tr key={item.case_id}>
                <td>
                  <Link
                    className="review-open"
                    to={`/app/cases/${item.case_id}`}
                  >
                    {item.case_id}
                  </Link>
                </td>
                <td>
                  <span
                    className={
                      "priority-pill priority-" +
                      String(item.priority ?? "low").toLowerCase()
                    }
                  >
                    {item.priority ?? item.status}
                  </span>
                </td>
                <td>{item.priority_score ?? "—"}</td>
                <td>{item.sla?.status ?? "—"}</td>
                <td>
                  <Link
                    className="review-open"
                    to={`/app/cases/${item.case_id}`}
                  >
                    Ouvrir →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {!loading && !queue.length && (
          <FeedbackMessage className="module-empty">
            Aucun élément dans la file.
          </FeedbackMessage>
        )}

        {loading && (
          <FeedbackMessage className="module-empty">
            Chargement de la file…
          </FeedbackMessage>
        )}
      </div>
    </section>
  );
}
