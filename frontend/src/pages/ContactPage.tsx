import { Link } from "react-router-dom";
import "@/styles/public.css";

export function ContactPage() {
  return <div className="rd-public">
    <header className="rd-public-nav">
      <Link className="rd-public-brand" to="/"><span>RD</span> Review Defense</Link>
      <nav aria-label="Navigation principale"><Link to="/produit">Produit</Link><Link to="/fonctionnement">Méthode</Link><Link to="/securite">Sécurité</Link><Link to="/tarifs">Tarifs</Link></nav>
      <Link className="rd-public-cta" to="/register">Commencer →</Link>
    </header>
    <main>
      <section className="rd-contact">
        <div><span className="rd-public-eyebrow">CONTACT</span><h1>Parlons d’abord<br/><em>du besoin.</em></h1><p>Si vous évaluez Review Defense, commencez par préciser ce que vous cherchez à organiser : analyse d’avis, documentation, suivi des dossiers ou validation des étapes sensibles.</p></div>
        <div className="rd-contact-panel">
          <span>PREMIÈRE ÉTAPE</span><h2>Créer un espace pour découvrir le parcours.</h2><p>La voie la plus directe pour explorer le produit est de commencer un espace. Vous pourrez ensuite examiner les fonctionnalités et le fonctionnement avant de décider de la suite.</p><Link className="rd-public-cta" to="/register">Créer mon espace →</Link>
          <hr/>
          <span>BESOIN D’INFORMATIONS</span><p>Pour les sujets juridiques, consultez les informations légales et la politique de confidentialité disponibles sur le site.</p><Link className="rd-public-secondary" to="/contact-juridique">Voir le contact juridique →</Link>
        </div>
      </section>
      <section className="rd-public-faq-strip"><h2>Vous cherchez encore à comprendre le produit ?</h2><div><Link to="/produit">Produit</Link><Link to="/fonctionnement">Fonctionnement</Link><Link to="/securite">Sécurité</Link><Link to="/tarifs">Tarifs</Link></div></section>
    </main>
    <footer className="rd-public-footer"><span>© 2026 Review Defense</span><Link to="/mentions-legales">Informations légales</Link><Link to="/confidentialite">Confidentialité</Link></footer>
  </div>;
}
