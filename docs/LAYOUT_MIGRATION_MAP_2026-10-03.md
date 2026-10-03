# Layout de develop — carte de migration

Date de référence : 3 octobre 2026.

## Organisation fonctionnelle

- `frontend/public/` : composants, pages, styles et assets publics React en cours de structuration.
- `frontend/auth/` : contexte et garde d'authentification React.
- `frontend/application/` : console React, pages, composants, hooks, services et types.
- `frontend/assets/` et les pages HTML historiques : assets et interface statique encore servis par WSGI.
- `backend/` : organisation modulaire par domaines, sans bascule automatique de l'exécution.
- `src/` : modules backend actuellement importés par l'application WSGI.
- `database/` : organisation cible des schémas et politiques.
- `migrations/` : répertoire réellement chargé par `scripts/migrate.py`.
- `admin/` : interfaces et domaines d'administration.
- `infrastructure/` : zone de destination documentée pour Docker, déploiement, serveur, monitoring et environnements.
- `tests/` : tests unitaires, intégration, sécurité et E2E.
- `docs/` : contrats d'architecture, API, sécurité, exploitation et produit.

## Chemins de production à ne pas casser

1. `wsgi.py` reste l'entrée WSGI.
2. `src.api_server.create_app` reste la fabrique API active.
3. `src/seo_site.py` conserve le rendu des routes SEO publiques.
4. `frontend/workspace.html`, `workspace.js` et `workspace.css` conservent le workspace historique servi par les routes espace.
5. `frontend/assets/` reste le répertoire statique utilisé par le WSGI actuel.
6. `scripts/start_production.sh` conserve les contrôles, migrations puis Gunicorn sur le port 8080 par défaut.
7. `scripts/migrate.py` continue de lire `migrations/*.sql`.

## Séquence de migration

- Étape 1 — organisation et documentation des frontières, sans déplacement de code.
- Étape 2 — inventaire des imports et dépendances par domaine.
- Étape 3 — extraction atomique d'un domaine à la fois, avec compatibilité des imports.
- Étape 4 — raccordement progressif du build React et du serveur statique après parité fonctionnelle.
- Étape 5 — retrait des anciens chemins uniquement après vérification des routes, déploiements, migrations et consommateurs.

## Hors périmètre de cette étape

Aucun changement de port, WSGI, route, schéma SQL, migration, secret, fournisseur externe, rôle ou comportement métier. Aucun dossier historique n'est supprimé.
