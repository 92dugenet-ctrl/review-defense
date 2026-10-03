import { MuseScene, Reveal } from "../MuseScene";

const controls = [
  ["01", "Accès", "Qui peut entrer dans l'espace."],
  ["02", "Permissions", "Ce que chaque rôle peut consulter ou faire."],
  ["03", "Historique", "Les événements importants restent lisibles."],
  ["04", "Preuves", "Chaque élément conserve son contexte."],
  ["05", "Validation", "Les actions sensibles restent soumises à une personne."],
  [
    "06",
    "Limites",
    "Le produit ne se présente pas comme une certification ou un conseil juridique.",
  ],
] as const;

export function SecurityControls() {
  return (
    <MuseScene className="muse-light">
      <Reveal>
        <div className="muse-eyebrow">CONTRÔLE DE L'ESPACE</div>
        <h2>Six axes pour garder le dossier lisible.</h2>

        <div className="muse-control-grid">
          {controls.map(([number, title, description]) => (
            <article key={number}>
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
