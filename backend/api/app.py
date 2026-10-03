"""Alias de compatibilité vers l'application WSGI canonique.

Certains anciens imports attendent encore backend.api.app. Ce module conserve
ce point d'accès historique, mais ne définit volontairement ni routes ni
pipeline HTTP distinct : toutes les requêtes passent par wsgi.py.

Cette délégation évite que l'application lancée selon deux chemins différents
se comporte différemment (routage public, API, contrôles et en-têtes HTTP).
"""

from wsgi import app as application

# Conserve les deux noms d'import historiquement utilisés par le projet.
app = application
