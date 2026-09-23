"""Production WSGI entrypoint with crawlable public SEO routes."""
from src.api_server import create_app
from src.seo_site import render as render_seo
from urllib.parse import parse_qs

_api = create_app()

def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    query = parse_qs(environ.get("QUERY_STRING", ""))
    legacy = {"features":"/produit/","how":"/comment-ca-marche/","services":"/services/","pricing":"/tarifs/","resources":"/ressources/","contact":"/contact/"}
    if path=="/" and query.get("page", [None])[0] in legacy:
        target=legacy[query["page"][0]]
        start_response("301 Moved Permanently", [("Location", target), ("Content-Length", "0")])
        return [b""]
    seo = render_seo(path)
    if seo is not None:
        status, headers, body = seo
        phrase = {200: "OK"}.get(status, "Error")
        headers = list(headers) + [("Content-Length", str(len(body))), ("X-Robots-Tag", "all")]
        start_response(f"{status} {phrase}", headers)
        return [body]
    return _api(environ, start_response)
