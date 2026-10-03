import { Link } from "react-router-dom";

import { MuseScene, Reveal } from "./MuseScene";

type NextMuseSceneProps = {
  eyebrow: string;
  title: string;
  to: string;
  label?: string;
  dark?: boolean;
};

export function NextMuseScene({
  eyebrow,
  title,
  to,
  label = "Voir la suite →",
  dark = false,
}: NextMuseSceneProps) {
  const sceneClass = dark ? "muse-dark-scene" : "muse-blue-scene";

  return (
    <MuseScene className={sceneClass}>
      <Reveal>
        <div className="muse-eyebrow">{eyebrow}</div>
        <h2>{title}</h2>
        <Link className="muse-pill muse-blue" to={to}>
          {label}
        </Link>
      </Reveal>
    </MuseScene>
  );
}
