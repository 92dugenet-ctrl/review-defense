import { MuseScene, Reveal } from "../MuseScene";
import { PublicActionLink } from "../PublicActionLink";

export function ContactHero() {
  return (
    <MuseScene className="muse-hero">
      <Reveal>
        <div className="muse-eyebrow">CONTACT</div>
        <h1>
          Parlons du besoin,
          <br />
          <em>pas d'un catalogue.</em>
        </h1>
        <p>
          Commencez par explorer le produit, son fonctionnement et son cadre
          de contrôle. Pour une question précise, dites-nous ce que vous
          cherchez à organiser.
        </p>
        <PublicActionLink to="/produit">Voir le produit</PublicActionLink>
      </Reveal>
    </MuseScene>
  );
}
