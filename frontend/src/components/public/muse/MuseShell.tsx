import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";

import { useMuseMotion } from "./useMuseMotion";
import "@/styles/muse-v3.css";

const publicLinks = [
  ["/produit", "Produit"],
  ["/fonctionnement", "Fonctionnement"],
  ["/securite", "Sécurité"],
  ["/tarifs", "Tarifs"],
  ["/contact", "Contact"],
] as const;

type MuseShellProps = {
  children: ReactNode;
};

export function MuseShell({ children }: MuseShellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const location = useLocation();

  useMuseMotion();

  // Close overlays and restore scrolling whenever the page changes.
  useEffect(() => {
    setMenuOpen(false);
    setSearchOpen(false);
    document.body.classList.remove("is-locked");
  }, [location.pathname]);

  // Prevent background scrolling while a menu or search panel is open.
  useEffect(() => {
    document.body.classList.toggle(
      "is-locked",
      menuOpen || searchOpen,
    );

    return () => {
      document.body.classList.remove("is-locked");
    };
  }, [menuOpen, searchOpen]);

  return (
    <div className="muse-site muse-reference-site">
      <div className="progress">
        <i />
      </div>

      <header className="site-header" id="header">
        <Link className="brand" to="/">
          ◉ Review Defense
        </Link>

        <nav aria-label="Navigation principale">
          {publicLinks.map(([path, label]) => (
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
            onClick={() => setSearchOpen(true)}
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
          onClick={() => setMenuOpen((isOpen) => !isOpen)}
        >
          ☰
        </button>
      </header>

      <nav
        className={`mobile-menu ${menuOpen ? "open" : ""}`}
        aria-label="Navigation mobile"
      >
        {publicLinks.map(([path, label]) => (
          <Link key={path} to={path}>
            {label}
          </Link>
        ))}

        <Link className="pill blue" to="/register">
          Créer mon espace
        </Link>
      </nav>

      {children}

      <footer id="developers">
        <div className="footer-top">
          <b>◉ Review Defense</b>

          <div>
            <h4>Produit</h4>
            <Link to="/produit">Produit</Link>
            <Link to="/fonctionnement">Fonctionnement</Link>
            <Link to="/securite">Sécurité</Link>
          </div>

          <div>
            <h4>Ressources</h4>
            <Link to="/contact">Contact</Link>
            <Link to="/tarifs">Tarifs</Link>
            <Link to="/fonctionnement">Fonctionnement</Link>
          </div>

          <div>
            <h4>Compte</h4>
            <Link to="/login">Connexion</Link>
            <Link to="/register">Créer un espace</Link>
            <Link to="/contact">Contact</Link>
          </div>
        </div>

        <small>
          © 2026 Review Defense — Analyse, dossiers, validation.
        </small>
      </footer>

      {searchOpen && (
        <div className="search-panel open">
          <button
            type="button"
            className="search-close"
            aria-label="Fermer la recherche"
            onClick={() => setSearchOpen(false)}
          >
            ×
          </button>

          <input
            autoFocus
            placeholder="Rechercher Review Defense…"
          />
          <p>Recherchez une fonctionnalité ou une information</p>
        </div>
      )}
    </div>
  );
}
