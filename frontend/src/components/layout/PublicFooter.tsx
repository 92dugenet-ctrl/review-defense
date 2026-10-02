import { Link } from "react-router-dom";
import { publicNavigation } from "./PublicHeader";

export function PublicFooter() {
  return <footer className="rd-footer">
    <div className="rd-footer-brand">
      <strong>Review Defense</strong>
      <span>Analyse · Dossiers · Validation</span>
      <small>Un espace pour structurer les avis qui demandent du contexte, sans automatiser les décisions sensibles.</small>
    </div>
    <div className="rd-footer-col"><b>Produit</b>{publicNavigation.map(([path, label]) => <Link key={path} to={path}>{label}</Link>)}</div>
    <div className="rd-footer-col"><b>Compte</b><Link to="/login">Connexion</Link><Link to="/register">Créer mon espace</Link><Link to="/contact">Contact</Link></div>
    <div className="rd-footer-col"><b>Légal</b><Link to="/mentions-legales">Mentions légales</Link><Link to="/confidentialite">Confidentialité</Link><Link to="/cookies">Cookies</Link><Link to="/cgu">CGU</Link><Link to="/cgv">CGV</Link></div>
    <div className="rd-footer-bottom"><span>© 2026 Review Defense. Tous droits réservés.</span><span>Les informations légales doivent être vérifiées et complétées avant publication commerciale.</span></div>
  </footer>;
}