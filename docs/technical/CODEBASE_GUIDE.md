# Guide de lecture du code — Review Defense

> Branche de référence : `develop`
>
> Ce document sert de carte d'orientation. Les explications détaillées doivent également
> être placées dans les fichiers sources, au plus près des fonctions et des blocs concernés.

## Comment lire le dépôt

Review Defense est organisé en plusieurs couches. Pour comprendre un parcours fonctionnel,
il faut suivre la donnée depuis l'interface jusqu'à l'API, puis aux services métier et au stockage.

| Répertoire | Rôle |
| --- | --- |
| `frontend/` | Interface web : pages publiques, console applicative, ressources CSS/JS, authentification et client API. |
| `backend/` | Services applicatifs : API, authentification, dossiers, avis, analyse, facturation, notifications et intégrations. |
| `database/` | Schéma relationnel et migrations SQL qui font évoluer la structure persistée. |
| `admin/` | Écrans et fonctions réservés à l'administration. |
| `docs/` | Documentation fonctionnelle, technique, sécurité et procédures de validation. |
| `.github/workflows/` | Automatisations GitHub Actions : intégration continue, builds, contrôles et déploiements. |
| `infrastructure/` | Configuration et ressources nécessaires à l'exécution et à l'exploitation. |
| `monitoring/` | Configuration de supervision et de collecte de métriques. |
| `scripts/` | Scripts d'exploitation, de maintenance ou de contrôle. |
| `tests/` | Tests automatisés qui vérifient les comportements attendus. |

## Parcours de lecture conseillés

### Comprendre le démarrage

1. Lire les fichiers de lancement à la racine (`main.py`, `app.py`, `start.py`,
   `wsgi.py`) pour identifier le point d'entrée réellement utilisé.
2. Suivre la configuration chargée par ce point d'entrée.
3. Identifier l'application HTTP, ses routes et les services qu'elles appellent.
4. Vérifier les fichiers de déploiement et les workflows qui démarrent cette application.

### Comprendre une fonctionnalité

1. Repérer l'écran ou le composant dans `frontend/`.
2. Suivre les appels du client API et les données envoyées.
3. Retrouver la route correspondante dans `backend/api/`.
4. Suivre les appels vers le service métier concerné dans `backend/`.
5. Identifier le dépôt ou le repository qui lit et écrit les données.
6. Relier ces opérations aux tables et migrations de `database/`.
7. Lire les tests associés pour comprendre les cas normaux et les cas limites.

### Comprendre les changements de base de données

Les migrations SQL sont des changements versionnés du schéma. Elles doivent être lues
dans l'ordre, car une migration peut dépendre des tables, colonnes ou index créés avant elle.
Ne pas modifier une migration déjà appliquée sans vérifier la stratégie de déploiement.

## Convention de commentaires dans le code

Les commentaires doivent expliquer l'intention et les relations, pas reformuler chaque ligne.

- **En-tête de module** : rôle du fichier, périmètre fonctionnel et principaux liens avec les autres modules.
- **Classe** : responsabilité, données qu'elle porte et dépendances importantes.
- **Fonction ou méthode** : objectif, paramètres significatifs, résultat, effets de bord et erreurs possibles.
- **Bloc non évident** : raison de l'algorithme, ordre des opérations, règle métier ou contrainte technique.
- **Flux inter-modules** : origine des données, transformation, destination et contrôle de sécurité associé.

## Règles de qualité

- Écrire les explications en français clair et conserver les noms techniques exacts.
- Documenter les raisons et les conséquences, plutôt que paraphraser le code.
- Ne pas inventer de comportement : vérifier les appels, les types, les tests et le schéma avant
  d'affirmer qu'un module est relié à un autre.
- Ne pas modifier le comportement applicatif lors d'une passe de documentation.
- Ne jamais documenter de secrets, jetons, mots de passe ou valeurs sensibles.
- Garder les commentaires à jour lorsqu'une fonction, une route ou un contrat change.
- Pour les fichiers générés, bundles compilés, médias et dépendances, privilégier la documentation
  de leur source ou de leur mode de génération plutôt que d'ajouter des commentaires artificiels.

## État de la passe de documentation

Ce guide constitue le point d'entrée documentaire. Il ne signifie pas que tous les fichiers sources
sont déjà annotés. La couverture doit être réalisée progressivement par domaine, puis vérifiée
par comparaison du diff et exécution des contrôles disponibles.
