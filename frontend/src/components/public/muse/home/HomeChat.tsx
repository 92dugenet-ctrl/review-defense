import { useState } from "react";

import { MuseScene } from "../MuseScene";

const experiences = {
  Analyse: {
    prompt: "J'ai trouvé les éléments disponibles pour ce dossier.",
    response: "Les informations sont regroupées et les points à vérifier sont signalés.",
  },
  Preuves: {
    prompt: "Les pièces disponibles sont rattachées au dossier.",
    response: "Chaque élément conserve sa source et son contexte.",
  },
  Validation: {
    prompt: "Une action nécessite votre validation.",
    response: "Vous gardez la main avant toute action sensible.",
  },
  Suivi: {
    prompt: "Le dossier dispose d'une prochaine étape identifiée.",
    response: "L'historique permet de retrouver les actions déjà réalisées.",
  },
  Historique: {
    prompt: "Les étapes précédentes sont conservées.",
    response: "Vous pouvez retrouver le contexte et les validations du dossier.",
  },
} as const;

type ExperienceTab = keyof typeof experiences;

export function HomeChat() {
  const [activeTab, setActiveTab] = useState<ExperienceTab>("Analyse");
  const activeExperience = experiences[activeTab];

  return (
    <MuseScene className="chat-scene" id="resources">
      <div className="two">
        <div className="chat-copy">
          <div className="eyebrow">L'EXPÉRIENCE REVIEW DEFENSE</div>
          <h2>Une interface qui suit votre façon de traiter un dossier.</h2>
          <div className="chips" role="group" aria-label="Étapes de traitement">
            {(Object.keys(experiences) as ExperienceTab[]).map((tab) => (
              <button
                key={tab}
                type="button"
                aria-pressed={activeTab === tab}
                className={activeTab === tab ? "active" : ""}
                onClick={() => setActiveTab(tab)}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        <div
          className="chat-window"
          id="experience-panel"
          aria-live="polite"
        >
          <div className="chat-head">Review Defense <span>●</span></div>
          <div className="chat-bubble">{activeExperience.prompt}</div>
          <div className="chat-bubble right">{activeTab}</div>
          <div className="chat-bubble">{activeExperience.response}</div>
          <p className="chat-caption">Exemple illustratif d'une étape du dossier.</p>
        </div>
      </div>
    </MuseScene>
  );
}
