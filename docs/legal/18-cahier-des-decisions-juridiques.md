# Cahier des décisions juridiques et consignes de validation — Review Défense

> **Document de travail — version 1.0 — 1er octobre 2026. NON VALIDÉ PAR UN AVOCAT. NE PAS PUBLIER COMME DOCUMENT CONTRACTUEL.**
>
> Ce cahier rassemble les choix communiqués par le porteur du projet. Il ne constitue ni un avis juridique, ni une certification de conformité, ni une preuve que les fonctionnalités décrites sont déjà opérationnelles. Toute clause devra être confrontée au code, à l'infrastructure, aux contrats fournisseurs et aux règles des plateformes avant le lancement.

## 1. Statut juridique du projet

- Porteur : **Gabriel Dugenet** (identité officielle à vérifier sur justificatif).
- Forme envisagée : **entreprise individuelle (EI)** en France.
- **Au 1er octobre 2026, la création est encore un projet ; les formalités d'immatriculation ne sont pas effectuées.**
- Date d'immatriculation, SIREN, SIRET et justificatif RNE : à compléter après création.
- Nom du service : Review Défense ; statut de nom commercial ou marque à confirmer.
- Adresse de domiciliation : communiquée séparément et destinée à être renseignée dans les documents définitifs après création et vérification des règles de publication. Elle n'est pas reproduite dans ce dépôt GitHub public.
- Contact projet : `contact.reviewdefense@gmail.com`. Aucun numéro de téléphone public prévu.
- Hébergeur désigné par le porteur : **eCloudService**. Sa raison sociale exacte, son adresse, son téléphone, ses régions d'hébergement et ses sauvegardes restent à vérifier sur facture ou contrat. Ne pas présenter « Trustera Intelligence » comme hébergeur.
- Le dépôt GitHub `92dugenet-ctrl/review-defense` est public. Ne jamais y ajouter d'adresse personnelle, pièce d'identité, facture, contrat confidentiel, donnée client, secret ou clé API.

**Conséquence :** les modèles juridiques sont prospectifs. Ils ne doivent pas présenter une EI comme déjà immatriculée, servir à facturer ou être publiés avant création et vérification de l'identité légale.

## 2. Activité, clientèle et territoire

- Clientèle exclusivement **professionnelle (B2B)** ; aucune souscription consommateur prévue.
- Marché visé : les 27 États membres de l'Union européenne.
- Langues prévues : français, anglais et allemand.
- Support exclusivement par e-mail à `contact.reviewdefense@gmail.com`.
- Délai de réponse annoncé : sous 24 heures ouvrées, du lundi au vendredi, hors jours fériés. Aucun engagement d'accusé de réception automatique immédiat.
- Un seul compte utilisateur par entreprise cliente ; aucun sous-compte collaborateur prévu.
- Double authentification obligatoire pour chaque compte.

À valider : contrôle raisonnable du statut professionnel des clients, identification contractuelle, pays effectivement servis et règles de TVA/facturation transfrontalières. Le modèle B2B n'exclut pas les obligations relatives aux personnes physiques dont les données figurent dans les avis.

## 3. Fonctionnalités et règles Google

Le service doit permettre :
- la connexion à Google Business Profile, sous réserve des autorisations, API et conditions Google ;
- l'ajout manuel d'avis et de pièces ;
- l'analyse, le classement, l'organisation et le suivi des avis et dossiers ;
- la préparation de dossiers de signalement, preuves et propositions de réponses ;
- le signalement direct à Google après validation expresse du client, uniquement lorsque les API, autorisations et conditions Google le permettent ; sinon, un dossier prêt à transmettre est remis au client.

Interdictions :
- faux signalements, signalements abusifs ou massifs injustifiés ;
- signaler un avis uniquement parce qu'il est négatif ;
- fabriquer ou altérer des preuves ;
- contourner les règles ou procédures de Google ;
- promettre une suppression.

Google reste seul décisionnaire de la suppression. Review Défense relève d'une **obligation de moyens**, non de résultat.

**Point de contrôle majeur :** vérifier les conditions Google Business Profile et API concernant l'accès, l'affichage, la mise en cache, la conservation, la transmission et la suppression des données. La volonté du porteur de conserver toutes les informations visibles sur l'auteur (nom affiché, photo, profil, lien, avis, note, date, réponse, métadonnées) ne dispense jamais de la minimisation RGPD ni des règles Google. Ne conserver que les données nécessaires et autorisées.

## 4. Frontière d'activité : éditeur SaaS

Positionnement choisi : éditeur d'un logiciel SaaS d'analyse, d'organisation et d'assistance opérationnelle aux signalements d'avis.

Le service n'a pas vocation à :
- fournir des consultations juridiques personnalisées ;
- se présenter comme cabinet d'avocats ou exercer la profession d'avocat ;
- représenter le client devant Google, une juridiction ou une administration ;
- engager une procédure judiciaire au nom du client ;
- agir comme société ou mandataire de recouvrement ;
- délivrer une qualification juridique définitive d'un avis.

L'IA et les outils peuvent détecter des **indices**, catégories de contenu et points d'attention, expliquer des règles de plateforme à titre informatif et préparer un dossier factuel. Ils ne doivent pas affirmer comme certaine une qualification juridique ni se substituer à un avocat. Le client garde la décision et peut consulter un professionnel du droit.

**Validation avocat indispensable :** vérifier que les fonctions réelles, l'interface, le marketing, les scripts commerciaux, les contrats et les opérations respectent cette frontière. Une clause de non-conseil ne suffit pas si, dans les faits, le service fournit des consultations ou accomplit des actes réglementés.

## 5. Validation humaine et cas clients

Aucune action extérieure ne peut être exécutée par l'IA seule. Validation expresse du client requise avant :
- publication ou envoi d'une réponse à un avis ;
- dépôt ou transmission d'un signalement Google ;
- demande de suppression ;
- transmission d'un dossier ou d'une preuve à un tiers ;
- communication au nom du client.

Conserver une trace proportionnée de la proposition, de la validation, de sa date et de l'action exécutée.

Aucun avis réel, capture, dossier, nom de client ou résultat identifiable ne sera publié comme exemple sans autorisation écrite préalable, vérification des droits des personnes concernées et occultation adaptée. Les exemples fictifs ou véritablement anonymisés sont préférables.

## 6. Données personnelles et conservation

Modes de collecte prévus : connexion Google Business Profile autorisée ou ajout manuel. Catégories envisagées : contenu d'avis, note, date, réponse, nom affiché, photo ou lien de profil si accessibles, métadonnées et justificatifs.

Cette liste est un inventaire potentiel, pas une autorisation de collecte globale. Pour chaque donnée : documenter finalité, base légale, nécessité, source, durée, droits des personnes et conditions Google. Ne pas conserver une photo, un identifiant ou un lien de profil si ce n'est pas nécessaire ou autorisé.

Règles commerciales décidées, à traduire dans un calendrier de conservation :
- pendant l'abonnement : données strictement nécessaires aux fonctions souscrites ;
- après résiliation : **30 jours** pour récupérer les données via un export ZIP à accès limité ;
- après ces 30 jours : suppression ou anonymisation des données opérationnelles, sous réserve des obligations légales et d'une purge documentée des sauvegardes ;
- sur demande expresse d'effacement : déclencher la suppression sans attendre les 30 jours, après vérification de la demande, sous réserve des données légalement conservables et des besoins de défense de droits.

En cas de demande d'effacement immédiat, prévenir que l'export ultérieur peut devenir impossible. Isoler les factures et pièces légalement conservables avec accès restreint. Définir séparément les délais de purge des sauvegardes, journaux et archives.

## 7. IA, sous-traitants et transferts

Des fournisseurs d'IA externes peuvent être utilisés pour analyser, classer, extraire, détecter des signaux, préparer des dossiers et proposer des réponses.

Règles décidées :
- masquage/pseudonymisation automatique des données personnelles non nécessaires avant transmission ;
- ne transmettre que les données nécessaires à la tâche ;
- interdiction contractuelle et paramétrage vérifiable empêchant l'utilisation des données client pour entraîner ou améliorer les modèles ;
- durée de conservation fournisseur limitée et documentée ;
- validation humaine avant toute action externe ;
- inventaire des fournisseurs, finalités, données, pays, sous-traitants ultérieurs, durées, contrats et mécanismes de transfert.

Si une table de correspondance ou les données originales permettent de retrouver l'auteur, le traitement est une **pseudonymisation**, pas une anonymisation irréversible. Ne pas promettre l'anonymat dans ce cas.

Stockage principal et sauvegardes prévus dans l'UE. Certains prestataires peuvent traiter des données hors UE si les transferts sont identifiés et encadrés par un mécanisme valide et des garanties appropriées. Distinguer lieu de stockage, accès support et lieu de traitement ; vérifier les faits dans les contrats et configurations.

## 8. Rôles RGPD et statistiques

Qualifier les rôles traitement par traitement :
- Review Défense responsable de traitement pour ses comptes, facturation, sécurité, support, prospection et relation commerciale ;
- client responsable de traitement et Review Défense sous-traitant lorsque les avis et dossiers sont traités uniquement sur instructions du client ;
- analyse distincte lorsque Review Défense détermine des finalités propres.

Les statistiques ne peuvent être réutilisées que si elles sont **effectivement anonymisées**, sans possibilité raisonnable d'identifier client, auteur d'avis ou autre personne. Pas de revente de données ou de statistiques réidentifiables. Tester et documenter l'anonymisation ; la pseudonymisation reste soumise au RGPD.

## 9. Offre, prix, paiement et facturation

Décisions commerciales :
- abonnements sans engagement ;
- formule mixte : abonnement et prestations complémentaires ;
- prestations complémentaires envisagées : audit de réputation, constitution d'un dossier de contestation, traitement approfondi d'un avis, accompagnement renforcé de dossiers complexes ;
- prix affichés en euros comme prix finaux TTC selon la page Tarifs ;
- paiement par PayPal et carte bancaire ;
- facture PDF automatique après chaque paiement, avec numérotation unique et chronologique ;
- résiliation volontaire : pas de remboursement au prorata de la période déjà payée ; accès jusqu'à la fin de la période payée, sous réserve des droits impératifs et recours en cas de défaillance ou d'erreur ;
- résiliation par e-mail à `contact.reviewdefense@gmail.com` ;
- échec de paiement non régularisé après **3 jours** : suspension de l'accès, sans résiliation automatique ;
- après régularisation : réactivation selon le processus prévu.

Le porteur souhaite bénéficier de la **franchise en base de TVA** au démarrage, sous réserve d'éligibilité et de confirmation après immatriculation. Les prix sont des prix finaux ; la mention fiscale et les règles applicables aux clients B2B d'autres États membres doivent être validées par un expert-comptable/fiscaliste. La franchise française ne règle pas automatiquement toutes les questions de TVA transfrontalière.

Avant validation des CGV, rapprocher la grille de prix, paliers, prestations, périodicités et options de la page Tarifs et de la configuration PayPal/carte. Ne pas recopier une ancienne grille sans vérification. Identifier le prestataire carte distinct de PayPal, s'il y en a un.

## 10. Résiliation, export et suppression

- Abonnements sans engagement.
- Résiliation demandée par e-mail à `contact.reviewdefense@gmail.com`.
- Accès jusqu'à la fin de la période payée.
- Export ZIP disponible 30 jours après résiliation.
- Suppression immédiate sur demande expresse, sous réserve des obligations légales et de la vérification de la demande.
- Suspension après impayé de 3 jours distincte de la résiliation.
- Confirmation écrite de la réception et de la date d'effet.

Les contrats doivent distinguer résiliation, suspension, désactivation, effacement et archivage légal. La procédure de résiliation par e-mail doit rester claire et ne pas créer d'obstacle disproportionné.

## 11. Sécurité

Mesures décidées ou souhaitées :
- 2FA obligatoire ;
- un compte par entreprise ;
- récupération sécurisée des comptes et protection des identifiants ;
- stockage et sauvegardes dans l'UE ;
- contrôle d'accès, journalisation, limitation des tentatives et gestion des incidents ;
- chiffrement en transit et au repos à vérifier ;
- sauvegardes, restauration, tests, purge et accès administrateur à documenter.

Ne pas affirmer qu'une mesure est déjà en production avant vérification du code, de l'infrastructure et des contrats.

## 12. Liste de contrôle avant lancement

### Identité
- [ ] Immatriculer l'EI via le Guichet unique.
- [ ] Vérifier identité officielle, SIREN, SIRET, extrait RNE, activité déclarée.
- [ ] Confirmer l'adresse professionnelle et les règles de publication de l'adresse personnelle.
- [ ] Confirmer le statut de Review Défense comme nom commercial/marque.
- [ ] Confirmer le régime de TVA et les obligations UE.
- [ ] Compléter les mentions légales et coordonnées officielles.

### Prestataires et infrastructure
- [ ] Obtenir raison sociale, adresse et contact juridique exacts d'eCloudService.
- [ ] Vérifier régions de stockage, sauvegardes, support et sous-traitants.
- [ ] Identifier le prestataire carte, e-mail, analytics, monitoring, OCR, IA, stockage et support.
- [ ] Obtenir les DPA, listes de sous-traitants, pays et mécanismes de transfert.

### Google et données
- [ ] Vérifier autorisations OAuth, API activées et validation éventuelle de l'application.
- [ ] Vérifier règles Google relatives à l'accès, l'affichage, la mise en cache, la conservation et la suppression.
- [ ] Vérifier la possibilité réelle de signalement automatisé.
- [ ] Définir les données d'auteur réellement nécessaires et les durées permises.
- [ ] Tester révocation d'accès Google et suppression des données associées.

### RGPD et IA
- [ ] Cartographie, bases légales, minimisation et durées.
- [ ] Registre, notices, procédure de droits, violations, conservation et effacement.
- [ ] DPA Article 28 adapté aux traitements réels.
- [ ] Vérifier nécessité d'une AIPD et désignation éventuelle d'un DPO.
- [ ] Prouver le masquage avant envoi IA et l'absence d'entraînement fournisseur.
- [ ] Valider transferts hors EEE et garanties.
- [ ] Qualifier les systèmes et obligations de transparence au titre de l'AI Act.

### Contrats, fiscalité et responsabilité
- [ ] Réviser CGU, CGV, politique de confidentialité, DPA, mentions légales et cookies.
- [ ] Définir pénalités de retard B2B et mentions de facture.
- [ ] Valider résiliation, suspension, remboursements et responsabilité.
- [ ] Rapprocher page Tarifs, PayPal, carte et factures.
- [ ] Valider TVA B2B intra-UE et facturation électronique selon le calendrier.
- [ ] Avis d'avocat sur la frontière logiciel / conseil juridique / représentation / recouvrement.
- [ ] Valider signalements, obligation de moyens et validation client.
- [ ] Vérifier marketing, témoignages et exemples de dossiers.

## 13. Mandat de revue pour l'avocat

Demander une revue de lancement, pas seulement une relecture :
1. qualification de l'activité et absence d'exercice d'une profession réglementée ;
2. conformité Google des collectes, stockages et signalements ;
3. RGPD : rôles, bases légales, minimisation, droits des auteurs d'avis, DPA, transferts et IA ;
4. AI Act : qualification du système et obligations applicables ;
5. CGU/CGV B2B : résiliation, suspension, remboursements, responsabilité et preuves ;
6. TVA et facturation B2B dans l'UE ;
7. mentions légales et immatriculation de l'EI ;
8. validation des pages publiques, du parcours de paiement et des consentements.

**Décision de publication :** aucun document légal ou contractuel ne doit être publié ni présenté comme définitif avant immatriculation, vérification des prestataires et de l'infrastructure, puis validation par l'avocat.