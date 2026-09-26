(() => {
  const KEY='rd_locale';
  const SUPPORTED=['fr','en'];
  const requested=new URLSearchParams(location.search).get('lang');
  if(SUPPORTED.includes(requested)) localStorage.setItem(KEY,requested);
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

  const shouldTranslate=()=>true;

  const extraTranslations={
"Le contenu éditorial met trop de temps à répondre.":"The editorial content is taking too long to respond.","Impossible de charger les ressources éditoriales.":"Unable to load editorial resources.","Réessayer":"Retry","Plateforme d’aide et de préparation — aucune suppression garantie.":"Assistance and preparation platform — no deletion is guaranteed.","Centralisez vos avis Google et transformez chaque situation en éléments lisibles : contenu, contexte, signaux, contradictions et points à vérifier.":"Centralize your Google reviews and turn each situation into clear, structured elements: content, context, signals, contradictions and points to verify.","Qualification assistée":"Assisted qualification","L’IA aide à distinguer les affirmations, les éléments factuels et les zones d’incertitude. L’utilisateur conserve la maîtrise de la qualification finale.":"AI helps distinguish claims, factual elements and areas of uncertainty. The user retains control of the final qualification.","Dossier de défense":"Defense case file","Regroupez chronologie, captures, échanges, sources publiques et autres pièces utiles dans un dossier structuré et traçable.":"Bring timelines, screenshots, exchanges, public sources and other useful evidence together in a structured, traceable case file.","La décision est explicite. Le dossier peut être gelé, relu et approuvé avant toute préparation d’une démarche externe.":"The decision is explicit. The case file can be frozen, reviewed and approved before any external action is prepared.","Suivi opérationnel":"Operational tracking","Retrouvez les dossiers ouverts, les éléments en attente, les validations demandées et les prochaines étapes depuis une même console.":"Find open cases, pending items, requested approvals and next steps from a single workspace.","Les décisions, validations et événements importants restent documentés afin de comprendre qui a fait quoi, quand et pourquoi.":"Decisions, approvals and important events remain documented so you can understand who did what, when and why.","Collecte":"Collection","L’avis et les informations disponibles sont rassemblés.":"The review and available information are collected.","Les signaux, affirmations et éléments à examiner sont structurés.":"Signals, claims and items to examine are structured.","Les pièces utiles sont reliées aux éléments concernés.":"Useful evidence is linked to the relevant items.","L’équipe documente la décision et peut geler le dossier.":"The team documents the decision and can freeze the case file.","Une validation humaine explicite autorise la préparation.":"Explicit human approval authorizes preparation.","Importez ou sélectionnez l’avis à examiner. Review Defense rassemble le contenu disponible, sa source, son contexte et les informations utiles au dossier.":"Import or select the review to examine. Review Defense gathers the available content, source, context and information relevant to the case file.","L’avis est découpé en éléments exploitables : affirmations, faits allégués, signaux, incohérences, contexte et points nécessitant une vérification.":"The review is broken down into actionable elements: claims, alleged facts, signals, inconsistencies, context and points requiring verification.","Chaque élément peut être qualifié et annoté. L’assistance IA accélère le tri et le rapprochement, mais la qualification finale reste sous contrôle de l’équipe.":"Each item can be qualified and annotated. AI assistance speeds up sorting and comparison, while final qualification remains under team control.","Ajoutez captures, échanges, documents, sources publiques et autres pièces pertinentes. Chaque preuve peut être reliée à l’élément qu’elle vient soutenir ou contredire.":"Add screenshots, exchanges, documents, public sources and other relevant evidence. Each item can be linked to the claim it supports or contradicts.","La chronologie, les faits, les preuves, les qualifications et les décisions sont réunis dans un dossier unique, lisible et traçable.":"The timeline, facts, evidence, qualifications and decisions are brought together in one readable, traceable case file.","L’équipe relit les éléments, formalise sa décision puis peut geler le dossier. Le gel crée un point de référence avant toute étape sensible.":"The team reviews the elements, records its decision and can then freeze the case file. Freezing creates a reference point before any sensitive step.","Une personne habilitée valide explicitement la suite. Review Defense prépare alors l’étape autorisée, sans exécuter automatiquement une action sensible sur Google.":"An authorized person explicitly approves the next step. Review Defense then prepares the authorized step without automatically executing a sensitive action on Google.","Comprendre ce qui est réellement écrit et séparer les faits des affirmations.":"Understand what is actually written and separate facts from claims.","Identifier les éléments qui méritent une vérification ou une preuve complémentaire.":"Identify items that require verification or additional evidence.","Relier chaque pièce au bon élément plutôt que conserver un dossier documentaire dispersé.":"Link every piece of evidence to the correct item instead of maintaining a fragmented document collection.","Conserver le contexte et l’ordre des événements pour rendre le dossier compréhensible.":"Preserve context and event order so the case file remains understandable.","Documenter qui a décidé, qui a approuvé et à quel moment.":"Document who decided, who approved and when.","Conserver les événements importants pour pouvoir reconstruire le raisonnement du dossier.":"Preserve important events so the case reasoning can be reconstructed.","Analyse le contexte, complète les informations et organise les preuves.":"Analyze context, complete information and organize evidence.","Relit le dossier et prend les décisions qui nécessitent une autorité humaine.":"Reviews the case file and makes decisions that require human authority.","Définit les rôles, permissions et règles internes applicables au traitement.":"Defines roles, permissions and internal rules applicable to the process.","Audit de réputation":"Reputation audit","Obtenir une photographie structurée de votre présence Google : volume d’avis, tendances, signaux récurrents et situations qui méritent une analyse.":"Get a structured view of your Google presence: review volume, trends, recurring signals and situations that deserve analysis.","Analyse d’avis":"Review analysis","Étudier un avis précis, son contexte et ses affirmations pour distinguer les éléments factuels des points qui nécessitent une vérification.":"Examine a specific review, its context and claims to distinguish factual elements from points requiring verification.","Réunir chronologie, captures, échanges, documents et sources dans un dossier organisé autour des éléments à démontrer.":"Bring timelines, screenshots, exchanges, documents and sources together in a case file organized around the points to establish.","Validation & décision":"Approval & decision","Faire relire le dossier, formaliser la décision et conserver une trace claire de l’approbation avant toute démarche externe.":"Have the case file reviewed, record the decision and keep a clear approval trail before any external action.","Piloter les dossiers ouverts, les étapes en attente, les responsabilités et les événements depuis un même espace.":"Manage open cases, pending steps, responsibilities and events from a single workspace.","Préparation contrôlée":"Controlled preparation","Préparer une démarche externe à partir d’un dossier validé, sans automatiser l’action sensible elle-même.":"Prepare an external process from an approved case file without automating the sensitive action itself.","Équipes réputation":"Reputation teams","Centralisez les situations sensibles et disposez d’un historique exploitable pour chaque avis.":"Centralize sensitive situations and maintain an actionable history for every review.","Reliez les échanges et les éléments de contexte aux dossiers qui nécessitent une analyse approfondie.":"Link exchanges and contextual information to cases requiring deeper analysis.","Qualité & conformité":"Quality & compliance","Structurez les preuves, les décisions et les validations avec une traçabilité adaptée aux processus internes.":"Structure evidence, decisions and approvals with traceability suited to internal processes.","Étude de l’avis et estimation du traitement.":"Review assessment and treatment estimate.","Préparation du dossier":"Case file preparation","Collecte des éléments et rédaction.":"Evidence collection and drafting.","Première soumission":"Initial submission","Préparation et envoi de la demande.":"Request preparation and submission.","Relance si nécessaire":"Follow-up if needed","Traitement avancé / escalade":"Advanced handling / escalation","Analyse complémentaire et dossier renforcé.":"Additional analysis and strengthened case file.","Identification des avis problématiques":"Identification of problematic reviews","Thèmes récurrents et axes d’amélioration":"Recurring themes and improvement areas","Recommandations personnalisées":"Personalized recommendations","Rapport détaillé et priorisation":"Detailed report and prioritization","Je sélectionne":"I select","un avis":"a review","Depuis mon espace<br>ou via l’audit":"From my workspace<br>or through the audit","J’ouvre le dossier":"I open the case file","Je valide":"I approve","chaque étape":"each step","Réponse directe, méthode de vérification, éléments à conserver, démarches possibles et conduite à tenir en cas de refus.":"Direct response, verification method, items to preserve, possible actions and what to do if the request is refused.","Lire l’article complet":"Read the full article","IA et contrôle humain":"AI & human oversight","Rôle de l’IA":"Role of AI","Vérification humaine":"Human verification","Ressources":"Resources","Contact":"Contact","Services":"Services","Tarifs":"Pricing"
  };
  const commonTranslations={
    'Fonctionnalités':'Features','Produit':'Product','Comment ça marche':'How it works','Sécurité':'Security','Contact':'Contact',
    'La décision finale appartient toujours à la plateforme':'The platform always makes the final decision.',
    'Structurez votre dossier avant toute démarche externe.':'Structure your case file before taking any external action.',
    'Réessayer':'Retry','Vue générale':'Overview','Décision':'Decision','Préparation':'Preparation','Traçabilité':'Traceability',
    'Analyse':'Analysis','Qualification':'Qualification','Preuves':'Evidence','Audits':'Audits','Dossiers':'Cases','Validations':'Approvals',
    'Avis Google à vérifier':'Google review to verify','À VÉRIFIER':'TO VERIFY','Éléments factuels':'Factual elements','Contradictions':'Contradictions',
    'Éléments à vérifier':'Items to verify','À vérifier':'To verify','Vérifiée':'Verified','Vérifiées':'Verified','Complète':'Complete',
    'Validation requise':'Approval required','Avant toute étape contrôlée':'Before any controlled step','03 éléments à vérifier':'03 items to verify',
    'Reprenez le contrôle de':'Take back control of','votre réputation.':'your reputation.','Voir comment ça marche':'See how it works',
    'Analyse structurée':'Structured analysis','Preuves documentées':'Documented evidence','Décisions humaines':'Human decisions',
    'Aide à l’analyse':'Analysis assistance','Preuves reliées':'Linked evidence','Dossiers traçables':'Traceable case files',
    'ÉVOLUTION DES DOSSIERS':'CASE PROGRESS','À vérifier par l’équipe':'To be reviewed by the team','Décision verrouillée':'Decision locked',
    'Préparation ≠ exécution.':'Preparation ≠ execution.','Chaque étape sensible reste sous le contrôle explicite de l’utilisateur habilité.':'Every sensitive step remains under the explicit control of an authorized user.',
    'Chaque pièce peut être associée à un dossier et à une décision.':'Each item can be linked to a case file and a decision.',
    'Intégrité & traçabilité':'Integrity & traceability','Découvrir le parcours':'Explore the workflow',
    'Démarrer →':'Start →','Parler à l’équipe →':'Talk to the team →','Voir comment ça marche →':'See how it works →',
    'Des solutions claires pour agir sur vos avis Google':'Clear solutions for managing your Google reviews',
    'Audit, défense et accompagnement ponctuels. Aucun abonnement requis.':'One-off audits, review defense and support. No subscription required.',
    'Audit de réputation':'Reputation audit','Un diagnostic complet de vos avis Google.':'A complete assessment of your Google reviews.',
    'Défense d’un avis':'Review defense','Un traitement professionnel':'Professional handling','et progressif.':'and a structured process.',
    'Démarrer un dossier':'Start a case','Packs de défense':'Defense packs','Des crédits pour traiter plusieurs avis,':'Credits for handling multiple reviews,',
    'à un tarif avantageux.':'at an advantageous rate.','Plus vous traitez de dossiers,':'The more cases you handle,','plus le coût unitaire diminue.':'the lower the unit cost.',
    'Exemple de parcours':'Workflow example','Un processus transparent, du début à la fin.':'A transparent process from start to finish.',
    'Le prix':'The price','baisse avec':'decreases with','l’ancienneté':'loyalty','/ mois au départ':'/ month initially',
    'Plancher fidélité : 37 € / mois':'Loyalty floor: €37 / month','Plancher fidélité : 69 € / mois':'Loyalty floor: €69 / month',
    'Plancher fidélité : 119 € / mois':'Loyalty floor: €119 / month','Année 2':'Year 2','Année 3+':'Year 3+',
    'Surveillance avancée + création de réponses.':'Advanced monitoring + response drafting.',
    'Surveillance avancée + réponses + besoins plus importants / multi-sites.':'Advanced monitoring + responses + larger or multi-site needs.',
    'guide pratique Review Defense pour vérifier les faits, structurer les preuves et préparer la suite.':'Review Defense practical guide to verify facts, structure evidence and prepare next steps.',
    'Plateforme d’aide et de préparation — aucune suppression garantie.':'Assistance and preparation platform — no deletion is guaranteed.',
    'Client vérifié':'Verified customer','Service déplorable, commande jamais reçue et aucune réponse du restaurant.':'Terrible service, order never received and no response from the restaurant.',
    'Expérience très décevante.':'Very disappointing experience.','Le produit ne correspondait pas à la description.':'The product did not match the description.',
    'Commande non reçue':'Order not received','Signal à vérifier avant toute action externe.':'Signal to verify before any external action.',
    'Vérifier la preuve de livraison':'Verify delivery evidence','Dossier documenté, contradiction à confirmer humainement.':'Documented case file, contradiction requiring human confirmation.',
    'Une contradiction nécessite encore une validation humaine.':'A contradiction still requires human approval.',
    'Console opérationnelle · actions externes toujours soumises à approbation humaine.':'Operational console · external actions always require human approval.',
    'Création de votre espace':'Creating your workspace','Inscription sécurisée':'Secure sign-up','Votre organisation':'Your organization','MFA disponible':'MFA available',
    'Créer mon espace gratuitement':'Create my workspace for free','J’ai déjà un compte':'I already have an account','Contrôle humain & serveur':'Human & server controls',
    'Aucune action Google externe n':'No external Google action is','Récupération sécurisée':'Secure recovery','Récupérer l’accès':'Recover access',
    'Jeton à usage contrôlé':'Controlled-use token','Le lien de récupération est limité dans le temps et à usage unique.':'The recovery link is time-limited and single-use.',
    'Si les informations sont valides, un email de récupération a été envoyé.':'If the information is valid, a recovery email has been sent.',
    'Mot de passe modifié. Vous pouvez maintenant vous connecter.':'Password changed. You can now log in.',
    'Vérification de l’email':'Email verification','Vérifier':'Verify',
    'Ce qui nécessite votre attention maintenant':'What needs your attention now','Examiner les avis et qualifier ceux qui nécessitent un dossier':'Review incoming reviews and qualify those requiring a case file',
    'Surveiller la capacité, les échéances et les priorités':'Monitor workload, deadlines and priorities',
    'Conserver et vérifier les éléments probants':'Preserve and verify evidence',
    'Prendre les décisions humaines requises avant toute préparation':'Make required human decisions before any preparation',
    'Préparer une démarche externe sans l’exécuter automatiquement':'Prepare an external process without executing it automatically',
    'Suivre les alertes opérationnelles et leur livraison':'Track operational alerts and their delivery',
    'Consulter la chronologie complète des actions':'View the complete action timeline',
    'Gérer votre formule, votre tarif fidélité et vos achats':'Manage your plan, loyalty pricing and purchases',
    'Gérer les membres, accès et contrôles de sécurité':'Manage members, access and security controls',
    'Vue opérationnelle':'Operational view','Déconnexion':'Log out','Avis ingérés':'Ingested reviews','Contrôles humains':'Human controls',
    'À TRAITER MAINTENANT':'TO HANDLE NOW','Votre prochaine action':'Your next action',
    'Le tableau de bord met en avant ce qui mérite votre attention avant le reste.':'The dashboard highlights what needs your attention first.',
    'Vérifier les validations':'Review approvals','Contrôler les preuves':'Check evidence','Pipeline':'Pipeline','Garde-fous':'Safeguards',
    'Qualification des avis':'Review qualification','Identifier rapidement les avis à examiner, sans déclencher d’action externe automatique.':'Quickly identify reviews to examine without triggering automatic external action.',
    'Inbox des avis':'Review inbox','Recherche et lecture des éléments disponibles.':'Search and review available items.',
    'Toutes les priorités':'All priorities','Créer le dossier':'Create case','Aucun avis disponible.':'No reviews available.',
    'Les avis ingérés apparaîtront ici après synchronisation.':'Ingested reviews will appear here after synchronization.',
    'Aucun dossier pour le moment.':'No cases yet.','Les nouveaux dossiers apparaîtront ici après ingestion.':'New cases will appear here after ingestion.',
    'Traçabilité conservée':'Traceability preserved','Les décisions et actions sensibles restent soumises aux contrôles humains et aux règles de sécurité.':'Decisions and sensitive actions remain subject to human controls and security rules.',
    'Charge par analyste':'Workload by analyst','Répartition actuelle issue du moteur de file SLA.':'Current allocation from the SLA queue engine.',
    'Aucune charge analyste disponible.':'No analyst workload available.','Signaux actifs':'Active signals','Prioriser les écarts SLA et contradictions à traiter.':'Prioritize SLA exceptions and contradictions to address.',
    'Aucune escalation active.':'No active escalations.','Le centre reste surveillé par les règles SLA.':'The center remains monitored by SLA rules.',
    'Registre des preuves':'Evidence register','Conserver, vérifier et relier les éléments de preuve avec une intégrité cryptographique explicite.':'Store, verify and link evidence with explicit cryptographic integrity.',
    'Éléments':'Items','preuves enregistrées':'recorded evidence','intégrité validée':'validated integrity','formats représentés':'represented formats',
    'Aucune preuve enregistrée.':'No evidence recorded.','Les éléments ingérés apparaîtront ici.':'Ingested items will appear here.',
    'Intégrité documentaire':'Document integrity','Chaque preuve conserve son empreinte SHA-256. La présentation ne modifie jamais le contenu source.':'Each item retains its SHA-256 fingerprint. The presentation never modifies the source content.',
    'Centre de validation':'Approval center','Chaque action sensible reste bloquée jusqu’à une validation humaine explicite et traçable.':'Every sensitive action remains blocked until explicit, traceable human approval.',
    'File de validation':'Approval queue','Examiner les demandes avant toute préparation d’action externe.':'Review requests before preparing any external action.',
    'Aucune demande de validation.':'No approval requests.','Les demandes nécessitant une décision humaine apparaîtront ici.':'Requests requiring human decisions will appear here.',
    'Préparation des soumissions':'Submission preparation','Préparer une action documentée après approbation, sans exécuter automatiquement d’action externe.':'Prepare a documented action after approval without automatically executing an external action.',
    'Aucune préparation de soumission.':'No submission preparations.','La préparation ne déclenche ni publication, ni suppression, ni réponse automatique sur Google.':'Preparation does not trigger publication, deletion or automatic replies on Google.',
    'Centre d’alertes':'Alert center','Prioriser les signaux sans déclencher d’action externe depuis cette vue.':'Prioritize signals without triggering external actions from this view.',
    'Aucune alerte enregistrée.':'No alerts recorded.','Les notifications opérationnelles apparaîtront ici.':'Operational notifications will appear here.',
    'Observabilité uniquement':'Observability only','Cette interface ne supprime, ne publie et ne répond à aucun avis Google automatiquement.':'This interface does not automatically delete, publish or reply to any Google review.',
    'DOCUMENT DE RÉFÉRENCE':'REFERENCE DOCUMENT','INFORMATION RGPD':'GDPR INFORMATION','MISE À JOUR · 24 SEPTEMBRE 2026':'UPDATED · SEPTEMBER 24, 2026','Information données personnelles':'Personal data information','Les données saisies (nom, e-mail, entreprise et message) servent à répondre à votre demande. Elles sont limitées à ce qui est nécessaire à cette finalité et ne sont pas utilisées pour une prospection commerciale sans le cadre juridique applicable. Pour exercer vos droits :':'The data you provide (name, email, company and message) is used to respond to your request. It is limited to what is necessary for this purpose and is not used for commercial prospecting outside the applicable legal framework. To exercise your rights:','Exercice des droits':'Exercising your rights','Les demandes sont traitées dans les délais prévus par le RGPD. Une demande complexe ou comportant plusieurs traitements peut nécessiter un délai supplémentaire lorsque la réglementation le permet ; la personne en est informée. La CNIL peut être saisie après une démarche préalable auprès du responsable du traitement.':'Requests are handled within the time limits provided by GDPR. A complex request or one involving multiple processing activities may require additional time where permitted by law; the requester will be informed. The French data protection authority (CNIL) may be contacted after first approaching the data controller.','Préférences cookies':'Cookie preferences','Les traceurs qui ne sont pas strictement nécessaires doivent faire l’objet d’un consentement préalable. À ce stade, aucun outil publicitaire ou analytique optionnel n’est activé par cette couche front-end.':'Trackers that are not strictly necessary require prior consent. At this stage, no optional advertising or analytics tools are enabled by this front-end layer.','Strictement nécessaires':'Strictly necessary','Session, sécurité et préférences indispensables.':'Session, security and essential preferences.','TOUJOURS ACTIFS':'ALWAYS ACTIVE','Mesure d’audience / publicité':'Analytics / advertising','Aucun traceur optionnel activé actuellement.':'No optional trackers are currently enabled.','INACTIFS':'INACTIVE','Fermer':'Close','Enregistrer':'Save','Cookies et traceurs':'Cookies and trackers','Review Defense utilise les traceurs strictement nécessaires au fonctionnement et à la sécurité. Aucun traceur optionnel n’est activé par cette couche front-end. Vous pouvez consulter ou modifier vos préférences à tout moment.':'Review Defense uses trackers that are strictly necessary for operation and security. No optional trackers are enabled by this front-end layer. You can review or change your preferences at any time.','Refuser les optionnels':'Reject optional trackers','Gérer':'Manage','Autoriser les optionnels':'Allow optional trackers'
  };
  Object.assign(translations,commonTranslations);
  Object.assign(translations,{
    'REPUTATION INTELLIGENCE · POUR LES ENTREPRISES':'REPUTATION INTELLIGENCE · FOR BUSINESSES',
    'WORKSPACE SÉCURISÉ':'SECURE WORKSPACE','ANALYSE ACTIVE':'ACTIVE ANALYSIS','À TRAITER MAINTENANT':'TO HANDLE NOW',
    'ÉLÉMENTS À VÉRIFIER':'ITEMS TO VERIFY','ÉVOLUTION DES DOSSIERS':'CASE PROGRESS','ANALYSE ACTIVE':'ACTIVE ANALYSIS',
    'REVIEW INTAKE':'REVIEW INTAKE','Avis ingérés':'Ingested reviews','Contrôles humains':'Human controls',
    'Éléments disponibles.':'Available items.','Résultats':'Results','Toutes les notes':'All ratings','1 étoile':'1 star','2 étoiles':'2 stars','3 étoiles':'3 stars','4 étoiles':'4 stars','5 étoiles':'5 stars',
    'Service déplorable, une arnaque totale.':'Terrible service, a complete scam.','Google · publié récemment · source vérifiée':'Google · recently published · verified source','Source vérifiée · contexte disponible':'Verified source · context available',
    '02 Décision':'02 Decision','03 Gel':'03 Freeze','04 Approbation':'04 Approval','05 Préparation':'05 Preparation','Preuves':'Evidence','Décisions':'Decisions','Audit':'Audit',
    'HUMAN APPROVAL':'HUMAN APPROVAL','HUMAN APPROVAL GATE':'HUMAN APPROVAL GATE','HUMAN GATE':'HUMAN GATE','SIGNAL DE DOSSIER':'CASE SIGNAL',
    '07 preuves':'7 pieces of evidence','7 preuves':'7 pieces of evidence','7 associées':'7 linked','Terminée':'Completed','En attente':'Pending',
    'Décision documentée':'Documented decision','Dossier gelable':'Case can be frozen','Approbation explicite':'Explicit approval','Action externe non automatique':'External action is not automatic',
    'Aucune étape sensible sans validation explicite':'No sensitive step without explicit approval','Analyse assistée':'Assisted analysis','Dossier documenté':'Documented case file','Préparation contrôlée':'Controlled preparation',
    'Voir comment ça marche':'See how it works','Démarrer →':'Start →','Parler à l’équipe':'Talk to the team','Voir les validations':'View approvals',
    'Créer mon espace gratuitement':'Create my workspace for free','J’ai déjà un compte':'I already have an account','Créer un compte':'Create an account','Créer mon compte':'Create my account',
    'Inscription sécurisée':'Secure sign-up','Votre organisation':'Your organization','MFA disponible':'MFA available','Mot de passe oublié ?':'Forgot password?','Contrôle humain & serveur':'Human & server controls',
    'Récupération sécurisée':'Secure recovery','Récupérer l’accès':'Recover access','Retour à la connexion':'Back to login','Jeton à usage contrôlé':'Controlled-use token',
    'Vérification de l’email':'Email verification','Vérifier':'Verify','Email professionnel':'Work email','Nom de l’entreprise':'Company name',
    'Ce qui nécessite votre attention maintenant':'What needs your attention now','Préparation':'Preparation','Préparer une démarche externe sans l’exécuter automatiquement':'Prepare an external process without executing it automatically',
    'Suivre les alertes opérationnelles et leur livraison':'Track operational alerts and delivery','Consulter la chronologie complète des actions':'View the complete action timeline',
    'Gérer votre formule, votre tarif fidélité et vos achats':'Manage your plan, loyalty pricing and purchases','Gérer les membres, accès et contrôles de sécurité':'Manage members, access and security controls',
    'Pipeline':'Pipeline','Ingestion → analyse → preuves → revue humaine → gel → approbation → préparation de soumission.':'Ingestion → analysis → evidence → human review → freeze → approval → submission preparation.',
    'Garde-fous':'Safeguards','RLS, audit, intégrité SHA-256, MFA et aucune action Google autonome.':'RLS, audit, SHA-256 integrity, MFA and no autonomous Google actions.',
    'REVIEW INTAKE':'REVIEW INTAKE','Recherche et lecture des éléments disponibles.':'Search and review available items.',
    'Créer le dossier':'Create case','Aucun avis disponible.':'No reviews available.','Les avis ingérés apparaîtront ici après synchronisation.':'Ingested reviews will appear here after synchronization.',
    'Aucun dossier pour le moment.':'No cases yet.','Les nouveaux dossiers apparaîtront ici après ingestion.':'New cases will appear here after ingestion.',
    'Traçabilité conservée':'Traceability preserved','Les décisions et actions sensibles restent soumises aux contrôles humains et aux règles de sécurité.':'Decisions and sensitive actions remain subject to human controls and security rules.',
    'EVIDENCE CONTROL':'EVIDENCE CONTROL','Éléments':'Items','preuves enregistrées':'recorded evidence','intégrité validée':'validated integrity','formats représentés':'represented formats',
    'Aucune preuve enregistrée.':'No evidence recorded.','Les éléments ingérés apparaîtront ici.':'Ingested items will appear here.',
    'HUMAN APPROVAL GATE':'HUMAN APPROVAL GATE','requiert une décision':'requires a decision','validation enregistrée':'approval recorded','contrôle négatif':'negative control',
    'Décision humaine requise':'Human decision required','Validation enregistrée':'Approval recorded','Contrôle clôturé':'Control closed',
    'Aucune demande de validation.':'No approval requests.','Les demandes nécessitant une décision humaine apparaîtront ici.':'Requests requiring a human decision will appear here.',
    'CONTROLLED SUBMISSION':'CONTROLLED SUBMISSION','Préparées':'Prepared','Approuvées':'Approved','Aucune exécution externe':'No external execution',
    'Aucune préparation de soumission.':'No submission preparations.','Les préparations approuvées apparaîtront ici.':'Approved preparations will appear here.',
    'Dernier verrou':'Final safeguard','La préparation ne déclenche ni publication, ni suppression, ni réponse automatique sur Google.':'Preparation does not trigger publication, deletion or automatic replies on Google.',
    'Centre d’alertes':'Alert center','Prioriser les signaux sans déclencher d’action externe depuis cette vue.':'Prioritize signals without triggering external actions from this view.',
    'Aucune alerte enregistrée.':'No alerts recorded.','Les notifications opérationnelles apparaîtront ici.':'Operational notifications will appear here.',
    'Observabilité uniquement':'Observability only','Cette interface ne supprime, ne publie et ne répond à aucun avis Google automatiquement.':'This interface does not automatically delete, publish or reply to any Google review.',
    'Contradiction examinée':'Contradiction reviewed','Dossier créé':'Case created','Je souhaite recevoir les ressources à cette adresse :':'I would like to receive resources at this address:'
  });
Object.assign(extraTranslations,{
"Paiement PayPal":"PayPal payment","Payer avec PayPal":"Pay with PayPal","PAYPAL CONNECTÉ":"PAYPAL CONNECTED","PAYPAL À CONFIGURER":"PAYPAL TO CONFIGURE","Historique":"History","Aucun paiement enregistré":"No payments recorded","Les transactions PayPal apparaîtront ici.":"PayPal transactions will appear here.","Choisir une formule":"Choose a plan","Abonnement confirmé":"Subscription confirmed","Paiement confirmé":"Payment confirmed","Paiement annulé":"Payment cancelled","Erreur de paiement PayPal":"PayPal payment error","Le paiement est séparé des actions Google.":"Payment is separate from Google actions.","Le serveur détermine le montant à partir de l’offre sélectionnée.":"The server determines the amount from the selected offer.","Gérez votre formule, vos achats et vos paiements depuis un espace unique.":"Manage your plan, purchases and payments from one place."
});
  Object.assign(translations,extraTranslations);
  const pairs=Object.entries(translations).sort((a,b)=>b[0].length-a[0].length);
  const protectedSelector='input,textarea,select,option,[data-i18n-ignore],script,style,code,pre,.review-text,blockquote';
  function translateNode(root){
    if(!isEnglish()||!shouldTranslate()) return;
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
    root.querySelectorAll?.('[title],[aria-label],[placeholder],[alt]').forEach(el=>{
      for(const attr of ['title','aria-label','placeholder','alt']){
        const value=el.getAttribute(attr); if(!value) continue;
        let next=value; for(const [fr,en] of pairs) if(next.includes(fr)) next=next.split(fr).join(en);
        if(next!==value) el.setAttribute(attr,next);
      }
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
    const host=document.querySelector('.public-actions')||document.querySelector('header .header-actions')||document.querySelector('header')||document.body;
    const b=document.createElement('button'); b.id='rd-language-switcher'; b.type='button'; b.className='rd-language-switcher'; b.textContent=isEnglish()?'FR':'EN'; b.setAttribute('aria-label',isEnglish()?'Passer en français':'Passer en anglais'); b.title=isEnglish()?'Passer en français':'Passer en anglais';
    b.onclick=()=>{localStorage.setItem(KEY,isEnglish()?'fr':'en');location.reload()};
    host.appendChild(b);
  }
  function run(){
    if(!isEnglish()) document.documentElement.lang='fr';
    if(isEnglish()&&shouldTranslate()) { setMeta(); translateNode(document.body); }
    addSwitcher();
  }
  window.ReviewDefenseI18n={setLanguage(l){if(SUPPORTED.includes(l)){localStorage.setItem(KEY,l);location.reload()}},getLanguage:()=>isEnglish()?'en':'fr',translate:translateNode};
  const observer=new MutationObserver(muts=>{if(!isEnglish()||!shouldTranslate())return; muts.forEach(m=>m.addedNodes.forEach(n=>{if(n.nodeType===1)translateNode(n)})); addSwitcher();});
  observer.observe(document.documentElement,{subtree:true,childList:true});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run,{once:true});else run();
})();
