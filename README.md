# Review Defense

## Architecture cible

- `frontend/public` : pages marketing, composants publics, assets et styles.
- `frontend/auth` : connexion et inscription.
- `frontend/application` : espace client authentifié (dashboard, avis, analyse, dossiers, documents, facturation, paramètres).
- `backend` : API et services métier répartis par domaine.
- `database` : migrations, schémas et politiques PostgreSQL.
- `admin` : interfaces et opérations d'administration.
- `tests` : tests unitaires, intégration, sécurité et E2E.
- `docs` : documentation technique, juridique, sécurité et API.

## Compatibilité pendant la migration

Les répertoires historiques `src/`, `migrations/`, `frontend/src/` et les pages HTML historiques sont conservés temporairement. Ils restent les chemins d'exécution de référence tant que les imports, routes WSGI, serveur statique, migrations et workflows n'ont pas été basculés et testés. Les chemins modulaires ajoutés réutilisent les fichiers sources de référence sans changement fonctionnel ; ils constituent une étape de migration, pas encore une bascule d'exécution.

## Sources consolidées

- Frontend React et composants publics : `audit/muse-modular-20260930`.
- Workspace client : `frontend/client-admin-workspace`.
- Backend, migrations et tests : base `develop`.
- Documentation d'architecture et de recette : `tmp-commercial-rebuild` / `archive/pre-core-reset-2026-09-28`.

## Règles de migration

1. Ne pas supprimer les chemins historiques avant validation des dépendances et du déploiement.
2. Ne jamais dupliquer ni renuméroter une migration déjà exécutée.
3. Toute bascule inclut imports, routes, permissions, tests et configuration.
4. Toute évolution fonctionnelle passe les tests automatisés et une recette navigateur avant intégration à `main`.
