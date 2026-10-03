# API et composition

## Responsabilité cible

Regrouper la composition HTTP, la configuration applicative, les adaptateurs transverses et les composants d'exploitation qui ne relèvent pas d'un domaine métier.

## Fichiers présents

- `api_server.py`, `app.py`, `app_shell.py` : composition et assemblage de l'application.
- `config.py`, `deployment.py`, `production_config.py` : configuration et déploiement.
- `database.py`, `postgres_*.py`, `migration_runner.py` : persistance et intégration PostgreSQL.
- `background_jobs.py`, `processing_jobs.py`, `e2e_pipeline.py` : orchestration des traitements.
- `errors.py`, `observability.py`, `resilience.py` : erreurs, supervision et résilience.
- `privacy_service.py`, `business_calendar.py`, `operations_ui.py`, `seo_*.py` : services transverses actuellement rangés ici.

## Source exécutée

Le point d'entrée WSGI utilise `src.api_server.create_app`. Les fichiers de ce dossier sont une organisation cible / un miroir transitoire et ne doivent pas être considérés comme activés.

## Frontières à respecter

- L'API orchestre les domaines; elle ne doit pas devenir propriétaire de toute la logique métier.
- Les contrôles d'authentification, d'autorisation et de tenant restent côté serveur.
- Préserver routes, méthodes, statuts, enveloppes JSON, erreurs et middleware.
- Les migrations actives sont lues depuis `migrations/` par le runner actuel; ne pas déplacer ce chemin dans cette étape.

## État

Aucune bascule runtime. Avant toute extraction, comparer chaque module à son équivalent `src/` et vérifier les imports relatifs, notamment les références inter-domaines.
