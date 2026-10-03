import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { SectionHeading } from "@/components/layout/SectionHeading";
import { api } from "@/services/api/client";

type ReviewSummary = {
  review_id: string;
  rating: number;
  text: string;
  author_display_name?: string | null;
  published_at?: string | null;
};

type CaseSummary = {
  case_id: string;
  status: string;
  priority?: string;
};

type QueueItem = {
  case_id: string;
  priority?: string;
  priority_score?: number;
  status: string;
};

const CASE_STATUSES = ["OPEN", "IN_PROGRESS", "PENDING", "CLOSED"];

/** Formats a review date for the compact dashboard activity list. */
function formatDate(value?: string | null) {
  return value
    ? new Date(value).toLocaleDateString("fr-FR", {
        day: "2-digit",
        month: "short",
      })
    : "—";
}

/**
 * Organization overview showing recent reviews, active cases and review queue.
 * The page aggregates three read-only API resources for the dashboard widgets.
 */
export function DashboardPage() {
  const [reviews, setReviews] = useState<ReviewSummary[]>([]);
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api.get<{ items: ReviewSummary[] }>("/v1/reviews"),
      api.get<{ items: CaseSummary[] }>("/v1/cases"),
      api.get<{ items: QueueItem[] }>("/v1/review-queue"),
    ])
      .then(([reviewsResponse, casesResponse, queueResponse]) => {
        setReviews(reviewsResponse.items ?? []);
        setCases(casesResponse.items ?? []);
        setQueue(queueResponse.items ?? []);
      })
      .catch((caught) => {
        setError(
          caught instanceof Error
            ? caught.message
            : "Impossible de charger votre activité.",
        );
      })
      .finally(() => setLoading(false));
  }, []);

  const averageRating = reviews.length
    ? (
        reviews.reduce((total, review) => total + review.rating, 0) /
        reviews.length
      ).toFixed(1)
    : "—";

  const criticalCount = queue.filter(
    (item) => String(item.priority).toUpperCase() === "CRITICAL",
  ).length;

  return (
    <section className="dashboard-page">
      <header className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <span className="eyebrow">VUE D’ENSEMBLE</span>
          <h1>
            Votre activité,
            <br />
            <em>en un coup d’œil.</em>
          </h1>
          <p>
            Les signaux importants sont regroupés ici pour que votre équipe
            sache quoi regarder ensuite.
          </p>
        </div>

        <div className="dashboard-hero-actions">
          <Link className="button button-primary" to="/app/reviews">
            Voir les avis →
          </Link>
          <Link className="button button-secondary" to="/app/cases">
            Ouvrir les dossiers
          </Link>
        </div>
      </header>

      {error && (
        <div className="dashboard-error" role="alert">
          <div>
            <strong>Le tableau de bord n’a pas pu être chargé.</strong>
            <span>{error}</span>
          </div>
          <Link className="button button-secondary" to="/app/dashboard">
            Réessayer
          </Link>
        </div>
      )}

      <div className="dashboard-metrics">
        <article>
          <span>Avis suivis</span>
          <strong>{loading ? "—" : reviews.length}</strong>
          <small>dans votre espace</small>
        </article>

        <article className="dashboard-metric-focus">
          <span>Note moyenne</span>
          <strong>{loading ? "—" : averageRating}</strong>
          <small>sur les avis chargés</small>
        </article>

        <article>
          <span>Dossiers</span>
          <strong>{loading ? "—" : cases.length}</strong>
          <small>créés dans l’espace</small>
        </article>

        <article>
          <span>À examiner</span>
          <strong>{loading ? "—" : queue.length}</strong>
          <small>
            {criticalCount
              ? criticalCount +
                " critique" +
                (criticalCount > 1 ? "s" : "")
              : "aucun critique"}
          </small>
        </article>
      </div>

      <div className="dashboard-main-grid">
        <article className="dashboard-surface">
          <SectionHeading
            eyebrow="RÉCENTS"
            title="Derniers avis"
            action={
              <Link to="/app/reviews" className="review-open">
                Tout voir →
              </Link>
            }
          />

          {reviews.slice(0, 6).map((review) => (
            <Link
              className="dashboard-review-row"
              key={review.review_id}
              to={`/app/reviews/${review.review_id}`}
            >
              <span className="dashboard-rating">
                {review.rating}
                <small>/5</small>
              </span>

              <div className="dashboard-review-content">
                <strong>{review.author_display_name || "Client"}</strong>
                <span>
                  {review.text.length > 120
                    ? review.text.slice(0, 120) + "…"
                    : review.text}
                </span>
              </div>

              <time>{formatDate(review.published_at)}</time>
              <b>→</b>
            </Link>
          ))}

          {!reviews.length && !loading && (
            <div className="dashboard-empty">
              <strong>Aucun avis à afficher.</strong>
              <span>Les nouveaux avis apparaîtront ici.</span>
            </div>
          )}
        </article>

        <article className="dashboard-surface">
          <SectionHeading
            eyebrow="PRIORITÉ"
            title="À examiner"
            action={
              <Link to="/app/analysis" className="review-open">
                Analyse →
              </Link>
            }
          />

          {queue.slice(0, 6).map((item) => (
            <Link
              className="dashboard-queue-row"
              key={item.case_id}
              to={`/app/cases/${item.case_id}`}
            >
              <i>!</i>
              <div>
                <strong>Dossier {item.case_id.slice(0, 8)}</strong>
                <span>
                  Score {item.priority_score ?? "—"} · {item.status}
                </span>
              </div>
              <span
                className={
                  "dashboard-priority dashboard-priority-" +
                  String(item.priority ?? "low").toLowerCase()
                }
              >
                {item.priority ?? "standard"}
              </span>
            </Link>
          ))}

          {!queue.length && !loading && (
            <div className="dashboard-empty">
              <strong>La file est vide.</strong>
              <span>Aucune intervention prioritaire actuellement.</span>
            </div>
          )}
        </article>
      </div>

      <div className="dashboard-lower-grid">
        <article className="dashboard-surface">
          <SectionHeading eyebrow="RÉPARTITION" title="État des dossiers" />

          <div className="dashboard-status-list">
            {CASE_STATUSES.map((status) => (
              <div key={status}>
                <span>{status.replace("_", " ")}</span>
                <strong>
                  {cases.filter(
                    (item) => String(item.status).toUpperCase() === status,
                  ).length}
                </strong>
              </div>
            ))}
          </div>
        </article>

        <article className="dashboard-surface">
          <SectionHeading
            eyebrow="PROCHAINE ÉTAPE"
            title="Continuer le travail"
          />

          <div className="dashboard-next-content">
            <i>→</i>
            <div>
              <strong>
                {queue[0]
                  ? "Dossier " + queue[0].case_id.slice(0, 8)
                  : "Aucun dossier prioritaire"}
              </strong>
              <span>
                {queue[0]
                  ? "Revoir les éléments et ouvrir le dossier."
                  : "Votre espace est à jour."}
              </span>
            </div>

            {queue[0] && (
              <Link to={`/app/cases/${queue[0].case_id}`}>Ouvrir →</Link>
            )}
          </div>
        </article>
      </div>
    </section>
  );
}
