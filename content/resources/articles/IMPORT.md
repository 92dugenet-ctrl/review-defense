# Resource article import

The repository contains 91 article folders and a central registry. Their HTML and
SVG entrypoints are scaffolds until the original source package is imported.

To import the original content without rewriting or summarizing it:

```bash
python scripts/import_resource_articles.py --zip /path/to/Review_Defense_91_Articles_Complete_Site_Package.zip
```

The importer validates that the package index has exactly 91 unique slugs and
that each slug has exactly one HTML, Markdown and SVG source before writing
anything. It then copies all 273 original source files into their corresponding
folders, refreshes article metadata and marks the records as published.

Review the diff, run the repository test suite, and commit the import together
with any sitemap or card updates. Do not mark the import as complete before the
script reports all four counts as 91.
