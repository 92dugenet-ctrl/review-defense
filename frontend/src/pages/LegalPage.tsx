import{Link,useLocation}from"react-router-dom";

type LegalKey="mentions-legales"|"confidentialite"|"cookies"|"cgu"|"cgv"|"accessibilite"|"contact-juridique";

const pages:Record<LegalKey,{title:string;intro:string;sections:{title:string;body:string}[]}>={
 "mentions-legales":{title:"Mentions légales",intro:"Informations relatives à l’éditeur du site et aux responsables techniques. Les champs entre crochets doivent être complétés avant la mise en production commerciale.",sections:[
 {title:"Éditeur du site",body:"[RAISON SOCIALE / NOM DE L’ENTREPRENEUR] — [FORME JURIDIQUE]. Siège social : [ADRESSE]. Immatriculation : [RCS / RNE / VILLE]. SIREN/SIRET : [À COMPLÉTER]. Capital social, lorsqu’il est applicable : [À COMPLÉTER]. Adresse e-mail : [EMAIL DE CONTACT]. Téléphone : [À COMPLÉTER]."},
 {title:"Directeur de la publication",body:"[NOM ET QUALITÉ DU DIRECTEUR DE LA PUBLICATION À COMPLÉTER]."},
 {title:"Hébergement",body:"Hébergeur : [NOM DE L’HÉBERGEUR À COMPLÉTER]. Adresse : [ADRESSE DE L’HÉBERGEUR]. Téléphone : [TÉLÉPHONE DE L’HÉBERGEUR]. Ces informations doivent être vérifiées auprès de l’hébergeur effectivement utilisé en production."},
 {title:"Propriété intellectuelle",body:"Les éléments du site Review Defense, notamment textes, interfaces, logos, graphismes, logiciels et contenus, sont protégés dans la mesure prévue par les textes applicables. Les droits détenus par des tiers restent la propriété de leurs titulaires. Toute réutilisation doit respecter les droits applicables."},
 {title:"Responsabilité",body:"Les informations publiées sur le site ont une vocation informative et commerciale. Review Defense ne se présente pas comme un cabinet d’avocats, une société de recouvrement ou un prestataire fournissant des conseils juridiques. Les décisions prises à partir des informations ou analyses du service restent sous la responsabilité de l’utilisateur."}
 ]},
 "confidentialite":{title:"Politique de confidentialité",intro:"Cette politique décrit les principes à compléter et à appliquer aux traitements réellement mis en œuvre par Review Defense. Elle doit être finalisée à partir de la cartographie réelle des données, fournisseurs et durées de conservation.",sections:[
 {title:"Responsable du traitement",body:"Responsable : [IDENTITÉ JURIDIQUE À COMPLÉTER]. Contact relatif aux données personnelles : [EMAIL / DPO OU CONTACT RGPD À COMPLÉTER]."},
 {title:"Données susceptibles d’être traitées",body:"Selon les fonctionnalités réellement utilisées : identité et coordonnées professionnelles, informations de compte, données de connexion, contenus d’avis, dossiers et documents transmis, échanges avec le service, données de facturation et informations techniques nécessaires à la sécurité et au fonctionnement. Ne collecter que les données nécessaires à chaque finalité."},
 {title:"Finalités et bases légales",body:"Les finalités peuvent notamment inclure la création et gestion du compte, l’exécution du contrat, la fourniture du service, la sécurité, la gestion de la facturation, le support et, lorsque cela est applicable, la mesure d’audience ou la prospection. Chaque traitement doit être associé à sa base légale réelle et documentée."},
 {title:"Destinataires et sous-traitants",body:"Les données peuvent être accessibles aux équipes autorisées et aux prestataires techniques strictement nécessaires au service. La liste effective des sous-traitants, leurs rôles, les éventuels transferts hors UE et les garanties associées doivent être renseignés avant publication."},
 {title:"Durées de conservation",body:"Les durées doivent être définies par catégorie de données et par finalité : compte, dossiers, pièces jointes, facturation, sécurité, support et obligations légales. [TABLEAU DES DURÉES À COMPLÉTER APRÈS CARTOGRAPHIE]."},
 {title:"Droits des personnes",body:"Selon les conditions prévues par le RGPD, les personnes peuvent notamment disposer de droits d’accès, rectification, effacement, limitation, opposition et portabilité, ainsi que du droit de retirer un consentement lorsqu’un traitement repose sur celui-ci. Une demande peut être adressée à [EMAIL RGPD À COMPLÉTER]. Une réclamation peut être adressée à la CNIL."},
 {title:"Sécurité",body:"Review Defense doit mettre en œuvre des mesures techniques et organisationnelles adaptées aux risques : contrôle des accès, authentification, journalisation, sauvegardes, chiffrement lorsque pertinent, gestion des secrets, limitation des privilèges et procédure de gestion des incidents. Les mesures effectivement déployées doivent être décrites et vérifiées avant publication."}
 ]},
 "cookies":{title:"Cookies et traceurs",intro:"Cette page doit refléter exclusivement les cookies et traceurs réellement présents sur le site.",sections:[
 {title:"Principe",body:"Certains traceurs nécessitent une information préalable et un consentement avant leur dépôt ou leur lecture. Les traceurs strictement nécessaires peuvent relever d’une exception, sous réserve de respecter les conditions applicables."},
 {title:"Traceurs utilisés",body:"[INVENTAIRE À COMPLÉTER : nom du traceur, fournisseur, finalité, durée, domaine, nature, base juridique et éventuel transfert]. Aucun traceur optionnel ne doit être déclaré ici sans avoir été vérifié dans le code et les services chargés par le site."},
 {title:"Vos choix",body:"Lorsque le consentement est requis, le site doit permettre d’accepter, de refuser et de modifier son choix de manière claire. Le retrait du consentement doit rester accessible. La simple poursuite de la navigation ne vaut pas consentement."},
 {title:"Mesure d’audience",body:"Si une solution de mesure d’audience est utilisée, son régime doit être vérifié au regard des conditions d’exemption ou de consentement applicables. La configuration réellement déployée doit être documentée."}
 ]},
 "cgu":{title:"Conditions générales d’utilisation",intro:"Règles applicables à l’utilisation du site et du service Review Defense. La version contractuelle définitive doit être validée juridiquement avant mise en production.",sections:[
 {title:"Objet",body:"Review Defense fournit un service logiciel destiné à aider les professionnels à analyser, documenter et suivre des avis et dossiers associés. Le service ne remplace pas l’appréciation humaine du client."},
 {title:"Accès au service",body:"L’utilisateur doit fournir des informations exactes, protéger ses identifiants et utiliser le service conformément à la loi et aux présentes conditions. Les accès peuvent être suspendus en cas de risque de sécurité ou de violation des conditions, selon les modalités contractuelles définitives."},
 {title:"Validation humaine",body:"Les analyses, suggestions ou propositions générées par le service constituent une aide à la décision. Le client conserve la validation des actions et la responsabilité de leur utilisation."},
 {title:"Contenus utilisateur",body:"L’utilisateur reste responsable des contenus qu’il importe ou transmet au service et doit disposer des droits et autorisations nécessaires. Les modalités de traitement de ces contenus sont précisées dans la politique de confidentialité et, lorsque nécessaire, dans les accords de traitement des données."},
 {title:"Disponibilité et sécurité",body:"Les objectifs de disponibilité, maintenance, sauvegarde, sécurité et gestion des incidents doivent être définis dans la documentation contractuelle applicable au plan souscrit."},
 {title:"Droit applicable",body:"[DROIT APPLICABLE, JURIDICTION ET CLAUSES DE RÈGLEMENT DES LITIGES À COMPLÉTER APRÈS VALIDATION JURIDIQUE]."}
 ]},
 "cgv":{title:"Conditions générales de vente",intro:"Conditions commerciales du service SaaS. Les éléments tarifaires et contractuels doivent correspondre exactement à l’offre réellement vendue.",sections:[
 {title:"Vendeur et client",body:"Vendeur : [IDENTITÉ JURIDIQUE À COMPLÉTER]. Le client est le professionnel ou, lorsque l’offre le permet, la personne souscrivant au service. Les informations d’identification et de facturation doivent être vérifiées au moment de la commande."},
 {title:"Offres et prix",body:"Les plans, fonctionnalités, périodicité et prix sont ceux présentés sur la page Tarifs et au moment de la souscription. [MONNAIE, TVA, PRIX HT/TTC, RÈGLES DE MODIFICATION DES PRIX ET CONDITIONS DE PROMOTION À COMPLÉTER]."},
 {title:"Commande et paiement",body:"La commande est confirmée selon le parcours de paiement effectivement utilisé. Les modalités de facturation, renouvellement, échec de paiement, résiliation et remboursement doivent correspondre à la configuration réelle du prestataire de paiement et de l’offre."},
 {title:"Rétractation et statut du client",body:"Le régime applicable dépend notamment de la qualité du client et du contrat conclu. [MODALITÉS APPLICABLES AUX CONSOMMATEURS À COMPLÉTER SI L’OFFRE EST OUVERTE AUX CONSOMMATEURS]."},
 {title:"Médiation",body:"Si le service est proposé à des consommateurs, les coordonnées du médiateur de la consommation compétent doivent être indiquées de manière visible sur le site et dans les documents contractuels, après désignation effective d’un médiateur référencé. [MÉDIATEUR, ADRESSE ET SITE À COMPLÉTER]."},
 {title:"Résiliation",body:"Les modalités de résiliation, préavis, échéance et effets sur les données doivent être précisées selon le modèle d’abonnement réellement commercialisé."}
 ]},
 "accessibilite":{title:"Accessibilité",intro:"Déclaration et feuille de route d’accessibilité du site Review Defense.",sections:[
 {title:"Engagement",body:"Review Defense vise une interface utilisable par le plus grand nombre, avec navigation clavier, structure sémantique, contrastes suffisants, alternatives textuelles, états de focus visibles et respect de la préférence prefers-reduced-motion lorsque la technologie le permet."},
 {title:"État de conformité",body:"[À AUDITER ET À COMPLÉTER : niveau de conformité, périmètre audité, date de l’audit, résultats et exceptions]. Cette page ne doit pas déclarer une conformité qui n’a pas été vérifiée."},
 {title:"Signaler une difficulté",body:"Pour signaler un problème d’accessibilité, contactez [EMAIL ACCESSIBILITÉ À COMPLÉTER] en indiquant la page concernée, la difficulté rencontrée et, si possible, la technologie utilisée."}
 ]},
 "contact-juridique":{title:"Contact juridique et données",intro:"Point de contact pour les demandes relatives aux mentions légales, aux données personnelles et aux conditions contractuelles.",sections:[
 {title:"Contact",body:"Email juridique : [EMAIL À COMPLÉTER]. Adresse postale : [ADRESSE À COMPLÉTER]. Responsable données personnelles : [CONTACT / DPO À COMPLÉTER]."},
 {title:"Demandes relatives aux données",body:"Pour exercer un droit ou poser une question relative à un traitement, utilisez [EMAIL RGPD À COMPLÉTER]. Des informations permettant de vérifier l’identité du demandeur peuvent être nécessaires pour protéger les données concernées."},
 {title:"Réclamation",body:"Une demande doit d’abord être adressée à Review Defense afin de permettre son traitement. Lorsque les conditions sont réunies, une personne peut également saisir l’autorité de contrôle compétente, notamment la CNIL en France."}
 ]}
};

export function LegalPage(){
 const key=useLocation().pathname.replace(/^\\//,"") as LegalKey;
 const page=pages[key]??pages["mentions-legales"];
 return <main className="rd-legal">
  <style>{`.rd-legal{min-height:100vh;background:#fff;color:#172026;font-family:Inter,system-ui,sans-serif}.rd-legal-nav{height:78px;border-bottom:1px solid #e3e6e8;display:flex;align-items:center;justify-content:space-between;padding:0 clamp(20px,5vw,68px);font-size:11px}.rd-legal-nav strong{font-size:15px}.rd-legal-nav a{color:#172026;text-decoration:none}.rd-legal-wrap{max-width:920px;margin:auto;padding:90px 20px 110px}.rd-legal-eyebrow{font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#1264d6}.rd-legal h1{font-size:clamp(48px,7vw,82px);line-height:.95;letter-spacing:-.06em;margin:18px 0 24px}.rd-legal-intro{max-width:720px;color:#68727a;font-size:15px;line-height:1.75;margin-bottom:65px}.rd-legal-section{padding:28px 0;border-top:1px solid #e3e6e8}.rd-legal-section h2{font-size:21px;margin:0 0 13px;letter-spacing:-.03em}.rd-legal-section p{max-width:760px;color:#566168;font-size:13px;line-height:1.8;margin:0}.rd-legal-note{margin-top:45px;padding:18px;border:1px solid #e3e6e8;background:#f7f8f9;color:#68727a;font-size:11px;line-height:1.7}.rd-legal-back{display:inline-flex;margin-top:45px;padding:11px 16px;border-radius:999px;background:#172026;color:#fff!important}@media(max-width:650px){.rd-legal-wrap{padding-top:55px}.rd-legal h1{font-size:48px}.rd-legal-intro{margin-bottom:35px}}\`}</style>
  <nav className="rd-legal-nav"><Link to="/"><strong>Review Defense</strong></Link><Link to="/">Retour au site</Link></nav>
  <div className="rd-legal-wrap"><div className="rd-legal-eyebrow">Informations légales</div><h1>{page.title}</h1><p className="rd-legal-intro">{page.intro}</p>
   {page.sections.map((section,i)=><section className="rd-legal-section" key={i}><h2>{section.title}</h2><p>{section.body}</p></section>)}
   <div className="rd-legal-note"><strong>À compléter avant publication commerciale :</strong> les éléments entre crochets correspondent à des informations que le dépôt Review Defense ne permet pas de vérifier aujourd’hui. Ils doivent être remplacés par les informations exactes de l’éditeur et par les configurations réellement déployées.</div>
   <Link className="rd-legal-back" to="/">Retour à Review Defense</Link>
  </div>
 </main>;
}
