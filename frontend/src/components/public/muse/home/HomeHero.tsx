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
    <section className="scene hero" id="hero">
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

        <div className="muse-word" aria-hidden="true">
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
