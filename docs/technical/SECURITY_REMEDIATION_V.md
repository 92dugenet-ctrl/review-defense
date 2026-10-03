# Lot V — migration CSP progressive et authentification cookie

## CSP en observation

- La politique CSP actuellement appliquée est conservée afin de ne pas casser
  les pages marketing et le workspace historique, qui génèrent encore des
  gestionnaires d'événements inline et des styles inline.
- Un en-tête Content-Security-Policy-Report-Only ajoute une politique candidate
  sans unsafe-inline, avec script-src-attr 'none' et style-src-attr 'none'.
  Les violations sont visibles dans la console de sécurité du navigateur ;
  aucune politique de blocage n'est changée dans ce lot.
- Les deux blocs style de frontend/index.html ont été déplacés dans
  frontend/assets/inline-overrides.css et chargés comme feuille externe.
- La migration complète des gestionnaires inline de frontend/assets/public.js
  et frontend/assets/app.js reste à faire avant le retrait de unsafe-inline.

## Authentification navigateur par cookie

- REVIEW_DEFENSE_COOKIE_AUTH_ENABLED est un nouveau drapeau de configuration,
  désactivé par défaut pour permettre un déploiement coordonné.
- Lorsque le mode est activé, les réponses qui créent/renouvellent une session
  placent le token opaque dans un cookie HttpOnly, SameSite=Lax, Path=/ et
  Secure en production. Le bearer token est retiré du JSON de réponse.
- Le cookie de production utilise le préfixe __Host- (Secure, Path=/ et sans
  attribut Domain). Le mode local utilise un nom de cookie sans préfixe.
- Le serveur accepte le cookie comme source d'authentification lorsque le
  bearer Authorization n'est pas présent. La résolution de session, la
  révocation et le chargement du rôle restent inchangés.
- GET /v1/auth/csrf fournit un jeton CSRF dérivé par HMAC du token de session.
  Toute mutation utilisant le cookie exige le même jeton dans X-CSRF-Token.
  Les routes publiques d'authentification et le webhook PayPal sont exemptés.
- Le frontend React conserve le jeton CSRF uniquement en mémoire et l'ajoute
  aux requêtes mutantes. Au rechargement, il le récupère via le cookie.
- Le mode Bearer existant reste pris en charge lorsque le drapeau est désactivé.

## Activation coordonnée

1. Déployer le backend et le frontend de ce lot.
2. En environnement de production HTTPS, activer
   REVIEW_DEFENSE_COOKIE_AUTH_ENABLED=true.
3. Vérifier les parcours de connexion, inscription, rafraîchissement,
   rotation, changement de mot de passe, déconnexion et navigation après
   rechargement dans l'environnement de déploiement.
4. Examiner les violations Content-Security-Policy-Report-Only dans les
   navigateurs avant toute évolution de la politique CSP appliquée.

## Limites connues

- La CSP appliquée conserve unsafe-inline tant que les gestionnaires
  événementiels du workspace et des pages marketing n'ont pas été migrés.
- Le mode cookie est opt-in, il n'est pas activé par défaut.
- Les anciens clients qui exigent explicitement access_token dans le JSON
  doivent rester en mode Bearer jusqu'à leur migration.
- Le jeton CSRF est dérivé du token de session avec HMAC-SHA256 et n'est pas
  stocké côté serveur ; sa protection dépend de l'impossibilité pour un site
  tiers de lire les réponses same-origin et de la politique SameSite.
- Aucun test, build, typecheck, lint ou workflow GitHub Actions n'a été exécuté.

## Vérification statique

Inspection des chemins d'authentification, du transport API React, de la
politique CSP, des fichiers HTML servis et des réponses WSGI.
