"""Production WSGI entrypoint for Review Defense.

The application and API remain owned by the backend; the public interface is
served by the new frontend shell.
"""
from src.api_server import create_app

_application = create_app()

def app(environ, start_response):
    return _application(environ, start_response)
