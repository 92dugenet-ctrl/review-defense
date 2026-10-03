# Assets historiques servis par le runtime

## Rôle

Ce dossier contient les feuilles CSS, scripts JavaScript, images, illustrations et médias utilisés par les pages historiques et le workspace.

## Groupes de fichiers

- `public.css`, `home.css`, `seo.css`, `premium-console-v640.css` et autres feuilles : styles publics et console.
- `public.js`, `home.js`, `app.js`, `console-*.js`, `billing.js`, `i18n.js` : comportements et modules JavaScript historiques.
- `seo-articles.js`, `seo-renderer.js` : rendu/contenu SEO.
- `hero/`, `audit/`, `legal/`, `packs/`, `partners/`, `tarif/`, `traitement/` : médias et illustrations.

## État runtime

Le serveur WSGI actuel sert les ressources statiques depuis `frontend/assets/`. Les chemins et noms de fichiers peuvent donc être référencés directement par des pages HTML, le CSS, le JS ou le backend.

## Règles

- Ne pas renommer ou déplacer un asset sans rechercher toutes ses références.
- Préserver les chemins absolus/relatifs et les paramètres de version de cache.
- Ne pas remplacer un asset utilisé par la console sans vérifier les pages concernées.
- Les copies sous `frontend/public/assets/` sont transitoires jusqu'à bascule du serveur statique et validation navigateur.
