import { Link } from "react-router-dom";
import "@/styles/public.css";

const resources = [
  ["Comprendre", "Comment lire un avis qui mérite une vérification", "Un cadre simple pour distinguer le contenu reçu, le contexte disponible, les éléments à réunir et les questions qui restent ouvertes."],
  ["Méthode", "Construire un dossier d’avis exploitable", "Pourquoi rattacher les captures, documents, échanges et décisions au même contexte facilite le suivi lorsque plusieurs étapes se succèdent."],
  ["Contrôle", "Pourquoi garder une validation humaine", "Une automatisation peut préparer une étape. La décision sensible doit rester compréhensible et attribuable à la personne qui la valide."],
  ["FAQ", "Les questions à poser avant de choisir un outil", "Accès, preuves, historique, limites de l’automatisation et place de l’équipe : une grille pour examiner le sujet sans promesse artificielle."],
];

export function ResourcesPage() {
  return <div className="rd-public">
    <header className="rd-public-nav">
      <Link className="rd-public-brand" to="/"><span>RD</span> Review Defense</Link>
      <nav aria-label="Navigation principale"><Link to="/produit">Produit</Link><Link to="/fonctionnement">Méthode</Link><Link to="/securite">Sécurité</Link><Link to="/tarifs">Tarifs</Link></nav>
      <Link className="rd-public-cta" to="/register">Commencer →</Link>
    </header>
    <main>
      <section className="rd-public-hero rd-resources-hero">
        <div><span className="rd-public-eyebrow">RESSOURCES</span><h1>Des réponses avant<br/><em>la décision.</em></h1></div>
        <div className="rd-public-hero-copy"><p>Les ressources publiques servent à comprendre la méthode et ses limites. Elles ne remplacent ni une analyse juridique ni les règles propres à votre plateforme d’avis.</p></div>
      </section>
      <section className="rd-resource-list">
        {resources.map(([tag,title,text], index) => <article key={title}>
          <div className="rd-resource-index">0{index + 1}</div>
          <div><span>{tag}</span><h2>{title}</h2><p>{text}</p></div>
          {tag === "FAQ" ? <Link to="/securite">Explorer →</Link> : <Link to="/produit">Voir le produit →</Link>}
        </article>)}
      </section>
      <section className="rd-public-note"><strong>Une question reste sans réponse ?</strong><p>Commencez par le fonctionnement du produit : il présente le parcours, les rôles et le principe de validation.</p><Link to="/fonctionnement">Lire la méthode →</Link></section>
    </main>
    <footer className="rd-public-footer"><span>© 2026 Review Defense</span><Link to="/mentions-legales">Informations légales</Link><Link to="/confidentialite">Confidentialité</Link></footer>
  </div>;
}
