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

export function MuseShell({ children }: MuseShellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  useMuseMotion();

  useEffect(() => {
    setMenuOpen(false);
    document.body.classList.remove("is-locked");
  }, [location.pathname]);

  useEffect(() => {
    document.body.classList.toggle("is-locked", menuOpen);

    if (!menuOpen) {
      return () => document.body.classList.remove("is-locked");
    }

    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMenuOpen(false);
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
