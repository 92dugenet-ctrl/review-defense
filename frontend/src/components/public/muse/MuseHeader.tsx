import { Link, NavLink } from "react-router-dom";

const navigation = [
  ["/produit", "Produit"],
  ["/fonctionnement", "Fonctionnement"],
  ["/securite", "Sécurité"],
  ["/tarifs", "Tarifs"],
  ["/contact", "Contact"],
] as const;

type MuseHeaderProps = {
  menuOpen: boolean;
  onMenuToggle: () => void;
};

export function MuseHeader({ menuOpen, onMenuToggle }: MuseHeaderProps) {
  return (
    <>
      <header className="site-header" id="header">
        <Link className="brand" to="/" aria-label="Review Defense, accueil">
          ◉ Review Defense
        </Link>

        <nav aria-label="Navigation principale">
          {navigation.map(([path, label]) => (
            <NavLink key={path} to={path}>
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="actions">
          <Link className="pill blue" to="/register">
            Créer mon espace
          </Link>
        </div>

        <button
          type="button"
          className="menu-toggle"
          aria-label={menuOpen ? "Fermer le menu" : "Ouvrir le menu"}
          aria-expanded={menuOpen}
          aria-controls="mobile-menu"
          onClick={onMenuToggle}
        >
          {menuOpen ? "×" : "☰"}
        </button>
      </header>

      <nav
        id="mobile-menu"
        className={`mobile-menu ${menuOpen ? "open" : ""}`}
        aria-label="Navigation mobile"
        aria-hidden={!menuOpen}
      >
        {navigation.map(([path, label]) => (
          <NavLink
            key={path}
            to={path}
            tabIndex={menuOpen ? 0 : -1}
            onClick={() => { if (menuOpen) onMenuToggle(); }}
          >
            {label}
          </NavLink>
        ))}
        <Link
          className="pill blue"
          to="/register"
          tabIndex={menuOpen ? 0 : -1}
          onClick={() => { if (menuOpen) onMenuToggle(); }}
        >
          Créer mon espace
        </Link>
      </nav>
    </>
  );
}
