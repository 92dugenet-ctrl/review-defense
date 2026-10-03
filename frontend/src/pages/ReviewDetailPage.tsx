// Détail d'un avis importé : charge /v1/reviews/{id} à partir du paramètre de route.
// L'écran expose les informations et signaux associés, puis peut demander la création d'un dossier
// via /v1/cases. La création effective, les contrôles de doublon et l'association à l'organisation
// sont décidés par l'API ; la navigation ne fait qu'ouvrir le dossier retourné.

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { BackLink } from "@/components/layout/BackLink";
import { DetailMeta } from "@/components/layout/DetailMeta";
import { FeedbackMessage } from "@/components/layout/FeedbackMessage";
import { SignalRow } from "@/components/layout/SignalRow";
import { api } from "@/services/api/client";

type ReviewDetails = {
  review?: {
    source?: string;
    rating?: number;
    author_display_name?: string | null;
    published_at?: string | null;
    text?: string;
    review_url?: string;
  };
  policy_signals?: unknown[];
};

/** Shows one imported review and lets the user open a case for further work. */
export function ReviewDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState<ReviewDetails | null>(null);
  const [error, setError] = useState("");
  const [creatingCase, setCreatingCase] = useState(false);

  useEffect(() => {
    if (!id) return;

    api
      .get<ReviewDetails>(`/v1/reviews/${id}`)
      .then(setData)
      .catch((caught) => {
        setError(
          caught instanceof Error ? caught.message : "Avis introuvable",
        );
      });
  }, [id]);

  async function createCase() {
    if (!id) return;

    setCreatingCase(true);
    setError("");

    try {
      const response = await api.post<{ case?: { case_id?: string } }>(
        "/v1/cases",
        { review_id: id },
      );
      navigate(`/app/cases/${response.case?.case_id ?? ""}`);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Impossible de créer le dossier",
      );
    } finally {
      setCreatingCase(false);
    }
  }

  if (error) {
    return (
      <section className="workspace">
        <FeedbackMessage className="form-error">{error}</FeedbackMessage>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="workspace">
        <FeedbackMessage className="empty">Chargement…</FeedbackMessage>
      </section>
    );
  }

  const review = data.review ?? {};

  return (
    <section className="workspace">
      <BackLink to="/app/reviews">← Tous les avis</BackLink>

      <div className="detail-layout">
        <article className="panel detail-main">
          <span className="eyebrow">AVIS · {review.source ?? "SOURCE"}</span>

          <div className="detail-rating">
            <span className={`rating r${review.rating}`}>
              {review.rating}
            </span>

            <div>
              <h1>{review.author_display_name || "Client"}</h1>
              <p>
                {review.published_at
                  ? new Date(review.published_at).toLocaleString("fr-FR")
                  : "Date inconnue"}
              </p>
            </div>
          </div>

          <blockquote>“{review.text}”</blockquote>

          <DetailMeta>
            <span>Source</span>
            <b>{review.source ?? "—"}</b>

            <span>URL</span>
            <b>
              {review.review_url ? (
                <a
                  href={review.review_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Ouvrir la source →
                </a>
              ) : (
                "—"
              )}
            </b>
          </DetailMeta>
        </article>

        <aside className="panel">
          <span className="eyebrow">ANALYSE</span>
          <h2>Signaux détectés</h2>

          {(data.policy_signals ?? []).map((signal, index) => (
            <SignalRow key={index}>
              {typeof signal === "string"
                ? signal
                : JSON.stringify(signal)}
            </SignalRow>
          ))}

          {!data.policy_signals?.length && (
            <FeedbackMessage className="empty">
              Aucun signal remonté.
            </FeedbackMessage>
          )}

          <button
            className="button button-dark button-wide"
            onClick={() => void createCase()}
            disabled={creatingCase}
          >
            {creatingCase ? "Création…" : "Créer un dossier →"}
          </button>
        </aside>
      </div>
    </section>
  );
}
