import { Link } from "react-router-dom";
import { publicNavigation } from "./PublicHeader";

export function PublicFooter() {
  return <footer className="rd-footer">
    <div className="rd-footer-brand"><strong>Review Defense</strong><span>Analyse · Preuves · Dossiers · Validation</span><small>Service SaaS destiné à aider les professionnels à analyser, documenter et suivre leurs avis. Les décisions et validations restent sous le contrôle du client.</small></div>
    <div className="rd-footer-col"><b>Navigation</b>{publicNavigation.map(([path, label]) => <Link key={path} to={path}>{label}</Link>)}<Link to="/login">Connexion</Link></div>
    <div className="rd-footer-col"><b>Informations légales</b><Link to="/mentions-legales">Mentions légales</Link><Link to="/confidentialite">Politique de confidentialité</Link><Link to="/cookies">Cookies et traceurs</Link><Link to="/cgu">Conditions générales d'utilisation</Link><Link to="/cgv">Conditions générales de vente</Link></div>
    <div className="rd-footer-col"><b>Conformité</b><Link to="/confidentialite">Protection des données — RGPD</Link><Link to="/cgv#mediation">Réclamations et médiation</Link><Link to="/accessibilite">Accessibilité</Link><Link to="/contact-juridique">Contact juridique</Link></div>
    <div className="rd-footer-bottom"><span>© 2026 Review Defense. Tous droits réservés.</span><span>Les informations entre crochets dans les pages légales doivent être remplacées par les données exactes de l’éditeur avant publication commerciale.</span></div>
  </footer>;
}
