# Composants du site public

## Rôle

Composants réutilisables du site vitrine : navigation, pied de page, animations et assemblage des blocs de page.

## Organisation

- `PublicHeader.tsx` et `PublicFooter.tsx` : chrome commun du site.
- `MuseMotion.tsx` : comportement/animation transversale.
- `muse/` : sections et compositions propres aux pages Home, Product, Method, Pricing, Security et Contact.

## Dépendances

Les composants dépendent de React et des styles/assets du site public. Ils ont un équivalent parallèle sous `src/components/public/`; vérifier les écarts avant toute fusion ou suppression.

## État

Structure cible/copie de transition. Le build Vite configuré utilise actuellement `src/main.tsx`, pas un point d'entrée autonome dans ce dossier.
