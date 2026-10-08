#!/usr/bin/env python3
"""Import the 91-article Review Defense package into the repository.

Usage:
  python scripts/import_resource_articles.py --zip /path/to/Review_Defense_91_Articles_Complete_Site_Package.zip

The script validates the package before writing any article files. It then copies
the supplied HTML, Markdown and SVG sources into their dedicated article folders
and updates the central registry using the package's own index.html titles and
categories. It never invents article copy.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
ARTICLE_ROOT = ROOT / "content" / "resources" / "articles"
REGISTRY_PATH = ARTICLE_ROOT / "registry.json"
EXPECTED_COUNT = 91
LINK_RE = re.compile(
    r'<li><a href="/ressources/([^"]+)/"><strong>(.*?)</strong><span>(.*?)</span></a></li>',
    re.DOTALL,
)


def parse_catalog(index_html: str) -> list[dict[str, str]]:
    records = []
    for slug, title, category in LINK_RE.findall(index_html):
        records.append({
            "slug": slug,
            "title": html.unescape(re.sub(r"<[^>]+>", "", title)).strip(),
            "category": html.unescape(re.sub(r"<[^>]+>", "", category)).strip(),
        })
    if len(records) != EXPECTED_COUNT:
        raise ValueError(f"Package index must contain {EXPECTED_COUNT} articles; found {len(records)}")
    if len({r["slug"] for r in records}) != EXPECTED_COUNT:
        raise ValueError("Package index contains duplicate article slugs")
    return records


def find_source(names: set[str], folder: str, slug: str, suffix: str) -> str:
    matches = [
        n for n in names
        if n.startswith(folder + "/") and PurePosixPath(n).name.endswith("-" + slug + suffix)
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {folder} source for {slug}; found {len(matches)}")
    return matches[0]


def import_package(zip_path: Path) -> dict[str, int]:
    if not zip_path.is_file():
        raise FileNotFoundError(f"ZIP not found: {zip_path}")

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        roots = sorted({
            str(PurePosixPath(n).parent)
            for n in names
            if n.endswith("/index.html") and PurePosixPath(n).name == "index.html"
        })
        index_candidates = [
            n for n in names
            if PurePosixPath(n).name == "index.html"
            and "articles" not in PurePosixPath(n).parts
        ]
        if len(index_candidates) != 1:
            raise ValueError(f"Expected one package index.html; found {len(index_candidates)}")
        package_index = index_candidates[0]
        index_dir = str(PurePosixPath(package_index).parent)
        prefix = index_dir + "/"
        index_html = archive.read(package_index).decode("utf-8")
        catalog = parse_catalog(index_html)

        # Validate every source before mutating the checkout.
        validated = []
        for record in catalog:
            slug = record["slug"]
            validated.append({
                **record,
                "html_source": find_source(names, prefix + "articles/html", slug, ".html"),
                "markdown_source": find_source(names, prefix + "articles/markdown", slug, ".md"),
                "svg_source": find_source(names, prefix + "illustrations", slug, ".svg"),
            })

        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        if len(registry.get("articles", [])) != EXPECTED_COUNT:
            raise ValueError("Repository registry does not contain exactly 91 article records")
        old_by_slug = {a["slug"]: a for a in registry["articles"]}
        if set(old_by_slug) != {a["slug"] for a in catalog}:
            raise ValueError("ZIP slugs do not match repository registry; refusing partial import")

        ARTICLE_ROOT.mkdir(parents=True, exist_ok=True)
        for record in validated:
            slug = record["slug"]
            folder = ARTICLE_ROOT / slug
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "index.html").write_bytes(archive.read(record["html_source"]))
            (folder / "article.md").write_bytes(archive.read(record["markdown_source"]))
            (folder / "illustration.svg").write_bytes(archive.read(record["svg_source"]))
            metadata = {
                "id": old_by_slug[slug].get("id", ""),
                "slug": slug,
                "title": record["title"],
                "category": record["category"],
                "route": f"/ressources/{slug}/",
                "status": "published",
                "sourcePackage": zip_path.name,
                "sourceFiles": {
                    "html": record["html_source"],
                    "markdown": record["markdown_source"],
                    "illustration": record["svg_source"],
                },
                "localFiles": {
                    "content": "article.md",
                    "html": "index.html",
                    "illustration": "illustration.svg",
                },
                "routeConnector": "content/resources/articles/registry.json",
            }
            (folder / "metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        by_slug = {r["slug"]: r for r in catalog}
        for article in registry["articles"]:
            record = by_slug[article["slug"]]
            article["title"] = record["title"]
            article["category"] = record["category"]
            article["status"] = "published"
            article["sourceFiles"] = {
                "html": record["html_source"],
                "markdown": record["markdown_source"],
                "illustration": record["svg_source"],
            }
        registry["status"] = "published"
        registry["sourcePackage"] = zip_path.name
        registry["articleCount"] = EXPECTED_COUNT
        REGISTRY_PATH.write_text(
            json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return {"articles": len(validated), "html": len(validated), "markdown": len(validated), "svg": len(validated)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", required=True, type=Path, help="Path to the source package ZIP")
    args = parser.parse_args()
    try:
        counts = import_package(args.zip.resolve())
    except (OSError, ValueError, zipfile.BadZipFile, KeyError) as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1
    print("Import complete: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
