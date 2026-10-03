import { MuseScene, Reveal } from "../MuseScene";

const states = [
  ["Reçu", "Ce qui est entré dans le dossier."],
  ["Vérifié", "Ce qui a été examiné ou complété."],
  ["Préparé", "Ce qui est prêt pour la prochaine intervention."],
  ["Décidé", "Ce qui a été validé."],
] as const;

export function MethodLogic() {
  return (
    <MuseScene>
      <div className="muse-two">
        <Reveal>
          <div className="muse-eyebrow">LA LOGIQUE</div>
          <h2>
            Chaque étape laisse <em>quelque chose derrière elle.</em>
          </h2>
        </Reveal>

        <Reveal>
          <div className="muse-state-list">
            {states.map(([title, description]) => (
              <div key={title}>
                <b>{title}</b>
                <span>{description}</span>
              </div>
            ))}
          </div>
        </Reveal>
      </div>
    </MuseScene>
  );
}
