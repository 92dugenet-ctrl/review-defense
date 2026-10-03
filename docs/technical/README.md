# Documentation technique — Review Defense

Cette documentation décrit le code présent et les chemins d'exécution observés. Les répertoires d'architecture cible et les copies historiques ne doivent pas être considérés comme du code runtime actif sans vérifier leurs consommateurs.

## Guides de lecture

- [Guide de lecture du code](./CODEBASE_GUIDE.md) — points d'entrée, structure et conventions.
- [Architecture métier transversale](./BUSINESS_ARCHITECTURE.md) — flux entre frontend, API, services, intégrations et persistance.
- [Guide d'exploitation](./OPERATIONS_GUIDE.md) — configuration, démarrage, migrations et workers.
- [Audit de cohérence configuration/déploiement](./UNIFIED_DEPLOYMENT_CONFIGURATION_AUDIT.md) — variables, injection Compose, proxy, workers, certification et workflows.
- [Cartographie technique exhaustive](./TECHNICAL_MAP.md) — inventaire des sources, routes, API et migrations.
- [Traçabilité des dépendances](./DEPENDENCY_MAP.md) — relations entre pages, endpoints, services, intégrations et repositories.
- [Audit des modules inutilisés et redondants](./UNUSED_AND_REDUNDANT_MODULES_AUDIT.md) — arborescences parallèles, duplications, candidats à arbitrage et limites des conclusions statiques.
- [Audit du cycle de vie des données](./DATA_LIFECYCLE_AUDIT.md) — migrations, sauvegardes PostgreSQL, preuves, isolation tenant, conservation et effacement.
- [Audit des suppressions et de l'intégrité référentielle](./DELETION_INTEGRITY_AUDIT.md) — cascades SQL, références orphelines potentielles, suppressions de comptes et organisations, preuves et effacement.

## Règles de maintenance

- Un module absent du chemin WSGI principal n'est pas automatiquement inutilisé.
- Examiner imports dynamiques, scripts, workflows, URLs statiques et commandes d'hébergement avant suppression.
- Ne pas synchroniser automatiquement les migrations SQL : comparer noms, contenus, runners et historique de base.
- Conserver les parcours HTML historiques et React tant que le routage de production n'a pas basculé explicitement.
- Toute suppression doit être ciblée et justifiée par l'absence de consommateurs.
- Ne pas confondre clôture administrative d'une demande d'effacement et preuve d'exécution technique de toutes les suppressions.

## Contrôle

La revue documentaire porte sur les diffs, l'arbre Git, les imports et références statiques. Aucun test, build, typecheck ou workflow de test ne doit être exécuté.
