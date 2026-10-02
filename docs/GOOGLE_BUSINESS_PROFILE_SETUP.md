# Configuration du hub client — Google Business Profile

## Pré-requis Google

Dans le projet Google Cloud utilisé par Review Defense :

- Activer les API Google Business Profile nécessaires à la gestion des comptes, des établissements et à la lecture des avis.
- Configurer l'écran de consentement OAuth et publier/autoriser les comptes de test selon l'état de validation Google.
- Créer un client OAuth de type application Web.
- Ajouter comme URI de redirection autorisée l'URL exacte `REVIEW_DEFENSE_PUBLIC_BASE_URL` suivie de `/v1/integrations/google/callback`.
- Autoriser le scope `https://www.googleapis.com/auth/business.manage`.

## Variables serveur

Renseigner ces variables dans l'environnement du serveur, jamais dans le frontend :

```dotenv
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
REVIEW_DEFENSE_GOOGLE_TOKEN_KEY=
REVIEW_DEFENSE_GOOGLE_STATE_KEY=
REVIEW_DEFENSE_PUBLIC_BASE_URL=https://votre-domaine.example
```

Générer une clé Fernet dédiée au chiffrement des jetons :

```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Générer une clé indépendante pour signer les états OAuth :

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Les deux clés doivent être persistantes entre redémarrages et identiques sur tous les workers. Ne pas réutiliser la clé MFA ou un secret PayPal. Les valeurs ne doivent jamais être commitées dans Git.

## Parcours

1. L'utilisateur authentifié démarre la connexion depuis `/client` ou `/admin`.
2. Le serveur crée un état signé à durée limitée et un vérificateur PKCE. L'état est stocké en base, lié à l'organisation et à l'utilisateur.
3. Le navigateur est redirigé vers Google après une requête de démarrage authentifiée par Bearer Token.
4. Le callback vérifie la signature, l'expiration et consomme atomiquement l'état une seule fois depuis PostgreSQL. Les migrations `032` et `033` limitent l'accès tenantless au seul état opaque transmis au callback et forcent l'application des politiques RLS sur les tables du hub.
5. Les jetons d'accès et de renouvellement sont chiffrés avec Fernet avant persistance.
6. L'utilisateur choisit un établissement. Le serveur vérifie que le compte et l'établissement appartiennent réellement à la connexion Google, puis synchronise jusqu'à 50 avis dans cette première page.
7. Les jetons expirés sont renouvelés côté serveur. Si aucun jeton de renouvellement n'est disponible ou si Google le refuse, l'utilisateur doit reconnecter son compte.

## Limites fonctionnelles et sécurité

- L'intégration Google est strictement en lecture seule : comptes, établissements et avis peuvent être consultés/synchronisés ; aucune réponse, suppression, signalement ou modification de fiche n'est exposée.
- Toutes les routes authentifiées utilisent l'organisation portée par la session. Aucun `organization_id` n'est accepté depuis le corps HTTP.
- Les rôles `OWNER`, `ADMIN` et `CLIENT` peuvent démarrer une connexion, sélectionner une fiche et modifier le profil ou déposer des documents. Les autres rôles peuvent consulter les données selon les autorisations de leur espace.
- Les documents sont limités à 25 Mio, contrôlés par type MIME et nom de fichier, stockés dans le coffre objet avec une empreinte SHA-256, et téléchargeables uniquement par un membre authentifié de la même organisation.
- Les clés Google et les jetons ne sont jamais renvoyés au navigateur.
- L'API de découverte retourne les erreurs Google par connexion sans exposer de jetons.

## Routes

| Méthode | Route | Fonction |
|---|---|---|
| `POST` | `/v1/integrations/google/start` | Démarrer OAuth et obtenir l'URL Google |
| `GET` | `/v1/integrations/google/callback` | Valider le callback et enregistrer les jetons |
| `GET` | `/v1/integrations/google/locations` | Lister les comptes et établissements accessibles |
| `POST` | `/v1/integrations/google/select-location` | Vérifier la sélection et synchroniser les avis |
| `GET` / `POST` | `/v1/client/profile` | Lire / mettre à jour le profil entreprise |
| `GET` / `POST` | `/v1/client/documents` | Lister / déposer des documents |
| `GET` | `/v1/client/documents/{id}/download` | Télécharger un document de son organisation |

## Validation avant production

- Appliquer toutes les migrations jusqu'à `033`.
- Configurer les quatre variables Google/cryptographiques ci-dessus sur chaque instance.
- Vérifier l'URI de callback à l'identique dans Google Cloud.
- Exécuter `node --check frontend/workspace.js` et `node --check frontend/assets/app.js`.
- Exécuter `python -m pytest -q tests/test_client_monitoring_hub.py tests/test_v57_google.py` puis la suite complète.
- Effectuer un test OAuth avec un compte Google de test et vérifier l'isolation entre deux organisations.
- Ne pas activer la fonctionnalité en production tant que le test OAuth réel et la vérification RLS PostgreSQL n'ont pas été effectués.
