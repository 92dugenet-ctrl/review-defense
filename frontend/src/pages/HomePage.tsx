import { useEffect, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { PublicHeader as Header } from "@/components/layout/PublicHeader";
import { PublicFooter as Footer } from "@/components/layout/PublicFooter";
import "@/styles/muse-landing.css";

const faqs = [
  ["À quoi sert Review Defense ?", "À transformer les avis qui demandent du contexte en dossiers structurés : ce qui est reçu, ce qui est disponible, ce qui manque et ce qui attend une décision."],
  ["Est-ce un outil qui répond automatiquement aux avis ?", "Non. Review Defense peut organiser les informations et préparer une étape, mais les actions sensibles restent soumises à une validation humaine."],
  ["Que retrouve-t-on dans un dossier ?", "Le contenu de l’avis, le contexte disponible, les preuves associées, l’historique du traitement et les prochaines étapes."],
  ["Puis-je commencer progressivement ?", "Oui. Vous pouvez commencer avec les dossiers qui demandent déjà votre attention puis élargir l’usage lorsque le processus est maîtrisé."],
];

function Reveal({ children }: { children: ReactNode }) {
  return <div className="rd-reveal">{children}</div>;
}

export function HomePage() {
  useEffect(() => {
    const elements = document.querySelectorAll<HTMLElement>(".rd-reveal");
    const observer = new IntersectionObserver(
      entries => entries.forEach(entry => entry.isIntersecting && entry.target.classList.add("is-visible")),
      { threshold: 0.14, rootMargin: "0px 0px -8% 0px" },
    );
    elements.forEach(element => observer.observe(element));
    return () => observer.disconnect();
  }, []);

  return <div className="rd-home">
    <Header />
    <main>
      <section className="rd-home-hero">
        <div className="rd-home-hero-copy">
          <Reveal>
            <span className="rd-eyebrow">REVIEW DEFENSE</span>
            <h1>Les avis qui demandent du contexte méritent <em>un vrai dossier.</em></h1>
            <p>Analysez ce qui est reçu, réunissez les éléments utiles et suivez chaque étape sans perdre la maîtrise des décisions sensibles.</p>
            <div className="rd-home-actions">
              <Link className="rd-primary-button" to="/register">Créer mon espace →</Link>
              <Link className="rd-text-button" to="/produit">Voir le produit</Link>
            </div>
          </Reveal>
        </div>
        <Reveal>
          <div className="rd-hero-card" aria-label="Vue synthétique d’un dossier Review Defense">
            <div className="rd-hero-card-top"><span>ESPACE DE TRAVAIL</span><b>01 / DOSSIER</b></div>
            <div className="rd-hero-card-title">Un avis. Son contexte. La suite à décider.</div>
            <div className="rd-hero-status"><span className="status-dot" /> Validation humaine requise</div>
            <div className="rd-hero-lines"><i /><i /><i /></div>
            <div className="rd-hero-mini-grid"><span><b>3</b> preuves</span><span><b>2</b> étapes</span><span><b>1</b> décision</span></div>
          </div>
        </Reveal>
      </section>

      <section className="rd-home-problem">
        <div className="rd-home-container rd-two-col">
          <Reveal><span className="rd-eyebrow">LE PROBLÈME</span><h2>Le texte de l’avis n’est souvent que le début.</h2></Reveal>
          <Reveal><p>Quand une situation mérite d’être vérifiée, les informations sont rarement au même endroit. Il faut retrouver le contexte, réunir les preuves, comprendre ce qui a déjà été fait et savoir qui doit décider de la suite.</p></Reveal>
        </div>
        <div className="rd-home-container rd-signal-grid">
          <Reveal><article><b>01</b><h3>Ce qui est reçu</h3><p>Avis, source et informations disponibles au départ.</p></article></Reveal>
          <Reveal><article><b>02</b><h3>Ce qui manque</h3><p>Éléments à vérifier, captures ou documents encore absents.</p></article></Reveal>
          <Reveal><article><b>03</b><h3>Ce qui attend</h3><p>Prochaine étape, validation et historique du traitement.</p></article></Reveal>
        </div>
      </section>

      <section className="rd-home-product story-section">
        <div className="rd-home-container">
          <div className="rd-section-heading">
            <Reveal><span className="rd-eyebrow">LE PRODUIT</span><h2>Un dossier de référence, pas une boîte à outils de plus.</h2></Reveal>
            <Reveal><p>Review Defense rassemble les informations autour de la situation pour que chacun puisse reprendre le dossier avec le même contexte.</p></Reveal>
          </div>
          <Reveal><img className="rd-feature-visual" src="/visual-workspace.svg" alt="Interface Review Defense montrant un dossier, ses preuves, son historique et une validation humaine" loading="lazy" /></Reveal>
          <div className="rd-feature-caption"><span>ESPACE DE TRAVAIL</span><strong>Le contexte reste attaché au dossier.</strong><Link to="/produit">Explorer le produit →</Link></div>
        </div>
      </section>

      <section className="rd-home-process">
        <div className="rd-home-container rd-two-col">
          <Reveal><span className="rd-eyebrow">LE PARCOURS</span><h2>Chaque étape prépare la suivante.</h2></Reveal>
          <Reveal><p>Le traitement suit un fil simple : recevoir, qualifier, réunir, préparer, valider puis suivre. L’automatisation intervient pour organiser le travail, pas pour remplacer la décision.</p><Link className="rd-text-button" to="/fonctionnement">Voir les six étapes →</Link></Reveal>
        </div>
        <div className="rd-home-container"><Reveal><img className="rd-process-visual" src="/visual-process.svg" alt="Les six étapes du parcours Review Defense, de la réception au suivi" loading="lazy" /></Reveal></div>
      </section>

      <section className="rd-home-security security-section">
        <div className="rd-home-container rd-two-col rd-security-intro">
          <Reveal><span className="rd-eyebrow">CONTRÔLE</span><h2>Le logiciel prépare.<br /><em>L’humain valide.</em></h2></Reveal>
          <Reveal><p>Les accès, permissions, historiques, preuves et validations font partie du cadre de travail. Review Defense ne présente pas ses automatismes comme une certification ou un conseil juridique.</p><Link className="rd-text-button" to="/securite">Voir les contrôles →</Link></Reveal>
        </div>
        <div className="rd-home-container"><Reveal><img className="rd-controls-visual" src="/visual-controls.svg" alt="Vue des six axes de contrôle de Review Defense" loading="lazy" /></Reveal></div>
      </section>

      <section className="rd-home-faq">
        <div className="rd-home-container rd-two-col">
          <Reveal><span className="rd-eyebrow">QUESTIONS</span><h2>Les réponses avant de commencer.</h2></Reveal>
          <div className="rd-faq-list">{faqs.map(([question, answer]) => <Reveal key={question}><details><summary>{question}<span>+</span></summary><p>{answer}</p></details></Reveal>)}</div>
        </div>
      </section>

      <section className="rd-home-final pricing">
        <Reveal><span className="rd-eyebrow">POUR COMMENCER</span><h2>Commencez avec les dossiers qui demandent déjà votre attention.</h2><p>Découvrez le produit, choisissez votre formule et créez votre espace lorsque le fonctionnement vous convient.</p><div className="rd-home-actions"><Link className="rd-primary-button" to="/tarifs">Voir les offres →</Link><Link className="rd-secondary-button" to="/register">Créer mon espace</Link></div></Reveal>
      </section>
    </main>
    <Footer />
  </div>;
}
