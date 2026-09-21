"""Production WSGI entrypoint with crawlable public SEO routes."""
from src.api_server import create_app
from src.seo_site import render as render_seo

_api = create_app()

def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    seo = render_seo(path)
    if seo is not None:
        status, headers, body = seo
        phrase = {200: "OK"}.get(status, "Error")
        headers = list(headers) + [("Content-Length", str(len(body))), ("X-Robots-Tag", "all")]
        start_response(f"{status} {phrase}", headers)
        return [body]
    return _api(environ, start_response)
