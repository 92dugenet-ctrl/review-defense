# Auth — interface d'authentification React

## Responsabilité

Fournir l'état d'authentification partagé et les écrans d'accès à l'application.

## Fichiers

- `AuthContext.tsx` : état utilisateur, chargement de session, login, inscription, logout et rafraîchissement du profil.
- `RequireAuth.tsx` : garde de navigation pour les routes protégées.
- `login/LoginPage.tsx` : écran de connexion.
- `register/RegisterPage.tsx` : écran d'inscription.

## Contrat backend observé

Le contexte appelle notamment `/v1/auth/login`, `/v1/auth/register`, `/v1/me` et `/v1/logout`. Il conserve le jeton d'accès et l'identifiant d'organisation en session navigateur.

## Sécurité

La garde React améliore le parcours utilisateur mais ne sécurise pas une API. Le backend doit continuer à valider le jeton, le rôle, l'organisation et l'autorisation de chaque opération. Ne jamais considérer une valeur stockée dans le navigateur comme une preuve d'autorisation.

## État de migration

Des fichiers d'authentification équivalents existent sous `src/auth/`. Vite résout actuellement l'alias `@` vers `src/`; vérifier le consommateur effectif avant de modifier l'un ou l'autre emplacement.
