import { useState } from "react";
import { Link } from "react-router-dom";

import { MuseScene } from "../MuseScene";
import { homeProcess } from "./HomeData";

const filters = ["Tous", "Entrée", "Lecture", "Preuves"] as const;

export function HomeResearch() {
  const [activeFilter, setActiveFilter] = useState<(typeof filters)[number]>("Tous");
  const visibleSteps = homeProcess.filter(
    ([, , , category]) => activeFilter === "Tous" || category === activeFilter,
  );

  return (
    <MuseScene className="publications" id="research">
      <div className="research-layout">
        <aside aria-label="Filtrer les étapes">
          <div className="eyebrow">FILTRER PAR ÉTAPE</div>
          <div className="research-filters" role="group" aria-label="Étapes du dossier">
            {filters.map((filter) => (
              <button
                key={filter}
                type="button"
                className={activeFilter === filter ? "active" : ""}
                aria-pressed={activeFilter === filter}
                onClick={() => setActiveFilter(filter)}
              >
                {filter}
              </button>
            ))}
          </div>
        </aside>

        <div>
          <div className="eyebrow">DOSSIERS</div>
          <h2>Le contexte, dans le bon ordre.</h2>
          <div className="papers" aria-live="polite">
            {visibleSteps.map(([number, title, description, category]) => (
              <article key={number}>
                <small>{category.toUpperCase()} · {number}</small>
                <h3>{title}</h3>
                <p>{description}</p>
                <Link to="/fonctionnement">Voir l'étape →</Link>
              </article>
            ))}
            {visibleSteps.length === 0 && (
              <p role="status">Aucune étape ne correspond à ce filtre.</p>
            )}
          </div>
        </div>
      </div>
    </MuseScene>
  );
}
