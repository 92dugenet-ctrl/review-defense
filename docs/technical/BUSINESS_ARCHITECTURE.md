# Architecture métier transversale — Review Defense

Ce document suit les données et les responsabilités à travers le frontend, l'API, les services métier, les intégrations et la persistance. Il décrit les chemins visibles dans la branche `develop`, sans supposer que tous les modules historiques sont raccordés au runtime.

## 1. Carte générale

```text
Navigateur React
  ├─ Router / RequireAuth / AppShell
  ├─ Pages Reviews, Cases, CaseDetail, Analysis, Notifications, Billing
  └─ services/api/client.ts
        │ HTTP + Bearer token
        ▼
wsgi.py → src/api_server.py (ReviewDefenseAPI)
  ├─ Authentification, rôle, organisation, validation HTTP, idempotence
  ├─ Services métier (Case*, evidence, billing, notifications)
  ├─ Adaptateurs d'intégration (Google Business Profile, PayPal, SMTP)
  └─ Repository applicatif
        │ transactions avec contexte organisation
        ▼
PostgreSQL + stockage objet des preuves
        │
        └─ Workers / files persistées pour les tâches différées
```

La règle de lecture est importante : le frontend déclenche et présente les opérations, l'API authentifie et autorise, les services appliquent les règles métier, les adaptateurs parlent aux systèmes externes et les repositories persistent l'état. Une page React ou un type TypeScript ne constitue pas une autorisation serveur.

## 2. Point d'entrée réellement utilisé

Le point d'entrée WSGI `wsgi.py` importe `create_app` depuis `src.api_server`. Cette factory construit `ReviewDefenseAPI`, qui centralise le routage HTTP `/v1`, l'identité de l'acteur, le contexte d'organisation, les contrôles de rôle, les limites de requête et la conversion des erreurs.

Les services sont assemblés dans le constructeur de `ReviewDefenseAPI`. Ils reçoivent les dépendances nécessaires (store, repository, audit) au lieu de traiter eux-mêmes le protocole HTTP. Le repository PostgreSQL est l'adaptateur de persistance de l'API ; il ne doit pas être confondu avec les services métier.

Le frontend React passe par `frontend/src/services/api/client.ts`. Le hook `useApi` simplifie l'état de chargement et d'erreur dans les pages. Le routeur protège l'espace applicatif avec `RequireAuth`, mais les permissions effectives sont contrôlées de nouveau côté API.

## 3. Parcours Google Business Profile → avis

Le parcours utilisateur visible dans l'API actuelle est :

1. Un membre autorisé démarre OAuth via les routes d'intégration Google.
2. L'API crée un state signé/temporisé et un vérificateur PKCE, conserve le contexte organisation/utilisateur et redirige vers Google.
3. Le callback échange le code contre des jetons ; les connexions et secrets sont conservés côté serveur.
4. L'API énumère les comptes et établissements associés à la connexion.
5. Le membre sélectionne un établissement ; l'API vérifie que le compte et le lieu appartiennent bien à cette connexion.
6. L'API lit les avis via `GoogleBusinessProfileClient`, les normalise en `ReviewContext` et les enregistre pour l'organisation.
7. Les pages Reviews et ReviewDetail lisent ensuite les routes `/v1/reviews`.

**Frontière Google :** le client importé par `src/api_server.py` est `src/google_business_profile.py`. Il est orienté authentification et lecture/synchronisation des avis. Les interfaces de mutation de ce module refusent la soumission de signalement et la réponse à un avis. Il ne faut donc pas décrire le parcours actuel comme une suppression automatique ou une réponse automatique à Google.

### Pipeline de notifications Google

Les modules `google_pubsub_receiver.py`, `google_sync_engine.py` et `postgres_sync.py` décrivent un pipeline distinct pour recevoir des notifications authentifiées, dédupliquer les événements, créer des travaux persistés et réconcilier les avis en arrière-plan.

Le récepteur Pub/Sub valide l'enveloppe et son identité, le repository de synchronisation enregistre le reçu et le travail, puis le moteur de synchronisation utilise le client Google pour relire les ressources. Ce chemin asynchrone doit être lu comme un ensemble de composants dédiés ; ne pas supposer qu'il est automatiquement déclenché par le simple chargement de la page Reviews.

## 4. Avis → dossier

Le parcours de création d'un dossier part d'un avis déjà importé :

```text
ReviewsPage / ReviewDetailPage
  └─ POST /v1/cases { review_id }
       ├─ API : session, rôle et organisation
       ├─ vérifie que l'avis existe dans cette organisation
       ├─ _idem(...) : protège les commandes rejouées
       └─ CaseLifecycleService.create(...)
            ├─ crée l'identité du dossier
            ├─ persiste le dossier si repository disponible
            └─ journalise la transition
```

Un dossier relie un avis à un espace de travail métier. `CaseService` reconstruit le contexte à partir du repository et du store ; `CaseLifecycleService` gère création et liste. La clé de lecture est toujours le couple organisation/dossier, pas un identifiant isolé.

Les pages Cases et CaseDetail consomment respectivement `/v1/cases` et `/v1/cases/{id}/workspace`. Le workspace rassemble les données nécessaires à l'écran : avis, preuves, éléments d'analyse, contradictions, décisions et traces disponibles.

## 5. Dossier → preuves → éléments factuels

Le dépôt d'une preuve suit ce parcours :

1. Le client envoie un fichier associé à un dossier existant via `POST /v1/evidence`.
2. L'API vérifie le dossier, les métadonnées, le format Base64 et les limites de taille.
3. `EvidenceVault` stocke les octets dans le stockage configuré et calcule les métadonnées d'intégrité (taille, empreinte SHA-256, clé objet).
4. Les métadonnées et faits associés sont enregistrés dans le contexte de l'organisation.
5. Si le type est pris en charge et qu'aucun fait n'a été fourni, `evidence_ocr.py` peut convertir le contenu en texte ; `evidence_extraction.py` propose alors des faits candidats.
6. Les faits extraits restent non vérifiés jusqu'à une action explicite de validation.

La séparation est fondamentale :
- le coffre conserve la pièce originale ;
- l'OCR produit du texte lisible ;
- l'extraction produit des suggestions ;
- la vérification humaine change l'état de confiance d'un fait ;
- la matrice de preuves met en relation les éléments et les points à examiner.

Une suggestion extraite n'est pas une preuve validée et ne doit pas être utilisée comme décision automatique. L'empreinte permet de contrôler l'intégrité du contenu ; elle ne garantit pas à elle seule l'authenticité de son origine.

## 6. Analyse, contradictions et revue humaine

L'analyse métier est organisée en plusieurs services spécialisés :

- `CaseEvidenceMatrixService` construit une vue des éléments disponibles par rapport au dossier.
- `CaseContradictionService` recherche des incohérences et conserve les constats/dispositions.
- `CaseReviewService` prépare la checklist et calcule la readiness à partir des éléments manquants et des tâches terminées.
- `CaseEscalationService` suit les échéances et niveaux d'escalade associés au SLA.

La readiness est un indicateur de préparation du dossier, pas une décision de fond. Une contradiction est un point à examiner, pas une preuve automatique de fraude ou d'irrégularité. Les services conservent les éléments et leurs états ; l'interface présente les résultats au membre autorisé.

## 7. Décision, gel et préparation de soumission

Le chemin décisionnel est distinct de l'analyse :

```text
Dossier et éléments examinés
  └─ CaseDecisionService.create(...)
       └─ crée une décision et sa justification
            └─ freeze(...)
                 ├─ produit une photographie figée du dossier
                 └─ attache l'empreinte de cette photographie
                      └─ approve(...)
                           └─ enregistre une approbation humaine
                                └─ CaseSubmissionService.prepare(...)
                                     └─ prépare un enregistrement local
```

Le gel fournit un instantané stable des informations qui ont servi à la décision. L'approbation conserve l'identité de la personne qui valide. La préparation de soumission crée un enregistrement local et matérialise la suite possible du processus.

**Limite externe :** `CaseSubmissionService` prépare localement la soumission ; son contrat actuel indique `external_call=False`. Ce service ne transmet pas un signalement à Google. Il faut garder cette frontière explicite dans les écrans, les textes commerciaux et les futures évolutions.

## 8. Notifications et tâches asynchrones

Les événements métier peuvent alimenter une outbox persistée. La création d'une notification et sa livraison sont deux étapes distinctes :

```text
Service métier / escalade
  └─ NotificationOutbox : enregistre un message et sa clé de déduplication
       └─ NotificationWorker : réserve un message et gère les tentatives
            └─ NotificationDelivery : remet au canal configuré
                 └─ statut, erreur et audit
```

Une notification créée n'est pas nécessairement livrée. Les états de réservation, les reprises et les délais permettent de gérer les erreurs sans faire dépendre la transaction métier d'un serveur SMTP. Les endpoints de consultation et les commandes de livraison/annulation restent soumis aux permissions API.

Les files de traitement suivent le même principe : un travail est créé avec son organisation, son type, son payload et sa clé d'idempotence ; un worker le réserve temporairement, exécute le handler et marque le résultat ou programme une reprise. Les workers sont des processus séparés du serveur HTTP.

## 9. Facturation et PayPal

Le catalogue et les droits fonctionnels sont décrits côté backend par `billing_service.py`. Les adaptateurs PayPal gèrent les échanges OAuth/REST et la vérification des webhooks.

La page Billing lit les offres et l'état de facturation via l'API, charge le SDK PayPal côté navigateur et transmet l'identifiant d'abonnement après approbation. Le navigateur ne décide pas de l'état final de l'abonnement : le backend doit vérifier les informations fournisseur et mettre à jour l'état de facturation. Les contrôles d'accès aux fonctions doivent s'appuyer sur les droits serveur, pas seulement sur l'affichage du menu.

## 10. Persistance, isolation et audit

Les responsabilités de stockage sont séparées :

| Composant | Données / rôle |
|---|---|
| `PostgresRepository` | Connexions, transactions et contexte tenant PostgreSQL |
| `PostgresAPIRepository` | Traduction des opérations applicatives en requêtes de persistance |
| `PostgresSyncRepository` | Reçus Pub/Sub, curseurs et travaux de synchronisation Google |
| `EvidenceVault` | Octets des pièces et métadonnées de stockage |
| `MemoryStore` | Cache/mode local et assemblage en mémoire ; ne remplace pas PostgreSQL partagé en production |
| Journal d'audit | Acteur, organisation, action, ressource et métadonnées de transition |

Les opérations multi-tenant doivent toujours transporter l'identifiant d'organisation. Les transactions PostgreSQL configurent un contexte local utilisé par les politiques de sécurité de la base. Les journaux d'audit expliquent qui a effectué une transition et sur quelle ressource ; ils ne remplacent pas les enregistrements métier.

## 11. Modules parallèles et chemins historiques

Plusieurs fichiers ont des noms ou des contrats proches. Avant de modifier un composant, rechercher ses imports et son instanciation :

- `src/api_server.py` est le serveur sélectionné par `wsgi.py`.
- `src/google_business_profile.py` est le client Google importé par ce serveur ; `src/google_integration.py` est une autre implémentation d'intégration et ne doit pas être déclarée active dans le parcours HTTP sans vérifier son appelant.
- `background_jobs.py` et `processing_jobs.py` fournissent des abstractions de files différentes ; les adapters PostgreSQL ont leur propre cycle de vie.
- `backend/api/api_server.py` est une implémentation parallèle historique, non sélectionnée par le point d'entrée WSGI courant.
- Les répertoires `backend/*` peuvent représenter une organisation cible ; leur présence ne prouve pas que les routes de production les importent.

Ne pas fusionner, déplacer ou supprimer ces modules sur la seule base de leur nom. Le graphe d'import réel et le point d'entrée d'exécution déterminent leur rôle.

## 12. Comment tracer une fonctionnalité de bout en bout

Pour toute évolution, suivre cette séquence :

1. **Écran** : identifier la page React et l'action utilisateur.
2. **Transport** : relever la méthode HTTP, l'URL et le payload dans le client API.
3. **Route** : trouver le bloc correspondant dans `src/api_server.py`.
4. **Sécurité** : identifier l'identité, le rôle, l'organisation, l'idempotence et les limites.
5. **Service** : suivre les règles métier et les transitions d'état.
6. **Adaptateur** : repérer les appels Google, PayPal, SMTP ou stockage objet.
7. **Persistance** : retrouver la méthode repository et les tables/migrations concernées.
8. **Asynchrone** : vérifier si un outbox, une file ou un worker prend le relais.
9. **Audit et affichage** : suivre les événements conservés et la réponse affichée au membre.

Ce chemin de lecture doit permettre de répondre à cinq questions pour chaque opération : qui l'a déclenchée, sur quelle organisation, quelles règles sont appliquées, quelles données changent et quels effets externes sont réellement exécutés.

## Index technique complémentaire

La cartographie exhaustive des fichiers, routes React, familles API, migrations et frontières runtime est disponible dans [TECHNICAL_MAP.md](./TECHNICAL_MAP.md).
