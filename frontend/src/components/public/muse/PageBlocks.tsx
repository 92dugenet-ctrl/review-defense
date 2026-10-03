import { MuseScene, Reveal } from "./MuseScene";
import { PublicActionLink } from "./PublicActionLink";

type NextMuseSceneProps = {
  eyebrow: string;
  title: string;
  to: string;
  label?: string;
  dark?: boolean;
};

/**
 * Reusable end-of-page section that points visitors to the next public step.
 * Individual pages supply the copy and route; this component owns the layout.
 */
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
        <PublicActionLink to={to}>{label}</PublicActionLink>
      </Reveal>
    </MuseScene>
  );
}
