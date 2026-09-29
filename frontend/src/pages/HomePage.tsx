import { Link } from "react-router-dom";

export function HomePage() {
  return (
    <main className="marketing-page">
      <header className="marketing-header">
        <div className="brand">
          <span className="brand-mark">RD</span>
          <span><strong>Review Defense</strong><small>Plateforme de travail</small></span>
        </div>
        <nav aria-label="Navigation publique">
          <a href="#platform">Plateforme</a>
          <a href="#principles">Principes</a>
          <Link to="/login">Connexion</Link>
        </nav>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">REVIEW DEFENSE · PLATFORM</span>
          <h1>Comprendre. Documenter. Préparer.</h1>
          <p>
            Une base SaaS structurée pour analyser les avis, organiser les dossiers,
            relier les preuves et garder les décisions sous contrôle humain.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" to="/app">Ouvrir le workspace</Link>
            <a className="button button-secondary" href="#platform">Découvrir la plateforme</a>
          </div>
        </div>

        <div className="hero-card" aria-label="Aperçu du workspace">
          <div className="hero-card-header">
            <span className="signal">●</span>
            <span>Workspace</span>
            <span className="muted">Review Defense</span>
          </div>
          <div className="hero-card-grid">
            <div><small>AVIS</small><strong>124</strong><span>à analyser</span></div>
            <div><small>DOSSIERS</small><strong>18</strong><span>ouverts</span></div>
            <div><small>PREUVES</small><strong>73</strong><span>reliées</span></div>
          </div>
          <div className="hero-card-line"><span /><span /><span /></div>
        </div>
      </section>

      <section id="platform" className="feature-grid">
        {[
          ["01", "Une architecture claire", "Les surfaces métier sont séparées des services, hooks, types et composants UI."],
          ["02", "Des contrats explicites", "Le frontend consommera directement les routes et réponses du backend existant."],
          ["03", "Une expérience cohérente", "Tokens, composants et états communs évitent les interfaces isolées et incohérentes."]
        ].map(([number, title, body]) => (
          <article className="feature-card" key={number}>
            <span>{number}</span>
            <h2>{title}</h2>
            <p>{body}</p>
          </article>
        ))}
      </section>

      <section id="principles" className="principles">
        <span className="eyebrow">FOUNDATION</span>
        <h2>Le produit sera construit autour du workflow réel.</h2>
        <p>Pas de faux endpoints, pas de logique métier dupliquée dans l’interface, pas de dépendance à l’ancien frontend.</p>
      </section>
    </main>
  );
}