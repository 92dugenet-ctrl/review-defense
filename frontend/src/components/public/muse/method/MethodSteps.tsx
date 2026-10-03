import { MuseScene, Reveal } from "../MuseScene";

const steps = [
  ["01", "Recevoir", "Le signal entre dans le dossier.", "Entrée"],
  [
    "02",
    "Qualifier",
    "Le contenu est distingué entre établi, disponible et à vérifier.",
    "Lecture",
  ],
  [
    "03",
    "Réunir",
    "Les captures, documents et sources utiles sont rattachés.",
    "Preuves",
  ],
  [
    "04",
    "Préparer",
    "Le contexte est ordonné pour rendre la suite lisible.",
    "Préparation",
  ],
  [
    "05",
    "Valider",
    "Une personne habilitée décide de l'action à retenir.",
    "Décision",
  ],
  [
    "06",
    "Suivre",
    "Le dossier reste exploitable après l'action.",
    "Continuité",
  ],
] as const;

export function MethodSteps() {
  return (
    <MuseScene className="muse-light">
      <div className="muse-process-list">
        {steps.map(([number, title, description, label]) => (
          <Reveal key={number}>
            <article className={number === "05" ? "decision" : ""}>
              <b>{number}</b>
              <div>
                <small>{label}</small>
                <h2>{title}</h2>
                <p>{description}</p>
              </div>
              <span>
                {number === "05" ? "VALIDATION HUMAINE" : "→"}
              </span>
            </article>
          </Reveal>
        ))}
      </div>
    </MuseScene>
  );
}
