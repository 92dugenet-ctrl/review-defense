const PUBLIC_ROUTES={home:'/',compliance:'/conformite/',features:'/produit/',how:'/comment-ca-marche/',services:'/services/',pricing:'/tarifs/',resources:'/ressources/',contact:'/contact/',legal:'/mentions-legales/',privacy:'/confidentialite/',cgv:'/cgv/',cgu:'/cgu/',cookies:'/cookies/',security:'/securite/',retention:'/conservation-donnees/',rights:'/droits-rgpd/',breach:'/violation-donnees/',subprocessors:'/sous-traitants/',ai:'/ia-et-controle-humain/'};
const PUBLIC_META={
 home:['Review Defense | Analyse et défense de votre réputation','Analysez, qualifiez et documentez vos avis Google. Préparez des dossiers traçables avec validation humaine.'],
 features:['Produit Review Defense | Analyse, preuves et traçabilité','Analyse, qualification, preuves, dossiers et traçabilité dans une console B2B conçue pour vos équipes.'],
 how:['Comment ça marche | Review Defense','Un workflow clair : avis, analyse, qualification, preuves, dossier, décision humaine et préparation contrôlée.'],
 services:['Services B2B | Review Defense','Accompagnement structuré pour analyser, qualifier, documenter et suivre les situations liées aux avis en ligne.'],
 pricing:['Tarifs | Review Defense','Découvrez les niveaux d’offre Review Defense et choisissez l’organisation adaptée à votre usage.'],
 resources:['Ressources | Review Defense','Guides pratiques sur les avis Google, les preuves, le signalement et la gestion de réputation.'],
 contact:['Contact | Review Defense','Demandez une démonstration ou contactez l’équipe Review Defense.'],
 legal:['Mentions légales | Review Defense','Informations légales relatives à Review Defense.'],privacy:['Politique de confidentialité | Review Defense','Comment Review Defense traite, protège et conserve les données personnelles.'],cgv:['CGV | Review Defense','Conditions générales de vente de la plateforme Review Defense.'],cgu:['CGU | Review Defense','Conditions générales d’utilisation de Review Defense.'],cookies:['Cookies | Review Defense','Politique relative aux cookies et traceurs de Review Defense.'],security:['Sécurité | Review Defense','Principes de sécurité et de protection des données de Review Defense.'],retention:['Conservation des données | Review Defense','Règles de conservation et de suppression des données Review Defense.'],rights:['Droits RGPD | Review Defense','Exercer vos droits sur vos données personnelles.'],breach:['Violation de données | Review Defense','Organisation de Review Defense en cas de violation de données.'],subprocessors:['Sous-traitants | Review Defense','Prestataires participant au traitement des données.'],compliance:['Centre conformité | Review Defense','Documents juridiques, RGPD, sécurité et contrôle humain de Review Defense.'],
 ai:['IA et contrôle humain | Review Defense','Utilisation de l’intelligence artificielle et contrôle humain dans Review Defense.']
};
function setPublicMeta(page){
 const m=PUBLIC_META[page]||PUBLIC_META.home;
 document.title=m[0];
 let d=document.querySelector('meta[name="description"]'); if(!d){d=document.createElement('meta');d.name='description';document.head.appendChild(d)} d.content=m[1];
 let c=document.querySelector('link[rel="canonical"]'); if(!c){c=document.createElement('link');c.rel='canonical';document.head.appendChild(c)} c.href=location.origin+(PUBLIC_ROUTES[page]||'/');
}
const PUBLIC_NAV_ITEMS=[
 ['features','Produit'],['how','Comment ça marche'],['services','Services'],['pricing','Tarifs'],['resources','Ressources']
];
const PUBLIC_FOOTER_GROUPS=[
 ['Produit',[['Fonctionnalités','/produit/'],['Comment ça marche','/comment-ca-marche/'],['Tarifs','/tarifs/']]],
 ['Ressources',[['Guides & SEO','/ressources/'],['Analyser un avis Google','/analyse-avis-google/'],['Contact','/contact/']]],
 ['Confiance',[['Centre conformité','/conformite/'],['Sécurité','/securite/'],['Confidentialité','/confidentialite/'],['Conservation des données','/conservation-donnees/'],['Sous-traitants','/sous-traitants/'],['IA & contrôle humain','/ia-et-controle-humain/']]],
 ['Juridique',[['Mentions légales','/mentions-legales/'],['CGV','/cgv/'],['CGU','/cgu/'],['Cookies','/cookies/'],['Droits RGPD','/droits-rgpd/'],['Violations de données','/violation-donnees/']]]
];
function publicHeader(active){
 return '<header class="public-header" data-public-shell="header"><div class="rd-nav-inner"><a class="public-brand" href="/"><b class="brand-mark">RD</b><span>Review Defense</span></a><nav class="public-nav" aria-label="Navigation principale">'+PUBLIC_NAV_ITEMS.map(x=>'<button class="'+(active===x[0]?'active':'')+'" data-public="'+x[0]+'">'+x[1]+'</button>').join('')+'</nav><div class="public-actions"><button class="btn-secondary" id="public-login">Connexion</button><button class="btn-primary" id="public-cta">Analyser un avis <span>→</span></button></div><button class="mobile-menu" id="mobile-menu" aria-label="Menu">☰</button></div></header>';
}
function publicFooter(){
 return '<footer class="public-footer" data-public-shell="footer"><div class="rd-footer-inner"><div class="footer-brand"><a class="public-brand" href="/"><b class="brand-mark">RD</b><span>Review Defense</span></a><p>Analyse, qualification et préparation de dossiers liés aux avis en ligne.</p><small>Préparation ≠ exécution. Les décisions externes restent sous contrôle humain.</small></div>'+PUBLIC_FOOTER_GROUPS.map(g=>'<div><b>'+g[0]+'</b>'+g[1].map(x=>'<a href="'+x[1]+'">'+x[0]+'</a>').join('')+'</div>').join('')+'</div><div class="footer-bottom"><span>© 2026 Review Defense</span><span>Plateforme d’aide et de préparation — aucune suppression garantie.</span></div></footer>';
}
function publicShell(active,body){
 return '<div class="marketing" data-public-shell="site"><div class="public-shell-header">'+publicHeader(active)+'</div><main>'+body+'</main><div class="public-shell-footer">'+publicFooter()+'</div></div>';
}
function ensurePublicStyles(){if(document.getElementById('public-styles'))return;const link=document.createElement('link');link.id='public-styles';link.rel='stylesheet';link.href='/assets/public.css?v=6501';document.head.appendChild(link)}
function productMockup(){
 return '<div class="rd-product-stage"><div class="rd-product-glow"></div><div class="rd-product-window"><div class="rd-window-top"><div class="window-dots"><i></i><i></i><i></i></div><b>Review Defense</b><span>Workspace</span></div><div class="rd-window-body"><aside><strong>RD</strong><span class="active">⌂ Tableau</span><span>◌ Mes avis</span><span>⌕ Analyse</span><span>□ Dossiers</span><span>◇ Preuves</span><span>✓ Suivi</span><span>◫ Rapports</span></aside><div class="rd-preview-main"><div class="preview-toolbar"><div><small>ANALYSE · DOSSIER REV-88421</small><h3>Avis Google à vérifier</h3></div><span class="rd-mini-badge">À VÉRIFIER</span></div><div class="preview-review"><div class="stars">★☆☆☆☆</div><b>« Service déplorable, une arnaque totale. »</b><span>Google · publié récemment · source vérifiée</span></div><div class="preview-kpis"><div><small>SIGNAUX</small><strong>03</strong><span>à examiner</span></div><div><small>PREUVES</small><strong>07</strong><span>associées</span></div><div><small>STATUT</small><strong>Gel</strong><span>validation requise</span></div></div><div class="preview-chain"><span class="done">01 Analyse</span><span class="done">02 Décision</span><span class="current">03 Gel</span><span>04 Approbation</span><span>05 Préparation</span></div><div class="preview-chart"><div class="chart-line"></div><div class="chart-labels"><span>Éléments factuels</span><span>Contradictions</span><span>Preuves</span></div></div></div></div></div><div class="rd-floating-card"><span>HUMAN APPROVAL</span><strong>Validation requise</strong><small>Avant toute étape contrôlée</small></div><div class="hero-signal-card"><span class="signal-dot"></span><div><small>SIGNAL DE DOSSIER</small><strong>03 éléments à vérifier</strong></div><b>LIVE</b></div></div>';
}
function homePage(){ /* hero-section */
 /* V6.40 commercial contract markers: HUMAN APPROVAL · La décision finale appartient toujours à la plateforme */
 return '<section class="rd-home-hero hero-section"><div class="mountain-wash"><div class="matterhorn-real" aria-hidden="true"><div class="matterhorn-photo"></div><div class="matterhorn-haze"></div><div class="matterhorn-glow"></div></div><div class="hero-orbit hero-orbit-a"></div><div class="hero-orbit hero-orbit-b"></div></div><div class="rd-container rd-hero-grid"><div class="rd-hero-copy"><div class="hero-status-line"><span class="status-pulse"></span><span>ANALYSE ACTIVE</span><i></i><span>WORKSPACE SÉCURISÉ</span></div><span class="rd-eyebrow-pill">REPUTATION INTELLIGENCE · POUR LES ENTREPRISES</span><h1>Reprenez le contrôle de<br><span>votre réputation.</span></h1><p class="rd-hero-lead">Analysez vos avis Google, puis utilisez Review Defense pour identifier les éléments à vérifier et constituer des dossiers solides. Une approche structurée, sécurisée et centrée sur la validation humaine. Gardez le contrôle sur chaque décision.</p><div class="rd-hero-actions"><button class="btn-primary rd-btn-lg" onclick="location.href=&quot;/analyse-avis-google/&quot;">Analyser un avis <span>→</span></button><button class="btn-secondary rd-btn-lg" onclick="showPublicPage(&quot;how&quot;)"><span class="play-dot">▶</span> Voir comment ça marche</button></div><div class="rd-trust-line"><span>✓ Analyse structurée</span><span>✓ Preuves documentées</span><span>✓ Décisions humaines</span></div><div class="hero-microcopy"><span>REVIEW DEFENSE · V6.40</span><span>Contrôle humain à chaque étape</span></div></div>'+productMockup()+'</div><div class="rd-container hero-confidence"><span>UNE PLATEFORME POUR STRUCTURER VOTRE DÉFENSE</span><b>Analyse</b><b>Qualification</b><b>Preuves</b><b>Traçabilité</b><b>Validation humaine</b></div></section><section class="rd-section problem-section"><div class="rd-container"><div class="rd-section-heading centered"><span class="rd-eyebrow">LE PROBLÈME</span><h2>Quand un avis devient un dossier,<br><span>l’information doit rester claire.</span></h2><p>Les avis contestés impliquent souvent des faits dispersés, des preuves difficiles à relier et des décisions qui doivent rester explicites.</p></div><div class="rd-value-grid"><article><span>01</span><h3>Qualifier</h3><p>Distinguer les éléments factuels, les affirmations et les points qui nécessitent une vérification.</p></article><article><span>02</span><h3>Documenter</h3><p>Rassembler les éléments utiles et relier les preuves aux affirmations qu’elles permettent d’examiner.</p></article><article><span>03</span><h3>Décider</h3><p>Conserver une décision humaine explicite avant toute préparation d’une démarche externe.</p></article></div></div></section><section class="rd-section console-section"><div class="rd-container"><div class="rd-section-heading"><span class="rd-eyebrow">UNE CONSOLE B2B</span><h2>Tout le dossier.<br><span>Au même endroit.</span></h2><p>Une interface conçue pour comprendre rapidement ce qui s’est passé, ce qui reste à vérifier et ce qui nécessite une validation.</p><button class="btn-secondary" onclick="showPublicPage(&quot;features&quot;)">Découvrir le produit →</button></div><div class="console-showcase"><div class="console-top"><b>Review Defense</b><span>Tableau de bord</span><span>Derniers dossiers</span><span class="console-avatar">RD</span></div><div class="console-content"><aside><b>TABLEAU DE BORD</b><span>Mes avis</span><span>Analyse</span><span>Dossiers</span><span>Preuves</span><span>Suivi</span></aside><div><div class="console-kpis"><div><small>Avis analysés</small><b>124</b><em>+12%</em></div><div><small>À vérifier</small><b>07</b><em>+5%</em></div><div><small>Dossiers actifs</small><b>18</b><em>+8%</em></div><div><small>Approbations</small><b>03</b><em>en attente</em></div></div><div class="console-panels"><div><small>ÉVOLUTION DES DOSSIERS</small><div class="fake-chart"><i></i><i></i><i></i><i></i><i></i><i></i></div></div><div><small>PROCHAINES ACTIONS</small><ul><li>Vérifier 3 éléments factuels</li><li>Préparer le dossier REV-88421</li><li>Attendre validation humaine</li></ul></div></div></div></div></div></section><section class="rd-section evidence-section"><div class="rd-container evidence-grid"><div class="evidence-visual"><div class="evidence-card"><small>EVIDENCE VAULT</small><h3>Preuves reliées au dossier</h3><div class="evidence-row"><span>Capture datée</span><b>Vérifiée</b></div><div class="evidence-row"><span>Échange client</span><b>À vérifier</b></div><div class="evidence-row"><span>Source publique</span><b>Vérifiée</b></div></div></div><div class="rd-section-heading"><span class="rd-eyebrow">PREUVES & TRAÇABILITÉ</span><h2>Chaque élément utile<br><span>reste relié au dossier.</span></h2><p>Conservez une chronologie lisible, les éléments factuels disponibles et l’historique des décisions. La plateforme aide à préparer ; elle ne décide pas à votre place.</p><div class="mini-points"><span>✓ Empreintes et intégrité</span><span>✓ Journal d’audit</span><span>✓ Validation explicite</span></div></div></div></section><section class="rd-section security-section"><!-- SERVICES · HUMAN CONTROL · Aucune suppression garantie · Structurez votre dossier avant toute démarche externe. --><div class="rd-container"><div class="rd-section-heading centered"><span class="rd-eyebrow">CONFIANCE</span><h2>La sécurité comme <span>cadre de travail.</span></h2><p>MFA, RBAC, isolation organisationnelle, journalisation et contrôle humain s’intègrent au parcours de travail.</p></div><div class="security-grid"><article><b>MFA</b><span>Accès renforcé</span></article><article><b>RBAC</b><span>Rôles contrôlés</span></article><article><b>AUDIT</b><span>Actions tracées</span></article><article><b>HUMAN GATE</b><span>Validation explicite</span></article></div></div></section><section class="rd-section pricing-teaser"><div class="rd-container rd-pricing-banner"><div><span class="rd-eyebrow">TARIFS</span><h2>Un niveau adapté<br><span>à votre organisation.</span></h2><p>Des offres présentées clairement, avec leurs limites et leur périmètre.</p></div><button class="btn-primary rd-btn-lg" onclick="showPublicPage(&quot;pricing&quot;)">Voir les tarifs →</button></div></section><section class="rd-final-cta"><div class="mountain-cta"></div><div class="rd-container"><span class="rd-eyebrow">PRÊT À COMMENCER&nbsp;?</span><h2>Commencez par un avis.<br><span>Construisez le dossier.</span></h2><p>Analysez une situation avant toute démarche externe et gardez le contrôle sur les décisions importantes.</p><button class="btn-primary rd-btn-lg" onclick="location.href=&quot;/analyse-avis-google/&quot;">Analyser un avis <span>→</span></button><small>Préparation ≠ exécution. La plateforme concernée conserve la décision finale.</small></div></section>';
}
function renderSignup(){location.assign('/app')}
function featuresPage(){return '<section class="page-hero"><div class="page-mountain"></div><span>UNE CONSOLE, UNE VISION</span><h1>Tout ce qu’il faut pour<br><span>défendre votre réputation.</span></h1><p>Analysez, qualifiez, documentez et préparez vos dossiers dans un espace B2B conçu pour garder chaque étape lisible.</p></section><section class="feature-grid premium-grid">'+[['◈','Analyse structurée','Centralisez les avis et identifiez les éléments qui méritent une vérification humaine.'],['⌁','Preuves & contradictions','Reliez les affirmations aux éléments disponibles et conservez leur intégrité.'],['✓','Workflow humain','Décision, gel, approbation puis préparation : chaque étape reste contrôlée.'],['◫','Dossiers & suivi','Suivez priorités, échéances, responsabilités et état des dossiers.'],['◎','Audit complet','Conservez la trace des décisions, validations et événements importants.'],['▣','Sécurité par conception','MFA, RBAC, isolation organisationnelle et contrôles de session.']].map(x=>'<article><i>'+x[0]+'</i><small>FEATURE</small><h3>'+x[1]+'</h3><p>'+x[2]+'</p></article>').join('')+'</section><section class="cta-band premium-cta"><h2>Une console claire pour des décisions documentées.</h2><p>Découvrez le parcours complet de l’analyse à la préparation contrôlée.</p><button class="btn-primary" onclick="showPublicPage(&quot;how&quot;)">Voir le workflow →</button></section>'}
function howPage(){return '<section class="page-hero"><div class="page-mountain"></div><span>UN PROCESSUS SIMPLE ET TRAÇABLE</span><h1>Du premier avis à la<br><span>préparation du dossier.</span></h1><p>Le travail suit une chaîne explicite. L’automatisation accélère la préparation ; la décision reste humaine.</p></section><section class="steps premium-steps">'+[['01','⌕','Analyse','Lire, structurer et identifier les éléments à examiner.'],['02','◫','Qualification','Distinguer faits, affirmations, signaux et points à vérifier.'],['03','□','Preuves','Rassembler les éléments disponibles et les relier aux affirmations.'],['04','♙','Dossier & décision','Documenter la décision et geler le dossier avant approbation.'],['05','↗','Préparation contrôlée','Préparer l’étape externe après validation explicite.']].map(x=>'<article><span>'+x[0]+'</span><i>'+x[1]+'</i><h3>'+x[2]+'</h3><p>'+x[3]+'</p></article>').join('')+'</section><section class="human-gate"><div><span class="rd-eyebrow">HUMAN GATE</span><h2>Préparation ≠ exécution.</h2><p>Aucune action Google externe sensible n’est exécutée automatiquement. La validation humaine reste une étape explicite du parcours.</p></div><button class="btn-primary" onclick="location.href=&quot;/analyse-avis-google/&quot;">Analyser un avis →</button></section>'}
function servicesPage(){return '<section class="page-hero"><div class="page-mountain"></div><span>SERVICES B2B</span><h1>Un accompagnement structuré pour<br><span>vos dossiers.</span></h1><p>Analyse, qualification, constitution des preuves et suivi : un cadre clair pour les équipes réputation, support, qualité et conformité.</p></section><section class="feature-grid premium-grid">'+[['◎','Analyse d’avis','Évaluer une situation et identifier les éléments qui nécessitent une vérification.'],['▣','Préparation de dossier','Organiser faits, preuves, chronologie et contexte avant toute démarche.'],['◫','Accompagnement','Suivre les étapes et conserver une traçabilité claire du dossier.'],['✓','Validation humaine','Aucune action sensible n’est exécutée sans validation explicite.'],['⌁','Suivi opérationnel','Centraliser responsabilités, statuts, échéances et événements.'],['◈','Transparence','Aucune suppression n’est garantie : la plateforme concernée conserve la décision finale.']].map(x=>'<article><i>'+x[0]+'</i><small>SERVICE</small><h3>'+x[1]+'</h3><p>'+x[2]+'</p></article>').join('')+'</section><section class="cta-band premium-cta"><h2>Vous avez une situation à structurer&nbsp;?</h2><p>Commencez par analyser l’avis et les éléments disponibles.</p><button class="btn-primary" onclick="location.href=&quot;/analyse-avis-google/&quot;">Analyser un avis →</button></section>'}
function selectPricingOffer(type,name,price,offerId){
 try{localStorage.setItem('rd_selected_offer',JSON.stringify({type,name,price,offer_id:offerId||null,selected_at:new Date().toISOString()}));}catch(e){}
 location.href='/app?pricing_offer='+encodeURIComponent(offerId||type);
}
function pricingPage(){
 const audits=[['1–9','79 €'],['10–49','149 €'],['50–99','249 €'],['100–249','399 €'],['250–499','599 €'],['500–999','899 €'],['1 000–2 499','1 290 €'],['2 500+','Sur devis']];
 const defense=[['01','Analyse initiale et qualification','Étude de l’avis et estimation du traitement.','49 €'],['02','Préparation du dossier','Collecte des éléments et rédaction.','+ 49 €'],['03','Première soumission','Préparation et envoi de la demande.','+ 59 €'],['04','Relance si nécessaire','Suivi et nouvelle soumission.','+ 49 €'],['05','Traitement avancé / escalade','Analyse complémentaire et dossier renforcé.','+ 69 €']];
 const packs=[['5 dossiers','490 €','98 €','starter'],['10 dossiers','990 €','99 €','plus'],['25 dossiers','1 990 €','80 €','pro'],['50 dossiers','3 490 €','70 €','business'],['100 dossiers','5 900 €','59 €','enterprise']];
 return '<section class="reference-pricing">'+
 '<div class="reference-pricing-head"><div><span class="reference-kicker">REVIEW DEFENSE</span><h1>Des solutions claires pour agir sur vos avis Google</h1><p>Audit, défense et accompagnement ponctuels. Aucun abonnement requis.</p></div><div class="reference-head-note"><strong>Des entreprises<br>mieux protégées<br>chaque jour</strong><span>↗</span></div></div>'+
 '<div class="reference-pricing-grid">'+
 '<article class="reference-panel audit-panel"><div class="reference-panel-title"><div class="reference-icon blue">⌕</div><div><h2>Audit de réputation</h2><p>Un diagnostic complet de vos avis Google.</p></div></div><ul class="reference-checks">'+['Analyse de la note et des tendances','Identification des avis problématiques','Thèmes récurrents et axes d’amélioration','Recommandations personnalisées','Rapport détaillé et priorisation'].map(x=>'<li><i>✓</i>'+x+'</li>').join('')+'</ul><div class="reference-table"><div class="reference-table-head"><span>Nombre d’avis</span><b>Prix</b></div>'+audits.map(x=>'<button type="button" class="reference-table-row" onclick="selectPricingOffer(\'audit\',\'Audit '+x[0]+' avis\',\''+x[1]+'\',\'audit_'+x[0].replace(/[^0-9]/g,'_')+'\')"><span>'+x[0]+'</span><b>'+x[1]+'</b></button>').join('')+'</div><button class="reference-panel-cta blue-cta" type="button" onclick="selectPricingOffer(\'audit\',\'Audit de réputation\',\'Selon volume\',\'audit\')">Demander un audit <span>→</span></button></article>'+
 '<article class="reference-panel defense-panel"><div class="reference-panel-title"><div class="reference-icon red">◇</div><div><h2>Défense d’un avis</h2><p>Un traitement professionnel<br>et progressif.</p></div></div><div class="reference-steps">'+defense.map(x=>'<button type="button" class="reference-step" onclick="selectPricingOffer(\'defense_step\',\''+x[1]+'\',\''+x[3].replace('+ ','')+'\',\'defense_'+x[0]+'\')"><b>'+x[0]+'</b><span><strong>'+x[1]+'</strong><small>'+x[2]+'</small></span><em>'+x[3]+'</em></button>').join('')+'</div><div class="reference-total"><span>Estimation totale par dossier</span><strong>De 49 € à 275 €</strong><p>Vous ne payez que les étapes nécessaires,<br>avec votre validation à chaque étape.</p></div><button class="reference-panel-cta red-cta" type="button" onclick="selectPricingOffer(\'defense_step\',\'Analyse initiale et qualification\',\'49 €\',\'defense_01\')">Démarrer un dossier <span>→</span></button></article>'+
 '<article class="reference-panel packs-panel"><div class="reference-panel-title"><div class="reference-icon green">□</div><div><h2>Packs de défense</h2><p>Des crédits pour traiter plusieurs avis,<br>à un tarif avantageux.</p></div></div><div class="reference-pack-table"><div class="reference-pack-head"><span>Pack</span><b>Prix du pack</b><em>Valeur indicative<br>par dossier</em></div>'+packs.map(x=>'<button type="button" class="reference-pack-row" onclick="selectPricingOffer(\'credit_pack\',\''+x[0]+'\',\''+x[1]+'\',\'pack_'+x[3]+'\')"><span>'+x[0]+'</span><b>'+x[1]+'</b><em>'+x[2]+'</em></button>').join('')+'</div><ul class="reference-checks green-checks"><li><i>✓</i>Utilisation flexible selon vos besoins</li><li><i>✓</i>Validité des crédits : 24 mois</li><li><i>✓</i>Suivi de tous vos dossiers dans votre espace</li></ul><div class="reference-pack-note"><span>◉</span><strong>Plus vous traitez de dossiers,<br>plus le coût unitaire diminue.</strong></div><button class="reference-panel-cta green-cta" type="button" onclick="selectPricingOffer(\'credit_pack\',\'Pack 5 dossiers\',\'490 €\',\'pack_starter\')">Choisir un pack <span>→</span></button></article>'+
 '</div>'+
 '<div class="reference-lower-grid"><section class="reference-journey"><div class="reference-lower-head"><div class="reference-lower-icon blue">◎</div><div><h3>Exemple de parcours</h3><p>Un processus transparent, du début à la fin.</p></div></div><div class="reference-journey-steps">'+[['Je sélectionne<br>un avis','Depuis mon espace<br>ou via l’audit','▤'],['J’ouvre le dossier<br>49 €','Analyse et qualification','⌕'],['Je valide<br>chaque étape','et ne paie que si besoin','✓'],['Suivi du dossier','et historique complet<br>dans mon espace','▥']].map((x,i)=>(i?'<span class="journey-arrow">→</span>':'')+'<button type="button" class="journey-card" onclick="'+(i===1?"selectPricingOffer('defense_step','Analyse initiale et qualification','49 €','defense_01')":"location.href='/app'")+'"><i>'+x[2]+'</i><strong>'+x[0]+'</strong><small>'+x[1]+'</small></button>').join('')+'</div></section><section class="reference-why"><div class="reference-lower-head"><div class="reference-lower-icon crown">♛</div><div><h3>Pourquoi choisir Review Defense ?</h3></div></div><ul><li>Une méthodologie professionnelle</li><li>Des prix transparents et sans surprise</li><li>Vous gardez le contrôle à chaque étape</li><li>Aucune promesse de suppression (Google reste décisionnaire)</li><li>Un suivi complet de tous vos dossiers</li></ul></section></div>'+
 '<div class="reference-bottom"><div class="reference-bottom-brand"><span>✓</span><div><strong>Protégez votre réputation, en toute confiance.</strong><small>Des outils sérieux, un accompagnement clair, des tarifs justes.</small></div></div><div class="reference-quote"><em>“Transformez un problème en opportunité de confiance.”</em><strong>REVIEW DEFENSE</strong></div><button class="reference-main-cta" type="button" onclick="selectPricingOffer(\'defense_step\',\'Analyse initiale et qualification\',\'49 €\',\'defense_01\')">Commencer maintenant <span>→</span></button></div>'+
 '<p class="reference-legal">Les crédits et prestations sont soumis aux conditions applicables. Chaque étape de défense nécessitant une démarche externe reste soumise à validation humaine explicite. Google conserve la décision finale concernant ses contenus.</p>'+
 '</section>';
}
function resourcesPage(){const cards=[['GUIDE','Comment supprimer un faux avis Google ?','/comment-supprimer-un-avis-google/'],['E-RÉPUTATION','Comment reconnaître un faux avis Google ?','/comment-reconnaitre-un-faux-avis-google/'],['DOSSIER','Comment prouver qu’un avis Google est faux ?','/comment-prouver-qu-un-avis-google-est-faux/'],['PROCÉDURE','Comment signaler un avis Google ?','/signaler-un-avis-google/'],['REFUS','Que faire quand Google refuse de supprimer un avis ?','/que-faire-quand-google-refuse-de-supprimer-un-avis/'],['PILIER','Analyse et qualification des avis Google','/analyse-avis-google/']];return '<section class="page-hero"><div class="page-mountain"></div><span>CONSEILS, GUIDES ET SEO</span><h1>Comprendre avant<br><span>d’agir.</span></h1><p>Un hub éditorial pour vérifier les faits, structurer les preuves et comprendre les procédures liées aux avis.</p></section><section class="article-grid premium-articles">'+cards.map((x,i)=>'<article><div class="article-image article-'+i+'"></div><small>'+x[0]+'</small><h3>'+x[1]+'</h3><p>Vérifications, éléments utiles et étapes à connaître avant d’agir.</p><a href="'+x[2]+'">Lire le guide <span>→</span></a></article>').join('')+'</section><section class="newsletter-band"><div><span class="rd-eyebrow">RESSOURCES</span><h2>Recevez les prochains guides.</h2><p>Un contenu utile, sans promesses artificielles.</p></div><a class="btn-primary" href="/contact/">Nous contacter →</a></section>'}
function legalPage(kind){
 const pages={
  legal:{k:'ÉDITEUR',title:'Mentions légales',intro:'Informations légales relatives au site et à la plateforme Review Defense.',sections:[
   ['Éditeur','Review Defense — société en cours d’immatriculation. Les mentions d’identification définitives de l’éditeur seront publiées avant la mise en ligne commerciale définitive.','Contact : contact@review-defense.com.'],
   ['Infrastructure','L’application sépare la couche applicative, les données structurées, les documents et les sauvegardes. Les fournisseurs techniques et leurs informations contractuelles sont documentés dans la page Sous-traitants.','Les paramètres d’hébergement, de localisation et de transfert sont vérifiés avant le lancement commercial.'],
   ['Objet','Review Defense fournit un environnement d’analyse, de qualification, de documentation, de suivi et de préparation de dossiers liés aux avis en ligne.','Le service ne garantit pas la suppression d’un avis. La plateforme concernée conserve sa décision finale.']
  ]},
  privacy:{k:'CONFIDENTIALITÉ',title:'Politique de confidentialité',intro:'Principes applicables aux données personnelles traitées par Review Defense.',sections:[
   ['Responsable du traitement','Le responsable du traitement sera l’entité exploitante de Review Defense, dont l’identité complète sera publiée avant le lancement commercial. Contact : contact@review-defense.com.',''],
   ['Données traitées','Selon l’usage : identité et coordonnées professionnelles, compte, organisation et rôle, avis et contenus transmis, pièces et preuves, métadonnées de dossiers, journaux de sécurité et d’audit, données de facturation et demandes d’assistance.',''],
   ['Finalités','Fournir le service, sécuriser les comptes, gérer les organisations et permissions, analyser et structurer les dossiers, assurer la traçabilité, le support, la prévention des abus et les obligations légales.',''],
   ['Architecture','eCloud Serve : application et accès. Supabase/PostgreSQL : données structurées. Cloudflare R2 : documents privés. Une destination séparée est prévue pour les sauvegardes.','Les localisations et mécanismes de transfert applicables sont vérifiés contractuellement avant lancement.'],
   ['Conservation','Les durées dépendent de la finalité, de la relation contractuelle, des obligations légales et des besoins de sécurité. Voir la Politique de conservation.',''],
   ['Droits','Vous pouvez demander l’accès, la rectification, l’effacement, la limitation, l’opposition lorsque le droit s’applique et la portabilité lorsque les conditions sont réunies.','Contact : contact@review-defense.com. Une réclamation peut être adressée à la CNIL.'],
   ['Sécurité','Mesures prévues : contrôle d’accès, MFA, RBAC, isolation organisationnelle, chiffrement approprié, stockage privé, journalisation, sauvegardes et gestion des incidents.','Aucune mesure ne garantit un risque nul.']
  ]},
  cgv:{k:'VENTE',title:'Conditions générales de vente',intro:'Cadre contractuel applicable aux offres commerciales Review Defense.',sections:[
   ['Périmètre','Les offres, tarifs, limites d’usage et services souscrits sont ceux présentés lors de la commande ou dans le document contractuel applicable.',''],
   ['Compte et utilisateurs','Le client fournit des informations exactes et protège ses moyens d’accès. Les utilisateurs sont responsables de leur usage dans le cadre des permissions attribuées.',''],
   ['Prix et paiement','Les prix, taxes, échéances et modalités de paiement sont ceux indiqués lors de la souscription. Les offres Enterprise peuvent faire l’objet d’un devis ou contrat spécifique.',''],
   ['Service','Review Defense met en œuvre des moyens raisonnables pour assurer la disponibilité et la sécurité. Des maintenances, incidents ou dépendances fournisseurs peuvent affecter temporairement le service.',''],
   ['Limites','Review Defense ne garantit ni la suppression d’un avis, ni l’acceptation d’un signalement, ni une décision favorable d’une plateforme tierce.','Aucune action externe sensible n’est exécutée automatiquement sans validation humaine explicite.'],
   ['Résiliation','Les modalités de durée, renouvellement et résiliation dépendent de l’offre souscrite et des conditions communiquées au client.'],
   ['Données','Le traitement des données personnelles est régi par la Politique de confidentialité et, lorsque nécessaire, par un accord de sous-traitance.'],
   ['Droit applicable','Les dispositions définitives relatives au droit applicable, à la juridiction compétente et aux éventuelles médiations seront finalisées avec les informations de l’entité exploitante avant le lancement commercial.']
  ]},
  cgu:{k:'UTILISATION',title:'Conditions générales d’utilisation',intro:'Règles d’utilisation de la plateforme Review Defense.',sections:[
   ['Accès','L’accès est réservé aux utilisateurs autorisés par leur organisation. Chaque utilisateur doit protéger ses identifiants et signaler toute compromission.'],
   ['Usage autorisé','La plateforme doit être utilisée conformément aux lois applicables, aux droits des tiers, aux règles des plateformes concernées et aux consignes de sécurité.'],
   ['Contenus','Le client reste responsable de disposer des droits et bases légales nécessaires pour transmettre avis, documents, preuves et autres contenus.'],
   ['Contrôle humain','Les éléments produits ou suggérés doivent être vérifiés. Une action externe sensible nécessite une validation humaine explicite.'],
   ['Interdictions','Sont notamment interdits les accès frauduleux, l’utilisation d’identifiants tiers, le contournement des contrôles et l’introduction volontaire de code malveillant.']
  ]},
  cookies:{k:'TRACEURS',title:'Politique cookies et traceurs',intro:'Principes applicables aux cookies et traceurs utilisés par Review Defense.',sections:[
   ['Traceurs nécessaires','Les traceurs strictement nécessaires au fonctionnement, à la session ou à la sécurité peuvent être utilisés lorsqu’ils sont indispensables au service.'],
   ['Traceurs non essentiels','Tout outil d’analyse, de publicité ou de mesure non strictement nécessaire doit être identifié et, lorsque requis, soumis au consentement préalable.'],
   ['Évolution','Si de nouveaux outils sont ajoutés, la présente politique et le mécanisme de consentement seront mis à jour lorsque nécessaire.'],
   ['Contact','Pour toute question : contact@review-defense.com.']
  ]},
  security:{k:'SÉCURITÉ',title:'Politique de sécurité',intro:'Principes de sécurité de l’architecture cible Review Defense.',sections:[
   ['Séparation','eCloud Serve porte la couche applicative et l’accès ; Supabase/PostgreSQL les données structurées ; Cloudflare R2 les documents privés ; une destination indépendante les sauvegardes.'],
   ['Accès','Authentification, MFA, rôles et permissions contrôlent les accès. L’API reste responsable des autorisations ; le frontend n’est jamais une barrière de sécurité suffisante.'],
   ['Multi-tenant','Les ressources sont rattachées à une organisation et les contrôles serveur vérifient appartenance, rôle et périmètre.'],
   ['Documents','Les documents sont stockés dans un espace privé. Le téléchargement est autorisé par le serveur et peut être limité par un accès temporaire.'],
   ['Audit','Les événements de sécurité, décisions, validations et actions sensibles sont journalisés pour permettre la traçabilité et l’investigation.'],
   ['Sauvegarde','Les sauvegardes sont séparées de l’environnement principal et font l’objet de contrôles de restauration. Les objectifs RPO/RTO sont définis avant lancement.'],
   ['Incidents','Les incidents suivent une procédure de détection, confinement, préservation des preuves, restauration et notification lorsque la réglementation l’exige.']
  ]},
  retention:{k:'DONNÉES',title:'Politique de conservation des données',intro:'Principes de conservation, archivage et suppression.',sections:[
   ['Comptes','Conservés pendant la relation contractuelle puis selon les nécessités légales, de sécurité et de gestion des litiges.'],
   ['Dossiers et preuves','Conservés pendant la période nécessaire au traitement du dossier et à la relation contractuelle, puis supprimés ou archivés selon les règles applicables.'],
   ['Journaux','Conservés pendant une durée proportionnée aux finalités de sécurité, traçabilité et preuve, avec accès restreint.'],
   ['Facturation','Les pièces nécessaires aux obligations comptables et fiscales sont conservées pendant les durées légales applicables.'],
   ['Sauvegardes','Les sauvegardes suivent une rétention distincte. Une donnée supprimée de l’environnement actif peut subsister temporairement dans une sauvegarde jusqu’à son expiration.']
  ]},
  rights:{k:'RGPD',title:'Exercer vos droits',intro:'Procédure pratique pour demander l’accès, la rectification, l’effacement ou la limitation.',sections:[
   ['1. Demande','Écrivez à contact@review-defense.com en précisant votre demande et, si nécessaire, l’organisation ou le compte concerné.'],
   ['2. Vérification','Des informations complémentaires peuvent être demandées lorsque cela est nécessaire pour éviter une divulgation à un tiers.'],
   ['3. Traitement','La demande est enregistrée, qualifiée et traitée dans les délais prévus par le RGPD. Les exceptions légales sont expliquées lorsqu’un droit ne peut pas être exercé intégralement.'],
   ['4. Réponse','La réponse est adressée par un moyen approprié. Lorsque plusieurs systèmes sont concernés, la recherche couvre l’application, les données structurées, les documents et les éléments pertinents de sauvegarde selon leur cycle de vie.'],
   ['Réclamation','Vous pouvez saisir la CNIL si vous estimez que vos droits ne sont pas respectés.']
  ]},
  breach:{k:'INCIDENTS',title:'Violation de données',intro:'Organisation de Review Defense en cas de violation ou suspicion de violation de données personnelles.',sections:[
   ['Détection','Les alertes, journaux, signalements utilisateurs et fournisseurs sont analysés pour identifier les incidents susceptibles d’affecter confidentialité, intégrité ou disponibilité.'],
   ['Confinement','Les accès ou flux concernés peuvent être limités, les preuves préservées et les secrets compromis révoqués ou renouvelés.'],
   ['Évaluation','L’incident est qualifié selon sa nature, son périmètre, les données concernées et le risque pour les personnes.'],
   ['Notification','Lorsque le RGPD l’exige, l’autorité compétente et les personnes concernées sont informées selon les délais et modalités applicables.'],
   ['Après incident','Les causes, mesures correctives et actions de prévention sont documentées.']
  ]},
  subprocessors:{k:'FOURNISSEURS',title:'Sous-traitants et transferts',intro:'Prestataires techniques utilisés ou prévus par l’architecture Review Defense.',sections:[
   ['eCloud Serve','Couche applicative, accès, authentification, sessions et services d’application. Les modalités exactes de localisation et de sous-traitance sont vérifiées contractuellement.'],
   ['Supabase','Base PostgreSQL destinée aux données structurées : organisations, utilisateurs, dossiers, avis, métadonnées et audit.'],
   ['Cloudflare R2','Stockage objet privé destiné aux documents, PDF, images et pièces jointes.'],
   ['Sauvegarde séparée','Destination indépendante pour les sauvegardes et la récupération. Le fournisseur définitif sera ajouté au registre avant lancement.'],
   ['Transferts','Toute localisation ou transfert hors EEE fait l’objet d’une vérification et d’un mécanisme juridique approprié lorsque requis.'],
   ['Mise à jour','La liste des sous-traitants est revue avant chaque changement significatif d’architecture ou de fournisseur.']
  ]},
  ai:{k:'IA',title:'IA et contrôle humain',intro:'Principes applicables à l’utilisation de fonctions d’intelligence artificielle dans Review Defense.',sections:[
   ['Rôle de l’IA','L’IA peut assister l’analyse, la qualification, la comparaison d’éléments ou la préparation de contenus. Elle ne remplace pas la décision humaine.'],
   ['Validation','Les éléments produits ou suggérés par l’IA doivent être vérifiés avant utilisation dans un dossier ou une démarche externe.'],
   ['Actions Google','Review Defense n’effectue pas automatiquement la suppression, le signalement ou la réponse à un avis Google. Toute action externe sensible reste soumise à une validation humaine explicite.'],
   ['Limites','Les utilisateurs doivent tenir compte des erreurs possibles et vérifier les informations importantes avant utilisation.'],
   ['Données','Les données transmises à des fonctions IA sont limitées au besoin du service et traitées selon les engagements contractuels et la Politique de confidentialité.']
  ]}
 };
 const p=pages[kind]||pages.legal;
 const cards=p.sections.map(s=>'<article><small>'+esc(s[0].toUpperCase())+'</small><h3>'+esc(s[0])+'</h3><p>'+esc(s[1])+'</p></article>').join('');
 return '<section class="page-hero"><div class="page-mountain"></div><span>'+esc(p.k)+'</span><h1>'+esc(p.title)+'</h1><p>'+esc(p.intro)+'</p></section><section class="feature-grid premium-grid legal-copy">'+cards+'</section><section class="human-gate"><div><span class="rd-eyebrow">CONTACT</span><h2>Une question sur ce document&nbsp;?</h2><p>Écrivez-nous à contact@review-defense.com. Les informations d’identification de l’éditeur seront complétées avant le lancement commercial définitif.</p></div><a class="btn-primary" href="mailto:contact@review-defense.com">Nous contacter →</a></section>';
}
function compliancePage(){
 const docs=[
  ['🔒','Confidentialité','Politique de confidentialité','privacy','Données personnelles, finalités, architecture, conservation, droits et sécurité.'],
  ['⚖️','Mentions légales','Informations légales','legal','Éditeur, infrastructure, objet du service et informations réglementaires.'],
  ['📄','CGU','Conditions générales d’utilisation','cgu','Règles d’accès, usages autorisés, contenus et contrôle humain.'],
  ['💼','CGV','Conditions générales de vente','cgv','Cadre commercial, prix, service, limites et résiliation.'],
  ['🍪','Cookies','Cookies et traceurs','cookies','Traceurs nécessaires, consentement et évolution des outils.'],
  ['🛡️','Sécurité','Politique de sécurité','security','Accès, MFA, RBAC, multi-tenant, documents, audit et incidents.'],
  ['🗄️','Conservation','Politique de conservation','retention','Comptes, dossiers, preuves, journaux, facturation et sauvegardes.'],
  ['👤','Droits RGPD','Exercer vos droits','rights','Accès, rectification, effacement, limitation, opposition et portabilité.'],
  ['🚨','Violations','Gestion des violations de données','breach','Détection, confinement, évaluation, notification et retour d’expérience.'],
  ['🔗','Sous-traitants','Sous-traitants et transferts','subprocessors','Prestataires techniques, stockage et vérification des transferts.'],
  ['🤖','IA','IA et contrôle humain','ai','Rôle de l’IA, vérification humaine et limites des fonctions assistées.']
 ];
 return '<section class="page-hero"><div class="page-mountain"></div><span>CONFIANCE · RGPD · JURIDIQUE</span><h1>Centre conformité<br><span>et documents.</span></h1><p>Retrouvez ici les documents de référence de Review Defense. Chaque carte ouvre directement le document correspondant.</p></section>'+
  '<section class="feature-grid premium-grid legal-hub-grid">'+docs.map(x=>'<button type="button" class="legal-hub-card" onclick="showPublicPage(&quot;'+x[3]+'&quot;)"><i>'+x[0]+'</i><small>'+x[1].toUpperCase()+'</small><h3>'+x[2]+'</h3><p>'+x[4]+'</p><span>Ouvrir le document →</span></button>').join('')+'</section>'+
  '<section class="human-gate"><div><span class="rd-eyebrow">PARCOURS RGPD</span><h2>Une demande concernant vos données&nbsp;?</h2><p>Le centre RGPD permet de comprendre vos droits. Les demandes de compte peuvent aussi être enregistrées depuis l’espace client.</p></div><button class="btn-primary" onclick="showPublicPage(&quot;rights&quot;)">Voir mes droits RGPD →</button></section>';
}

function contactPage(){return '<section class="contact-layout premium-contact"><div class="page-mountain"></div><div><span>BESOIN D’AIDE ?</span><h1>Une question ?<br><span>Une démonstration ?</span></h1><p>Présentez-nous votre besoin. L’équipe peut vous aider à comprendre le parcours et le périmètre de Review Defense.</p><div class="contact-points"><span>✉ contact@review-defense.com</span><span>⌕ France</span><span>◷ Réponse selon disponibilité de l’équipe</span></div></div><form class="contact-form" onsubmit="event.preventDefault();toast(&quot;Votre message a bien été préparé.&quot;,&quot;success&quot;);this.reset()"><h3>Parlons de votre besoin</h3><label>Nom complet<input required></label><label>E-mail<input type="email" required></label><label>Entreprise<input></label><label>Message<textarea rows="5" required></textarea></label><button class="btn-primary">Envoyer le message</button></form></section>'}
function marketingLayout(active,body){ensurePublicStyles();setPublicMeta(active||'home');document.body.innerHTML=publicShell(active,body);document.querySelectorAll('[data-public]').forEach(x=>x.onclick=()=>showPublicPage(x.dataset.public));document.getElementById('public-login').onclick=()=>location.href='/app';document.getElementById('public-cta').onclick=()=>location.href='/analyse-avis-google/';initPremiumInteractions();document.getElementById('mobile-menu')?.addEventListener('click',()=>document.querySelector('.public-nav')?.classList.toggle('open'))}
function showPublicPage(page,push=true){if(page==='accept-invitation'){invitationSignupPage();return}const p={home:['',homePage()],compliance:['compliance',compliancePage()],features:['features',featuresPage()],how:['how',howPage()],services:['services',servicesPage()],pricing:['pricing',pricingPage()],resources:['resources',resourcesPage()],contact:['contact',contactPage()],legal:['legal',legalPage('legal')],privacy:['privacy',legalPage('privacy')],cgv:['cgv',legalPage('cgv')],cgu:['cgu',legalPage('cgu')],cookies:['cookies',legalPage('cookies')],security:['security',legalPage('security')],retention:['retention',legalPage('retention')],rights:['rights',legalPage('rights')],breach:['breach',legalPage('breach')],subprocessors:['subprocessors',legalPage('subprocessors')],ai:['ai',legalPage('ai')]};const x=p[page]||p.home;if(push&&PUBLIC_ROUTES[page]&&location.pathname!==PUBLIC_ROUTES[page])history.pushState({publicPage:page},'',PUBLIC_ROUTES[page]);marketingLayout(x[0],x[1])}
window.addEventListener('popstate',()=>{const page=Object.keys(PUBLIC_ROUTES).find(k=>PUBLIC_ROUTES[k]===location.pathname)||'home';showPublicPage(page,false)});
function invitationSignupPage(){
 ensurePublicStyles();
 const p=new URLSearchParams(location.search);
 const token=p.get('token')||p.get('invitation_token')||'';
 const org=p.get('organization_id')||'';
 const email=p.get('email')||'';
 document.body.innerHTML='<main class="auth-page"><div class="auth-card"><div class="brand large">REVIEW<span>DEFENSE</span></div><div class="auth-shell-premium"><div class="auth-brand-lockup"><span class="auth-mark">RD</span><div><strong>REVIEW DEFENSE</strong><small>Activation de votre compte</small></div></div><div class="auth-trust-row"><span>Compte sécurisé</span><span>Accès organisationnel</span><span>MFA disponible</span></div><form id="invitation-signup" class="stack auth-form"><div><div class="eyebrow">ACCOUNT ACTIVATION</div><h1>Créer mon compte</h1><p>Activez votre accès à Review Defense à partir de l’invitation reçue de votre organisation.</p></div><label>Organisation<input name="organization_id" autocomplete="organization" required value="'+esc(org)+'"></label><label>Email professionnel<input name="email" type="email" autocomplete="email" required value="'+esc(email)+'"></label><label>Code d’invitation<input name="invitation_token" autocomplete="one-time-code" required value="'+esc(token)+'"></label><label>Mot de passe<input name="password" type="password" autocomplete="new-password" minlength="12" required></label><label>Confirmer le mot de passe<input name="password_confirmation" type="password" autocomplete="new-password" minlength="12" required></label><button class="btn-primary auth-submit" type="submit">Activer mon compte</button><div id="signup-error" class="error"></div><button type="button" class="link-btn" id="signup-login">J’ai déjà un compte</button></form><div class="auth-boundary"><strong>Accès client</strong><span>Votre rôle et vos permissions sont définis par l’organisation qui vous invite. Les actions sensibles restent soumises aux contrôles humains.</span></div></div></div></main>';
 document.getElementById('invitation-signup').onsubmit=async e=>{
   e.preventDefault();
   const f=new FormData(e.currentTarget);
   const password=String(f.get('password')||''), confirmation=String(f.get('password_confirmation')||'');
   const err=document.getElementById('signup-error');
   if(password!==confirmation){err.textContent='Les deux mots de passe ne correspondent pas.';return}
   try{
     const d=await api('/v1/organization/invitations/accept',{method:'POST',body:JSON.stringify({
       organization_id:String(f.get('organization_id')),email:String(f.get('email')),invitation_token:String(f.get('invitation_token')),password
     })});
     if(d.access_token){localStorage.setItem('rd_token',d.access_token);location.href='/app';return}
     document.querySelector('.auth-form').innerHTML='<div class="eyebrow">EMAIL VERIFICATION</div><h1>Vérifiez votre e-mail</h1><p>Votre compte a été créé. Consultez votre boîte mail pour confirmer votre adresse avant de vous connecter.</p><button type="button" class="btn-primary" id="go-login">Retour à la connexion</button>';
     document.getElementById('go-login').onclick=()=>renderLogin();
   }catch(x){err.textContent=x.message||'Impossible d’activer le compte.'}
 };
 document.getElementById('signup-login').onclick=()=>renderLogin();
}

window.addEventListener('popstate',()=>{const page=Object.keys(PUBLIC_ROUTES).find(k=>PUBLIC_ROUTES[k]===location.pathname)||'home';showPublicPage(page,false)});

function initPremiumInteractions(){
  const root=document.querySelector('.marketing');
  if(!root || root.dataset.premiumReady==='1') return;
  root.dataset.premiumReady='1';
  const reduce=window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  root.querySelectorAll('.rd-workflow-visual article').forEach((card,index)=>{
    card.setAttribute('tabindex','0');
    card.setAttribute('role','button');
    card.dataset.step=String(index+1);
    const activate=()=>{
      root.querySelectorAll('.rd-workflow-visual article').forEach(x=>x.classList.remove('is-selected'));
      card.classList.add('is-selected');
    };
    card.addEventListener('click',activate);
    card.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate();}});
  });
  root.querySelectorAll('.rd-value-grid article,.security-grid article,.resource-cards a,.feature-grid article,.article-grid article').forEach(card=>{
    card.addEventListener('click',()=>card.classList.toggle('is-selected'));
  });
  root.querySelectorAll('.btn-primary,.btn-secondary').forEach(btn=>{
    btn.addEventListener('pointerdown',()=>btn.classList.add('is-pressed'));
    btn.addEventListener('pointerup',()=>btn.classList.remove('is-pressed'));
    btn.addEventListener('pointercancel',()=>btn.classList.remove('is-pressed'));
    btn.addEventListener('pointerleave',()=>btn.classList.remove('is-pressed'));
  });
  if(!reduce){
    root.querySelectorAll('.rd-product-window,.evidence-card,.console-showcase').forEach(card=>{
      card.addEventListener('pointermove',e=>{
        if(e.pointerType!=='mouse') return;
        const r=card.getBoundingClientRect();
        const x=(e.clientX-r.left)/r.width-.5;
        const y=(e.clientY-r.top)/r.height-.5;
        card.style.setProperty('--rx',(-y*2.2).toFixed(2)+'deg');
        card.style.setProperty('--ry',(x*2.2).toFixed(2)+'deg');
      });
      card.addEventListener('pointerleave',()=>{card.style.setProperty('--rx','0deg');card.style.setProperty('--ry','0deg');});
    });
    const hero=root.querySelector('.rd-home-hero');
    const mountain=root.querySelector('.matterhorn-real');
    if(hero && mountain){
      hero.addEventListener('pointermove',e=>{
        if(e.pointerType!=='mouse') return;
        const r=hero.getBoundingClientRect();
        const x=(e.clientX-r.left)/r.width-.5;
        const y=(e.clientY-r.top)/r.height-.5;
        mountain.style.setProperty('--mx',(x*18).toFixed(2)+'px');
        mountain.style.setProperty('--my',(y*10).toFixed(2)+'px');
      });
      hero.addEventListener('pointerleave',()=>{mountain.style.setProperty('--mx','0px');mountain.style.setProperty('--my','0px');});
      let ticking=false;
      const parallax=()=>{
        const y=Math.min(window.scrollY,900);
        mountain.style.setProperty('--scroll-y',(y*.08).toFixed(2)+'px');
        ticking=false;
      };
      window.addEventListener('scroll',()=>{if(!ticking){requestAnimationFrame(parallax);ticking=true;}},{passive:true});
      parallax();
    }
    root.querySelectorAll('.rd-section,.rd-final-cta').forEach(section=>{
      const obs=new IntersectionObserver(entries=>entries.forEach(entry=>{
        if(entry.isIntersecting){entry.target.classList.add('is-visible');obs.unobserve(entry.target);}
      }),{threshold:.08});
      obs.observe(section);
    });
  } else {
    root.querySelectorAll('.rd-section,.rd-final-cta').forEach(x=>x.classList.add('is-visible'));
  }
}
