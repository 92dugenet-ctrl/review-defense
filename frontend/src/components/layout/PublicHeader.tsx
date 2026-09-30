import { useState } from "react";
import { Link } from "react-router-dom";

export const publicNavigation = [
  ["/produit", "Produit"],
  ["/solutions", "Solutions"],
  ["/fonctionnement", "Fonctionnement"],
  ["/securite", "Sécurité"],
  ["/tarifs", "Tarifs"],
  ["/ressources", "Ressources"],
  ["/contact", "Contact"],
] as const;

export function PublicHeader() {
  const [open, setOpen] = useState(false);
  return <header className="rd-head">
    <div className="rd-head-left">
      <button type="button" className="rd-menu" aria-label="Ouvrir le menu principal" aria-expanded={open} onClick={() => setOpen(!open)}><span /></button>
      <Link className="rd-brand" to="/" onClick={() => setOpen(false)}><span className="rd-mark">RD</span>Review Defense</Link>
    </div>
    <div className="rd-actions">
      <Link className="rd-head-cta" to="/register">Commencer →</Link>
    </div>
    {open && <div className="rd-panel">
      {publicNavigation.map(([path, label]) => <Link key={path} to={path} onClick={() => setOpen(false)}>{label}<span>→</span></Link>)}
      <Link to="/login" onClick={() => setOpen(false)}>Connexion<span>→</span></Link>
    </div>}
  </header>;
}
