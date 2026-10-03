# Composants du site public

## Rôle

Zone de transition contenant uniquement des variantes publiques historiques qui ne sont pas les composants canoniques du build React.

## Organisation

- `muse/pricing/PricingCatalog.tsx` : ancienne variante du catalogue de tarifs. Elle ne doit pas être confondue avec la version active sous `src/components/public/muse/pricing/`, qui comprend aussi le parcours d'abonnement PayPal.

Les composants `PublicHeader.tsx` et `PublicFooter.tsx` ont été retirés de ce dossier car ils étaient strictement identiques aux composants canoniques `src/components/layout/PublicHeader.tsx` et `PublicFooter.tsx`.

## Dépendances

Le build Vite utilise `src/main.tsx` et le routeur actif importe les composants depuis `src/`. Ne pas réintroduire ici des copies de composants déjà présents dans `src/`.

## État

Contenu conservé à titre historique. `PricingCatalog.tsx` est une variante ancienne non compilée par la configuration Vite actuelle.
