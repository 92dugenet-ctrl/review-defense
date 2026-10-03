import type { ReactNode } from "react";

type MuseSceneProps = {
  children: ReactNode;
  className?: string;
  id?: string;
};

type RevealProps = {
  children: ReactNode;
};

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

export function Reveal({ children }: RevealProps) {
  return <div className="reveal">{children}</div>;
}
