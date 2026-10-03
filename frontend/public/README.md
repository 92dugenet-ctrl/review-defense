# Public — site vitrine React cible

## Responsabilité

Ce dossier regroupe les composants et pages React destinés au site public : accueil, produit, méthode, sécurité, tarifs et contact. Il sépare la présentation publique de l'espace authentifié.

## Organisation

- `components/` : en-tête, pied de page, animations et composants de sections.
- `components/muse/` : composition des pages publiques par univers fonctionnel (home, product, method, pricing, security, contact).
- `pages/` : composants de pages publiques, selon les fichiers présents.
- `styles/` : styles du site public.
- `assets/` : médias, illustrations et scripts/assets publics copiés depuis les chemins historiques.

## État de migration

Ce dossier est une structure cible et contient des copies de transition. `MIGRATION.md` précise que les pages et assets ont été copiés depuis les emplacements historiques; les URL relatives et le routage doivent être vérifiés avant tout changement de serveur statique.

Le code public React existe aussi sous `src/components/public/` et `src/pages/`. Le point d'entrée Vite actuellement configuré est `src/main.tsx`; ne pas supposer que `public/` est le point d'entrée de production.

## Règles

- Garder les pages publiques indépendantes des composants nécessitant une session.
- Ne pas embarquer de secret ni de contrôle d'accès côté client.
- Préserver les métadonnées SEO, liens canoniques, chemins des médias et navigation.
- Avant convergence avec `src/components/public/`, comparer les composants et vérifier le rendu de chaque route publique.
