import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { FeedbackMessage } from "@/components/layout/FeedbackMessage";
import { PageHeading } from "@/components/layout/PageHeading";
import { api } from "@/services/api/client";

type Review = {
  review_id: string;
  rating: number;
  text: string;
  author_display_name?: string | null;
  source?: string;
  published_at?: string | null;
};

type ReviewsResponse = {
  items?: Review[];
};

/** Searchable and filterable list of reviews imported into the workspace. */
export function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [query, setQuery] = useState("");
  const [rating, setRating] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<ReviewsResponse>("/v1/reviews")
      .then((response) => setReviews(response.items ?? []))
      .catch((caught) => {
        setError(
          caught instanceof Error
            ? caught.message
            : "Impossible de charger les avis.",
        );
      })
      .finally(() => setLoading(false));
  }, []);

  const filteredReviews = useMemo(
    () =>
      reviews.filter((review) => {
        const matchesRating =
          rating === "all" || String(review.rating) === rating;
        const searchableText = (
          review.text +
          " " +
          (review.author_display_name ?? "")
        ).toLowerCase();
        const matchesQuery = searchableText.includes(query.toLowerCase());

        return matchesRating && matchesQuery;
      }),
    [reviews, rating, query],
  );

  return (
    <section className="workspace">
      <PageHeading
        as="header"
        className="reviews-heading"
        eyebrow="AVIS"
        title="Votre bibliothèque d’avis."
        description="Recherchez, filtrez et ouvrez un avis pour lancer un dossier."
        action={
          <Link className="button button-secondary" to="/app/cases">
            Voir les dossiers →
          </Link>
        }
      />

      <div className="reviews-toolbar">
        <label>
          Recherche
          <input
            aria-label="Rechercher un avis ou un auteur"
            placeholder="Rechercher un avis ou un auteur…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>

        <label>
          Note
          <select
            aria-label="Filtrer par note"
            value={rating}
            onChange={(event) => setRating(event.target.value)}
          >
            <option value="all">Toutes</option>
            {[5, 4, 3, 2, 1].map((value) => (
              <option key={value} value={value}>
                {value} étoiles
              </option>
            ))}
          </select>
        </label>

        <div className="reviews-summary">
          <span>
            <strong>{loading ? "—" : filteredReviews.length}</strong> résultat
            {filteredReviews.length > 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {error && (
        <FeedbackMessage className="form-error" role="alert">
          {error}
        </FeedbackMessage>
      )}

      <div className="reviews-table-wrap">
        <table className="reviews-table">
          <thead>
            <tr>
              <th>Note</th>
              <th>Avis</th>
              <th>Source</th>
              <th>Date</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filteredReviews.map((review) => (
              <tr key={review.review_id}>
                <td>
                  <span className="review-rating">{review.rating}/5</span>
                </td>
                <td>
                  <div className="review-cell">
                    <strong>{review.author_display_name || "Client"}</strong>
                    <span>{review.text}</span>
                  </div>
                </td>
                <td className="review-source">{review.source || "Google"}</td>
                <td className="review-date">
                  {review.published_at
                    ? new Date(review.published_at).toLocaleDateString("fr-FR")
                    : "—"}
                </td>
                <td>
                  <Link
                    className="review-open"
                    to={`/app/reviews/${review.review_id}`}
                  >
                    Ouvrir →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {!loading && !filteredReviews.length && (
          <div className="reviews-table-empty">
            <strong>Aucun résultat.</strong>
            <span>Modifiez votre recherche ou vos filtres.</span>
          </div>
        )}

        {loading && (
          <div className="reviews-table-empty">Chargement des avis…</div>
        )}
      </div>
    </section>
  );
}
