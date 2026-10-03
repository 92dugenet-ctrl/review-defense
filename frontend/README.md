# Review Defense — guide du frontend

Ce document décrit l'organisation du frontend React et les responsabilités de ses principaux modules. Il sert de point d'entrée avant de modifier le code.

## Démarrage et points d'entrée

- `src/main.tsx` monte l'application React, les styles globaux, le fournisseur d'authentification et le routeur.
- `src/app/router.tsx` déclare les URL publiques, les pages légales, les écrans de connexion et les routes de l'espace client.
- `index.html` est une entrée HTML historique distincte. Ne pas la supprimer ou la fusionner sans vérifier la configuration Vite et le déploiement.

## Organisation de `src/`

| Dossier | Responsabilité |
| --- | --- |
| `app/` | Configuration et déclaration des routes |
| `auth/` | Session, authentification et protection des routes |
| `components/layout/` | Éléments d'interface partagés par l'espace client |
| `components/public/muse/` | Composition des pages publiques et composants du design Muse |
| `hooks/` | Hooks React réutilisables |
| `pages/` | Écrans associés aux routes |
| `services/api/` | Communication HTTP avec le backend |
| `styles/` | Variables, styles globaux et styles du site public |
| `types/` | Types partagés des réponses et objets API |

## Parcours d'une requête API

1. Une page ou un hook appelle une méthode de `api` dans `services/api/client.ts`.
2. Le client HTTP ajoute les en-têtes communs et, pour les routes `/v1/`, le jeton de session si nécessaire.
3. La réponse est convertie en JSON ou en texte.
4. Une réponse HTTP en erreur devient une instance de `ApiError`, que l'interface peut afficher à l'utilisateur.

Les composants d'interface ne doivent pas construire eux-mêmes les URL de base ni réimplémenter la gestion commune du jeton.

## Authentification et autorisation

- `AuthContext.tsx` expose l'utilisateur courant, l'état de chargement et les actions de connexion, inscription, déconnexion et actualisation.
- `sessionToken.ts` centralise la lecture de la clé de session dans `sessionStorage`.
- `RequireAuth.tsx` empêche l'accès aux routes de l'espace client lorsqu'aucune session authentifiée n'est disponible.
- Le routeur regroupe les écrans privés sous `/app`.
- Les autorisations fines, notamment les droits liés à une organisation ou à un rôle, doivent être contrôlées côté backend. Masquer un bouton dans le frontend ne constitue pas une protection d'accès.

## Pages publiques et espace client

Les pages publiques sont principalement composées à partir de `components/public/muse/` et de `MuseShell`. Les pages de l'espace client se trouvent dans `pages/` et utilisent les composants partagés de `components/layout/`.

Le shell public et le shell de l'application authentifiée sont distincts. Une modification du menu ou du pied de page public ne doit pas modifier la navigation de l'espace client.

## Conventions de maintenance

- Une instruction ou un élément JSX par ligne lorsque cela améliore la lecture.
- Utiliser des noms explicites pour les états, fonctions, paramètres et réponses API.
- Extraire une fonction lorsqu'elle représente une action métier identifiable ou évite une imbrication difficile à lire.
- Préférer des types dédiés aux objets API plutôt que `any` lorsque le contrat est connu.
- Documenter les responsabilités et les effets de bord aux frontières des modules ; éviter les commentaires qui répètent littéralement le code.
- Conserver les chemins d'API, les méthodes HTTP, les noms de propriétés JSON et les règles métier existantes lors d'une passe de formatage.
- Ne pas déplacer ou supprimer une feuille de style, une route ou un composant avant d'avoir recherché toutes ses références.

## Vérifications avant intégration

Après une passe de refactorisation, exécuter au minimum le contrôle TypeScript et le build du frontend, puis les tests concernés. Les modifications purement documentaires et de formatage doivent également être relues pour vérifier qu'elles n'ont pas changé les appels API ou les conditions métier.
