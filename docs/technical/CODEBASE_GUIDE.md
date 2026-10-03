# Guide de lecture du code — Review Defense

> Branche de référence : `develop`
>
> Ce guide explique comment se repérer dans le dépôt. Les explications de détail
> doivent également se trouver dans les fichiers sources, au plus près des blocs concernés.

## Architecture réellement exécutée

Le projet comporte des zones de destination et des chemins historiques encore actifs.
Ne pas supposer qu'un répertoire modulaire est automatiquement le code exécuté.

| Élément | Rôle dans l'exécution |
| --- | --- |
| `scripts/start_production.sh` | Contrôle la configuration, applique les migrations, puis lance Gunicorn. |
| `scripts/production_check.py` | Vérifie les prérequis de production avant le démarrage. |
| `scripts/migrate.py` | Applique les fichiers `migrations/*.sql` dans PostgreSQL. |
| `wsgi.py` | Route les requêtes HTTP vers SEO, fichiers frontend, API et endpoints opérationnels. |
| `src/api_server.py` | Construit l'application API et ses services. |
| `src/production_config.py` | Charge les paramètres de l'application et valide les prérequis runtime. |
| `src/deployment.py` | Décrit l'URL publique, la confiance proxy et les en-têtes de sécurité. |
| `frontend/src/main.tsx` | Monte l'application React dans le navigateur. |
| `frontend/vite.config.ts` | Configure les entrées HTML, l'alias de sources et la compilation React. |
| `Dockerfile` | Compile les ressources frontend et construit l'image backend Python. |
| `docker-compose*.yml` | Décrit les services PostgreSQL, application et proxy selon l'environnement. |

## Parcours de démarrage en production

```text
Docker / plateforme
  └─ Dockerfile : image Python + frontend compilé
      └─ scripts/start_production.sh
          ├─ scripts/production_check.py
          │   ├─ src.production_config.ProductionConfig
          │   └─ src.deployment.DeploymentConfig
          ├─ scripts/migrate.py
          │   └─ migrations/*.sql → PostgreSQL
          └─ Gunicorn
              └─ wsgi:app
                  ├─ src.api_server.create_app
                  ├─ src.seo_site (pages SEO)
                  └─ frontend/ (ressources et shells web)
```

## Parcours de démarrage React

```text
Vite / build frontend
  └─ frontend/react.html
      └─ frontend/src/main.tsx
          ├─ AuthProvider
          ├─ RouterProvider
          └─ styles globaux
```

Le frontend React et les pages HTML historiques coexistent. Le routage WSGI
et les entrées Vite ne sont pas un seul et même mécanisme.

## Répertoires du dépôt

| Répertoire | Rôle |
| --- | --- |
| `frontend/` | Interface web, ressources publiques, espace applicatif et code React. |
| `src/` | Implémentation Python actuellement importée par WSGI. |
| `backend/` | Organisation cible par domaines et points de compatibilité ; vérifier chaque import avant usage. |
| `database/` | Documentation et organisation cible du schéma. |
| `migrations/` | Migrations SQL lues par le script opérationnel. |
| `admin/` | Interfaces et fonctions réservées à l'administration. |
| `docs/` | Documentation fonctionnelle, technique, juridique et sécurité. |
| `.github/workflows/` | Automatisations GitHub Actions. |
| `infrastructure/` | Documentation et zones cibles d'organisation de l'infrastructure. |
| `monitoring/` | Configuration de supervision. |
| `scripts/` | Démarrage, migration, maintenance et opérations. |

## Comment lire une fonctionnalité

1. Repérer la page ou le composant dans le frontend réellement utilisé.
2. Suivre l'appel au client HTTP et les données transmises.
3. Retrouver la route API dans l'application WSGI/API.
4. Suivre les services métier appelés et les règles qu'ils appliquent.
5. Identifier le repository ou le stockage qui lit et écrit les données.
6. Relier les opérations aux tables et migrations SQL correspondantes.
7. Vérifier les autorisations et les effets de bord aux frontières des modules.

## Configuration

Les variables sont fournies par l'environnement d'exécution, généralement Docker/Compose
ou la plateforme d'hébergement. `.env.example` donne un modèle, pas des secrets utilisables.
Les modules `src/production_config.py`, `src/deployment.py` et `src/config.py`
ont des responsabilités distinctes : lire leurs commentaires avant de modifier une variable.

## Convention de documentation dans le code

- **Fichier** : rôle, périmètre, point d'entrée et relations importantes.
- **Classe** : responsabilité, données portées et dépendances.
- **Fonction** : objectif, paramètres, résultat, effets de bord et erreurs.
- **Bloc non évident** : raison de l'ordre des opérations, règle métier ou contrainte.
- **Flux inter-modules** : origine des données, transformation, destination et sécurité.

Les commentaires doivent expliquer l'intention et les liens, pas reformuler chaque ligne.
Ne pas inventer de comportement ni documenter de secrets. Pour les fichiers générés,
documenter la source ou la commande de génération plutôt que le résultat compilé.

## Contrôle de documentation

Les modifications de ce chantier sont documentaires. La revue porte sur les différences Git,
les imports et références visibles, la cohérence des chemins, les commentaires et les longueurs
de lignes. Aucun test, build, suite de tests ou workflow de test ne doit être exécuté.


## Architecture métier transversale

Pour suivre les parcours complets entre l'interface, l'API, les services métier, les intégrations et la persistance, consulter [BUSINESS_ARCHITECTURE.md](./BUSINESS_ARCHITECTURE.md). Ce document décrit notamment le parcours Google → avis → dossier → preuves → analyse → validation humaine → préparation locale, ainsi que les frontières des notifications, workers et paiements.

## Cartographie technique exhaustive

Pour l'inventaire des fichiers Python, TypeScript et SQL, les routes React, les familles d'API et les différences entre arborescences historiques et chemins actifs, consulter [TECHNICAL_MAP.md](./TECHNICAL_MAP.md).

## Traçabilité des dépendances

Pour suivre les appels entre les pages React, les routes API, les services métier, les intégrations, les repositories et les tables SQL, consulter [DEPENDENCY_MAP.md](./DEPENDENCY_MAP.md).
