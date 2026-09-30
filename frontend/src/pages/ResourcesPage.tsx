import { Link } from "react-router-dom";
import { PublicHeader } from "@/components/layout/PublicHeader";
import { PublicFooter } from "@/components/layout/PublicFooter";
import "@/styles/public.css";

const resources = [
  ["Comprendre","Comment lire un avis qui mérite une vérification","Distinguer le contenu reçu, le contexte disponible, les éléments à réunir et les questions qui restent ouvertes.","/produit"],
  ["Méthode","Construire un dossier d’avis exploitable","Pourquoi rattacher captures, documents, échanges et décisions au même contexte facilite le suivi lorsque plusieurs étapes se succèdent.","/fonctionnement"],
  ["Organisation","Passer de l’avis au suivi","Une méthode simple pour savoir ce qui a été reçu, ce qui a été vérifié, ce qui manque et ce qui attend une validation.","/fonctionnement"],
  ["Contrôle","Pourquoi garder une validation humaine","Une automatisation peut préparer une étape. La décision sensible doit rester compréhensible et attribuable à la personne qui la valide.","/securite"],
  ["Sécurité","Les questions à poser avant de choisir un outil","Accès, permissions, historique, données et limites de l’automatisation : les points à examiner avant de confier des dossiers à un logiciel.","/securite"],
  ["FAQ","Questions fréquentes","Retrouvez les principales réponses sur le fonctionnement, les rôles, la sécurité et les limites du service.","/securite"],
];

export function ResourcesPage() {
  return <div className="rd-public">
    <PublicHeader />
    <main>
      <section className="rd-public-hero rd-resources-hero">
        <div><span className="rd-public-eyebrow">RESSOURCES</span><h1>Comprendre avant<br/><em>de décider.</em></h1></div>
        <div className="rd-public-hero-copy"><p>Les ressources publiques servent à comprendre la méthode, les usages et les limites de Review Defense. Elles ne remplacent ni une analyse juridique ni les règles propres à votre plateforme d’avis.</p><Link className="rd-public-link" to="/fonctionnement">Découvrir la méthode →</Link></div>
      </section>

      <section className="rd-resource-list" aria-label="Ressources Review Defense">
        {resources.map(([tag,title,text,path], index) => <article key={title}><div className="rd-resource-index">0{index + 1}</div><div><span>{tag}</span><h2>{title}</h2><p>{text}</p></div><Link to={path}>Explorer →</Link></article>)}
      </section>

      <section className="rd-public-band">
        <div><span className="rd-public-eyebrow">UNE RÈGLE SIMPLE</span><h2>Un outil doit aussi expliquer ses limites.</h2></div>
        <p>Review Defense aide à organiser le travail. Il ne transforme pas une hypothèse en fait, ne remplace pas un professionnel du droit et ne retire pas à l’entreprise la responsabilité de ses décisions.</p>
      </section>

      <section className="rd-public-final">
        <span className="rd-public-eyebrow">BESOIN D’ALLER PLUS LOIN ?</span>
        <h2>Voyez comment le produit transforme un avis en dossier suivi.</h2>
        <p>Le parcours complet présente les six étapes du traitement, de la réception jusqu’au suivi.</p>
        <div><Link className="rd-public-cta" to="/produit">Voir le produit →</Link><Link className="rd-public-secondary" to="/contact">Nous contacter</Link></div>
      </section>
    </main>
    <PublicFooter />
  </div>;
}
