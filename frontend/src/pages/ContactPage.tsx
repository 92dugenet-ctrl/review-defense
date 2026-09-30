import { Link } from "react-router-dom";
import { PublicHeader } from "@/components/layout/PublicHeader";
import { PublicFooter } from "@/components/layout/PublicFooter";
import "@/styles/public.css";

const topics = [
  ["Découverte","Vous souhaitez comprendre le produit, son fonctionnement ou les cas d’usage.","/produit"],
  ["Tarifs","Vous voulez comparer les abonnements et les prestations proposées.","/tarifs"],
  ["Sécurité","Vous cherchez à comprendre les accès, les rôles, l’historique et les principes de contrôle.","/securite"],
  ["Juridique","Votre demande concerne les documents contractuels, la confidentialité ou les informations légales.","/contact-juridique"],
];

export function ContactPage() {
  return <div className="rd-public">
    <PublicHeader />
    <main>
      <section className="rd-contact">
        <div><span className="rd-public-eyebrow">CONTACT</span><h1>Parlons d’abord<br/><em>du besoin.</em></h1><p>Si vous évaluez Review Defense, commencez par préciser ce que vous cherchez à organiser : analyse d’avis, documentation, suivi des dossiers ou validation des étapes sensibles.</p></div>
        <div className="rd-contact-panel">
          <span>PREMIÈRE ÉTAPE</span><h2>Découvrez le parcours avant de changer votre organisation.</h2><p>La voie la plus directe est de créer un espace et de parcourir le produit. Vous pourrez ensuite examiner les fonctionnalités et décider de la suite.</p><Link className="rd-public-cta" to="/register">Créer mon espace →</Link>
          <hr/>
          <span>UNE DEMANDE PRÉCISE ?</span><p>Choisissez directement le sujet qui correspond à votre question.</p>
          <div className="rd-contact-links">{topics.map(([title,text,path]) => <Link key={title} to={path}><strong>{title}</strong><span>{text}</span><b>→</b></Link>)}</div>
        </div>
      </section>

      <section className="rd-public-faq-strip">
        <h2>Avant de nous contacter, vous pouvez aussi consulter les pages principales.</h2>
        <div><Link to="/produit">Produit</Link><Link to="/solutions">Solutions</Link><Link to="/fonctionnement">Fonctionnement</Link><Link to="/securite">Sécurité</Link><Link to="/tarifs">Tarifs</Link><Link to="/ressources">Ressources</Link></div>
      </section>
    </main>
    <PublicFooter />
  </div>;
}
