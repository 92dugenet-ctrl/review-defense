# Audit technique RGPD préliminaire — constats vérifiables

> État du dépôt : branche main consultée le 1er octobre 2026. Audit statique du code source uniquement. Aucun accès à la production, aux consoles fournisseurs, aux bases de données réelles, aux journaux d'exploitation, aux sauvegardes ni aux comptes clients.

## 1. Identité juridique de l'exploitant

L'exploitant a communiqué exercer en France sous la forme d'une entreprise individuelle (EI), sous le nom Gabriel Dugenet / « Dugenet Gabriel ». Review Défense est le nom du service ; son statut de nom commercial ou de marque reste à confirmer sur justificatif. L'identité n'a pas été vérifiée auprès du RNE.

Conséquences : les contrats doivent identifier Gabriel Dugenet, entrepreneur individuel (EI), et non une société distincte. Aucun capital social ne doit être mentionné. L'adresse, le SIREN, le SIRET, l'immatriculation applicable, la TVA, les coordonnées professionnelles et l'hébergeur restent à compléter. Voir `16-identite-juridique-EI.md` et `17-audit-statut-EI.md`.

## 1. Périmètre examiné

- `src/api_server.py`
- `src/privacy_service.py`
- `src/identity.py`
- `src/evidence_vault.py`
- `src/production_config.py`
- `src/security_hardening.py`
- `src/postgres_api_repository.py`
- `migrations/024_v641_rgpd_privacy_workflow.sql`
- `migrations/029_v643_processing_architecture.sql`
- `.env.example`
- `docker-compose.production.yml`
- `requirements.txt`
- tests de sécurité, intégration et opérations.

## 2. Constats techniques

### T01 — Demandes de droits : fondation présente, parcours incomplet

**Preuve repérée :** `api_server.py` expose GET/POST/PATCH sur `/v1/privacy/requests`, avec types ACCESS, RECTIFICATION, ERASURE, RESTRICTION, OBJECTION et PORTABILITY. La migration 024 crée `privacy_requests` et une échéance par défaut de 30 jours.

**Limites observées :**
- les routes de l'API passent par l'authentification utilisateur ; aucun canal public de demande pour une personne dont les données figurent dans un avis ou un dossier n'a été identifié ;
- la route PATCH permet les statuts RECEIVED, IN_REVIEW, COMPLETED et REJECTED, mais le code observé ne démontre pas un workflow complet de vérification, instruction, réponse et preuve de clôture ;
- le champ `details` accepte un objet JSON libre ; prévoir validation, minimisation et prévention de la collecte de justificatifs excessifs ;
- le dépôt ne démontre pas un mécanisme d'alerte d'échéance, d'escalade ni de contrôle qualité des réponses ;
- l'assistance du sous-traitant au client responsable de traitement doit être formalisée séparément.

**Action :** créer un canal privacy externe, un workflow d'identité proportionné, une horloge de délai, des modèles de réponse, une piste d'audit durable et des tests de bout en bout.

### T02 — Export de données : périmètre explicitement limité

**Preuve repérée :** `GET /v1/privacy/export` appelle `_privacy_export`. La fonction retourne les données de compte, les demandes, les consentements et certains événements d'audit issus du store mémoire. Le payload indique explicitement que les données métier appartenant à l'organisation ne sont pas couvertes automatiquement.

**Risque :** ne pas présenter cette route comme un export exhaustif au titre des articles 15 ou 20. Il faut distinguer l'accès aux données personnelles de la portabilité, dont le champ est plus étroit, et traiter les données selon le rôle du client et de Review Défense.

**Action :** définir un inventaire des systèmes et un export par personne et par rôle, avec filtres de droits des tiers, données métier, fichiers, historique, destinataires et format. Documenter les limites et faire valider la portée.

### T03 — Effacement et fermeture de compte : preuve non identifiée

**Preuve repérée :** dans les routes examinées de `api_server.py`, aucune route explicite de suppression de compte ou d'effacement complet n'a été trouvée. La présence d'une demande ERASURE n'est pas la preuve d'une suppression automatisée.

**Action :** implémenter un workflow de suppression/archivage qui couvre compte, membres, jetons, MFA, intégrations, dossiers, pièces, caches, journaux, exports et sauvegardes, avec exceptions documentées et suppression post-restauration. Ne pas supprimer les données d'un client sans vérifier les instructions et responsabilités.

### T04 — Consentements : table et endpoints présents, preuve de consentement à renforcer

**Preuve repérée :** migration 024 crée `privacy_consents` avec `purpose`, `policy_version`, `granted`, `granted_at` et `withdrawn_at`. Les routes GET/POST permettent de consulter et enregistrer un choix.

**Limites observées :**
- le code accepte une finalité et une version de politique fournies par l'appelant, sans démonstration d'un catalogue contrôlé de finalités ;
- un choix `granted=false` crée un nouvel enregistrement avec `withdrawn_at`, sans démontrer la mise à jour cohérente de la preuve initiale ni l'arrêt effectif du traitement ;
- aucune preuve de bannière cookies/CMP bloquant les traceurs non essentiels n'a été établie dans ce contrôle statique.

**Action :** séparer consentement RGPD et consentement cookies/ePrivacy ; implémenter finalités, preuve, retrait, synchronisation avec les tags et tests réseau avant/après choix.

### T05 — Cloisonnement PostgreSQL : RLS activé, configuration à vérifier

**Preuve repérée :** migration 024 active RLS et crée des politiques basées sur `current_setting('app.organization_id', true)`. D'autres migrations utilisent également des politiques tenant-scoped.

**Point de contrôle :** la migration 024 ne montre pas `FORCE ROW LEVEL SECURITY` sur ces deux tables. Il faut vérifier le rôle PostgreSQL réellement utilisé en production : propriétaire des tables, superutilisateur ou rôle doté de `BYPASSRLS` peuvent modifier l'effet pratique de RLS. Ne pas conclure à une fuite sans examiner le rôle et les connexions.

**Action :** auditer les grants, propriétaire, rôle applicatif, initialisation/effacement du contexte de tenant à chaque transaction, pooling et tests croisés. Envisager FORCE RLS et des tests dédiés si compatibles avec le modèle d'exploitation.

### T06 — Pièces justificatives : stockage persistant, cycle de vie à documenter

**Preuve repérée :** `docker-compose.production.yml` déclare un volume PostgreSQL et un volume `review_defense_evidence` monté sur `/data/evidence`. `evidence_vault.py` contient un adaptateur filesystem et des contrôles d'isolation par organisation.

**Limites observées :** le dépôt ne prouve pas le chiffrement au repos, le scan antivirus en production, la politique de sauvegarde, la localisation du volume, la gestion des accès opérateurs, la purge automatique ou la suppression des sauvegardes. Le fallback de stockage local dans `/tmp` en production doit être éliminé ou strictement interdit si la configuration attendue manque.

**Action :** vérifier la configuration de production réelle, stockage privé, chiffrement, antivirus, permissions système, sauvegardes chiffrées, restauration et purge.

### T07 — Sous-traitants et transferts : inventaire incomplet

**Preuve repérée :** dépendances/variables indiquent PostgreSQL, SMTP, Google Business Profile et PayPal. Le code inclut OCR et traitement de pièces.

**Limites observées :** le dépôt ne révèle pas les contrats fournisseurs, les entités contractantes, régions de données, lieux de support, sous-traitants ultérieurs, réutilisation des données ni mécanismes de transfert.

**Action :** compléter le registre fournisseur avec les contrats, DPA, listes de sous-traitants, lieux de traitement et garanties de transfert.

### T08 — IA : qualification non établie

**Preuve repérée :** le code visible comprend extraction, OCR, classification de signaux et suggestions de faits. Les dépendances et variables d'environnement examinées ne suffisent pas à démontrer un fournisseur de modèle génératif externe.

**Limites observées :** impossible de conclure que le produit n'utilise pas d'IA dans un environnement, service ou intégration non présent dans les fichiers examinés. La qualification AI Act et les obligations RGPD dépendent des fonctions réellement activées et des rôles.

**Action :** inventaire exhaustif du code, appels réseau, secrets d'environnement (sans divulguer les valeurs), fournisseurs, prompts, données envoyées et décisions influencées.

### T09 — Pages juridiques publiques : routes présentes, contenu dédié non démontré

**Preuve repérée :** les routes `/mentions-legales/`, `/confidentialite/`, `/cgv/`, `/cgu/`, `/cookies/`, `/securite/`, `/conservation-donnees/`, `/droits-rgpd/`, `/violation-donnees/`, `/sous-traitants/` et `/ia-et-controle-humain/` sont redirigées vers le shell `index.html` dans le routeur observé.

**Action :** créer les pages dédiées, puis vérifier qu'elles sont servies avec un contenu adapté et accessibles depuis le footer et les formulaires. Les modèles avec champs incomplets doivent rester en environnement de préproduction.

### T10 — Tests RGPD : couverture insuffisante

**Preuve repérée :** les tests comprennent un test de construction d'export qui retire certains secrets, mais les tests repérés ne démontrent pas un parcours complet d'exercice des droits, d'effacement, de retrait de consentement, de purge de fichiers et de sauvegardes ou de réponse à une violation.

**Action :** créer tests API + PostgreSQL + multi-tenant + délais + exports + suppression + audit + restauration + CMP.

## 3. Niveau de maturité préliminaire

Ce document n'attribue pas de score de conformité. Les fondations techniques sont réelles mais plusieurs obligations documentaires et opérationnelles ne sont pas démontrées par le dépôt. Le statut global doit rester **« conformité non démontrée — plan de remédiation en cours »** tant que les preuves de production et les documents contractuels ne sont pas réunis.

## 4. Preuves nécessaires hors dépôt

- Accès lecture seule aux consoles hébergeur, DNS, sauvegardes, e-mail, Google, PayPal, analytics et éventuels fournisseurs IA.
- Export des variables d'environnement **sans secrets** : noms, fonctions et régions.
- Contrats, DPA, conditions fournisseurs et listes de sous-traitants.
- Configuration réelle PostgreSQL : rôles, grants, RLS, backups, chiffrement.
- Configuration réelle du stockage de preuves.
- Scan cookies et traceurs sur toutes les pages et dans l'application.
- Parcours réels d'inscription, paiement, synchronisation Google, upload, support et fermeture de compte.
- Politique de conservation actuelle et procédure de support.

## 5. Conclusion

Le dépôt contient des composants de sécurité, de cloisonnement et de gestion des droits, mais ceux-ci ne démontrent pas à eux seuls une conformité RGPD complète. Les priorités sont l'identité du responsable, le registre, le DPA, l'inventaire des sous-traitants et transferts, l'effectivité des droits, l'effacement réel, les cookies et la conservation des données. Une validation juridique finale doit être réalisée par un professionnel compétent après collecte des informations manquantes.
