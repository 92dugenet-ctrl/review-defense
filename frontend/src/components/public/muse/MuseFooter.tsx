import { Link } from "react-router-dom";

const footerGroups = [
  {
    title: "Produit",
    links: [
      ["/produit", "Produit"],
      ["/fonctionnement", "Fonctionnement"],
      ["/securite", "Sécurité"],
      ["/tarifs", "Tarifs"],
    ],
  },
  {
    title: "Ressources",
    links: [
      ["/contact", "Contact"],
      ["/accessibilite", "Accessibilité"],
    ],
  },
  {
    title: "Compte",
    links: [
      ["/login", "Connexion"],
      ["/register", "Créer un espace"],
    ],
  },
  {
    title: "Informations légales",
    links: [
      ["/mentions-legales", "Mentions légales"],
      ["/confidentialite", "Confidentialité"],
      ["/cookies", "Cookies"],
      ["/cgu", "CGU"],
      ["/cgv", "CGV"],
    ],
  },
] as const;

export function MuseFooter() {
  return (
    <footer id="footer">
      <div className="footer-top">
        <Link className="footer-brand" to="/" aria-label="Review Defense, accueil">
          ◉ Review Defense
        </Link>
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
      <small>© {new Date().getFullYear()} Review Defense — Analyse, dossiers, validation.</small>
    </footer>
  );
}
