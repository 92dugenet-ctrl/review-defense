# Server

Zone cible pour les contrats liés au serveur et à son exploitation.

État actuel : `wsgi.py` est l'entrée WSGI active ; `src/api_server.py` compose l'API ; Gunicorn est lancé par `scripts/start_production.sh`. Les routes, variables d'environnement, ports et contrôles de démarrage restent dans leurs emplacements actuels.
