import { MuseScene } from "../MuseScene";
import { PublicActionLink } from "../PublicActionLink";

export function HomeSocial() {
  return (
    <MuseScene className="social" id="about">
      <div>
        <div className="social-head">
          <div>
            <div className="eyebrow">REVIEW DEFENSE</div>
            <h2>Autour du dossier, tout reste lisible.</h2>
          </div>
          <PublicActionLink to="/securite">Voir les contrôles</PublicActionLink>
        </div>
        <div className="social-grid">
          <div className="social-main">
            <img src="/visual-workspace.svg" alt="Travail collectif Review Defense" />
            <span>Travaillez là où vous êtes</span>
            <strong>Un même contexte pour les personnes qui interviennent.</strong>
          </div>
          {["Analyse", "Preuves", "Validation", "Suivi"].map((item) => (
            <div className="social-mini" key={item}>{item}</div>
          ))}
        </div>
      </div>
    </MuseScene>
  );
}
