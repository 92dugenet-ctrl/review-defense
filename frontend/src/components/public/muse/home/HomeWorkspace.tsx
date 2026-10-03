import { MuseScene } from "../MuseScene";
import { PublicActionLink } from "../PublicActionLink";

export function HomeWorkspace() {
  return (
    <MuseScene className="light" id="muse">
      <div className="two">
        <div>
          <div className="eyebrow">POSTE DE TRAVAIL</div>
          <h2>Prêt à traiter vos avis avec plus de contexte ?</h2>
          <p>
            Un endroit pour rechercher, organiser et préparer les
            informations utiles avant d'agir.
          </p>
          <PublicActionLink to="/produit">Découvrir le produit</PublicActionLink>
        </div>

        <div className="orb-stage" aria-hidden="true">
          <div className="orb o1">⌁</div>
          <div className="orb o2">✦</div>
          <div className="orb o3">◫</div>
          <div className="orb main-orb">◌</div>
        </div>
      </div>
    </MuseScene>
  );
}
