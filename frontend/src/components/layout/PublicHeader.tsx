import { useState } from "react";
import { Link } from "react-router-dom";

export const publicNavigation = [
  ["/produit", "Produit"],
  ["/fonctionnement", "Fonctionnement"],
  ["/securite", "Sécurité"],
  ["/tarifs", "Tarifs"],
] as const;

export function PublicHeader() {
  const [open, setOpen] = useState(false);
  return <header className="rd-head">
    <div className="rd-head-left">
      <button type="button" className="rd-menu" aria-label="Ouvrir le menu principal" aria-expanded={open} aria-controls="public-navigation" onClick={() => setOpen(!open)}><span /></button>
      <Link className="rd-brand" to="/" onClick={() => setOpen(false)}><span className="rd-mark">RD</span>Review Defense</Link>
    </div>
    <nav id="public-navigation" className="rd-desktop-nav" aria-label="Navigation principale">
      {publicNavigation.map(([path, label]) => <Link key={path} to={path}>{label}</Link>)}
    </nav>
    <div className="rd-actions">
      <Link className="rd-login-link" to="/login">Connexion</Link>
      <Link className="rd-head-cta" to="/register">Créer mon espace →</Link>
    </div>
    {open && <div className="rd-panel" id="public-navigation-mobile">
      {publicNavigation.map(([path, label]) => <Link key={path} to={path} onClick={() => setOpen(false)}>{label}<span>→</span></Link>)}
      <Link to="/login" onClick={() => setOpen(false)}>Connexion<span>→</span></Link>
      <Link className="mobile-primary" to="/register" onClick={() => setOpen(false)}>Créer mon espace<span>→</span></Link>
    </div>}
  </header>;
}