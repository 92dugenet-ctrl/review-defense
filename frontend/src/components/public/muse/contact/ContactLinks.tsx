import { Link } from "react-router-dom";

import { MuseScene } from "../MuseScene";

const contactLinks = [
  {
    title: "Produit",
    description: "Parcourir l'espace de travail.",
    to: "/produit",
  },
  {
    title: "Fonctionnement",
    description: "Voir les six étapes.",
    to: "/fonctionnement",
  },
  {
    title: "Sécurité",
    description: "Examiner les contrôles.",
    to: "/securite",
  },
  {
    title: "Tarifs",
    description: "Voir les formats disponibles.",
    to: "/tarifs",
  },
] as const;

export function ContactLinks() {
  return (
    <MuseScene className="muse-light">
      <div className="muse-product-grid four">
        {contactLinks.map(({ title, description, to }) => (
          <Link className="muse-simple-card" to={to} key={title}>
            <small>{title}</small>
            <h3>{description}</h3>
            <b>→</b>
          </Link>
        ))}
      </div>
    </MuseScene>
  );
}
