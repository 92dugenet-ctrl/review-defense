// Cadre commun du site public : enveloppe les pages marketing avec l'en-tête, le pied de page,
// les styles Muse et les comportements de navigation mobile/animation.
// Les pages filles fournissent uniquement leur contenu ; ce shell gère le cycle de vie du menu,
// le verrouillage du scroll et les comportements transversaux liés au changement de route.

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useLocation } from "react-router-dom";

import { MuseFooter } from "./MuseFooter";
import { MuseHeader } from "./MuseHeader";
import { useMuseMotion } from "./useMuseMotion";
import "@/styles/muse-v3.css";

type MuseShellProps = {
  children: ReactNode;
};

/**
 * Application shell for the public marketing pages.
 *
 * It centralizes the shared header/footer, public-site styles, scroll motion,
 * and mobile-menu lifecycle. Page components provide only their own content.
 */
export function MuseShell({ children }: MuseShellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  useMuseMotion();

  // Close the mobile menu after navigation to another route.
  useEffect(() => {
    setMenuOpen(false);
    document.body.classList.remove("is-locked");
  }, [location.pathname]);

  // Lock page scrolling while the mobile navigation is open.
  useEffect(() => {
    document.body.classList.toggle("is-locked", menuOpen);

    if (!menuOpen) {
      return () => document.body.classList.remove("is-locked");
    }

    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    };

    window.addEventListener("keydown", closeOnEscape);

    return () => {
      window.removeEventListener("keydown", closeOnEscape);
      document.body.classList.remove("is-locked");
    };
  }, [menuOpen]);

  return (
    <div className="muse-site muse-reference-site">
      <div className="progress" aria-hidden="true">
        <i />
      </div>

      <MuseHeader
        menuOpen={menuOpen}
        onMenuToggle={() => setMenuOpen((open) => !open)}
      />

      <main>{children}</main>
      <MuseFooter />
    </div>
  );
}
