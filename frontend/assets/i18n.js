(() => {
  const KEY='rd_locale';
  const SUPPORTED=['fr','en'];
  const isEnglish=()=>localStorage.getItem(KEY)==='en';
  const translations = {
    'Produit':'Product','Comment ça marche':'How it works','Services':'Services','Tarifs':'Pricing','Ressources':'Resources',
    'Connexion':'Log in','Déconnexion':'Log out','Analyser un avis':'Analyze a review','Voir comment ça marche':'See how it works',
    'Centre conformité':'Compliance center','Sécurité':'Security','Confidentialité':'Privacy','Conservation des données':'Data retention',
    'Sous-traitants':'Subprocessors','IA & contrôle humain':'AI & human oversight','Mentions légales':'Legal notice','CGV':'Terms of Sale','CGU':'Terms of Use','Cookies':'Cookies','Droits RGPD':'GDPR rights','Violations de données':'Data breaches',
    'Analyse active':'ACTIVE ANALYSIS','Workspace sécurisé':'SECURE WORKSPACE','Reputation intelligence · pour les entreprises':'REPUTATION INTELLIGENCE · FOR BUSINESSES',
    'Reprenez le contrôle de':'Take back control of','votre réputation.':'your reputation.',
    'Analysez vos avis Google et identifiez rapidement les éléments à vérifier.':'Analyze your Google reviews and quickly identify what needs to be verified.',
    'Review Defense vous aide à structurer les preuves et à préparer un dossier clair, avec une validation humaine à chaque étape.':'Review Defense helps you structure evidence and prepare a clear case file, with human approval at every step.',
    'Analyse structurée':'Structured analysis','Preuves documentées':'Documented evidence','Décisions humaines':'Human decisions',
    'L’INTERFACE':'THE INTERFACE','Une vue claire de':'A clear view of','votre dossier.':'your case file.',
    'Retrouvez rapidement les avis, les éléments à vérifier, les preuves et les validations en cours.':'Quickly find reviews, items to verify, evidence and pending approvals.',
    'Tableau de bord':'Dashboard','Mes avis':'My reviews','Analyse':'Analysis','Dossiers':'Cases','Preuves':'Evidence','Suivi':'Tracking','Rapports':'Reports',
    'Avis analysés':'Reviews analyzed','À vérifier':'To verify','Dossiers actifs':'Active cases','Approbations':'Approvals',
    'À TRAITER MAINTENANT':'TO HANDLE NOW','Votre prochaine action':'Your next action',
    'Le tableau de bord met en avant ce qui mérite votre attention avant le reste.':'The dashboard highlights what needs your attention first.',
    'Suivre les dossiers actifs':'Track active cases','Vérifier les validations':'Review approvals','Contrôler les preuves':'Check evidence',
    'PRODUIT':'PRODUCT','LES BRIQUES DU PRODUIT':'PRODUCT BUILDING BLOCKS','LE PARCOURS':'WORKFLOW','LA CONSOLE':'THE CONSOLE',
    'PREUVES & CONTEXTE':'EVIDENCE & CONTEXT','IA ASSISTÉE':'AI ASSISTANCE','SÉCURITÉ & GOUVERNANCE':'SECURITY & GOVERNANCE',
    'Une plateforme complète pour':'A complete platform to','comprendre, documenter et préparer.':'understand, document and prepare.',
    'Pas seulement une analyse.':'More than analysis.','Un véritable dossier de travail.':'A real working case file.',
    'Préparation ≠ exécution.':'Preparation ≠ execution.','Validation humaine':'Human approval','Traçabilité complète':'Full traceability',
    'De l’avis brut au':'From raw review to','dossier prêt à être validé.':'a case file ready for approval.',
    'Tout le nécessaire pour':'Everything you need to','structurer une défense.':'structure a defense.',
    'Une vue opérationnelle,':'An operational view,','pas un simple rapport.':'not just a report.',
    'Les preuves restent reliées au contexte.':'Evidence remains linked to context.',
    'Construire un dossier que':'Build a case file that','l’on peut réellement relire.':'can actually be reviewed.',
    'L’IA accélère le travail.':'AI accelerates the work.','Elle ne prend pas la décision.':'It does not make the decision.',
    'Le produit est pensé pour':'The product is designed for','les organisations.':'organizations.',
    'COMMENT ÇA MARCHE · WORKFLOW COMPLET':'HOW IT WORKS · COMPLETE WORKFLOW',
    'Un avis entre.':'A review goes in.','Un dossier structuré en sort.':'A structured case file comes out.',
    'LE PARCOURS EN 7 ÉTAPES':'THE 7-STEP WORKFLOW','Chaque étape a':'Every step has','un objectif précis.':'a specific objective.',
    'Collecter':'Collect','Analyser':'Analyze','Qualifier':'Qualify','Rassembler les preuves':'Gather evidence','Construire le dossier':'Build the case file','Décider et geler':'Decide and freeze','Approuver et préparer':'Approve and prepare',
    'Commencer une analyse':'Start an analysis','Découvrir le parcours':'Explore the workflow',
    'Décider avec des preuves. Soumettre avec contrôle humain.':'Decide with evidence. Submit with human control.',
    'Chaque dossier reste traçable, tenant-scoped et protégé par des étapes explicites.':'Every case remains traceable, tenant-scoped and protected by explicit controls.',
    'Ouvrir les dossiers':'Open cases','Voir les validations':'View approvals',
    'Qualification des avis':'Review qualification','Identifier rapidement les avis à examiner, sans déclencher d’action externe automatique.':'Quickly identify reviews to examine without triggering automatic external action.',
    'Inbox des avis':'Review inbox','Rechercher un avis':'Search reviews','Filtrer par note':'Filter by rating','Toutes les notes':'All ratings',
    '1 étoile':'1 star','2 étoiles':'2 stars','3 étoiles':'3 stars','4 étoiles':'4 stars','5 étoiles':'5 stars',
    'Rechercher auteur, texte, source ou identifiant…':'Search author, text, source or ID…',
    'Aucun avis disponible.':'No reviews available.','Les avis ingérés apparaîtront ici après synchronisation.':'Ingested reviews will appear here after synchronization.',
    'Centre des dossiers':'Case center','Transformer chaque signal en dossier traçable, avec priorité, état et prochaine action clairement visibles.':'Turn every signal into a traceable case with clear priority, status and next action.',
    'File des dossiers':'Case queue','Rechercher un dossier':'Search cases','Filtrer les dossiers':'Filter cases','Tous les statuts':'All statuses',
    'Ouverts':'Open','En revue':'In review','En attente':'Pending','Clôturés':'Closed','Aucun dossier pour le moment.':'No cases yet.',
    'Charge & délais':'Workload & deadlines','Attention SLA':'SLA attention','SLA sous contrôle':'SLA under control',
    'Charge par analyste':'Workload by analyst','Contrôle humain':'Human control',
    'Registre des preuves':'Evidence register','Conserver, vérifier et relier les éléments de preuve avec une intégrité cryptographique explicite.':'Store, verify and link evidence with explicit cryptographic integrity.',
    'Intégrité vérifiée':'Integrity verified','Vérification requise':'Verification required','Éléments':'Items','Vérifiées':'Verified','Rejetées':'Rejected',
    'Rechercher une preuve':'Search evidence','Rechercher ID, type, statut ou SHA-256…':'Search ID, type, status or SHA-256…',
    'Centre de validation':'Approval center','Chaque action sensible reste bloquée jusqu’à une validation humaine explicite et traçable.':'Every sensitive action remains blocked until explicit, traceable human approval.',
    'En attente':'Pending','Approuvées':'Approved','Refusées':'Rejected',
    'Préparation des soumissions':'Submission preparation','Préparer une action documentée après approbation, sans exécuter automatiquement d’action externe.':'Prepare a documented action after approval without automatically executing an external action.',
    'Alertes opérationnelles':'Operational alerts','Surveiller les notifications, les signaux critiques et leur état de traitement avec une traçabilité lisible.':'Monitor notifications, critical signals and processing status with clear traceability.',
    'Centre d’alertes':'Alert center','Rechercher une alerte':'Search alerts','Tous les niveaux':'All levels','Critiques':'Critical','Élevées':'High','Avertissements':'Warnings',
    'Journal d’audit':'Audit log','Lecture seule':'Read only',
    'Votre abonnement Review Defense':'Your Review Defense subscription','Gérer votre formule, votre tarif fidélité et vos achats ponctuels depuis un espace unique.':'Manage your plan, loyalty pricing and one-off purchases from one place.',
    'FORMULE ACTUELLE':'CURRENT PLAN','Actif':'Active','Changer de formule':'Change plan','Continuer vers PayPal':'Continue to PayPal',
    'ACHATS PONCTUELS':'ONE-OFF PURCHASES','Audit de réputation':'Reputation audit','Défense d’un avis':'Review defense','Packs de défense':'Defense packs','Choisir':'Choose','Démarrer':'Start','Voir les packs':'View packs',
    'Historique des paiements':'Payment history','En attente de connexion PayPal':'Awaiting PayPal connection',
    'Organisation':'Organization','Gérer les membres, les rôles, la sécurité et les demandes relatives aux données. Les contrôles d’accès sont appliqués côté serveur.':'Manage members, roles, security and data requests. Access controls are enforced server-side.',
    'Accès':'Access','Portabilité':'Portability','Demandes RGPD':'GDPR requests','Centre de confidentialité':'Privacy center',
    'Exporter mes données':'Export my data','Demander l’accès':'Request access','Demander une rectification':'Request rectification','Demander l’effacement':'Request erasure','Demander la limitation':'Request restriction','Exercer une opposition':'Object to processing','Demander la portabilité':'Request portability',
    'Membres & rôles':'Members & roles','Inviter un membre':'Invite a member','Aucun membre.':'No members.',
    'Changer le mot de passe':'Change password','Configurer MFA':'Set up MFA','Isolation organisationnelle':'Organization isolation',
    'Créer mon compte':'Create my account','Créer mon espace gratuitement':'Create my workspace for free','J’ai déjà un compte':'I already have an account',
    'Nom de l’entreprise':'Company name','Email professionnel':'Work email','Mot de passe':'Password','Confirmer le mot de passe':'Confirm password',
    'Mot de passe oublié ?':'Forgot password?','Créer un compte':'Create an account','J’ai une invitation':'I have an invitation',
    'Récupérer l’accès':'Recover access','Envoyer le lien':'Send link','Retour à la connexion':'Back to login',
    'Vérification de l’email':'Email verification','Validation du lien…':'Validating link…','Vérifier':'Verify',
    'Les deux mots de passe ne correspondent pas.':'Passwords do not match.','Votre compte a été créé. Vérifiez votre e-mail avant de vous connecter.':'Your account has been created. Check your email before logging in.',
    'Impossible de créer le compte.':'Unable to create the account.','Afficher le mot de passe':'Show password','Masquer le mot de passe':'Hide password',
    'Code MFA':'MFA code','Entrez le code de votre application d’authentification.':'Enter the code from your authenticator app.',
    'Dashboard':'Dashboard','Vue opérationnelle':'Operational view','Rechercher':'Search','Décider avec des preuves. Soumettre avec contrôle humain.':'Decide with evidence. Submit with human control.',
    'Dossier':'Case','Ce qu’il reste à faire':'What remains to be done','Relire et approuver la décision avant toute préparation externe.':'Review and approve the decision before any external preparation.',
    'Le dossier est prêt pour l’étape suivante autorisée.':'The case is ready for the next authorized step.','Compléter ou vérifier les éléments signalés avant de poursuivre.':'Complete or verify the flagged items before continuing.',
    'Validation humaine':'Human approval','Prêt':'Ready','À compléter':'Needs completion','VÉRIFIER':'VERIFY','PRÉPARER':'PREPARE'
  };
  const pairs=Object.entries(translations).sort((a,b)=>b[0].length-a[0].length);
  const protectedSelector='input,textarea,select,option,[data-i18n-ignore],script,style,code,pre,.review-text,blockquote';
  function translateNode(root){
    if(!isEnglish()) return;
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:n=>{
      if(!n.nodeValue.trim()||n.parentElement?.closest(protectedSelector)) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }});
    const nodes=[]; while(walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(n=>{
      let v=n.nodeValue;
      for(const [fr,en] of pairs) if(v.includes(fr)) v=v.split(fr).join(en);
      if(v!==n.nodeValue)n.nodeValue=v;
    });
  }
  function setMeta(){
    if(!isEnglish()) return;
    document.documentElement.lang='en';
    const titles={
      '/':'Review Defense | Reputation intelligence and defense',
      '/produit/':'Review Defense Product | Analysis, evidence and traceability',
      '/comment-ca-marche/':'How it works | Review Defense',
      '/services/':'B2B Services | Review Defense',
      '/tarifs/':'Pricing | Review Defense',
      '/ressources/':'Resources | Review Defense',
      '/contact/':'Contact | Review Defense'
    };
    const desc={
      '/':'Analyze, qualify and document Google reviews. Prepare traceable case files with human approval.',
      '/produit/':'Analysis, qualification, evidence, case files and traceability in a B2B workspace designed for teams.',
      '/comment-ca-marche/':'A clear workflow from review to analysis, evidence, case file, human decision and controlled preparation.',
      '/services/':'Structured support for analyzing, qualifying, documenting and managing online review situations.',
      '/tarifs/':'Review Defense plans for organizations and teams.',
      '/ressources/':'Practical guides about Google reviews, evidence, reporting and reputation management.',
      '/contact/':'Request a demo or contact the Review Defense team.'
    };
    document.title=titles[location.pathname]||document.title;
    const d=document.querySelector('meta[name="description"]'); if(d&&desc[location.pathname])d.content=desc[location.pathname];
  }
  function addSwitcher(){
    if(document.getElementById('rd-language-switcher')) return;
    const host=document.querySelector('.public-actions')||document.querySelector('header .header-actions')||document.querySelector('header');
    if(!host)return;
    const b=document.createElement('button'); b.id='rd-language-switcher'; b.type='button'; b.className='rd-language-switcher'; b.textContent=isEnglish()?'FR':'EN'; b.title=isEnglish()?'Passer en français':'Switch to English';
    b.onclick=()=>{localStorage.setItem(KEY,isEnglish()?'fr':'en');location.reload()};
    host.appendChild(b);
  }
  function run(){
    if(!isEnglish()){document.documentElement.lang='fr';return;}
    setMeta(); translateNode(document.body); addSwitcher();
  }
  window.ReviewDefenseI18n={setLanguage(l){if(SUPPORTED.includes(l)){localStorage.setItem(KEY,l);location.reload()}},getLanguage:()=>isEnglish()?'en':'fr',translate:translateNode};
  const observer=new MutationObserver(muts=>{if(!isEnglish())return; muts.forEach(m=>m.addedNodes.forEach(n=>{if(n.nodeType===1)translateNode(n)})); addSwitcher();});
  observer.observe(document.documentElement,{subtree:true,childList:true});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run,{once:true});else run();
})();
