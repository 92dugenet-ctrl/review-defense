import { MuseScene, Reveal } from "../MuseScene";

const questions = [
  [
    "Le logiciel décide-t-il à ma place ?",
    "Non. Il prépare et organise le travail ; la décision sensible reste à la personne habilitée.",
  ],
  [
    "Cette page est-elle une certification ?",
    "Non. Elle présente les principes de contrôle du produit, pas une certification.",
  ],
  [
    "Les permissions sont-elles identiques partout ?",
    "Non. Elles dépendent du rôle et de la configuration de l'organisation.",
  ],
] as const;

export function SecurityFaq() {
  return (
    <MuseScene>
      <Reveal>
        <div className="muse-eyebrow">QUESTIONS</div>
        <h2>Les contrôles expliqués simplement.</h2>

        <div className="muse-faq">
          {questions.map(([question, answer]) => (
            <details key={question}>
              <summary>{question}</summary>
              <p>{answer}</p>
            </details>
          ))}
        </div>
      </Reveal>
    </MuseScene>
  );
}
