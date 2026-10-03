# Deployment

Zone cible pour les manifests et procédures de déploiement.

État actuel : les scripts opérationnels restent sous `scripts/`, notamment `start_production.sh`, `production_check.py`, `deploy_staging.py` et les scripts de certification. Le port par défaut reste 8080 et l'entrée WSGI reste `wsgi:app`. Aucun changement de port, de commande de démarrage ou d'infrastructure n'est inclus dans la structuration.
