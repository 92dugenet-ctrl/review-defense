import { Link } from "react-router-dom";

const footerGroups = [
  {
    title: "Produit",
    links: [
      ["/produit", "Produit"],
      ["/fonctionnement", "Fonctionnement"],
      ["/securite", "Sécurité"],
    ],
  },
  {
    title: "Ressources",
    links: [
      ["/contact", "Contact"],
      ["/tarifs", "Tarifs"],
    ],
  },
  {
    title: "Compte",
    links: [
      ["/login", "Connexion"],
      ["/register", "Créer un espace"],
    ],
  },
] as const;

export function MuseFooter() {
  return (
    <footer id="developers">
      <div className="footer-top">
        <b>◉ Review Defense</b>
        {footerGroups.map((group) => (
          <div key={group.title}>
            <h4>{group.title}</h4>
            {group.links.map(([path, label]) => (
              <Link key={path} to={path}>
                {label}
              </Link>
            ))}
          </div>
        ))}
      </div>
      <small>© 2026 Review Defense — Analyse, dossiers, validation.</small>
    </footer>
  );
}
