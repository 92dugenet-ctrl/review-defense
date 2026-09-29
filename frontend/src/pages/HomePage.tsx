import { Link } from "react-router-dom";

const pillars = [
  { n: "01", title: "Analyse", text: "Transformez un avis isolé en éléments lisibles : faits, signaux, contradictions et points à vérifier." },
  { n: "02", title: "Preuves", text: "Reliez captures, documents, sources et échanges au bon endroit dans le dossier." },
  { n: "03", title: "Décision", text: "Votre équipe garde la main. Le logiciel prépare et documente ; la décision reste humaine." },
];

const workflow = [
  ["01", "Avis", "Le signal entre dans votre espace."],
  ["02", "Analyse", "Les éléments à examiner sont structurés."],
  ["03", "Preuves", "Les pièces utiles sont reliées au contexte."],
  ["04", "Dossier", "La situation devient lisible et traçable."],
  ["05", "Validation", "Une personne habilitée décide de la suite."],
];

function ProductWindow() {
  return (
    <div className="rd-commercial-stage">
      <div className="rd-stage-orb rd-stage-orb-a" />
      <div className="rd-stage-orb rd-stage-orb-b" />
      <div className="rd-product-browser">
        <div className="rd-browser-top">
          <div className="rd-browser-dots"><i /><i /><i /></div>
          <strong>Review Defense</strong>
          <span>Workspace · Organisation</span>
          <b>•••</b>
        </div>
        <div className="rd-product-layout">
          <aside className="rd-product-rail">
            <div className="rd-product-logo">RD</div>
            <span className="active">⌂ <em>Tableau</em></span>
            <span>◌ <em>Mes avis</em></span>
            <span>⌕ <em>Analyse</em></span>
            <span>□ <em>Dossiers</em></span>
            <span>◇ <em>Preuves</em></span>
            <span>✓ <em>Suivi</em></span>
            <div className="rail-spacer" />
            <span>⚙ <em>Paramètres</em></span>
          </aside>
          <div className="rd-product-main">
            <div className="rd-product-heading">
              <div><small>ANALYSE · REV-88421</small><h3>Avis à vérifier</h3></div>
              <span>À VÉRIFIER</span>
            </div>
            <div className="rd-review-card">
              <div className="rd-review-rating">★☆☆☆☆</div>
              <strong>« Service déplorable, une arnaque totale. »</strong>
              <small>Source disponible · contexte à examiner</small>
            </div>
            <div className="rd-product-metrics">
              <div><small>SIGNAUX</small><b>03</b><span>à examiner</span></div>
              <div><small>PREUVES</small><b>07</b><span>associées</span></div>
              <div><small>STATUT</small><b>Gel</b><span>validation requise</span></div>
            </div>
            <div className="rd-product-flow">
              <span className="done">Analyse</span><i>→</i><span className="done">Décision</span><i>→</i><span className="current">Validation</span><i>→</i><span>Préparation</span>
            </div>
            <div className="rd-product-bottom">
              <div className="rd-bars"><small>ÉLÉMENTS À VÉRIFIER</small><div><i/><i/><i/><i/><i/></div></div>
              <div className="rd-human-gate"><small>HUMAN APPROVAL</small><strong>Validation requise</strong><span>Avant toute étape contrôlée</span></div>
            </div>
          </div>
        </div>
      </div>
      <div className="rd-floating-card rd-float-a"><small>IA ASSISTÉE</small><strong>7 éléments rapprochés</strong><span>Suggestions à vérifier</span></div>
      <div className="rd-floating-card rd-float-b"><small>TRAÇABILITÉ</small><strong>Décision verrouillée</strong><span>Historique conservé</span></div>
    </div>
  );
}

export function HomePage() {
  return (
    <div className="rd-commercial">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap');
        .rd-commercial{--blue:#2166f3;--blue2:#1748c7;--ink:#111827;--muted:#667085;--line:#e6e9ef;--soft:#f5f8fc;background:#fff;color:var(--ink);font-family:"DM Sans",Inter,system-ui,sans-serif;overflow:hidden}
        .rd-commercial *{box-sizing:border-box}.rd-commercial a{text-decoration:none;color:inherit}
        .rd-nav{position:sticky;top:0;z-index:50;height:76px;display:flex;align-items:center;justify-content:space-between;gap:28px;padding:0 clamp(20px,4vw,64px);border-bottom:1px solid rgb(230 233 239 / 75%);background:rgb(255 255 255 / 90%);backdrop-filter:blur(18px)}
        .rd-brand{display:flex;align-items:center;gap:10px;font-size:15px;font-weight:700;letter-spacing:-.04em;white-space:nowrap}.rd-brand-mark{display:grid;place-items:center;width:31px;height:31px;border-radius:9px;background:var(--ink);color:#fff;font-size:10px;font-weight:800}
        .rd-nav-links{display:flex;align-items:center;gap:30px;color:#475467;font-size:12px;font-weight:600}.rd-nav-links a{transition:color .18s}.rd-nav-links a:hover{color:var(--blue)}
        .rd-nav-actions{display:flex;align-items:center;gap:16px;font-size:12px;font-weight:650}.rd-login:hover{color:var(--blue)}
        .rd-nav-cta,.rd-primary{display:inline-flex;align-items:center;justify-content:center;gap:10px;border:0;background:var(--blue);color:#fff;border-radius:999px;min-height:42px;padding:0 19px;font:inherit;font-weight:700;box-shadow:0 8px 24px rgb(33 102 243 / 16%);transition:transform .18s,background .18s,box-shadow .18s}
        .rd-nav-cta:hover,.rd-primary:hover{background:var(--blue2);transform:translateY(-1px);box-shadow:0 12px 28px rgb(33 102 243 / 22%)}
        .rd-hero{position:relative;min-height:calc(100vh - 76px);display:grid;grid-template-columns:minmax(0,.88fr) minmax(500px,1.12fr);align-items:center;gap:30px;padding:72px clamp(20px,5vw,80px) 80px;background:linear-gradient(180deg,#fff 0%,#fbfcff 70%,#fff 100%)}
        .rd-hero:before{content:"";position:absolute;width:700px;height:700px;right:-250px;top:-250px;border-radius:50%;background:radial-gradient(circle,rgb(57 116 255 / 13%),transparent 66%);pointer-events:none}
        .rd-hero-copy{position:relative;z-index:2;max-width:650px}.rd-eyebrow{display:inline-flex;align-items:center;gap:8px;margin-bottom:22px;color:#315fd1;font-size:10px;font-weight:800;letter-spacing:.13em;text-transform:uppercase}.rd-eyebrow:before{content:"";width:7px;height:7px;border-radius:50%;background:#5f8eff;box-shadow:0 0 0 4px #edf3ff}
        .rd-hero h1{margin:0;max-width:720px;font-size:clamp(54px,6.4vw,94px);line-height:.93;letter-spacing:-.065em;font-weight:650}.rd-hero h1 em,.rd-section-title em{font-family:"Instrument Serif",Georgia,serif;font-weight:400;color:var(--blue)}
        .rd-hero-lead{max-width:570px;margin:28px 0 30px;color:#5d6878;font-size:16px;line-height:1.7}
        .rd-actions{display:flex;align-items:center;gap:22px;flex-wrap:wrap}.rd-secondary{font-size:12px;font-weight:700;color:#344054}.rd-secondary span{display:inline-grid;place-items:center;width:30px;height:30px;margin-right:7px;border:1px solid #dfe5ef;border-radius:50%}
        .rd-trust{display:flex;gap:22px;flex-wrap:wrap;margin-top:28px;color:#667085;font-size:10px;font-weight:600}.rd-trust span:before{content:"✓";margin-right:6px;color:#2c9b6c}
        .rd-commercial-stage{position:relative;min-height:610px;display:grid;place-items:center}.rd-stage-orb{position:absolute;border:1px solid rgb(33 102 243 / 13%);border-radius:50%}.rd-stage-orb-a{width:580px;height:580px}.rd-stage-orb-b{width:760px;height:760px}
        .rd-product-browser{position:relative;z-index:2;width:min(100%,700px);border:1px solid #dfe5ef;border-radius:18px;background:#fff;box-shadow:0 28px 80px rgb(16 24 40 / 13%),0 4px 14px rgb(16 24 40 / 5%);overflow:hidden;transform:perspective(1200px) rotateY(-3deg) rotateX(1deg)}
        .rd-browser-top{height:48px;display:flex;align-items:center;gap:12px;padding:0 15px;border-bottom:1px solid #edf0f5;background:#fbfcfe;color:#344054;font-size:10px}.rd-browser-top b{margin-left:auto;color:#98a2b3}.rd-browser-top span{color:#98a2b3}.rd-browser-dots{display:flex;gap:5px}.rd-browser-dots i{width:7px;height:7px;border-radius:50%;background:#d0d5dd}
        .rd-product-layout{display:grid;grid-template-columns:118px 1fr;min-height:455px}.rd-product-rail{display:flex;flex-direction:column;gap:5px;padding:15px 9px;border-right:1px solid #edf0f5;background:#fbfcfe;color:#98a2b3;font-size:9px}.rd-product-logo{display:grid;place-items:center;width:30px;height:30px;margin:0 0 13px;border-radius:9px;background:#101828;color:#fff;font-size:9px;font-weight:800}.rd-product-rail span{display:flex;align-items:center;gap:7px;padding:8px 7px;border-radius:7px}.rd-product-rail span.active{background:#eef4ff;color:#245ed6}.rd-product-rail em{font-style:normal}.rail-spacer{flex:1}
        .rd-product-main{padding:25px}.rd-product-heading{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.rd-product-heading small,.rd-review-card small,.rd-product-metrics small,.rd-human-gate small,.rd-bars small,.rd-floating-card small{display:block;color:#98a2b3;font-size:7px;font-weight:800;letter-spacing:.1em}.rd-product-heading h3{margin:5px 0 0;font-size:17px;letter-spacing:-.035em}.rd-product-heading>span{padding:6px 8px;border-radius:999px;background:#fff8e8;color:#b54708;font-size:7px;font-weight:800}
        .rd-review-card{display:grid;gap:7px;margin-top:20px;padding:17px;border:1px solid #e6e9ef;border-radius:12px;background:#fff}.rd-review-rating{color:#f59e0b;font-size:11px;letter-spacing:1px}.rd-review-card strong{font-size:12px;line-height:1.5}
        .rd-product-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}.rd-product-metrics div{display:grid;gap:4px;padding:12px;background:#f7f9fc;border-radius:10px}.rd-product-metrics b{font-size:20px;letter-spacing:-.04em}.rd-product-metrics span{color:#98a2b3;font-size:8px}
        .rd-product-flow{display:flex;align-items:center;gap:8px;margin:18px 0;color:#98a2b3;font-size:8px;font-weight:700}.rd-product-flow i{font-style:normal;color:#d0d5dd}.rd-product-flow span{padding:6px 8px;border-radius:7px;background:#f5f6f8}.rd-product-flow .done{background:#edf8f2;color:#157347}.rd-product-flow .current{background:#edf3ff;color:#245ed6}
        .rd-product-bottom{display:grid;grid-template-columns:1.2fr .8fr;gap:9px}.rd-bars,.rd-human-gate{padding:13px;border-radius:10px;background:#f8fafc}.rd-bars>div{display:flex;align-items:end;gap:7px;height:55px;margin-top:9px}.rd-bars i{display:block;flex:1;border-radius:4px 4px 1px 1px;background:#d8e5ff}.rd-bars i:nth-child(2){height:70%}.rd-bars i:nth-child(3){height:95%}.rd-bars i:nth-child(4){height:55%}.rd-bars i:nth-child(5){height:82%}.rd-human-gate{background:#eef4ff}.rd-human-gate strong{display:block;margin:8px 0 4px;color:#1748c7;font-size:11px}.rd-human-gate span{color:#667085;font-size:8px;line-height:1.4}
        .rd-floating-card{position:absolute;z-index:3;display:grid;gap:5px;padding:14px 16px;border:1px solid #e2e7ef;border-radius:12px;background:#fff;box-shadow:0 14px 35px rgb(16 24 40 / 10%)}.rd-floating-card strong{font-size:11px}.rd-floating-card span{color:#98a2b3;font-size:8px}.rd-float-a{left:-8px;bottom:84px}.rd-float-a small{color:#245ed6}.rd-float-b{right:-4px;top:94px}.rd-float-b small{color:#157347}
        .rd-strip{display:grid;grid-template-columns:1.2fr repeat(4,1fr);gap:0;padding:0 clamp(20px,5vw,80px);border-top:1px solid var(--line);border-bottom:1px solid var(--line);background:#fff}.rd-strip>*{padding:24px 20px;border-right:1px solid var(--line);font-size:10px}.rd-strip>*:last-child{border-right:0}.rd-strip-label{color:#98a2b3;font-weight:800;letter-spacing:.08em}.rd-strip b{font-size:12px}
        .rd-section{padding:125px clamp(20px,5vw,80px)}.rd-section-inner{max-width:1180px;margin:auto}.rd-section-kicker{display:block;margin-bottom:17px;color:#315fd1;font-size:10px;font-weight:800;letter-spacing:.13em}.rd-section-title{margin:0;max-width:800px;font-size:clamp(42px,5vw,70px);line-height:.98;letter-spacing:-.06em;font-weight:650}.rd-section-copy{max-width:560px;margin:22px 0 0;color:#667085;font-size:15px;line-height:1.7}
        .rd-story{background:#f7f9fc}.rd-pillars{display:grid;grid-template-columns:repeat(3,1fr);margin-top:70px;border-top:1px solid #dfe5ed}.rd-pillar{position:relative;padding:34px 28px 30px 0;border-right:1px solid #dfe5ed}.rd-pillar:not(:first-child){padding-left:28px}.rd-pillar:last-child{border-right:0}.rd-pillar small{color:#98a2b3;font-size:9px;font-weight:800}.rd-pillar h3{margin:40px 0 10px;font-size:24px;letter-spacing:-.04em}.rd-pillar p{margin:0;color:#667085;font-size:12px;line-height:1.65}.rd-pillar b{position:absolute;right:24px;top:34px;color:#245ed6;font-size:12px}
        .rd-dark{background:#101828;color:#fff;position:relative}.rd-dark:before{content:"";position:absolute;inset:0;background:radial-gradient(circle at 75% 25%,rgb(53 109 255 / 22%),transparent 33%);pointer-events:none}.rd-dark-inner{position:relative;z-index:1;max-width:1180px;margin:auto;display:grid;grid-template-columns:1fr 1fr;gap:80px;align-items:end}.rd-dark .rd-section-kicker{color:#9dbbff}.rd-dark .rd-section-copy{color:#b5bfce}
        .rd-human-card{margin-top:55px;display:grid;grid-template-columns:repeat(5,1fr);border:1px solid #344054;border-radius:16px;overflow:hidden}.rd-human-card div{padding:24px 18px;border-right:1px solid #344054}.rd-human-card div:last-child{border:0}.rd-human-card small{color:#98a2b3;font-size:8px}.rd-human-card strong{display:block;margin-top:10px;font-size:13px}.rd-human-card span{display:block;margin-top:5px;color:#98a2b3;font-size:9px;line-height:1.4}
        .rd-proof{background:#fff}.rd-proof-grid{display:grid;grid-template-columns:.9fr 1.1fr;gap:90px;align-items:center;margin-top:65px}.rd-proof-card{padding:26px;border:1px solid #e2e7ef;border-radius:18px;box-shadow:0 18px 45px rgb(16 24 40 / 7%)}.rd-proof-card header{display:flex;justify-content:space-between;padding-bottom:18px;border-bottom:1px solid #edf0f5}.rd-proof-card header strong{font-size:12px}.rd-proof-card header span{color:#157347;font-size:8px;font-weight:800}.rd-proof-row{display:flex;justify-content:space-between;gap:15px;padding:16px 0;border-bottom:1px solid #edf0f5;font-size:10px}.rd-proof-row span{color:#667085}.rd-proof-row b{color:#344054}.rd-proof-foot{display:flex;gap:10px;align-items:center;margin-top:18px;padding:12px;border-radius:10px;background:#f2f8f5;color:#157347}.rd-proof-foot i{font-style:normal;font-weight:900}.rd-proof-foot span{font-size:9px}.rd-proof-points{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:28px}.rd-proof-points span{color:#475467;font-size:11px}
        .rd-cta{padding:120px 20px;text-align:center;background:#f5f8ff}.rd-cta .rd-section-title{margin:0 auto}.rd-cta p{max-width:500px;margin:20px auto 30px;color:#667085;font-size:14px;line-height:1.6}
        .rd-footer{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:28px clamp(20px,5vw,80px);border-top:1px solid var(--line);color:#98a2b3;font-size:10px}.rd-footer a{color:#475467;font-weight:700}.rd-footer-brand{display:flex;align-items:center;gap:9px;color:#344054;font-weight:700}
        @media(max-width:1050px){.rd-hero{grid-template-columns:1fr;padding-top:55px}.rd-hero-copy{max-width:800px}.rd-commercial-stage{min-height:560px}.rd-nav-links{display:none}.rd-dark-inner,.rd-proof-grid{grid-template-columns:1fr;gap:45px}.rd-human-card{grid-template-columns:repeat(3,1fr)}.rd-human-card div:nth-child(3){border-right:0}.rd-human-card div:nth-child(n+4){border-top:1px solid #344054}}
        @media(max-width:700px){.rd-nav{height:66px}.rd-nav-actions .rd-login{display:none}.rd-nav-cta{min-height:38px;padding:0 15px;font-size:11px}.rd-hero{padding:52px 18px 50px;min-height:auto}.rd-hero h1{font-size:54px}.rd-hero-lead{font-size:14px}.rd-commercial-stage{min-height:440px;margin-top:15px}.rd-product-browser{transform:none;width:100%}.rd-product-layout{grid-template-columns:1fr}.rd-product-rail{display:none}.rd-product-main{padding:16px}.rd-floating-card{display:none}.rd-stage-orb-a{width:360px;height:360px}.rd-stage-orb-b{width:460px;height:460px}.rd-strip{grid-template-columns:1fr 1fr;padding:0 18px}.rd-strip>*{padding:16px 10px}.rd-strip>*:first-child{grid-column:1/-1;border-right:0}.rd-section{padding:82px 18px}.rd-pillars{grid-template-columns:1fr;margin-top:45px}.rd-pillar,.rd-pillar:not(:first-child){padding:25px 0;border-right:0;border-bottom:1px solid #dfe5ed}.rd-pillar:last-child{border-bottom:0}.rd-pillar h3{margin-top:26px}.rd-dark-inner{gap:35px}.rd-human-card{grid-template-columns:1fr 1fr}.rd-human-card div:nth-child(3){border-right:1px solid #344054}.rd-human-card div:nth-child(odd){border-right:0}.rd-proof-grid{gap:35px}.rd-proof-points{grid-template-columns:1fr}.rd-footer{align-items:flex-start;flex-direction:column}}
      `}</style>

      <header className="rd-nav">
        <Link to="/" className="rd-brand"><span className="rd-brand-mark">RD</span><span>Review Defense</span></Link>
        <nav className="rd-nav-links">
          <a href="#produit">Produit</a><a href="#methode">Méthode</a><a href="#securite">Sécurité</a><a href="#tarifs">Tarifs</a>
        </nav>
        <div className="rd-nav-actions"><Link className="rd-login" to="/login">Connexion</Link><Link className="rd-nav-cta" to="/register">Commencer <span>→</span></Link></div>
      </header>

      <main>
        <section className="rd-hero">
          <div className="rd-hero-copy">
            <span className="rd-eyebrow">REPUTATION INTELLIGENCE · POUR LES ENTREPRISES</span>
            <h1>Reprenez le contrôle de <em>vos avis.</em></h1>
            <p className="rd-hero-lead">Review Defense transforme les avis sensibles en dossiers lisibles, documentés et traçables. Analysez, structurez les preuves et préparez la suite — avec une validation humaine à chaque étape sensible.</p>
            <div className="rd-actions"><Link className="rd-primary" to="/register">Découvrir la plateforme <span>→</span></Link><a className="rd-secondary" href="#produit"><span>↓</span> Voir le produit</a></div>
            <div className="rd-trust"><span>Analyse structurée</span><span>Preuves documentées</span><span>Décisions humaines</span></div>
          </div>
          <ProductWindow />
        </section>

        <div className="rd-strip"><span className="rd-strip-label">UNE SEULE PLATEFORME</span><b>Analyse</b><b>Qualification</b><b>Preuves</b><b>Traçabilité</b></div>

        <section id="produit" className="rd-section rd-story">
          <div className="rd-section-inner">
            <span className="rd-section-kicker">LE PRODUIT</span>
            <h2 className="rd-section-title">Du signal au dossier,<br/><em>sans perdre le fil.</em></h2>
            <p className="rd-section-copy">Une expérience pensée comme un véritable outil de travail : moins de dispersion, plus de contexte, et une vue claire sur ce qui doit être vérifié.</p>
            <div className="rd-pillars">{pillars.map((p)=><article className="rd-pillar" key={p.n}><small>{p.n}</small><b>↗</b><h3>{p.title}</h3><p>{p.text}</p></article>)}</div>
          </div>
        </section>

        <section id="methode" className="rd-section rd-dark">
          <div className="rd-dark-inner">
            <div><span className="rd-section-kicker">LA MÉTHODE</span><h2 className="rd-section-title">Une IA qui prépare.<br/><em>Un humain qui décide.</em></h2></div>
            <p className="rd-section-copy">L’IA peut aider à comparer, rapprocher, synthétiser et structurer. Elle ne remplace pas la décision de votre équipe. Les étapes sensibles restent derrière un point de validation explicite.</p>
          </div>
          <div className="rd-section-inner">
            <div className="rd-human-card">{workflow.map(([n,t,d])=><div key={n}><small>{n}</small><strong>{t}</strong><span>{d}</span></div>)}</div>
          </div>
        </section>

        <section id="securite" className="rd-section rd-proof">
          <div className="rd-section-inner">
            <span className="rd-section-kicker">PREUVES & CONTRÔLE</span>
            <div className="rd-proof-grid">
              <div>
                <h2 className="rd-section-title">Construire un dossier que <em>l’on peut relire.</em></h2>
                <p className="rd-section-copy">Les pièces ne restent pas isolées. Elles sont reliées au contexte, aux décisions et à la chronologie pour garder une trace exploitable.</p>
                <div className="rd-proof-points"><span>✓ Captures et documents</span><span>✓ Sources et échanges</span><span>✓ Historique des décisions</span><span>✓ Journal d’audit</span></div>
              </div>
              <div className="rd-proof-card">
                <header><strong>DOSSIER · REV-88421</strong><span>TRAÇABILITÉ ACTIVE</span></header>
                <div className="rd-proof-row"><span>Capture datée · 24/09</span><b>Vérifiée</b></div>
                <div className="rd-proof-row"><span>Échange client · PDF</span><b>Vérifiée</b></div>
                <div className="rd-proof-row"><span>Source publique</span><b>À vérifier</b></div>
                <div className="rd-proof-row"><span>Chronologie</span><b>Complète</b></div>
                <div className="rd-proof-foot"><i>✓</i><span>Chaque pièce peut être associée à un dossier et à une décision.</span></div>
              </div>
            </div>
          </div>
        </section>

        <section id="tarifs" className="rd-cta">
          <span className="rd-section-kicker">DÉCOUVRIR REVIEW DEFENSE</span>
          <h2 className="rd-section-title">Commencez avec un seul avis.<br/><em>Voyez tout le parcours.</em></h2>
          <p>Créez votre espace et découvrez l’interface qui centralise analyse, preuves, dossiers et validations.</p>
          <Link className="rd-primary" to="/register">Créer mon espace <span>→</span></Link>
        </section>
      </main>

      <footer className="rd-footer">
        <span className="rd-footer-brand"><span className="rd-brand-mark">RD</span> Review Defense</span>
        <span>Analyse · Qualification · Preuves · Dossiers</span>
        <Link to="/login">Accéder au logiciel →</Link>
      </footer>
    </div>
  );
}
