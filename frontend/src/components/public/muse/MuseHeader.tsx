import { Link } from "react-router-dom";

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
  onSearchOpen: () => void;
};

export function MuseHeader({
  menuOpen,
  onMenuToggle,
  onSearchOpen,
}: MuseHeaderProps) {
  return (
    <>
      <header className="site-header" id="header">
        <Link className="brand" to="/">
          ◉ Review Defense
        </Link>

        <nav aria-label="Navigation principale">
          {navigation.map(([path, label]) => (
            <Link key={path} to={path}>
              {label}
            </Link>
          ))}
        </nav>

        <div className="actions">
          <button
            type="button"
            className="search-open"
            aria-label="Rechercher"
            onClick={onSearchOpen}
          >
            ⌕
          </button>
          <Link className="pill blue" to="/register">
            Créer mon espace
          </Link>
        </div>

        <button
          type="button"
          className="menu-toggle"
          aria-label="Menu"
          aria-expanded={menuOpen}
          aria-controls="mobile-menu"
          onClick={onMenuToggle}
        >
          ☰
        </button>
      </header>

      <nav
        id="mobile-menu"
        className={`mobile-menu ${menuOpen ? "open" : ""}`}
        aria-label="Navigation mobile"
        aria-hidden={!menuOpen}
      >
        {navigation.map(([path, label]) => (
          <Link key={path} to={path}>
            {label}
          </Link>
        ))}
        <Link className="pill blue" to="/register">
          Créer mon espace
        </Link>
      </nav>
    </>
  );
}
