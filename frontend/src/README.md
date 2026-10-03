# src — source React référencée par Vite

## Rôle actuel

Le dossier `src/` est la source React explicitement référencée par la configuration Vite actuelle :
- `vite.config.ts` ajoute `src/main.tsx` comme entrée React.
- L'alias `@` pointe vers `./src`.
- `tsconfig` doit rester cohérent avec cet alias.

## Organisation

- `main.tsx`, `app/router.tsx` : montage React et routes.
- `auth/` : contexte et garde d'authentification.
- `components/layout/` : shell et navigation de l'application.
- `components/public/` : composants du site public et sections Muse.
- `pages/` : pages publiques, authentification, espace client et administration.
- `services/api/`, `hooks/`, `types/` : client API, hooks et contrats.
- `styles/` : tokens, styles globaux et feuilles publiques.

## Relation avec application/ et public/

Des structures plus ciblées existent sous `application/` et `public/`. Certains fichiers sont des doublons ou des copies de transition. Ne pas supprimer `src/` ni déplacer ses pages tant que les consommateurs Vite/TypeScript et le rendu des routes n'ont pas été migrés.

## Règles

- Garder les alias Vite et TypeScript alignés.
- Préserver le point de montage `#root` et le contrat du client API.
- Ne pas confondre le build React avec le site statique servi actuellement par WSGI.
- Une migration doit comparer les implémentations, mettre à jour les imports, puis valider typecheck, build et navigation.
