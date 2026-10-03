import { Link } from "react-router-dom";

import { MuseScene } from "../MuseScene";

export function HomeTry() {
  return (
    <MuseScene className="blue-scene" id="try">
      <div className="two">
        <div>
          <div className="eyebrow">ESPACE DE TRAVAIL</div>
          <h2>Un espace qui vous aide à faire avancer les dossiers</h2>
          <p>
            Analysez, organisez les preuves, suivez les étapes et validez
            les actions sensibles.
          </p>

          <div className="store-buttons">
            <Link to="/register">Créer mon espace</Link>
            <Link to="/login">Se connecter</Link>
          </div>
        </div>

        <div className="phone-stage">
          <div className="phone">
            <div className="phone-head">Review Defense</div>
            <div className="ai-message">Votre point de suivi est prêt.</div>
            <div className="ai-message soft">
              3 dossiers à vérifier et 2 validations en attente.
            </div>
            <div className="phone-input">Ouvrir le dossier…</div>
          </div>
        </div>
      </div>
    </MuseScene>
  );
}
