import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/Button";
import { ApiError, api } from "@/services/api/client";
import type { Case, NotificationItem, Review, ReviewQueueItem } from "@/types/api";

type DashboardState = { reviews: Review[]; cases: Case[]; queue: ReviewQueueItem[]; notifications: NotificationItem[] };

function formatDate(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "short", year: "numeric" }).format(date);
}
function statusLabel(status?: string) {
  if (!status) return "Inconnu";
  return status.replaceAll("_", " ").toLowerCase().replace(/^./, (char) => char.toUpperCase());
}
function priorityClass(priority?: string) {
  const value = priority?.toUpperCase();
  if (value === "CRITICAL" || value === "HIGH") return "dashboard-priority dashboard-priority-high";
  if (value === "MEDIUM" || value === "NORMAL") return "dashboard-priority dashboard-priority-medium";
  return "dashboard-priority dashboard-priority-low";
}

export function DashboardPage() {
  const [state, setState] = useState<DashboardState>({ reviews: [], cases: [], queue: [], notifications: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const loadDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const [reviews, cases, queue, notifications] = await Promise.all([
        api.get<{ items: Review[] }>("/v1/reviews"),
        api.get<{ items: Case[] }>("/v1/cases"),
        api.get<{ items: ReviewQueueItem[] }>("/v1/review-queue"),
        api.get<{ items: NotificationItem[] }>("/v1/notifications"),
      ]);
      setState({ reviews: reviews.items ?? [], cases: cases.items ?? [], queue: queue.items ?? [], notifications: notifications.items ?? [] });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught : new ApiError("Impossible de charger le tableau de bord.", 0));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void loadDashboard(); }, []);

  const averageRating = useMemo(() => {
    if (!state.reviews.length) return "—";
    return (state.reviews.reduce((sum, review) => sum + review.rating, 0) / state.reviews.length).toFixed(1);
  }, [state.reviews]);
  const openCases = state.cases.filter((item) => !["CLOSED", "RESOLVED"].includes(item.status.toUpperCase())).length;
  const pendingNotifications = state.notifications.filter((item) => !["SENT", "CANCELLED", "DELIVERED"].includes(item.status.toUpperCase())).length;
  const recentReviews = [...state.reviews].sort((a, b) => new Date(b.published_at ?? 0).getTime() - new Date(a.published_at ?? 0).getTime()).slice(0, 5);

  return (
    <section className="dashboard-page">
      <div className="dashboard-heading">
        <div><span className="eyebrow">REVIEW DEFENSE · PILOTAGE</span><h1>Vue d’ensemble</h1><p>Suivez vos avis, dossiers et actions prioritaires depuis un seul espace.</p></div>
        <Button variant="secondary" onClick={() => void loadDashboard()} disabled={loading}>{loading ? "Actualisation…" : "Actualiser"}</Button>
      </div>

      {error && <div className="dashboard-error" role="alert"><div><strong>Le tableau de bord n’a pas pu être actualisé.</strong><span>{error.message}</span></div><Button variant="secondary" onClick={() => void loadDashboard()}>Réessayer</Button></div>}

      <div className="dashboard-kpis" aria-label="Indicateurs principaux">
        <article className="dashboard-kpi"><span className="dashboard-kpi-label">Avis suivis</span><strong>{loading ? "…" : state.reviews.length}</strong><span className="dashboard-kpi-meta">Toutes sources</span></article>
        <article className="dashboard-kpi"><span className="dashboard-kpi-label">Note moyenne</span><strong>{loading ? "…" : averageRating}</strong><span className="dashboard-kpi-meta">{state.reviews.length ? "Sur 5" : "Aucun avis"}</span></article>
        <article className="dashboard-kpi"><span className="dashboard-kpi-label">Dossiers ouverts</span><strong>{loading ? "…" : openCases}</strong><span className="dashboard-kpi-meta">À traiter</span></article>
        <article className="dashboard-kpi dashboard-kpi-accent"><span className="dashboard-kpi-label">Actions en attente</span><strong>{loading ? "…" : pendingNotifications}</strong><span className="dashboard-kpi-meta">Notifications</span></article>
      </div>

      <div className="dashboard-grid">
        <article className="dashboard-card">
          <div className="dashboard-card-heading"><div><span className="dashboard-card-kicker">ACTIVITÉ</span><h2>Derniers avis</h2></div><a href="/app/reviews">Voir tous les avis</a></div>
          {loading ? <div className="dashboard-empty">Chargement des avis…</div> : recentReviews.length ? <div className="dashboard-review-list">{recentReviews.map((review) => <div className="dashboard-review-row" key={review.review_id}><div className="dashboard-rating">{review.rating}/5</div><div className="dashboard-review-content"><strong>{review.text || "Avis sans texte"}</strong><span>{review.source} · {formatDate(review.published_at)}</span></div><span className="dashboard-review-source">{review.review_url ? "Voir" : "—"}</span></div>)}</div> : <div className="dashboard-empty"><strong>Aucun avis pour le moment</strong><span>Les avis disponibles apparaîtront ici dès leur synchronisation.</span></div>}
        </article>

        <article className="dashboard-card">
          <div className="dashboard-card-heading"><div><span className="dashboard-card-kicker">PRIORITÉS</span><h2>File de traitement</h2></div><a href="/app/cases">Dossiers</a></div>
          {loading ? <div className="dashboard-empty">Chargement…</div> : state.queue.length ? <div className="dashboard-queue">{state.queue.slice(0, 5).map((item) => <div className="dashboard-queue-row" key={item.case_id}><div><strong>{item.case_id.slice(0, 12)}</strong><span>{statusLabel(item.status)}{item.assigned_to ? " · " + item.assigned_to : ""}</span></div><span className={priorityClass(item.priority)}>{statusLabel(item.priority)}</span></div>)}</div> : <div className="dashboard-empty"><strong>File vide</strong><span>Aucun dossier prioritaire à afficher.</span></div>}
        </article>
      </div>

      <div className="dashboard-footer-grid">
        <article className="dashboard-card">
          <div className="dashboard-card-heading"><div><span className="dashboard-card-kicker">DOSSIERS</span><h2>État du portefeuille</h2></div><a href="/app/cases">Ouvrir</a></div>
          <div className="dashboard-status-list">{["OPEN", "IN_REVIEW", "RESOLVED", "CLOSED"].map((status) => <div key={status}><span>{statusLabel(status)}</span><strong>{loading ? "…" : state.cases.filter((item) => item.status.toUpperCase() === status).length}</strong></div>)}</div>
        </article>

        <article className="dashboard-card">
          <div className="dashboard-card-heading"><div><span className="dashboard-card-kicker">SUIVI</span><h2>Dernière activité</h2></div><a href="/app/notifications">Notifications</a></div>
          {state.notifications.length ? <div className="dashboard-notification"><span className="dashboard-notification-dot" /><div><strong>{pendingNotifications ? pendingNotifications + " action" + (pendingNotifications > 1 ? "s" : "") + " en attente" : "Aucune action urgente"}</strong><span>Dernier élément : {formatDate(state.notifications[0].created_at)}</span></div></div> : <div className="dashboard-empty"><strong>Aucune notification</strong><span>Votre activité récente apparaîtra ici.</span></div>}
        </article>
      </div>
    </section>
  );
}
