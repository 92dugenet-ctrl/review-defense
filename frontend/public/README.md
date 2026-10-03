# Public — site vitrine et ressources historiques

## Source React active

Le code React utilisé par le build et le routeur est centralisé dans :
- `src/main.tsx` : point d'entrée React ;
- `src/app/router.tsx` : routes React ;
- `src/pages/` : pages ;
- `src/components/public/` : composants publics ;
- `src/styles/` : styles importés par l'application.

Les copies React strictement identiques qui se trouvaient dans `public/components/` et `public/pages/` ont été retirées. Ne recréez pas de seconde source React dans ce dossier.

## Contenu conservé ici

- `assets/` : médias, illustrations et scripts statiques historiques ;
- `pages/*.html` : pages HTML historiques ;
- `styles/` : feuilles de style de transition ;
- les composants React spécifiques qui ne sont pas des doublons exacts (notamment certains composants d'habillage et le catalogue de tarifs) restent à examiner avant toute migration.

## Règles de migration

- Ne pas déplacer ni renommer les médias sans vérifier leurs URL et les routes du serveur.
- Ne pas supprimer les pages HTML historiques avant validation de la parité navigateur et de leur remplacement côté serveur.
- Toute nouvelle page React publique doit être développée dans `src/pages/` et utiliser les composants de `src/components/public/`.
- Les éléments conservés ici ne deviennent pas automatiquement des points d'entrée de production.
