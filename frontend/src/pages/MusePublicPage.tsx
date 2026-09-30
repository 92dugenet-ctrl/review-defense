import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api } from "@/services/api/client";
import "@/styles/muse-v3.css";
import { MuseMotion } from "@/components/public/MuseMotion";

const nav = [
  ["/produit", "Produit"],
  ["/fonctionnement", "Fonctionnement"],
  ["/securite", "Sécurité"],
  ["/tarifs", "Tarifs"],
  ["/contact", "Contact"],
] as const;

const faqs = [
  ["Que fait Review Defense ?", "Review Defense rassemble l'avis, son contexte, les éléments disponibles, les pièces utiles et les étapes de traitement dans un même espace."],
  ["Est-ce que les réponses sont envoyées automatiquement ?", "Non. Le logiciel peut préparer et organiser le travail, mais les actions sensibles restent sous validation humaine."],
  ["Que contient un dossier ?", "L'avis reçu, le contexte disponible, les preuves et sources associées, l'historique du traitement et la prochaine étape."],
  ["Puis-je commencer avec quelques dossiers ?", "Oui. L'espace est conçu pour commencer progressivement puis structurer davantage le traitement lorsque le volume augmente."],
  ["Qui garde la décision ?", "Une personne habilitée. Review Defense prépare le contexte et les actions possibles sans se substituer à la décision."],
];

const process = [
  ["01","Recevoir","Le signal entre dans le dossier.","Entrée"],
  ["02","Qualifier","Le contenu est distingué entre établi, disponible et à vérifier.","Lecture"],
  ["03","Réunir","Les captures, documents et sources utiles sont rattachés.","Preuves"],
  ["04","Préparer","Le contexte est ordonné pour rendre la suite lisible.","Préparation"],
  ["05","Valider","Une personne habilitée décide de l'action à retenir.","Décision"],
  ["06","Suivre","Le dossier reste exploitable après l'action.","Continuité"],
];

const controls = [
  ["01","Accès","Qui peut entrer dans l'espace."],
  ["02","Permissions","Ce que chaque rôle peut consulter ou faire."],
  ["03","Historique","Les événements importants restent lisibles."],
  ["04","Preuves","Chaque élément conserve son contexte."],
  ["05","Validation","Les actions sensibles restent soumises à une personne."],
  ["06","Limites","Le produit ne se présente pas comme une certification ou un conseil juridique."],
];

function Shell({ children }: { children: React.ReactNode }) {
  const [open,setOpen]=useState(false);
  const [search,setSearch]=useState(false);
  const location=useLocation();
  useEffect(()=>{setOpen(false);setSearch(false);document.body.classList.remove("muse-locked");window.scrollTo({top:0,behavior:"auto"})},[location.pathname]);
  return <div className="muse-site"><MuseMotion/>
    <div className="muse-progress"><i/></div>
    <header className="muse-header">
      <Link className="muse-brand" to="/">◉ <span>Review Defense</span></Link>
      <nav>{nav.map(([path,label])=><Link key={path} className={location.pathname===path?"active":""} to={path}>{label}</Link>)}</nav>
      <div className="muse-actions">
        <button className="muse-search-open" onClick={()=>{setSearch(true);document.body.classList.add("muse-locked")}} aria-label="Rechercher">⌕</button>
        <Link className="muse-pill muse-blue" to="/register">Créer mon espace</Link>
      </div>
      <button className="muse-menu-toggle" onClick={()=>setOpen(!open)} aria-expanded={open}>☰</button>
    </header>
    <div className={"muse-mobile-menu "+(open?"open":"")}>{nav.map(([path,label])=><Link key={path} to={path}>{label}</Link>)}<Link className="muse-pill muse-blue" to="/register">Créer mon espace</Link></div>
    {children}
    <footer className="muse-footer">
      <div className="muse-footer-top">
        <Link className="muse-brand" to="/">◉ <span>Review Defense</span></Link>
        <div><h4>Produit</h4><Link to="/produit">Produit</Link><Link to="/fonctionnement">Fonctionnement</Link><Link to="/securite">Sécurité</Link></div>
        <div><h4>Compte</h4><Link to="/login">Connexion</Link><Link to="/register">Créer un espace</Link><Link to="/contact">Contact</Link></div>
        <div><h4>Légal</h4><Link to="/mentions-legales">Mentions légales</Link><Link to="/confidentialite">Confidentialité</Link><Link to="/cgu">CGU</Link><Link to="/cgv">CGV</Link></div>
      </div>
      <small>© 2026 Review Defense — Analyse, dossiers, validation.</small>
    </footer>
    {search&&<div className="muse-search-panel"><button onClick={()=>{setSearch(false);document.body.classList.remove("muse-locked")}}>×</button><input autoFocus placeholder="Rechercher Review Defense…"/><p>Recherchez une fonctionnalité ou une information</p></div>}
  </div>;
}

function Scene({children,className="",id}:{children:React.ReactNode,className?:string,id?:string}) {
  return <section id={id} className={"muse-scene "+className}><div className="muse-scene-inner">{children}</div></section>;
}

function Reveal({children}:{children:React.ReactNode}) {
  return <div className="muse-reveal">{children}</div>;
}

function Home() {
 return <Shell><main>
  <Scene className="muse-hero muse-home-hero">
    <div className="muse-home-hero-inner">
      <Reveal><div className="muse-eyebrow">REVIEW DEFENSE · EN ACTION</div><h1>See how Review Defense<br/>works for you</h1><p>De l'avis reçu au dossier documenté, Review Defense vous aide à comprendre, organiser et préparer chaque situation.</p><Link className="muse-pill muse-blue" to="/register">Créer mon espace</Link></Reveal>
      <Reveal><div className="muse-hero-video"><video autoPlay muted loop playsInline preload="metadata" poster="https://images.unsplash.com/photo-1556761175-b413da4baf72?auto=format&fit=crop&w=1800&q=85" aria-label="Présentation vidéo Review Defense"><source src="https://www.ariaditerra.com/wp-content/uploads/2023/02/coverr-chef-preparing-a-dish-at-a-restaurant-6248-1080p.mp4" type="video/mp4"/></video><div className="muse-hero-overlay"><span>REVIEW DEFENSE</span><strong>Un dossier. Tout le contexte.</strong><small>Analyse · preuves · validation · suivi</small></div></div></Reveal>
    </div>
    <div className="muse-word muse-word-editorial"><span>Review</span><b>◌</b><span>Defense</span><em>est</em><strong>votre</strong><em>poste de travail</em></div>
  </Scene>

  <Scene className="muse-light" id="muse">
    <div className="muse-two muse-agent-layout">
      <Reveal><div className="muse-eyebrow">POSTE DE TRAVAIL</div><h2>Prêt à traiter vos avis avec plus de contexte ?</h2><p>Un espace pour réunir l'avis, les éléments disponibles, les preuves et les prochaines étapes avant d'agir.</p><Link className="muse-pill muse-blue" to="/produit">Découvrir le produit</Link></Reveal>
      <Reveal><div className="muse-orb-stage"><div className="muse-orb o1">⌁</div><div className="muse-orb o2">✦</div><div className="muse-orb o3">◫</div><div className="muse-orb main">◌</div></div></Reveal>
    </div>
  </Scene>

  <Scene id="faq">
    <Reveal><div className="muse-eyebrow">QUESTIONS FRÉQUENTES</div><h2>Comment Review Defense fonctionne ?</h2><div className="muse-faq">{faqs.map(([q,a])=><details key={q}><summary>{q}</summary><p>{a}</p></details>)}</div></Reveal>
  </Scene>

  <Scene className="muse-light" id="products">
    <Reveal><div className="muse-eyebrow">EXPLORER</div><h2>Tout ce qu'il faut pour faire avancer un dossier.</h2><div className="muse-product-grid muse-product-grid-reference">
      <article><img src="https://images.unsplash.com/photo-1551836022-d5d88e9218df?auto=format&fit=crop&w=1600&q=85" alt="Analyse Review Defense"/><div><small>ANALYSE</small><h3>Comprendre ce qui mérite d'être examiné.</h3><p>Lecture, qualification et contexte réunis au même endroit.</p></div></article>
      <article><img src="https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1600&q=85" alt="Dossier Review Defense"/><div><small>DOSSIERS</small><h3>Documenter ce qui compte vraiment.</h3><p>Sources, pièces et historique restent liés à la situation.</p></div></article>
    </div></Reveal>
  </Scene>

  <Scene className="muse-research" id="research">
    <div className="muse-research-reference">
      <aside><div className="muse-eyebrow">FILTRER PAR</div><button>Dossiers <b>+</b></button><button>Preuves <b>+</b></button><button>Étapes <b>+</b></button><button>Historique <b>+</b></button><Link to="/produit">Tout afficher</Link></aside>
      <Reveal><div className="muse-eyebrow">DOSSIERS</div><h2>Les informations utiles, dans le bon ordre.</h2><div className="muse-research-cards">
        <article><img src="https://images.unsplash.com/photo-1556761175-4b46a572b786?auto=format&fit=crop&w=1400&q=85" alt="Dossier équipe"/><small>ANALYSE · DOSSIER 01</small><h3>Réunir le contexte avant toute action.</h3><p>Les éléments importants sont présentés avec leur état et leur origine.</p><Link to="/fonctionnement">Voir le fonctionnement →</Link></article>
        <article><img src="https://images.unsplash.com/photo-1553877522-43269d4ea984?auto=format&fit=crop&w=1400&q=85" alt="Preuves et documentation"/><small>PREUVES · DOSSIER 02</small><h3>Conserver les pièces qui expliquent la situation.</h3><p>Chaque élément reste rattaché au dossier auquel il appartient.</p><Link to="/fonctionnement">Voir le fonctionnement →</Link></article>
      </div></Reveal>
    </div>
  </Scene>

  <Scene className="muse-overlay"><div className="muse-detail-reference"><div className="muse-detail-image"><img src="https://images.unsplash.com/photo-1556761175-b413da4baf72?auto=format&fit=crop&w=1800&q=85" alt="Préparation d'un dossier"/><div className="muse-loader"/></div><div className="muse-detail-panel"><div className="muse-eyebrow">REVIEW DEFENSE</div><h2>Préparer une situation complexe sans perdre le fil.</h2><p>Le dossier conserve le contexte, les preuves et les étapes de validation au même endroit.</p></div></div></Scene>

  <Scene className="muse-chat-reference" id="resources">
    <div className="muse-chat-reference-grid">
      <Reveal><div className="muse-chat-copy"><div className="muse-eyebrow">L'EXPÉRIENCE REVIEW DEFENSE</div><h2>Une interface qui suit votre façon de traiter un dossier.</h2><p>Comme dans une conversation, vous pouvez partir d'une question, ajouter du contexte et demander au logiciel de préparer la suite.</p><div className="muse-chips">{["Réponses structurées","Analyse du dossier","Preuves et documents","Suivi","Validation"].map((x,i)=><button key={x} className={i===0?"active":""}>{x}</button>)}</div></div></Reveal>
      <Reveal><div className="muse-chat"><header>Review Defense <span>●</span></header><div className="bubble">J'ai réuni les éléments disponibles dans ce dossier.</div><div className="bubble right">Qu'est-ce qui manque encore ?</div><div className="bubble">Deux pièces sont encore à vérifier avant validation.</div><div className="chat-input">Ajouter une instruction… <b>↑</b></div></div></Reveal>
    </div>
  </Scene>

  <Scene className="muse-blue-scene" id="try">
    <div className="muse-two muse-assistant-reference">
      <Reveal><div><div className="muse-eyebrow">REVIEW DEFENSE</div><h2>Votre espace de travail qui reste sous votre contrôle</h2><p>Préparez l'analyse, organisez les preuves, suivez les dossiers et validez les actions sensibles.</p><div className="muse-store-buttons"><Link to="/register">Créer mon espace</Link><Link to="/login">Se connecter</Link></div></div></Reveal>
      <Reveal><div className="muse-phone-stage"><div className="muse-phone"><strong>Review Defense</strong><div className="phone-message">Votre point de suivi est prêt.</div><div className="phone-message soft">3 dossiers à vérifier et 2 validations en attente.</div><div className="phone-input">Ouvrir le dossier…</div></div></div></Reveal>
    </div>
  </Scene>

  <Scene className="muse-social" id="about">
    <Reveal><div className="muse-social-head"><div><div className="muse-eyebrow">AUTOUR DU DOSSIER</div><h2>Un même contexte pour chaque personne qui intervient.</h2></div><Link className="muse-pill muse-blue" to="/securite">Voir les contrôles</Link></div>
      <div className="muse-social-grid"><div className="social-main"><img src="https://images.unsplash.com/photo-1556761175-4b46a572b786?auto=format&fit=crop&w=1600&q=85" alt="Équipe Review Defense"/><span>TRAVAIL COLLECTIF</span><strong>Analyse, preuves, validation et suivi au même endroit.</strong></div><div>Analyse</div><div>Preuves</div><div>Validation</div><div>Suivi</div></div>
    </Reveal>
  </Scene>

  <Scene className="muse-responsibility">
    <div className="muse-two muse-responsibility-reference"><Reveal><div><div className="muse-eyebrow">TRAVAIL RESPONSABLE</div><h2>Préparer avec l'IA.<br/>Décider avec l'humain.</h2><p>Review Defense organise les informations et prépare les étapes. Les décisions sensibles restent sous le contrôle d'une personne habilitée.</p></div></Reveal><Reveal><img src="https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1600&q=85" alt="Équipe en réunion"/></Reveal></div>
    <div className="muse-principles"><div><b>Contexte</b><span>Les informations restent rattachées au dossier.</span></div><div><b>Traçabilité</b><span>Les étapes importantes restent lisibles.</span></div><div><b>Validation</b><span>Une personne habilitée garde la décision.</span></div></div>
  </Scene>
 </main></Shell>;
}
function Product(){return <Shell><main><Scene className="muse-hero muse-product-page"><Reveal><div className="muse-eyebrow">LE PRODUIT</div><h1>Un poste de travail pour les avis qui demandent <em>du contexte.</em></h1><p>Analysez, documentez, suivez et validez dans une expérience pensée comme une suite de scènes de travail.</p><Link className="muse-pill muse-blue" to="/register">Créer mon espace</Link></Reveal></Scene><Scene className="muse-light"><Reveal><div className="muse-eyebrow">LES MOMENTS DE TRAVAIL</div><h2>Voir le dossier sous plusieurs angles.</h2><div className="muse-product-grid four">{[["01","Analyser","Comprendre le contenu reçu et les points à vérifier."],["02","Documenter","Rattacher les preuves et les sources."],["03","Suivre","Conserver l'état et la prochaine étape."],["04","Valider","Garder la décision entre des mains habilitées."]].map(x=><article className="muse-simple-card" key={x[0]}><b>{x[0]}</b><h3>{x[1]}</h3><p>{x[2]}</p></article>)}</div></Reveal></Scene><Scene><Reveal><div className="muse-two"><div><div className="muse-eyebrow">ESPACE DE TRAVAIL</div><h2>Tout ce qui explique la situation reste au même endroit.</h2></div><img className="muse-wide-image" src="https://images.unsplash.com/photo-1553877522-43269d4ea984?auto=format&fit=crop&w=1400&q=85" alt="Espace de travail"/></div></Reveal></Scene><Scene className="muse-blue-scene"><Reveal><div className="muse-eyebrow">ÉTAPE SUIVANTE</div><h2>Voyez comment le dossier avance.</h2><Link className="muse-pill" to="/fonctionnement">Voir le fonctionnement →</Link></Reveal></Scene></main></Shell>}

function Method(){return <Shell><main><Scene className="muse-hero"><Reveal><div className="muse-eyebrow">FONCTIONNEMENT</div><h1>Six étapes.<br/><em>Un même fil.</em></h1><p>Chaque étape prépare la suivante, avec une séparation claire entre préparation logicielle et décision humaine.</p></Reveal></Scene><Scene className="muse-light"><div className="muse-process-list">{process.map(([n,t,d,l])=><Reveal key={n}><article className={n==="05"?"decision":""}><b>{n}</b><div><small>{l}</small><h2>{t}</h2><p>{d}</p></div><span>{n==="05"?"VALIDATION HUMAINE":"→"}</span></article></Reveal>)}</div></Scene><Scene><div className="muse-two"><Reveal><div className="muse-eyebrow">LA LOGIQUE</div><h2>Chaque étape laisse <em>quelque chose derrière elle.</em></h2></Reveal><Reveal><div className="muse-state-list">{[["Reçu","Ce qui est entré dans le dossier."],["Vérifié","Ce qui a été examiné ou complété."],["Préparé","Ce qui est prêt pour la prochaine intervention."],["Décidé","Ce qui a été validé."]].map(x=><div key={x[0]}><b>{x[0]}</b><span>{x[1]}</span></div>)}</div></Reveal></div></Scene><Scene className="muse-blue-scene"><Reveal><div className="muse-eyebrow">ÉTAPE SUIVANTE</div><h2>Comprendre ce qui reste sous votre contrôle.</h2><Link className="muse-pill" to="/securite">Voir la sécurité →</Link></Reveal></Scene></main></Shell>}

function Security(){return <Shell><main><Scene className="muse-hero"><div className="muse-two"><Reveal><div className="muse-eyebrow">SÉCURITÉ / CONTRÔLE</div><h1>Voir ce qui est contrôlé.<br/><em>Comprendre ce qui reste humain.</em></h1></Reveal><Reveal><p>Accès, permissions, historique, contexte des preuves et validations forment le cadre de travail.</p></Reveal></div></Scene><Scene className="muse-light"><Reveal><div className="muse-eyebrow">CONTRÔLE DE L'ESPACE</div><h2>Six axes pour garder le dossier lisible.</h2><div className="muse-control-grid">{controls.map(([n,t,d])=><article key={n}><b>{n}</b><h3>{t}</h3><p>{d}</p></article>)}</div></Reveal></Scene><Scene><Reveal><div className="muse-two"><div><div className="muse-eyebrow">RESPONSABILITÉ</div><h2>Le logiciel prépare.<br/><em>L'humain valide.</em></h2></div><div className="muse-principles large"><div><b>Logiciel</b><span>Analyse et organise.</span></div><div><b>Logiciel</b><span>Prépare une étape.</span></div><div><b>Humain</b><span>Valide l'action sensible.</span></div></div></div></Reveal></Scene><Scene><Reveal><div className="muse-eyebrow">QUESTIONS</div><h2>Les contrôles expliqués simplement.</h2><div className="muse-faq">{[["Le logiciel décide-t-il à ma place ?","Non. Il prépare et organise le travail ; la décision sensible reste à la personne habilitée."],["Cette page est-elle une certification ?","Non. Elle présente les principes de contrôle du produit, pas une certification."],["Les permissions sont-elles identiques partout ?","Non. Elles dépendent du rôle et de la configuration de l'organisation."]].map(x=><details key={x[0]}><summary>{x[0]}</summary><p>{x[1]}</p></details>)}</div></Reveal></Scene><Scene className="muse-dark-scene"><Reveal><div className="muse-eyebrow">ÉTAPE SUIVANTE</div><h2>Voir les formats disponibles.</h2><Link className="muse-pill muse-blue" to="/tarifs">Voir les tarifs →</Link></Reveal></Scene></main></Shell>}

function Contact(){return <Shell><main><Scene className="muse-hero"><Reveal><div className="muse-eyebrow">CONTACT</div><h1>Parlons du besoin,<br/><em>pas d'un catalogue.</em></h1><p>Commencez par explorer le produit, son fonctionnement et son cadre de contrôle. Pour une question précise, dites-nous ce que vous cherchez à organiser.</p><Link className="muse-pill muse-blue" to="/produit">Voir le produit</Link></Reveal></Scene><Scene className="muse-light"><div className="muse-product-grid four">{[["Produit","Parcourir l'espace de travail.","/produit"],["Fonctionnement","Voir les six étapes.","/fonctionnement"],["Sécurité","Examiner les contrôles.","/securite"],["Tarifs","Voir les formats disponibles.","/tarifs"]].map(x=><Link className="muse-simple-card" to={x[2]} key={x[0]}><small>{x[0]}</small><h3>{x[1]}</h3><b>→</b></Link>)}</div></Scene><Scene className="muse-blue-scene"><Reveal><div className="muse-eyebrow">PRÊT À COMMENCER ?</div><h2>Créez votre espace lorsque le fonctionnement vous convient.</h2><Link className="muse-pill" to="/register">Créer mon espace →</Link></Reveal></Scene></main></Shell>}

function Pricing(){const [catalog,setCatalog]=useState<any[]>([]);const [error,setError]=useState("");const [selected,setSelected]=useState<string|null>(null);const groups=[{title:"Abonnements",k:["subscription"]},{title:"Audits",k:["audit"]},{title:"Défense",k:["defense_step","defense_package"]}];useEffect(()=>{api.get<any>("/v1/billing/catalog").then(d=>setCatalog(d.items??[])).catch(e=>setError(e instanceof Error?e.message:"Catalogue indisponible."))},[]);const loadPayPal=async(clientId:string,components:string,extra="")=>{document.querySelector('script[data-rd-paypal]')?.remove();await new Promise<void>((resolve,reject)=>{const s=document.createElement("script");s.src="https://www.paypal.com/sdk/js?client-id="+encodeURIComponent(clientId)+"&components="+components+"&currency=EUR&locale=fr_FR"+extra;s.async=true;s.dataset.rdPaypal="1";s.onload=()=>resolve();s.onerror=()=>reject(new Error("Impossible de charger PayPal."));document.head.appendChild(s)});if(!(window as any).paypal)throw new Error("PayPal indisponible.")};const pay=async(o:any)=>{setSelected(o.offer_id);try{if(!o.paypal_hosted_button_id)throw new Error("Paiement en ligne indisponible.");await loadPayPal("BAAftx79q4rSHY7vc2aYy_hgx3KB6GB15k__TBghUQyd1_ixXSqv71UHw1RXZvkR4cli25WsSirUKWt7zs","hosted-buttons");const id="paypal-"+o.offer_id;const node=document.getElementById(id);if(!node)throw new Error("Conteneur PayPal introuvable.");node.innerHTML="";(window as any).paypal.HostedButtons({hostedButtonId:o.paypal_hosted_button_id}).render("#"+id)}catch(e){setError(e instanceof Error?e.message:"Paiement indisponible.");setSelected(null)}};return <Shell><main><Scene className="muse-hero"><Reveal><div className="muse-eyebrow">TARIFS</div><h1>Choisissez le format qui correspond <em>à votre besoin.</em></h1><p>Abonnement de suivi, audit ponctuel ou traitement d'un avis précis.</p></Reveal></Scene>{error&&<div className="muse-price-error">{error}</div>}<Scene className="muse-light"><Reveal><div className="muse-pricing-groups">{groups.map(g=><section key={g.title}><div className="muse-eyebrow">{g.title.toUpperCase()}</div><h2>{g.title}</h2><div className="muse-price-grid">{catalog.filter(o=>g.k.includes(o.kind)).map(o=>{const quote=o.amount===null;const active=selected===o.offer_id;const price=quote?"Sur devis":Number(o.amount).toLocaleString("fr-FR",{minimumFractionDigits:0,maximumFractionDigits:2})+" €";return <article key={o.offer_id}><small>{o.kind==="subscription"?"ABONNEMENT":o.kind==="audit"?"AUDIT":"DÉFENSE"}</small><h3>{o.name_fr}</h3><strong>{price}</strong><p>{o.description_fr||"Format Review Defense adapté à votre besoin."}</p>{quote?<Link className="muse-pill muse-blue" to="/contact">Échanger →</Link>:active?<div id={"paypal-"+o.offer_id} className="muse-paypal"/>:<button className="muse-pill muse-blue" onClick={()=>pay(o)}>Payer en ligne →</button>}</article>})}</div></section>)}</div></Reveal></Scene><Scene className="muse-blue-scene"><Reveal><h2>Vous pouvez commencer progressivement.</h2><Link className="muse-pill" to="/register">Créer mon espace →</Link></Reveal></Scene></main></Shell>}

export function MusePublicPage(){const path=useLocation().pathname;const page=useMemo(()=>path==="/produit"?<Product/>:path==="/fonctionnement"?<Method/>:path==="/securite"?<Security/>:path==="/tarifs"?<Pricing/>:path==="/contact"?<Contact/>:<Home/>,[path]);return page}
