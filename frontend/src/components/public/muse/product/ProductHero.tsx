import { MuseScene, Reveal } from "../MuseScene";
import { PublicActionLink } from "../PublicActionLink";

export function ProductHero() {
  return (
    <MuseScene className="muse-hero">
      <Reveal>
        <div className="muse-eyebrow">LE PRODUIT</div>
        <h1>
          Un poste de travail pour les avis qui demandent{" "}
          <em>du contexte.</em>
        </h1>
        <p>
          Analysez, documentez, suivez et validez dans une expérience
          pensée comme une suite de scènes de travail.
        </p>
        <PublicActionLink to="/register">Créer mon espace</PublicActionLink>
      </Reveal>
    </MuseScene>
  );
}
