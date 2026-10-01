# Dossier juridique & RGPD — Review Défense

> **Statut : modèle de travail — NON VALIDÉ — NE PAS PUBLIER TEL QUEL.**  
> Version de travail : 0.1 — 1er octobre 2026. Périmètre : activité SaaS B2B exploitée depuis la France, hypothèse à confirmer.

## 1. Objet et limites

Ce dossier organise la conformité juridique de Review Défense : données personnelles, sécurité, sous-traitance, information des utilisateurs, contrats, cookies, prospection, gestion des droits et incidents. Il s'agit d'un audit documentaire et technique préliminaire du dépôt GitHub, pas d'une certification, d'un audit d'infrastructure en production ni d'un avis juridique d'avocat.

Les champs `[À COMPLÉTER]` sont des informations inconnues. Les formulations marquées **À CONFIRMER** ne doivent pas être présentées comme des garanties acquises. Aucun document ne doit être publié ou signé avant vérification avec les opérations réelles et validation juridique.

## 2. Résumé exécutif du dépôt examiné

Dépôt examiné : `92dugenet-ctrl/review-defense`, branche `main`, état consulté le 1er octobre 2026.

### Éléments repérés dans le code

- PostgreSQL 16 est déclaré dans le déploiement Docker de production ; une base persistante est configurée.
- Un volume persistant `/data/evidence` est déclaré pour les pièces justificatives.
- Le code prévoit comptes, organisations, rôles, sessions, invitations, authentification multifacteur et journaux d'événements.
- Une migration crée `privacy_requests` et `privacy_consents`, avec isolation par organisation au moyen de RLS.
- Des routes API existent pour exporter certaines données de compte, créer/lister/mettre à jour des demandes de droits et consulter/enregistrer des consentements.
- L'export actuellement visible couvre le compte, les demandes, les consentements et certains événements d'audit ; le code précise qu'il n'englobe pas automatiquement toutes les données métier de l'organisation.
- La configuration prévoit l'envoi d'e-mails SMTP pour vérification/récupération de compte.
- L'intégration Google Business Profile, la synchronisation, PayPal et le traitement de pièces justificatives apparaissent dans le dépôt.

### Écarts et inconnues importants

1. **Identité du responsable de traitement** : raison sociale, forme, adresse, SIREN/SIRET, TVA, représentant et contact vie privée non fournis.
2. **Régions d'hébergement et sauvegardes** : le dépôt décrit des volumes, mais ne prouve ni la localisation réelle du serveur, ni la localisation des sauvegardes, ni leur chiffrement, ni leur cycle d'effacement.
3. **Sous-traitants** : les contrats, lieux de traitement, sous-traitants ultérieurs et mécanismes de transfert de Google, PayPal, hébergeur, SMTP et autres fournisseurs doivent être collectés.
4. **Exercice des droits** : les routes repérées ne prouvent pas un parcours complet de vérification d'identité, d'orchestration d'effacement, de réponse, de suivi de délai et de traitement des données détenues pour le compte d'un client.
5. **Consentement** : une table et des endpoints existent, mais aucune preuve n'a été établie qu'un bandeau de cookies ou un gestionnaire de consentement conforme bloque effectivement les traceurs non essentiels.
6. **Durées de conservation** : aucune politique complète et validée de conservation, archivage, suppression et purge des sauvegardes n'a été démontrée.
7. **IA** : les fichiers d'environnement et dépendances examinés ne suffisent pas à identifier un fournisseur de modèle génératif. Il faut inventorier tout appel à un modèle, toute fonction d'IA et tout transfert de contenu client avant de rédiger des engagements.
8. **AIPD** : le besoin d'une analyse d'impact doit être évalué à partir des données, volumes, personnes, usages, risques et fonctionnalités réellement activés.
9. **Cookies et traceurs** : inventaire navigateur et tests réseau nécessaires ; ne pas supposer que seuls les cookies techniques sont présents.
10. **Documents contractuels** : CGU, CGV B2B, accord de sous-traitance, politique de confidentialité et mentions légales doivent être cohérents entre eux.

## 3. Cartographie provisoire des rôles

| Flux | Rôle probable de Review Défense | À confirmer |
|---|---|---|
| Création de compte, facturation, sécurité, support, prospection propre | Responsable de traitement | Finalités et moyens décidés par l'éditeur |
| Données d'avis, dossiers et preuves déposés par le client | Sous-traitant possible pour le compte du client | Le client détermine-t-il finalités et instructions ? Review Défense réutilise-t-il ces données ? |
| Données de connexion Google Business Profile | À qualifier traitement par traitement | Données reçues, permissions OAuth, durée, usage et rôles Google |
| Paiement PayPal | Review Défense responsable pour la gestion de la relation et de la facturation ; PayPal peut être responsable distinct pour ses traitements | Contrat, rôles exacts et données échangées |
| E-mails SMTP | Sous-traitant probable pour l'acheminement | Fournisseur, localisation, logs, rétention |
| Modèle d'IA éventuel | Sous-traitant ou responsable distinct selon le service et ses conditions | Fournisseur, région, réutilisation, rétention, DPA, transferts |

La qualification juridique dépend des faits et non du seul intitulé du contrat. Documenter le raisonnement pour chaque flux.

## 4. Plan d'action priorisé

| Priorité | Action | Preuve attendue |
|---|---|---|
| P0 | Compléter identité juridique et coordonnées | Extrait RNE/Kbis, SIREN, adresse, représentant |
| P0 | Inventorier tous les prestataires et flux | Liste contractuelle, DPA, régions, sous-traitants ultérieurs |
| P0 | Cartographier données, finalités, bases légales et destinataires | Registre article 30 complété |
| P0 | Définir rôles client/Review Défense et signer l'accord article 28 | DPA annexé aux CGV/contrat |
| P0 | Vérifier suppression, export, droits et sauvegardes | Tests reproductibles et procédures |
| P0 | Publier une politique de confidentialité fidèle au produit | Versions datées et preuve d'affichage |
| P1 | Mettre en place le consentement cookies si nécessaire | Scan de traceurs avant/après choix |
| P1 | Finaliser les durées de conservation | Matrice approuvée et jobs de purge testés |
| P1 | Formaliser sécurité et procédure de violation | Registre d'incidents, plan de réponse, exercice |
| P1 | Faire le screening AIPD et, si nécessaire, l'AIPD complète | Analyse signée et plan de réduction des risques |
| P1 | Qualifier l'usage de l'IA et l'AI Act | Inventaire modèles, notices et contrôles |
| P2 | Finaliser CGU, CGV, mentions légales et prospection | Validation avocat/comptable selon sujet |

## 5. Documents du dossier

- `01-registre-traitements.md` — registre provisoire des traitements.
- `02-politique-confidentialite.md` — modèle public à compléter.
- `03-accord-sous-traitance-rgpd.md` — annexe contractuelle article 28.
- `04-procedure-droits-personnes.md` — procédure d'exercice des droits.
- `05-procedure-violations-donnees.md` — procédure de gestion des violations.
- `06-conservation-effacement.md` — matrice de conservation et purge.
- `07-sous-traitants-transferts.md` — registre fournisseurs et transferts.
- `08-cookies-traceurs.md` — politique et spécification du gestionnaire de consentement.
- `09-mentions-legales.md` — modèle de mentions légales.
- `10-CGU-B2B.md` — conditions d'utilisation professionnelles.
- `11-CGV-B2B.md` — conditions de vente professionnelles.
- `12-screening-AIPD.md` — pré-évaluation de la nécessité d'une AIPD.
- `13-IA-et-transparence.md` — inventaire IA et obligations de transparence.
- `14-prospection-commerciale.md` — règles de prospection et opposition.

## 6. Références principales

- Règlement (UE) 2016/679 (RGPD), notamment articles 5, 6, 12 à 22, 24 à 28, 30, 32 à 35 et 44 à 49.
- Loi n° 78-17 du 6 janvier 1978 modifiée (Informatique et Libertés).
- Article 82 de la loi Informatique et Libertés et directive ePrivacy pour les traceurs.
- Loi n° 2004-575 du 21 juin 2004 (LCEN), notamment les mentions d'identification applicables.
- Code de commerce et Code de la consommation selon la clientèle et les modalités de vente.
- Règlement (UE) 2024/1689 (AI Act), si des systèmes d'IA entrent dans son champ.

## 7. Règle de mise à jour

Chaque changement de finalité, donnée collectée, fonctionnalité, prestataire, région d'hébergement, durée, destinataire ou technologie doit déclencher une revue du registre, de la politique de confidentialité, du DPA et, le cas échéant, de l'AIPD. Conserver un historique des versions et la date d'entrée en vigueur.
