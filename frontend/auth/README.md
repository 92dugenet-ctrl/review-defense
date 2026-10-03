# Auth — archive de migration

## Source active

L'authentification React utilisée par Vite est centralisée dans :
- `src/auth/AuthContext.tsx` : état de session et opérations d'authentification ;
- `src/auth/sessionToken.ts` : lecture centralisée du jeton ;
- `src/auth/RequireAuth.tsx` : garde des routes protégées ;
- `src/pages/LoginPage.tsx` et `src/pages/RegisterPage.tsx` : écrans utilisés par le routeur.

Vite et TypeScript compilent `src/` et l'alias `@/` pointe vers `src/`. Les copies strictement identiques de `RequireAuth`, `LoginPage` et `RegisterPage` ont donc été retirées de ce dossier.

## Fichier historique conservé

`AuthContext.tsx` est conservé temporairement comme référence d'ancienne implémentation. Il diffère du contexte actif : il lit directement une clé de session au lieu d'utiliser `src/auth/sessionToken.ts`. Il ne doit pas être importé dans le code actif ni servir de base à de nouveaux développements.

## Sécurité

La garde côté navigateur n'est qu'un contrôle d'interface. Le backend doit vérifier indépendamment le jeton, l'utilisateur, l'organisation et les autorisations pour chaque requête. Ne jamais faire confiance à l'identifiant d'organisation stocké dans le navigateur sans validation serveur.

## Règle

Toute évolution de l'authentification doit être faite dans `src/auth/` et `src/pages/`. Ne supprimer le contexte historique qu'après confirmation qu'aucun outil ou script de migration ne le consomme.
