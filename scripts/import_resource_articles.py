#!/usr/bin/env python3
"""Validate and import the official 91-article Review Defense ZIP package."""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COUNT = 91
ZIP_INDEX = "index.html"
ARTICLE_ROOT = ROOT / "frontend" / "ressources"
ASSET_ROOT = ROOT / "frontend" / "assets" / "articles"
CONTENT_ROOT = ROOT / "content" / "resources" / "articles"
REGISTRY_PATH = CONTENT_ROOT / "registry.json"


def locate_package_root(names: set[str]) -> str:
    matches = [name for name in names if name.endswith("/data/articles.json")]
    if len(matches) != 1:
        raise ValueError(f"Expected one data/articles.json; found {len(matches)}")
    return str(PurePosixPath(matches[0]).parent.parent)


def safe_slug(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9-]+", value):
        raise ValueError(f"Unsafe or unsupported article slug: {value!r}")
    return value


def find_source(names: set[str], root: str, folder: str, basename: str) -> str:
    expected = f"{root}/{folder}/{basename}"
    if expected not in names:
        raise ValueError(f"Missing source file: {expected}")
    return expected


def import_package(zip_path: Path) -> dict[str, int]:
    if not zip_path.is_file():
        raise FileNotFoundError(f"ZIP not found: {zip_path}")

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        root = locate_package_root(names)
        data_path = f"{root}/data/articles.json"
        catalog = json.loads(archive.read(data_path).decode("utf-8"))
        if not isinstance(catalog, list) or len(catalog) != EXPECTED_COUNT:
            raise ValueError(f"Package must contain exactly {EXPECTED_COUNT} article records")
        slugs = [safe_slug(str(item.get("slug", ""))) for item in catalog]
        if len(set(slugs)) != EXPECTED_COUNT:
            raise ValueError("Article catalogue contains duplicate slugs")

        validated = []
        for item in catalog:
            slug = safe_slug(str(item["slug"]))
            html_name = PurePosixPath(str(item["html"])).name
            md_name = PurePosixPath(str(item["markdown"])).name
            svg_name = PurePosixPath(str(item["illustration"])).name
            validated.append({
                **item,
                "slug": slug,
                "html_source": find_source(names, root, "articles/html", html_name),
                "markdown_source": find_source(names, root, "articles/markdown", md_name),
                "svg_source": find_source(names, root, "illustrations", svg_name),
            })

        # All 273 original source files are validated before the first write.
        CONTENT_ROOT.mkdir(parents=True, exist_ok=True)
        ASSET_ROOT.mkdir(parents=True, exist_ok=True)
        registry = []
        for item in validated:
            slug = item["slug"]
            html_bytes = archive.read(item["html_source"])
            md_bytes = archive.read(item["markdown_source"])
            svg_bytes = archive.read(item["svg_source"])
            article_dir = ARTICLE_ROOT / slug
            article_dir.mkdir(parents=True, exist_ok=True)
            (article_dir / "index.html").write_bytes(html_bytes)
            (CONTENT_ROOT / f"{slug}.md").write_bytes(md_bytes)
            (ASSET_ROOT / PurePosixPath(item["illustration"]).name).write_bytes(svg_bytes)
            metadata = {
                "id": item.get("id", ""),
                "slug": slug,
                "title": item.get("title", ""),
                "category": item.get("category", ""),
                "type": item.get("type", ""),
                "route": f"/ressources/{slug}/",
                "seoTitle": item.get("seo_title", ""),
                "metaDescription": item.get("meta_description", ""),
                "primaryKeyword": item.get("primary_keyword", ""),
                "searchIntent": item.get("search_intent", ""),
                "editorialAngle": item.get("editorial_angle", ""),
                "html": f"frontend/ressources/{slug}/index.html",
                "markdown": f"content/resources/articles/{slug}.md",
                "illustration": f"frontend/assets/articles/{PurePosixPath(item['illustration']).name}",
            }
            (article_dir / "metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            registry.append(metadata)

        REGISTRY_PATH.write_text(
            json.dumps({"status": "ready-for-review", "articleCount": len(registry), "articles": registry},
                       ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return {"articles": len(validated), "html": len(validated), "markdown": len(validated), "svg": len(validated)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", required=True, type=Path, help="Path to the original ZIP package")
    args = parser.parse_args()
    try:
        counts = import_package(args.zip.resolve())
    except (OSError, ValueError, zipfile.BadZipFile, KeyError, json.JSONDecodeError) as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1
    print("Import validated and completed: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
