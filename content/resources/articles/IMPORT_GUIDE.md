# Importer les 91 articles Review Defense depuis GitHub

La préparation de cet outil ne modifie pas le site visible. L'import s'exécute sur une branche dédiée, puis doit être relu avant fusion dans `main`.

## Étapes

1. Ouvrir l'onglet **Code** et sélectionner la branche `prepare/91-article-import` (à créer depuis `main` après l'installation de cet outil).
2. Dans `imports/`, téléverser le fichier original `Review_Defense_91_Articles_Complete_Site_Package.zip` via **Add file → Upload files**, puis valider le commit sur cette branche.
3. Ouvrir **Actions → Import Review Defense articles → Run workflow**. Choisir la branche `prepare/91-article-import`, conserver le chemin ZIP par défaut et lancer.
4. Attendre le résultat vert. Le workflow vérifie les 91 enregistrements et les 273 sources (HTML, Markdown, SVG), puis commit les fichiers importés sur la branche sélectionnée et retire le ZIP de son état courant.
5. Examiner les changements et ouvrir une pull request vers `main`. Ne pas fusionner avant la vérification de l'affichage, des routes et du sitemap.

## Contenu importé

- HTML : `frontend/ressources/<slug>/index.html`
- Illustrations SVG : `frontend/assets/articles/`
- Sources Markdown et métadonnées : `content/resources/articles/`

Le domaine du sitemap fourni dans le ZIP est un placeholder : il doit être remplacé par le domaine réel avant publication. Le workflow ne déploie pas automatiquement et ne fusionne jamais dans `main`.
