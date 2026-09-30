import { Link } from "react-router-dom";
import { PublicHeader } from "@/components/layout/PublicHeader";
import { PublicFooter } from "@/components/layout/PublicFooter";
import "@/styles/public.css";

const solutions = [
  { title:"Restaurants", kicker:"VOLUME & RÉPUTATION", text:"Les avis arrivent pendant que l’activité continue. L’enjeu est de retrouver rapidement le contexte et de ne pas perdre le fil des dossiers qui demandent une vérification.", points:["Centraliser les avis à examiner","Rattacher captures, documents et échanges au dossier","Conserver une validation humaine avant les étapes sensibles"] },
  { title:"Hôtellerie", kicker:"SUIVI DANS LE TEMPS", text:"Une situation peut nécessiter plusieurs vérifications et plusieurs personnes. Le dossier conserve l’historique pour que chacun puisse reprendre le traitement avec le même contexte.", points:["Suivre les dossiers ouverts","Retrouver les étapes déjà réalisées","Identifier les actions qui attendent une décision"] },
  { title:"Commerces", kicker:"RÉPUTATION LOCALE", text:"Quand chaque avis compte, une organisation simple permet de distinguer les retours courants des situations qui méritent un examen plus approfondi.", points:["Trier les situations qui demandent une attention","Conserver les éléments utiles","Préparer la prochaine étape sans automatiser la décision"] },
  { title:"Artisans & indépendants", kicker:"SIMPLICITÉ", text:"Une petite équipe n’a pas besoin d’un processus lourd. Review Defense apporte un point de référence pour documenter et suivre les dossiers importants.", points:["Commencer avec quelques dossiers","Voir ce qui est disponible et ce qui manque","Garder une chronologie lisible"] },
  { title:"Services", kicker:"CONTEXTE CLIENT", text:"Lorsque plusieurs échanges entourent un avis, le contexte devient aussi important que le texte publié. Le dossier rassemble les informations utiles autour de la situation.", points:["Relier avis et éléments associés","Structurer les informations disponibles","Préparer une réponse ou une étape de suivi"] },
  { title:"Réseaux & franchises", kicker:"VISION MULTI-SITES", text:"Plusieurs établissements peuvent suivre des situations différentes. L’organisation par dossiers facilite la continuité du traitement et la remontée des cas nécessitant une attention particulière.", points:["Conserver un historique par dossier","Faciliter la reprise entre intervenants","Structurer les validations importantes"] },
];

export function SolutionsPage() {
  return <div className="rd-public">
    <PublicHeader />
    <main>
      <section className="rd-public-hero rd-solutions-hero">
        <div><span className="rd-public-eyebrow">SOLUTIONS / MÉTIERS</span><h1>Le même principe.<br/><em>Des réalités de terrain différentes.</em></h1></div>
        <div className="rd-public-hero-copy"><p>Review Defense s’adapte au contexte dans lequel vos avis sont traités. Le produit ne promet pas une décision automatique : il fournit un cadre pour analyser, documenter, préparer et suivre.</p><Link className="rd-public-link" to="/produit">Voir le produit →</Link></div>
      </section>

      <section className="rd-solution-grid" aria-label="Solutions par métier">
        {solutions.map(item => <article className="rd-solution-card" key={item.title}><span>{item.kicker}</span><h2>{item.title}</h2><p>{item.text}</p><ul>{item.points.map(point => <li key={point}>{point}</li>)}</ul></article>)}
      </section>

      <section className="rd-public-band">
        <div><span className="rd-public-eyebrow">UNE BASE COMMUNE</span><h2>Un dossier, quel que soit votre métier.</h2></div>
        <p>Le principe reste identique : comprendre ce qui est reçu, réunir les éléments disponibles, préparer la suite et conserver une trace du traitement. Les décisions sensibles restent sous le contrôle de la personne habilitée.</p>
      </section>

      <section className="rd-public-final">
        <span className="rd-public-eyebrow">POUR COMMENCER</span>
        <h2>Commencez avec les dossiers qui demandent déjà votre attention.</h2>
        <p>Découvrez d’abord le produit, puis le parcours complet. Vous pouvez commencer petit et élargir l’usage à mesure que votre organisation prend en main la méthode.</p>
        <div><Link className="rd-public-cta" to="/register">Créer mon espace →</Link><Link className="rd-public-secondary" to="/fonctionnement">Voir le parcours</Link></div>
      </section>
    </main>
    <PublicFooter />
  </div>;
}
