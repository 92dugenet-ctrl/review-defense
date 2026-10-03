import type { ReactNode } from "react";

type MuseSceneProps = {
  children: ReactNode;
  className?: string;
  id?: string;
};

type RevealProps = {
  children: ReactNode;
};

/**
 * Provides the shared section structure used by the public Muse pages.
 * Styling and responsive behavior are intentionally defined in the Muse CSS.
 */
export function MuseScene({
  children,
  className = "",
  id,
}: MuseSceneProps) {
  return (
    <section className={`scene ${className}`} id={id}>
      <div className="scene-inner">{children}</div>
    </section>
  );
}

/**
 * Marks content for the public site's reveal-on-scroll presentation.
 * Motion behavior is handled centrally by the Muse motion layer.
 */
export function Reveal({ children }: RevealProps) {
  return <div className="reveal">{children}</div>;
}
