# Audit sécurité API et données sensibles — lot S

Date de revue : 2026-10-03  
Branche inspectée : `develop`  
Périmètre : code réellement référencé par l'application WSGI et le frontend React actif.  
Nature : revue statique des sources, configurations et migrations ; aucune exécution de code.

## Synthèse

Le dépôt contient plusieurs contrôles utiles : mots de passe PBKDF2-SHA256 avec sel aléatoire (310 000 itérations), tokens de session opaques générés par CSPRNG et stockés sous forme de hash, sessions persistées et révocables, contrôle du rôle rechargé depuis PostgreSQL, validation de taille/type déclarée des fichiers, stockage de fichiers privé avec permissions restrictives, chiffrement Fernet des secrets Google et MFA, vérification serveur de signature PayPal, et validation OIDC injectée pour Google Pub/Sub.

Ces mécanismes ne forment toutefois pas encore une politique homogène de sécurité opérationnelle. Les constats prioritaires concernent la consommation atomique des tokens de récupération, la protection HTTP absente sur les fichiers statiques servis directement, la portée locale des limiteurs de débit, le stockage du bearer token dans le navigateur et les différences de configuration entre les modes `production` et `prod`.

## Constats et priorités

### S-01 — Consommation du token de récupération non atomique

**Priorité : élevée**

Dans `src/api_server.py`, le parcours `POST /v1/auth/recovery/reset` vérifie l'état `used_at`, modifie le mot de passe, révoque les sessions, puis appelle séparément `consume_recovery_token()`. Le résultat booléen de cette consommation n'est pas contrôlé. Dans `src/identity_repository.py`, la consommation est une mise à jour conditionnelle `used_at IS NULL`, mais elle n'est pas incluse dans une transaction atomique avec la modification du mot de passe.

Deux demandes concurrentes peuvent donc franchir la lecture initiale avant qu'une seule ne consomme le token ; la seconde ne vérifie pas que la consommation a réussi avant de répondre avec succès et d'écrire son mot de passe. Les écritures de révocation et de mot de passe sont elles-mêmes séparées.

**À corriger :** fournir une opération repository unique qui verrouille/consomme le token et met à jour le mot de passe ainsi que les sessions dans une transaction ; refuser toute mise à jour si la consommation conditionnelle n'a pas affecté exactement une ligne. Ne jamais annoncer le succès avant le commit.

### S-02 — Les fichiers statiques du frontend ne reçoivent pas les en-têtes de sécurité

**Priorité : élevée**

Dans `src/api_server.py`, la branche WSGI qui sert `index.html`, `workspace.html`, `dist/*`, les scripts et les feuilles de style construit uniquement `Content-Type`, `Content-Length` et `X-Request-ID`. Elle ne réutilise pas `security_headers()`. Les réponses API et certaines pages SEO passent, elles, par l'ajout de ces en-têtes.

Conséquence : le frontend applicatif servi par cette branche n'obtient pas la CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, COOP/CORP ni HSTS depuis cette couche. La CSP existante ne protège donc pas de façon uniforme les pages SPA et les ressources statiques.

**À corriger :** centraliser la construction des en-têtes et l'appliquer à toutes les réponses HTML et statiques, y compris les réponses d'erreur et les redirections. Vérifier aussi la configuration du proxy en complément, sans compter sur lui implicitement.

### S-03 — Limitation des tentatives d'authentification non distribuée

**Priorité : élevée**

`RateLimiter` dans `src/security_hardening.py` conserve ses compteurs dans un dictionnaire du processus. `ReviewDefenseAPI` crée séparément les limiteurs généraux, d'authentification et de récupération en mémoire. Le code précise lui-même que ce mécanisme n'est pas partagé entre workers. Avec plusieurs workers Gunicorn, chaque processus possède donc son propre budget ; un client peut répartir les tentatives entre workers et dépasser le seuil global attendu. Le compteur général utilise aussi `REMOTE_ADDR`, qui correspond au proxy si l'adresse cliente n'est pas propagée de manière fiable.

**À corriger :** déplacer les compteurs sensibles dans un stockage partagé atomique (par exemple Redis ou PostgreSQL avec expiration), appliquer des clés distinctes par compte et origine, et documenter la chaîne de proxies de confiance. Conserver des réponses de connexion/récupération non révélatrices de l'existence d'un compte.

### S-04 — Bearer token conservé dans sessionStorage

**Priorité : élevée (réduction de l'impact XSS)**

`frontend/src/auth/sessionToken.ts` lit le token depuis `sessionStorage`, et `AuthContext.tsx` l'y écrit. `frontend/src/services/api/client.ts` le relit puis le transmet dans `Authorization: Bearer`. Ce choix évite la persistance après fermeture de l'onglet, mais tout script exécuté dans l'origine peut lire le token. L'usage de `credentials: include` ne transforme pas ce bearer token en cookie HttpOnly.

La CSP déclarée dans `src/deployment.py` autorise `'unsafe-inline'` pour les scripts, ce qui réduit la capacité de la CSP à limiter certaines injections. Par ailleurs, cette CSP n'est pas appliquée à la branche de service statique (S-02).

**À corriger :** privilégier un modèle de session par cookie `HttpOnly; Secure; SameSite` avec protection CSRF adaptée, ou documenter explicitement le risque résiduel si le bearer token est conservé. Supprimer les scripts inline non indispensables et passer à des nonces/hashes CSP. Traiter l'ensemble comme une défense en profondeur : aucune CSP ne remplace l'encodage et la prévention XSS.

### S-05 — Incohérence de clé MFA entre les environnements `prod` et `production`

**Priorité : élevée pour la disponibilité et la continuité de sécurité**

`ProductionConfig.production` reconnaît `production` et `prod`. En revanche, `ReviewDefenseAPI._mfa_key()` ne bloque l'absence de `REVIEW_DEFENSE_MFA_ENCRYPTION_KEY` que lorsque `environment == "production"`. Avec `REVIEW_DEFENSE_ENV=prod`, la fonction peut générer une clé Fernet aléatoire propre au processus. Les secrets MFA chiffrés avec cette clé ne sont pas garantis déchiffrables après redémarrage ou sur un autre worker.

**À corriger :** utiliser partout la propriété normalisée `self.config.production`, imposer une clé persistante en production et vérifier son format au démarrage, comme le fait déjà le chemin de chiffrement Google.

### S-06 — STARTTLS SMTP désactivable en production

**Priorité : moyenne à élevée selon le déploiement**

`ProductionConfig.from_env()` permet `SMTP_STARTTLS=false`. `validate_startup()` exige un hôte et un expéditeur SMTP, mais ne rend pas STARTTLS obligatoire en production. `recovery_email.py` appelle `smtp.starttls()` uniquement si l'option est vraie, puis peut s'authentifier avec les identifiants SMTP. Une configuration erronée peut donc envoyer des identifiants ou des messages de récupération sur une connexion non chiffrée.

**À corriger :** exiger TLS en production, échouer si STARTTLS n'est pas disponible, et envisager une validation stricte du certificat/nom d'hôte selon le transport choisi. Ne pas activer SMTP AUTH sur une connexion en clair.

### S-07 — Validation d'upload fondée sur le Content-Type fourni par le client

**Priorité : moyenne**

`validate_upload()` contrôle la taille, l'extension/nom et l'appartenance du `content_type` à une liste autorisée. Les routes de documents et de preuves décodent le Base64 et passent le type fourni par le client ; les octets ne sont pas systématiquement identifiés par signature de fichier avant stockage et extraction.

Un client peut donc déclarer un type autorisé pour un contenu d'une autre nature. Le nom et le type sont conservés dans les métadonnées et peuvent influencer les traitements d'extraction.

**À corriger :** détecter le format réel à partir des octets, rejeter les discordances, traiter les fichiers dans un environnement isolé avec limites CPU/mémoire/temps, et servir les téléchargements en pièce jointe avec un type sûr. Conserver la limite de taille actuelle comme plafond complémentaire, pas comme contrôle de contenu.

### S-08 — Protection des secrets d'intégration dépendante des clés d'environnement

**Priorité : moyenne (contrôle opérationnel à formaliser)**

Les tokens Google sont chiffrés avec Fernet via `REVIEW_DEFENSE_GOOGLE_TOKEN_KEY`, et les secrets MFA via `REVIEW_DEFENSE_MFA_ENCRYPTION_KEY`. Le mode production refuse l'absence de clé Google et, sous le libellé exact `production`, l'absence de clé MFA. Ces clés doivent être persistantes, sauvegardées séparément des données chiffrées, renouvelables avec une procédure de re-chiffrement et accessibles uniquement au processus serveur. Aucun gestionnaire de secrets externe ni rotation automatique n'est visible dans les fichiers inspectés.

**À faire :** documenter l'origine, les droits, la rotation, la restauration et la procédure de compromission des clés. Ne jamais les placer dans le frontend, les journaux ou les artefacts de build.

### S-09 — Payload PayPal complet conservé dans l'historique des événements

**Priorité : moyenne, à qualifier selon les champs reçus**

Le webhook PayPal est vérifié auprès de l'API PayPal avant traitement, ce qui est un contrôle positif. Cependant, l'événement reçu est placé tel quel dans `billing_events.payload` dans le chemin de persistance. Le dépôt ne montre pas, dans ce flux, de minimisation ou de filtrage des champs avant archivage.

**À corriger :** inventorier les champs effectivement nécessaires, stocker une projection minimale et expurger les identifiants/données personnelles non nécessaires. Définir une durée de conservation et un contrôle d'accès spécifique à l'historique de facturation.

## Contrôles positifs observés

- Mots de passe : PBKDF2-HMAC-SHA256, sel aléatoire de 16 octets et 310 000 itérations à la création.
- Sessions : bearer token aléatoire de 32 octets, hash SHA-256 persisté, expiration et révocation côté serveur ; l'authentification relit la session et le rôle effectif en base.
- SQL : les opérations repository examinées utilisent des paramètres SQL plutôt que de concaténer les valeurs utilisateur.
- Fichiers : plafond de 25 MiB dans le validateur, noms contrôlés, clés d'objet aléatoires, stockage filesystem avec répertoires `0700` et fichiers `0600`, contrôle tenant et empreinte SHA-256.
- MFA : TOTP à six chiffres, secret chiffré Fernet, vérification à la connexion pour OWNER/ADMIN et compteur anti-rejeu persistant lorsque le repository le fournit.
- Google OAuth : state/PKCE, consommation unique du state dans le composant observé, tokens chiffrés côté serveur.
- Pub/Sub : rejet par défaut si aucun vérificateur n'est fourni ; le vérificateur est injecté et doit effectuer la validation OIDC réelle.
- PayPal : signature vérifiée par l'API officielle avant d'accepter le webhook.
- Réponses API : erreurs internes génériques ; les détails d'exception ne sont pas renvoyés au client dans le chemin WSGI examiné.

## Plan de remédiation proposé

### P0 — à traiter avant d'élargir l'exposition
1. Rendre atomique la consommation du token de récupération et le changement de mot de passe.
2. Appliquer les en-têtes de sécurité à toutes les réponses statiques/HTML.
3. Garantir un rate limiting partagé pour connexion, récupération et routes sensibles.

### P1 — durcissement d'authentification et d'intégration
1. Décider du modèle de stockage du bearer token et réduire la surface XSS/CSP.
2. Unifier le contrôle de configuration MFA pour `prod` et `production`.
3. Rendre TLS SMTP obligatoire en production.
4. Détecter le type réel des fichiers avant stockage/extraction.

### P2 — gouvernance des données et exploitation
1. Minimiser le payload PayPal conservé.
2. Formaliser le cycle de vie, la rotation et la restauration des clés.
3. Compléter l'inventaire des journaux, traces, sauvegardes et données personnelles par environnement.

## Limites de la revue

- Audit statique du code et des configurations du dépôt ; aucun accès à la base de production, aux secrets réels, au proxy, au fournisseur SMTP, à Google, à PayPal ou au système de fichiers de production.
- Impossible de confirmer la configuration effective des variables d'environnement, le partage des limiteurs au niveau de l'infrastructure, les règles réseau, la configuration TLS du proxy ou les droits réels du compte PostgreSQL.
- Les constats décrivent les chemins de code inspectés ; ils ne constituent pas une certification de sécurité ni un avis juridique.

## Exécution

Aucun test, build, typecheck, lint, workflow GitHub Actions, appel réseau applicatif ou accès à la base n'a été effectué. Aucun code runtime n'a été modifié dans ce lot.
