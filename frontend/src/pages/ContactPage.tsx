import { Link } from "react-router-dom";
import { PublicHeader } from "@/components/layout/PublicHeader";
import { PublicFooter } from "@/components/layout/PublicFooter";
import "@/styles/public.css";

export function ContactPage() {
  return <div className="rd-public">
    <PublicHeader />
    <main>
      <section className="rd-contact rd-contact-simple">
        <div>
          <span className="rd-public-eyebrow">CONTACT</span>
          <h1>Parlons du besoin,<br /><em>pas d’un catalogue.</em></h1>
          <p>Si vous évaluez Review Defense, commencez par le produit et le parcours. Pour une question précise, indiquez simplement ce que vous cherchez à organiser et nous pourrons vous orienter.</p>
        </div>
        <div className="rd-contact-panel">
          <span>PREMIÈRE ÉTAPE</span>
          <h2>Commencer par voir le produit.</h2>
          <p>Le moyen le plus direct de comprendre Review Defense est de parcourir un dossier, ses étapes et ses contrôles.</p>
          <Link className="rd-public-cta" to="/produit">Voir le produit →</Link>
          <hr />
          <div className="rd-contact-choices">
            <Link to="/fonctionnement"><strong>Comprendre le parcours</strong><span>Les six étapes, de la réception au suivi.</span><b>→</b></Link>
            <Link to="/securite"><strong>Examiner les contrôles</strong><span>Accès, permissions, historique, preuves et validation.</span><b>→</b></Link>
            <Link to="/tarifs"><strong>Voir les offres</strong><span>Comparer les formats disponibles avant de commencer.</span><b>→</b></Link>
          </div>
        </div>
      </section>
      <section className="rd-contact-final">
        <span className="rd-public-eyebrow">PRÊT À COMMENCER ?</span>
        <h2>Créez votre espace lorsque le fonctionnement vous convient.</h2>
        <Link className="rd-public-cta" to="/register">Créer mon espace →</Link>
      </section>
    </main>
    <PublicFooter />
  </div>;
}
