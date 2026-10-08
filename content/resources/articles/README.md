# Review Defense — registre des 91 articles

Ce dossier prépare les connecteurs éditoriaux pour les 91 articles du package fourni.

- Chaque article possède un dossier dédié nommé selon son slug d’URL.
- `article.md` est le point d’entrée éditorial prévu pour le contenu Markdown.
- `metadata.json` relie le slug, la route publique attendue et les trois fichiers sources du ZIP (HTML, Markdown, SVG).
- `registry.json` est le registre central à utiliser pour raccorder les cartes de la mosaïque au renderer.
- Les fichiers sont volontairement des squelettes : le contenu source du ZIP et les SVG ne sont pas encore copiés dans ce dépôt.

## Route attendue

`/ressources/<slug>/`

Le branchement HTTP effectif doit lire le registre et rendre le contenu de l’article. Ne pas publier ces routes comme finalisées tant que l’import du contenu et les tests de résolution ne sont pas terminés.
