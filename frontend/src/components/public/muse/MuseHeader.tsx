import { Link, NavLink } from "react-router-dom";

/** Public routes shown in both desktop and mobile navigation. */
const navigation = [
  ["/produit", "La solution"],
  ["/fonctionnement", "Comment ça marche"],
  ["/securite", "Sécurité"],
  ["/tarifs", "Tarifs"],
  ["/contact", "Contact"],
] as const;

type MuseHeaderProps = {
  menuOpen: boolean;
  onMenuToggle: () => void;
};

/**
 * Shared public-site header.
 * The parent shell owns menu state; this component renders navigation and
 * reports interactions so desktop and mobile menus stay synchronized.
 */
export function MuseHeader({ menuOpen, onMenuToggle }: MuseHeaderProps) {
  return (
    <>
      <header className="site-header" id="header">
        <Link className="brand" to="/" aria-label="Review Defense, accueil">
          <span className="brand-mark" aria-hidden="true">R</span>
          <span>review<span className="brand-light">defense</span></span>
        </Link>

        <nav className="desktop-navigation" aria-label="Navigation principale">
          {navigation.map(([path, label]) => (
            <NavLink key={path} to={path}>
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="actions">
          <Link className="header-login" to="/login">Connexion</Link>
          <Link className="pill blue" to="/register">
            Créer mon espace <span aria-hidden="true">↗</span>
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
          <span />
          <span />
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
            onClick={() => {
              if (menuOpen) onMenuToggle();
            }}
          >
            {label}
          </NavLink>
        ))}
        <Link
          className="header-login"
          to="/login"
          tabIndex={menuOpen ? 0 : -1}
          onClick={() => {
            if (menuOpen) onMenuToggle();
          }}
        >
          Connexion
        </Link>
        <Link
          className="pill blue"
          to="/register"
          tabIndex={menuOpen ? 0 : -1}
          onClick={() => {
            if (menuOpen) onMenuToggle();
          }}
        >
          Créer mon espace
        </Link>
      </nav>
    </>
  );
}
