import { MuseScene, Reveal } from "../MuseScene";

const moments = [
  [
    "01",
    "Analyser",
    "Comprendre le contenu reçu et les points à vérifier.",
  ],
  ["02", "Documenter", "Rattacher les preuves et les sources."],
  ["03", "Suivre", "Conserver l'état et la prochaine étape."],
  [
    "04",
    "Valider",
    "Garder la décision entre des mains habilitées.",
  ],
] as const;

export function ProductMoments() {
  return (
    <MuseScene className="muse-light">
      <Reveal>
        <div className="muse-eyebrow">LES MOMENTS DE TRAVAIL</div>
        <h2>Voir le dossier sous plusieurs angles.</h2>

        <div className="muse-product-grid four">
          {moments.map(([number, title, description]) => (
            <article className="muse-simple-card" key={number}>
              <b>{number}</b>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </Reveal>
    </MuseScene>
  );
}
