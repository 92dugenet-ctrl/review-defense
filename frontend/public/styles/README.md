# Styles publics historiques

Ce dossier contient des feuilles CSS de transition et des variantes héritées. Le système React canonique se trouve dans `../../src/styles/` (voir `../../src/styles/README.md`).

Certaines feuilles ont actuellement une copie strictement identique dans `src/styles/` :
- `global.css`
- `muse-v3.css`
- `public-secondary.css`
- `tokens.css`

`style.css` est identique à `frontend/style.css`. `styles.css` est une autre feuille, distincte de `frontend/styles.css`.

Aucune de ces copies n'est supprimée par cette cartographie : confirmer d'abord les références dans les pages HTML, les liens directs et les chemins servis. Ne pas ajouter ici de nouvelles pages ou feuilles React canoniques.

## Chargements vérifiés

- Les pages HTML historiques sous `public/pages/` peuvent charger les feuilles de ce dossier par URL relative (par exemple `public/pages/index.html` charge `styles.css`).
- `public/styles/style.css` est identique à `frontend/style.css`, mais la page historique charge une feuille locale relative ; la copie est donc conservée.
- `public/styles/global.css`, `muse-v3.css`, `public-secondary.css` et `tokens.css` sont identiques aux fichiers React correspondants. Les copies sont conservées jusqu'à vérification de tous les consommateurs statiques.
- `public/styles/styles.css` est distinct de `frontend/styles.css` et est référencé par `public/pages/index.html` ; ne pas le confondre avec la feuille principale du workspace.

Aucun dédoublonnage n'est autorisé sur la seule base des empreintes : les chemins relatifs et URL publiques font partie du contrat des pages historiques.
