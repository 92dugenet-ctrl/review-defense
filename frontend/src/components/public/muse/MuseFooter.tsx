import { Link } from "react-router-dom";

/** Link groups displayed in the shared public-site footer. */
const footerGroups = [
  {
    title: "Solution",
    links: [
      ["/produit", "La solution"],
      ["/fonctionnement", "Comment ça marche"],
      ["/securite", "Sécurité"],
      ["/tarifs", "Tarifs"],
    ],
  },
  {
    title: "Accompagnement",
    links: [["/contact", "Nous contacter"]],
  },
  {
    title: "Votre espace",
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

/**
 * Shared footer for the public Muse pages.
 * Footer links are maintained in the footerGroups registry above.
 */
export function MuseFooter() {
  return (
    <footer id="footer">
      <div className="footer-top">
        <div className="footer-intro">
          <Link
            className="footer-brand"
            to="/"
            aria-label="Review Defense, accueil"
          >
            <span className="brand-mark" aria-hidden="true">R</span>
            <span>review<span className="brand-light">defense</span></span>
          </Link>
          <p>
            Des avis mieux compris. Des dossiers mieux suivis. Des décisions
            qui restent les vôtres.
          </p>
        </div>

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

      <div className="footer-bottom">
        <small>
          © {new Date().getFullYear()} Review Defense. Tous droits réservés.
        </small>
        <small>Conçu pour garder l'humain aux commandes.</small>
      </div>
    </footer>
  );
}
