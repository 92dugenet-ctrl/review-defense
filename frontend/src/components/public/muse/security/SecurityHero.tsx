import { MuseScene, Reveal } from "../MuseScene";

export function SecurityHero() {
  return (
    <MuseScene className="muse-hero">
      <div className="muse-two">
        <Reveal>
          <div className="muse-eyebrow">SÉCURITÉ / CONTRÔLE</div>
          <h1>
            Voir ce qui est contrôlé.
            <br />
            <em>Comprendre ce qui reste humain.</em>
          </h1>
        </Reveal>

        <Reveal>
          <p>
            Accès, permissions, historique, contexte des preuves et
            validations forment le cadre de travail.
          </p>
        </Reveal>
      </div>
    </MuseScene>
  );
}
