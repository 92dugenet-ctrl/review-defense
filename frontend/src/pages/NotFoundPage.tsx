import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <main className="center-page">
      <span className="eyebrow">404</span>
      <h1>Page introuvable</h1>
      <p>Cette route ne fait pas partie du frontend actuel.</p>
      <Link className="button button-primary" to="/">Retour à l’accueil</Link>
    </main>
  );
}