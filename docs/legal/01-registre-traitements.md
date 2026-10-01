# Registre des activités de traitement — version provisoire

> **Document interne — à compléter et vérifier.** Les fiches ci-dessous sont une première cartographie tirée des fonctions repérées dans le dépôt. Elles ne valent pas validation des flux en production.

## Responsable / sous-traitant

- Entité : [RAISON SOCIALE]
- Adresse : [ADRESSE]
- SIREN : [SIREN]
- Contact vie privée : [EMAIL]
- DPO : [NOM / COORDONNÉES / NON DÉSIGNÉ — À ÉVALUER]
- Version du registre : 0.1 — 01/10/2026

## Fiche T01 — Gestion des comptes et authentification

- Finalité : créer et administrer les comptes, authentifier les utilisateurs, gérer les rôles, invitations, sessions, MFA et récupération de compte.
- Personnes : représentants et salariés des clients, administrateurs et utilisateurs invités.
- Données : nom/prénom si collectés, adresse e-mail, identifiants internes, organisation, rôle, hash de mot de passe, métadonnées de session, événements de sécurité, données MFA.
- Base légale envisagée : exécution du contrat pour l'accès au service ; intérêt légitime pour la sécurité et la prévention des abus ; obligation légale si applicable.
- Destinataires : personnel habilité, hébergeur, fournisseur e-mail, prestataires de sécurité.
- Conservation : [DURÉE COMPTE ACTIF] ; après clôture [DURÉE DE GRÂCE] ; archives de preuve [DURÉE ET JUSTIFICATION].
- Sécurité : hash de mots de passe, tokens de session hachés, MFA disponible ; vérifier rotation, révocation, chiffrement, journaux et sauvegardes.
- Transferts : [PAYS / FOURNISSEURS].
- Rôle : Review Défense responsable de traitement.

## Fiche T02 — Gestion des avis, dossiers et pièces justificatives

- Finalité : permettre au client de centraliser un avis, analyser son contenu, organiser les faits et pièces, suivre les actions et décisions.
- Personnes : clients de Review Défense, auteurs d'avis, personnes citées dans les avis, salariés et interlocuteurs d'établissements.
- Données : texte d'avis, nom public ou pseudonyme, note, date, URL, identifiants de fiche, éléments de dossier, pièces, échanges et métadonnées de fichiers. Les textes libres peuvent révéler des données sensibles ou relatives à des infractions : limiter leur collecte et prévoir une procédure de traitement spécifique.
- Base légale : pour le client, à déterminer selon sa finalité ; pour Review Défense, exécution du contrat et traitement sur instructions documentées si sous-traitant. Ne pas utiliser le consentement comme base par défaut.
- Destinataires : utilisateurs autorisés du compte client, personnel support strictement habilité, hébergeur et prestataires techniques autorisés.
- Conservation : [DURÉE DU CONTRAT] puis restitution/suppression sous [DÉLAI], sous réserve des obligations légales et contentieux ; backups [CYCLE].
- Sécurité : isolation par organisation, contrôle d'accès, validation des fichiers, stockage privé ; vérifier chiffrement au repos/en transit, scan antivirus, liens temporaires, accès support et purge.
- Rôle : sous-traitant probable pour les données de dossier, à confirmer au regard des usages effectifs.

## Fiche T03 — Intégration Google Business Profile et synchronisation

- Finalité : connecter le compte ou la fiche d'établissement, récupérer/synchroniser les avis et données associées, si l'utilisateur active cette fonction.
- Personnes : administrateurs du compte Google, auteurs d'avis et contacts des établissements.
- Données : identifiants OAuth, jetons, identifiants de compte/établissement, avis, noms affichés, dates et contenus.
- Base légale : exécution du contrat / instructions du client pour la synchronisation ; intérêt légitime pour sécurité technique. Vérifier les permissions demandées.
- Destinataires : Google et prestataires d'infrastructure.
- Conservation : jetons jusqu'à déconnexion/révocation ou fin du besoin ; données synchronisées selon T02.
- Transferts : vérifier conditions Google, région, accès et mécanismes de transfert.
- Rôle : à qualifier flux par flux.

## Fiche T04 — Facturation et paiements

- Finalité : souscription, gestion des plans, facturation, paiement, prévention de la fraude, comptabilité.
- Personnes : clients professionnels, représentants et contacts de facturation.
- Données : société, nom, e-mail, adresse de facturation, plan, montant, statut, identifiant transaction et échanges avec PayPal.
- Base légale : exécution du contrat et obligations comptables/fiscales ; intérêt légitime pour défense des droits et prévention de la fraude.
- Destinataires : PayPal, banque, comptable, hébergeur, personnel finance autorisé.
- Conservation : pièces comptables selon les délais légaux applicables ; données de compte selon la matrice T01/T06.
- Rôle : Review Défense responsable de traitement pour la gestion contractuelle ; PayPal selon ses propres rôles.

## Fiche T05 — Support, notifications et e-mails transactionnels

- Finalité : répondre aux demandes, envoyer invitations, vérifications, réinitialisations et notifications demandées.
- Personnes : utilisateurs, contacts client et destinataires des notifications.
- Données : adresse e-mail, contenu de demande, identifiants, métadonnées d'envoi, événements de livraison.
- Base légale : contrat, intérêt légitime ou obligation légale selon le message. Les messages marketing sont traités séparément.
- Destinataires : fournisseur SMTP, hébergeur, support habilité.
- Conservation : [DURÉE SUPPORT] ; journaux techniques [DURÉE].
- Rôle : Review Défense responsable de traitement pour son support ; sous-traitant éventuel si traitement de demandes au nom du client.

## Fiche T06 — Sécurité, journalisation et prévention des abus

- Finalité : protéger le service, détecter les incidents, assurer traçabilité, gérer accès et prévenir les abus.
- Personnes : utilisateurs et visiteurs dont des données techniques sont collectées.
- Données : adresse IP ou dérivés, user-agent, horodatage, identifiants, traces d'accès, événements de sécurité, requêtes et identifiants de corrélation.
- Base légale : intérêt légitime et, le cas échéant, obligation légale.
- Destinataires : équipes habilitées, hébergeur et prestataires sécurité.
- Conservation : [DURÉE JUSTIFIÉE PAR CATÉGORIE], accès restreint ; distinguer journaux de sécurité, audit métier et logs applicatifs.
- Rôle : Review Défense responsable de traitement pour la sécurité de son service.

## Fiche T07 — Demandes d'exercice des droits et consentements

- Finalité : recevoir, instruire, suivre et répondre aux demandes RGPD ; prouver le choix exprimé lorsqu'un consentement est effectivement utilisé.
- Personnes : utilisateurs du service et, selon le rôle contractuel, personnes concernées par les données traitées pour les clients.
- Données : identité, coordonnées, type de demande, justificatif strictement nécessaire si doute raisonnable, échanges, décision, date, version de notice et preuve du consentement.
- Base légale : obligation légale ; intérêt légitime pour la traçabilité et la défense des droits.
- Destinataires : équipe privacy habilitée, prestataire technique.
- Conservation : [DURÉE DE PREUVE ET PRESCRIPTION À VALIDER] ; minimiser les justificatifs d'identité et supprimer les copies inutiles.
- Rôle : Review Défense responsable pour les demandes relatives à ses propres traitements ; assistance au client pour les demandes portant sur ses données.

## Fiche T08 — Prospection commerciale et gestion des contacts prospects

- Statut : **à confirmer** — cette fiche doit être conservée uniquement si Review Défense réalise effectivement de la prospection.
- Finalité : présenter les services à des professionnels, suivre les échanges, gérer les oppositions.
- Données : nom professionnel, fonction, adresse professionnelle, société, historique de contact et opposition.
- Base légale : intérêt légitime possible en B2B si la sollicitation est en rapport avec la fonction professionnelle et si l'information/opposition sont correctement assurées ; règles distinctes pour particuliers.
- Conservation : définir une durée opérationnelle, puis suppression ou archivage minimal de la liste d'opposition.
- Destinataires : CRM, fournisseur d'e-mail et équipe commerciale.

## Contrôles de mise à jour

Pour chaque fiche, renseigner : date de création, responsable interne, applications, lieux d'hébergement, pays, sous-traitants, mesures de sécurité, durées exactes, suppression des sauvegardes, transferts et lien vers la notice d'information. Le registre doit être actualisé à chaque évolution.
