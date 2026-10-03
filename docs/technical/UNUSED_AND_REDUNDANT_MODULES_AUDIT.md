# Lot K — Audit des modules inutilisés, parallèles et redondants

> Branche : `develop` — commit de référence : `d8229d943d15945e798e319165cccd2caf9125cc`.  
> Audit statique de l'arbre Git, des points d'entrée, imports visibles, routes et configurations.  
> **Aucune suppression, aucun déplacement et aucune modification du comportement applicatif.**

## 1. Niveaux de certitude

- **Actif confirmé** : raccordement direct observé depuis un point d'entrée, une route ou un composant consommateur.
- **Compatibilité / historique raccordé** : ancien nom ou ancien parcours qui délègue encore vers le runtime ou reste servi.
- **Parallèle confirmé** : autre implémentation ou arborescence existante, non sélectionnée par le point d'entrée de production examiné.
- **Candidat à arbitrage** : usage non retrouvé dans le chemin principal ; les usages indirects et externes doivent encore être exclus.
- **Non démontré** : les éléments statiques ne permettent pas de conclure.

L'absence d'import direct n'est jamais une preuve suffisante de code mort : les scripts, imports dynamiques, HTML, CSS, workflows, commandes d'hébergement et consommateurs externes comptent aussi.

## 2. Synthèse

| Zone | Constat confirmé | Décision |
|---|---|---|
| Backend | WSGI importe `src.api_server.create_app`; une autre API existe dans `backend/api/api_server.py`. | `src/` est la référence runtime courante. Ne pas supprimer `backend/` en bloc. |
| Compatibilité | `backend/api/app.py` réexporte `wsgi.app`. | Alias raccordé, à conserver tant que ses consommateurs externes ne sont pas exclus. |
| Frontend | `index.html` et `react.html` sont deux entrées ; WSGI sert HTML/SEO et ressources historiques. | Conserver les deux parcours jusqu'à migration explicite des URLs. |
| Assets | 62 chemins identiques entre `frontend/assets/` et `frontend/public/assets/`, mais des fichiers spécifiques à chaque arbre. | Pas de suppression globale ; contrôler les URLs WSGI et Vite. |
| Migrations | 29 fichiers identiques entre les deux répertoires, un fichier divergent et cinq migrations supplémentaires dans `migrations/`. | Le script de démarrage lit `migrations/`. Ne pas synchroniser automatiquement. |
| Google | L'API importe `src.google_business_profile`; `src.google_integration.py` est une autre implémentation. | Conserver le raccordement confirmé ; arbitrer le module parallèle plus tard. |
| Jobs | Files SQLite, adaptateurs PostgreSQL et workers de notification ont des contrats différents. | Ne pas fusionner sans tracer producteurs, tables et consommateurs. |
| Lancements | `main.py`, `start.py` et `bot.py` convergent vers `wsgi:app`. | Wrappers alternatifs/plateforme, pas des applications métier distinctes. |

## 3. Backend : chemin actif et copie parallèle

Le chemin de production confirmé est :

```text
scripts/start_production.sh
  → scripts/production_check.py
  → scripts/migrate.py
  → Gunicorn / wsgi:app
  → src.api_server.create_app()
  → services métier, repositories et intégrations
```

`wsgi.py` importe explicitement `create_app` depuis `src.api_server`. C'est la référence à suivre pour une modification de l'API de production actuelle.

`backend/` regroupe des modules par domaines : `api/`, `authentication/`, `billing/`, `cases/`, `notifications/`, `reviews/` et `analysis/`. Leurs noms recoupent ceux de `src/`, mais les fichiers ne sont pas une copie byte à byte générale.

- `backend/api/api_server.py` est une implémentation parallèle ; le WSGI courant ne l'importe pas.
- `backend/api/app.py` importe `app` depuis `wsgi` et l'expose aussi sous `application`. C'est un alias de compatibilité, pas une deuxième application.
- Les modules classés sous `backend/` ne deviennent pas actifs parce qu'ils sont rangés par domaine.
- Des usages indirects, scripts ou déploiements secondaires peuvent toutefois exister.

**Décision :** garder les deux arbres en place. Une étape ultérieure devra qualifier chaque module backend : extraction en cours, référence cible, compatibilité, ancien code ou module appelé indirectement. Ne pas supprimer sur la seule base de l'absence d'import depuis WSGI.

## 4. Frontend : deux parcours

### Site HTML historique / SEO

Le WSGI importe `src.seo_site` et rend les pages SEO reconnues. La racine `/` sert `frontend/index.html`. Ce document charge les scripts et styles historiques et contient des liens vers les anciennes URLs. Le WSGI sert aussi certains chemins applicatifs via `workspace.html`.

### Application React

`frontend/react.html` fournit `#root` et charge `src/main.tsx`. Celui-ci monte `AuthProvider` et `RouterProvider`. Le routeur est `frontend/src/app/router.tsx`.

Routes déclarées : pages marketing (`/`, `/produit`, `/fonctionnement`, `/securite`, `/tarifs`, `/contact`), pages légales, compte (`/login`, `/register`) et espace protégé `/app/*` (dashboard, avis, dossiers, analyse, notifications, facturation, paramètres, confidentialité, administration). Une route de repli affiche `NotFoundPage`.

Les composants de sections ne sont pas des routes : ils sont composés par les pages. Exemples confirmés :
- `HomePage` → `MuseShell` et `HomeBlocks` → sections `home/*` ;
- `MuseShell` → en-tête, pied de page, styles Muse et hook de mouvement ;
- `main.tsx` → contexte d'authentification et routeur ;
- pages protégées → `AppShell` et client API partagé.

Un composant absent directement de `router.tsx` peut être un enfant, layout, hook, type ou service. Ne pas le classer orphelin sur cette seule lecture.

### Duplications d'assets

Comparaison des blobs Git par chemin relatif :
- 62 chemins identiques dans `frontend/assets/` et `frontend/public/assets/` ;
- 1 chemin commun divergent : `README.md` ;
- 27 chemins uniquement dans `frontend/assets/` ;
- 1 chemin uniquement dans `frontend/public/assets/` : `js/public.js`.

Le WSGI sert explicitement `/assets/*` depuis `frontend/assets/`. Vite utilise `frontend/public/` comme répertoire public de l'application compilée. Des contenus identiques ne signifient donc pas que les chemins de livraison sont interchangeables.

**Décision :** conserver les deux parcours web et les arbres d'assets jusqu'à une migration explicite des URLs, du rendu SEO et des ressources.

## 5. Migrations SQL : duplication partielle

`scripts/migrate.py` calcule `ROOT / "migrations"` et lit `migrations/*.sql`. C'est le répertoire opérationnel confirmé par ce script.

| Comparaison par nom | Nombre |
|---|---:|
| SQL identiques entre les deux arbres | 29 |
| SQL commun mais divergent | 1 |
| SQL seulement dans `migrations/` | 5 |
| README seulement dans `database/migrations/` | 1 |

Fichier divergent : `029_v643_processing_architecture.sql`.

Fichiers uniquement dans `migrations/` :
- `023_v70_paypal_billing.sql`
- `031_v641_client_monitoring_hub.sql`
- `032_v641_google_oauth_state_callback_rls.sql`
- `033_v645_client_hub_force_rls.sql`
- `034_v646_force_privacy_billing_rls.sql`

`src/migration_runner.py` est un runner distinct : il dérive la version du préfixe numérique et vérifie les checksums. Il n'est pas le script appelé par le démarrage décrit ici. À l'inverse, `scripts/migrate.py` utilise le nom complet du fichier comme identifiant de version.

**Décision :** ne pas fusionner, synchroniser ou supprimer un arbre avant d'avoir choisi le runner de chaque environnement et vérifié l'historique réel du schéma. La différence SQL ne doit pas être écrasée.

## 6. Google : adaptateurs parallèles

`src/api_server.py` importe explicitement les classes Google depuis `src.google_business_profile.py`. C'est le raccordement confirmé au niveau de l'API.

`src/google_integration.py` contient une autre implémentation OAuth/REST, avec ses propres abstractions de stockage de jetons et de transport. Elle n'est pas interchangeable avec `google_business_profile.py`.

Le flux de synchronisation est encore distinct : réception/authentification Pub/Sub, enregistrement des événements, curseurs, planification de jobs et réconciliation des avis.

**Décision :** garder `google_business_profile.py` comme dépendance confirmée. Classer `google_integration.py` comme candidat à arbitrage ; vérifier imports indirects, anciens flux OAuth, scripts et configurations externes avant toute décision.

## 7. Files de jobs et workers

| Module | Rôle observé | Relation |
|---|---|---|
| `src/background_jobs.py` | File SQLite générique : états, priorité, idempotence, baux | Ses types/états sont réutilisés par `src/postgres_sync.py` |
| `src/processing_jobs.py` | File SQLite de traitements avec événements et corrélation | Contrat distinct |
| `src/postgres_sync.py` | Événements Google, curseurs et file PostgreSQL | Domaine synchronisation |
| `src/postgres_processing.py` | Adaptateur PostgreSQL de traitements | Utilisé par `scripts/worker.py` |
| `src/notification_worker.py` | Worker de notification applicatif | Utilisé par `NotificationService` |
| `src/postgres_notification_worker.py` | Worker PostgreSQL de l'outbox | Réservation SQL et livraison |

`scripts/worker.py` assemble `PostgresProcessingQueue` et exécute un traitement. Il importe aussi `PostgresNotificationWorker`, mais le chemin visible dans ce script ne confirme pas à lui seul que ce worker est démarré par cet entrypoint.

**Décision :** ne pas fusionner ces systèmes. Pour chacun, tracer producteur, table, type de job, processus consommateur, retries, idempotence, tenant et supervision.

## 8. Points d'entrée de compatibilité

| Fichier | Rôle | Classement |
|---|---|---|
| `wsgi.py` | Routeur HTTP de production | Actif confirmé |
| `main.py` | Lance Gunicorn sur `wsgi:app` | Lanceur alternatif |
| `start.py` | Lance Gunicorn sur `wsgi:app`, avec `SERVER_PORT` / `PORT` | Lanceur alternatif |
| `bot.py` | Adaptateur eCloudServ vers `wsgi:app` | Compatibilité plateforme |
| `backend/api/app.py` | Réexport de `wsgi.app` | Alias de compatibilité |

Ils convergent vers le même WSGI et peuvent répondre à des conventions d'hébergement différentes. Vérifier la commande configurée sur chaque plateforme avant retrait.

## 9. Candidats à arbitrage — pas des suppressions proposées

| Candidat | Vérifications nécessaires |
|---|---|
| `backend/api/api_server.py` et modules associés | Imports de scripts, déploiements secondaires, outils d'exploitation, consommateurs externes, extraction en cours |
| `src/google_integration.py` | Imports indirects, workers, scripts, ancien OAuth et variables d'environnement |
| `src/processing_jobs.py` | Usages locaux, scripts et consommateurs dynamiques |
| `src/postgres_notification_worker.py` | Commandes de plateforme, processus réellement lancé et autres consommateurs |
| `database/migrations/` | Runner des environnements secondaires et état du schéma |
| `frontend/public/assets/` | URLs Vite, ressources générées et chemins statiques |
| `main.py`, `start.py`, `bot.py` | Configuration réelle de chaque hébergeur |
| Composants React non déclarés comme routes | Imports depuis pages/layouts, imports dynamiques, CSS et HTML |

## 10. Ordre de rationalisation

1. Confirmer les points d'entrée configurés sur chaque environnement.
2. Décider du rôle cible de `backend/` par module.
3. Tracer les producteurs/consommateurs des files de jobs.
4. Choisir le runner SQL et la source canonique des migrations.
5. Cartographier les URLs historiques, SEO, workspace et assets avant une bascule frontend.
6. Traiter chaque suppression ultérieure dans un changement séparé, justifié par l'absence de consommateurs et la migration de ses responsabilités.

## 11. Limites et conclusion

L'audit porte sur l'arbre Git et les raccordements statiques visibles sur `develop`. Les imports dynamiques, variables d'environnement, commandes configurées hors dépôt, appels externes et chemins d'exécution conditionnels peuvent ne pas être visibles. Les fichiers SQL ont été comparés par blob Git, sans exécuter leur effet sur une base.

Il existe des implémentations parallèles et des duplications partielles confirmées, mais pas de preuve suffisante pour déclarer globalement des fichiers supprimables. Les chemins confirmés à préserver sont le WSGI, `src.api_server`, les migrations lues par `scripts/migrate.py`, et les parcours web qui continuent d'être servis.

**Aucun test, build, typecheck, commande de certification, workflow ou test navigateur n'a été exécuté.** L'audit repose uniquement sur la lecture du dépôt, de l'arbre Git et des références statiques.
