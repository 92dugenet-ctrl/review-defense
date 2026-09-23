"""Single production WSGI entrypoint for Review Defense.

All HTTP routing is owned by src.api_server.create_app().
This module intentionally contains no second routing layer.
"""
from src.api_server import create_app

app = create_app()
