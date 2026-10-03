# Guide de lecture du code — Review Defense

> Branche de référence : `develop`
>
> Les explications de détail doivent se trouver dans les fichiers sources, au plus près des blocs concernés.

## Architecture réellement exécutée

| Élément | Rôle |
| --- | --- |
| `scripts/start_production.sh` | Contrôle la configuration, applique les migrations, lance Gunicorn. |
| `scripts/production_check.py` | Vérifie les prérequis de production. |
| `scripts/migrate.py` | Applique `migrations/*.sql`. |
| `wsgi.py` | Route HTTP vers SEO, frontend, API et endpoints opérationnels. |
| `src/api_server.py` | Construit l'application API courante. |
| `src/production_config.py` | Charge et valide la configuration runtime. |
| `src/deployment.py` | Décrit URL publique, proxy et en-têtes de sécurité. |
| `frontend/src/main.tsx` | Monte React depuis `react.html`. |
| `frontend/vite.config.ts` | Configure les deux entrées HTML, alias et Vite. |

## Démarrage production

```text
scripts/start_production.sh
  → scripts/production_check.py
  → scripts/migrate.py → migrations/*.sql
  → Gunicorn → wsgi:app
      ├─ src.api_server.create_app
      ├─ src.seo_site
      └─ frontend/ (pages et ressources web)
```

## Deux parcours frontend

- `frontend/index.html` : site HTML historique servi à la racine par WSGI.
- `frontend/react.html` : shell React qui charge `src/main.tsx`, puis `AuthProvider` et `RouterProvider`.

Le routage WSGI, le rendu SEO, les pages statiques historiques et les routes React sont des mécanismes distincts. Voir [l'audit frontend](../../frontend/src/DEPENDENCY_AUDIT.md).

## Répertoires

| Répertoire | Rôle |
| --- | --- |
| `frontend/` | Site, ressources publiques, workspace historique et application React. |
| `src/` | Implémentation Python importée par le WSGI courant. |
| `backend/` | Arborescence parallèle par domaines et points de compatibilité ; vérifier chaque import. |
| `database/` | Schéma et organisation documentaire cible ; ne pas présumer que ses migrations sont celles du démarrage. |
| `migrations/` | SQL lu par `scripts/migrate.py`. |
| `admin/` | Interfaces et fonctions réservées à l'administration. |
| `docs/` | Documentation fonctionnelle, technique, juridique et sécurité. |
| `.github/workflows/` | Automatisations GitHub Actions. |
| `scripts/` | Démarrage, migration, maintenance et opérations. |

## Comment lire une fonctionnalité

1. Repérer la page dans le frontend réellement servi.
2. Suivre le client HTTP et les données transmises.
3. Retrouver la route dans `src.api_server`.
4. Suivre les services métier et leurs règles.
5. Identifier repository et stockage.
6. Relier les opérations aux migrations réellement appliquées.
7. Vérifier workers, scripts, imports indirects et frontières de sécurité.

## Convention de documentation

- **Fichier** : rôle, périmètre, entrée et relations importantes.
- **Classe** : responsabilité, données et dépendances.
- **Fonction** : objectif, paramètres, résultat, effets et erreurs.
- **Bloc non évident** : raison de l'ordre des opérations, règle ou contrainte.
- **Flux inter-modules** : origine, transformation, destination et sécurité.

Les commentaires doivent expliquer l'intention et les liens, pas reformuler chaque ligne.

## Avant de déclarer un module inutilisé

Consulter [l'audit des modules inutilisés et redondants](./UNUSED_AND_REDUNDANT_MODULES_AUDIT.md). L'absence d'import direct ne prouve pas l'absence d'usage : examiner scripts, imports dynamiques, routes, HTML, CSS, workflows et configurations d'hébergement.

## Contrôle documentaire

La revue porte sur les diffs, imports et références visibles, chemins, commentaires et longueurs de lignes. Aucun test, build, typecheck, suite de tests ou workflow de test ne doit être exécuté.

Pour les flux métier, consulter [BUSINESS_ARCHITECTURE.md](./BUSINESS_ARCHITECTURE.md) ; pour les liens entre pages, endpoints, services et repositories, consulter [DEPENDENCY_MAP.md](./DEPENDENCY_MAP.md).
