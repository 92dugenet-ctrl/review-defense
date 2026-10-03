import { MuseScene } from "../MuseScene";

export function HomeResearchDetail() {
  return (
    <MuseScene className="overlay-scene" id="research-detail">
      <div className="research-detail">
        <div className="dim-card">
          <div className="detail-summary">
            <span className="detail-status">DOSSIER STRUCTURÉ</span>
            <strong>Éléments regroupés</strong>
            <span>Contexte · Sources · Historique</span>
          </div>
        </div>
        <div className="research-panel">
          <div className="eyebrow">DOSSIER</div>
          <h2>Préparer une situation complexe sans perdre le fil.</h2>
          <p>
            Les informations utiles restent liées au dossier et à son
            historique, avec les éléments à vérifier clairement identifiés.
          </p>
        </div>
      </div>
    </MuseScene>
  );
}
