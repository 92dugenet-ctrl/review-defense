"""Point d'entrée compatible avec le déploiement eCloudServ.

Ce fichier ne contient pas la logique métier de Review Defense.
Il prépare la commande Gunicorn qui charge l'application WSGI définie dans
wsgi.py. Les paramètres de processus sont configurables par variables
d'environnement afin de pouvoir adapter le serveur sans modifier le code.
"""

from __future__ import annotations

import os
import sys


def build_gunicorn_command(port: str | int | None = None) -> list[str]:
    """Construit la commande de lancement du serveur HTTP.

    Le port explicite est prioritaire, puis PORT, puis 8080 par défaut.
    Gunicorn importe ensuite l'objet app du module wsgi (wsgi:app).
    Les workers traitent plusieurs processus, les threads plusieurs requêtes
    dans chaque processus ; les valeurs sont ajustables via l'environnement.
    """
    selected = str(port or os.environ.get("PORT") or "8080")

    return [
        sys.executable,
        "-m",
        "gunicorn",
        "--bind",
        f"0.0.0.0:{selected}",
        "--workers",
        os.environ.get("GUNICORN_WORKERS", "2"),
        "--threads",
        os.environ.get("GUNICORN_THREADS", "4"),
        "--timeout",
        os.environ.get("GUNICORN_TIMEOUT", "60"),
        "wsgi:app",
    ]


if __name__ == "__main__":
    # Remplace le processus Python courant par Gunicorn. Cela transmet
    # proprement les signaux système au serveur dans les conteneurs.
    os.execv(sys.executable, build_gunicorn_command())
