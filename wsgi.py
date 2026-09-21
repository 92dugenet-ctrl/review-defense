"""Production WSGI entrypoint."""
from src.api_server import create_app

app = create_app()
