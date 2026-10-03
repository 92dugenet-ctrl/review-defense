import { PublicActionLink } from "../PublicActionLink";

export function HomeHero() {
  return (
    <section className="scene hero" id="hero">
      <div className="hero-video-bg">
        <video
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          poster="/visual-workspace.svg"
          aria-label="Présentation de Review Defense"
        >
          <source
            src="https://www.ariaditerra.com/wp-content/uploads/2023/02/coverr-chef-preparing-a-dish-at-a-restaurant-6248-1080p.mp4"
            type="video/mp4"
          />
        </video>
      </div>

      <div className="hero-scrim" />

      <div className="scene-inner hero-inner">
        <div className="eyebrow">REVIEW DEFENSE · EN ACTION</div>
        <h1>
          Voyez comment Review Defense
          <br />
          travaille pour vous
        </h1>
        <p>
          De l'avis reçu au dossier documenté, structurez chaque situation
          avec plus de contexte et de contrôle.
        </p>

        <PublicActionLink to="/register">Créer mon espace</PublicActionLink>

        <div className="muse-word">
          <span>Review</span>
          <b>◌</b>
          <span>Defense</span>
          <em>est</em>
          <strong>votre</strong>
          <em>poste de travail</em>
        </div>
      </div>
    </section>
  );
}
