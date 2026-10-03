import { useEffect, useRef } from "react";

import { PublicActionLink } from "../PublicActionLink";

export function HomeHero() {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const syncPlayback = () => {
      if (motionPreference.matches) {
        video?.pause();
        return;
      }
      void video?.play().catch(() => undefined);
    };

    syncPlayback();
    motionPreference.addEventListener("change", syncPlayback);
    return () => motionPreference.removeEventListener("change", syncPlayback);
  }, []);

  return (
    <section className="scene hero" id="hero" aria-labelledby="home-hero-title">
      <div className="hero-video-bg" aria-hidden="true">
        <video
          ref={videoRef}
          muted
          loop
          playsInline
          preload="metadata"
          poster="/visual-workspace.svg"
        >
          <source
            src="/assets/hero/review-defense-hero-centered-fixed-1920x1080.mp4"
            type="video/mp4"
          />
        </video>
      </div>
      <div className="hero-scrim" />

      <div className="scene-inner hero-inner">
        <div className="hero-copy">
          <div className="eyebrow">LA GESTION DES AVIS, ENFIN STRUCTURÉE</div>
          <h1 id="home-hero-title">
            Voyez plus clair.
            <br />
            Agissez avec méthode.
          </h1>
          <p>
            Review Defense vous aide à analyser les avis, réunir les éléments
            utiles et suivre chaque dossier en gardant la maîtrise des décisions.
          </p>
          <div className="hero-actions">
            <PublicActionLink to="/register">Créer mon espace</PublicActionLink>
            <a className="hero-secondary-link" href="#products">
              Découvrir la solution <span aria-hidden="true">↓</span>
            </a>
          </div>
        </div>

        <div className="hero-bottom-line" aria-hidden="true">
          <span>ANALYSE</span>
          <i />
          <span>DOCUMENTATION</span>
          <i />
          <span>VALIDATION</span>
          <i />
          <span>SUIVI</span>
        </div>
      </div>
    </section>
  );
}
