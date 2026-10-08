"""Lookup helpers for the 91 Review Defense resource-article scaffolds.

The HTTP router can use these helpers to connect /ressources/<slug>/ to the
corresponding content/resources/articles/<slug>/ directory. The article files
are scaffolds until the source HTML/Markdown/SVG package is imported.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REGISTRY_PATH = _REPO_ROOT / "content" / "resources" / "articles" / "registry.json"
_ARTICLES_ROOT = _REPO_ROOT / "content" / "resources" / "articles"


def _load_registry() -> dict[str, Any]:
    with _REGISTRY_PATH.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def list_resource_articles() -> list[dict[str, Any]]:
    """Return all resource article records, in editorial order."""
    return list(_load_registry().get("articles", []))


def get_resource_article(slug: str) -> dict[str, Any] | None:
    """Return the registry record for a slug, or None if it is unknown."""
    clean_slug = slug.strip("/")
    for article in _load_registry().get("articles", []):
        if article.get("slug") == clean_slug:
            return article
    return None


def resolve_resource_article(slug: str) -> dict[str, Any] | None:
    """Resolve a slug to its content files without exposing arbitrary paths."""
    article = get_resource_article(slug)
    if article is None:
        return None
    directory = (_ARTICLES_ROOT / article["slug"]).resolve()
    if _ARTICLES_ROOT.resolve() not in directory.parents:
        return None
    return {
        **article,
        "directory_path": directory,
        "markdown_path": directory / "article.md",
        "html_path": directory / "index.html",
        "illustration_path": directory / "illustration.svg",
        "is_ready": article.get("status") == "published"
        and (directory / "index.html").is_file()
        and (directory / "illustration.svg").is_file(),
    }


def is_resource_article_path(path: str) -> bool:
    """Recognize the canonical /ressources/<slug>/ URL pattern."""
    normalized = "/" + path.strip("/") + "/"
    prefix = "/ressources/"
    if not normalized.startswith(prefix):
        return False
    slug = normalized[len(prefix):-1]
    return bool(slug) and get_resource_article(slug) is not None
