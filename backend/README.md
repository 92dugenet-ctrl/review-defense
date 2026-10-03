# Backend — organisation cible par domaine

Ce répertoire est la **cible de classement du backend**, pas le point d'entrée actuellement exécuté en production.

## Règle de lecture

- **Runtime actif :** `wsgi.py → src.api_server.create_app`. Les imports exécutés proviennent actuellement de `src/`.
- **Organisation cible :** les sous-dossiers de `backend/` regroupent les responsabilités par domaine.
- **Migration :** un fichier placé dans `backend/` n'est pas automatiquement activé. Une extraction doit vérifier les imports, dépendances transitives, consommateurs, contrats, permissions et tests.
- **Pas de double source de vérité :** ne pas maintenir deux implémentations divergentes ni synchroniser les fichiers par copie aveugle.

## Index des domaines

| Dossier | Responsabilité cible | État observé |
|---|---|---|
| `api/` | Composition HTTP, configuration et adaptateurs transverses | Miroir transitoire de modules de `src/`; non chargé par WSGI |
| `authentication/` | Identité, MFA, récupération et durcissement de sécurité | Modules organisés; runtime encore dans `src/` |
| `organizations/` | Organisations et périmètres de tenant | Emplacement réservé, pas d'implémentation Python identifiée |
| `permissions/` | Autorisations et politiques d'accès | Emplacement réservé, pas d'implémentation Python identifiée |
| `users/` | Gestion du cycle de vie utilisateur | Emplacement réservé, pas d'implémentation Python identifiée |
| `cases/` | Cycle de vie, décision, soumission et espace dossier | Modules organisés; runtime encore dans `src/` |
| `reviews/` | Avis Google et revue opérationnelle | Modules présents; frontière avec Cases à clarifier |
| `analysis/` | Analyse, contradictions, politiques et extraction de preuves | Modules présents; plusieurs responsabilités restent transversales |
| `documents/` | Documents, preuves et stockage | Emplacement réservé; implémentations actives encore dans `src/` |
| `notifications/` | Outbox, politiques, livraison, workers et alertes | Modules organisés; runtime encore dans `src/` |
| `billing/` | Catalogue, facturation et adaptateur PayPal | Modules organisés; runtime encore dans `src/` |

## Règles avant toute extraction

1. Définir la responsabilité et le contrat public du domaine.
2. Cartographier les imports et dépendances dans les deux sens.
3. Vérifier les frontières organisationnelles et les contrôles d'autorisation.
4. Extraire un seul domaine à la fois, sans modifier les contrats HTTP.
5. Conserver une compatibilité d'import pendant la transition.
6. Ne retirer l'ancien module qu'après vérification de tous ses consommateurs.

## Chemins d'exécution à préserver

`wsgi.py`, `src/api_server.py`, `src/seo_site.py`, `frontend/assets/`, `migrations/` et les scripts de démarrage restent les chemins de référence. Voir `docs/LAYOUT_MIGRATION_MAP_2026-10-03.md` et `docs/BACKEND_DOMAIN_EXTRACTION_MAP_2026-10-03.md`.
