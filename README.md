# Review Defense

## Architecture réellement exécutée

Le dépôt contient une architecture cible organisée par domaines, mais les chemins
historiques restent encore au cœur de l'exécution. Il faut distinguer les répertoires
de destination des points d'entrée réellement utilisés.

### Backend et serveur HTTP

- `scripts/start_production.sh` : lance les contrôles de configuration, les migrations, puis Gunicorn.
- `wsgi.py` : point d'entrée WSGI chargé par Gunicorn ; distribue les requêtes vers le frontend public, le rendu SEO et l'API.
- `src/api_server.py` : composition de l'application API et de ses services métier.
- `src/production_config.py` et `src/deployment.py` : configuration et règles de démarrage/déploiement.
- `migrations/` : fichiers SQL réellement lus par `scripts/migrate.py`.

### Frontend

- `frontend/index.html` et les ressources historiques : page publique servie par la couche WSGI.
- `frontend/src/main.tsx` : point d'entrée React utilisé par la page `react.html`.
- `frontend/src/app/router.tsx` : routes de l'application React.
- `frontend/application/` : documentation et éléments historiques de transition ; ce dossier n'est pas la source React compilée par Vite.

### Infrastructure

- `Dockerfile` : compile le frontend avec Node puis assemble l'image Python d'exécution.
- `docker-compose.yml` : environnement local avec PostgreSQL.
- `docker-compose.staging.yml` : staging avec PostgreSQL, application privée et Caddy en reverse proxy TLS.
- `docker-compose.production.yml` : production avec PostgreSQL et application ; le proxy TLS est externe à cette stack.
- `Caddyfile` : configuration du reverse proxy utilisé par le Compose de staging.
- `.env.example` : inventaire indicatif des variables ; les secrets réels sont fournis par l'environnement.

## Compatibilité pendant la migration

Les répertoires historiques `src/`, `migrations/`, `frontend/src/` et les pages HTML
historiques sont conservés. Ils restent les chemins d'exécution de référence tant que
les imports, routes WSGI, serveur statique, migrations et déploiements n'ont pas été
basculés. Les chemins modulaires ajoutés constituent une étape de migration, pas
automatiquement une nouvelle source d'exécution.

## Règles de migration

1. Ne pas supprimer les chemins historiques avant d'avoir retracé leurs consommateurs.
2. Ne jamais dupliquer ni renuméroter une migration déjà appliquée.
3. Documenter les dépendances, les contrats de données et les effets de bord avant une extraction.
4. Préserver les routes, payloads JSON, statuts HTTP, permissions et effets de persistance.
5. Ne pas déplacer les fichiers actifs de déploiement sans adapter les chemins qui les invoquent.
