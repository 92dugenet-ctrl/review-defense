# Déploiement

Ce répertoire est la zone cible pour les manifests et la documentation
des procédures de déploiement.

## Organisation actuelle

Les scripts opérationnels restent sous `scripts/`, notamment :

- `start_production.sh` : contrôles, migrations, puis démarrage Gunicorn ;
- `production_check.py` : vérifications préalables au démarrage ;
- `deploy_staging.py` : déploiement de l'environnement de staging ;
- les scripts de certification TLS.

Le point d'entrée WSGI reste `wsgi:app`. Le port applicatif par défaut
reste `8080`.

## Contrat de production

- L'application démarre via `scripts/start_production.sh`.
- Les contrôles de production précèdent l'exécution des migrations.
- Les migrations sont exécutées avant le démarrage de Gunicorn.
- Le reverse proxy transmet le trafic vers le port applicatif `8080`.
- Les paramètres sensibles sont fournis par l'environnement, jamais ajoutés
  en dur dans les manifests.

## Limites de cette étape

Cette structuration est documentaire et améliore la lisibilité des fichiers
existants. Elle ne change ni les ports, ni les commandes de démarrage,
ni les variables d'environnement, ni les secrets, ni les migrations,
ni le comportement de production.

Aucun fichier historique n'est déplacé ou supprimé dans cette étape.
