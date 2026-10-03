"""Lanceur local et serveur pour Review Defense.

Ce script est une alternative courte à main.py. Il démarre Gunicorn avec
l'application WSGI commune (wsgi:app). Il ne crée pas une seconde application
et ne doit donc pas contenir de routes ou de règles métier.
"""

import os
import subprocess
import sys


if __name__ == "__main__":
    # SERVER_PORT permet de distinguer le port de ce lanceur de PORT,
    # utilisé par de nombreux environnements de déploiement.
    port = os.environ.get("SERVER_PORT", os.environ.get("PORT", "8080"))

    # subprocess.call renvoie le code de sortie de Gunicorn ; SystemExit le
    # transmet au système pour que les outils d'exploitation voient l'échec.
    raise SystemExit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "gunicorn",
                "--bind",
                f"0.0.0.0:{port}",
                "--workers",
                "2",
                "--threads",
                "4",
                "--timeout",
                "60",
                "wsgi:app",
            ]
        )
    )
