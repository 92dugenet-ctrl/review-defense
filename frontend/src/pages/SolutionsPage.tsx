import { Link } from "react-router-dom";
import "@/styles/public.css";

const solutions = [
  {
    title: "Restaurants",
    kicker: "VOLUME & RÉPUTATION",
    text: "Quand les avis arrivent au fil du service, le besoin n’est pas seulement de répondre vite : il faut retrouver le contexte, les éléments associés et l’état de chaque dossier.",
    points: ["Centraliser les avis à examiner", "Rattacher les éléments utiles au dossier", "Conserver une validation humaine avant les étapes sensibles"],
  },
  {
    title: "Hôtels",
    kicker: "SUIVI DANS LE TEMPS",
    text: "Un avis peut nécessiter plusieurs vérifications ou interventions. Le dossier permet de conserver le fil du traitement au lieu de disperser les informations.",
    points: ["Suivre les dossiers ouverts", "Retrouver l’historique du traitement", "Identifier les étapes qui attendent une décision"],
  },
  {
    title: "Commerces & artisans",
    kicker: "MOINS DE RECHERCHE",
    text: "Pour une petite équipe, chaque dossier doit rester lisible. Review Defense structure le travail sans imposer une décision automatique.",
    points: ["Voir ce qui est disponible", "Repérer ce qui manque", "Préparer la prochaine étape avant validation"],
  },
];

export function SolutionsPage() {
  return <div className="rd-public">
    <header className="rd-public-nav">
      <Link className="rd-public-brand" to="/"><span>RD</span> Review Defense</Link>
      <nav aria-label="Navigation principale">
        <Link to="/produit">Produit</Link><Link to="/fonctionnement">Méthode</Link><Link to="/securite">Sécurité</Link><Link to="/tarifs">Tarifs</Link>
      </nav>
      <Link className="rd-public-cta" to="/register">Commencer →</Link>
    </header>

    <main>
      <section className="rd-public-hero rd-solutions-hero">
        <div>
          <span className="rd-public-eyebrow">SOLUTIONS / MÉTIERS</span>
          <h1>Le même principe.<br/><em>Des réalités de terrain différentes.</em></h1>
        </div>
        <div className="rd-public-hero-copy">
          <p>Review Defense s’adapte au contexte dans lequel vos avis sont traités. Cette page ne promet pas un résultat métier automatique : elle montre où l’organisation du dossier peut aider.</p>
          <Link className="rd-public-link" to="/produit">Voir le produit →</Link>
        </div>
      </section>

      <section className="rd-solution-grid" aria-label="Solutions par métier">
        {solutions.map((item) => <article className="rd-solution-card" key={item.title}>
          <span>{item.kicker}</span><h2>{item.title}</h2><p>{item.text}</p>
          <ul>{item.points.map((point) => <li key={point}>{point}</li>)}</ul>
        </article>)}
      </section>

      <section className="rd-public-band">
        <div><span className="rd-public-eyebrow">CE QUE LE LOGICIEL NE FAIT PAS</span><h2>Il ne transforme pas une hypothèse en vérité.</h2></div>
        <p>Les éléments disponibles peuvent être incomplets. Review Defense sert à structurer l’examen et la documentation ; les décisions sensibles restent sous le contrôle de la personne habilitée.</p>
      </section>

      <section className="rd-public-final">
        <span className="rd-public-eyebrow">POUR COMMENCER</span>
        <h2>Commencez avec les dossiers qui demandent déjà votre attention.</h2>
        <p>Pas besoin de changer toute votre organisation pour découvrir la méthode. Commencez par comprendre comment le dossier, les preuves et la validation s’articulent.</p>
        <div><Link className="rd-public-cta" to="/register">Créer mon espace →</Link><Link className="rd-public-secondary" to="/fonctionnement">Voir le parcours</Link></div>
      </section>
    </main>
    <footer className="rd-public-footer"><span>© 2026 Review Defense</span><Link to="/mentions-legales">Informations légales</Link><Link to="/confidentialite">Confidentialité</Link></footer>
  </div>;
}
