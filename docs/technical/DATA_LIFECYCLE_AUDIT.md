# Audit du cycle de vie des données — lot N

> Revue statique de la branche `develop` au 3 octobre 2026. Aucun accès à une base réelle, aucun export de données, aucune restauration et aucune exécution de tests n'ont été effectués.

## Synthèse

Le parcours runtime observé est `scripts/start_production.sh` → `scripts/migrate.py` → `migrations/*.sql`. PostgreSQL et les preuves sont conservés dans deux volumes Docker distincts. Les politiques RLS et les métadonnées de preuve existent, mais la sauvegarde PostgreSQL seule ne constitue pas une sauvegarde complète du système.

Le lot N harmonise les identifiants et empreintes des migrations dans les deux runners et sécurise les arguments et permissions des scripts de sauvegarde/restauration. Il ne modifie aucune migration SQL déjà publiée et ne supprime aucun fichier historique.

## 1. Chaîne des migrations

### Source runtime

- `scripts/start_production.sh` appelle `scripts/migrate.py` avant Gunicorn.
- `scripts/migrate.py` lit `migrations/*.sql`, par ordre lexical.
- L'identifiant stable est désormais le nom complet sans extension, par exemple `023_v640_session_restore`.
- Le registre `schema_migrations` conserve `version`, `filename`, `checksum` et `applied_at`.
- Le verrou advisory est partagé avec `src/migration_runner.py`, afin de sérialiser les lanceurs qui utilisent ce contrat.

### Écarts historiques constatés

- `migrations/` contient 35 entrées SQL ; `database/migrations/` n'en contient que 30, plus un README. Les deux arborescences ne sont donc pas des copies synchronisées.
- Les fichiers `023_v640_session_restore.sql` et `023_v70_paypal_billing.sql` partagent le préfixe numérique `023`. Un runner qui identifie une migration par ce seul préfixe provoque une collision.
- L'ancien `src/migration_runner.py` identifiait les versions par préfixe numérique et attendait une colonne `filename` non nullable. Le runner de démarrage utilisait le nom complet et ne créait pas les colonnes `filename` et `checksum`.
- `scripts/dr_validate.py` lit `schema_migrations.checksum`. Le schéma créé par l'ancien runner de démarrage ne garantissait pas cette colonne.

### Contrat unifié dans le lot N

Les deux runners utilisent désormais le nom complet du fichier comme identifiant, le même verrou advisory et les colonnes `filename` et `checksum`. Les entrées historiques sans empreinte sont complétées à partir du fichier correspondant ; une divergence déjà renseignée provoque une erreur plutôt qu'une réexécution silencieuse.

La migration `023_v70_paypal_billing.sql` n'est pas renommée : cela évite de changer l'identité d'une migration potentiellement déjà appliquée. La seconde arborescence n'est pas synchronisée automatiquement.

## 2. Sauvegarde et restauration PostgreSQL

### Ce que font les scripts

- `scripts/postgres_backup.py` utilise `pg_dump --format=custom --no-owner`.
- Le mot de passe extrait de l'URL PostgreSQL est transmis via `PGPASSWORD`, pas dans la ligne de commande.
- `scripts/postgres_restore.py` utilise `pg_restore --clean --if-exists --no-owner`.
- La restauration exige une URL cible explicite et `--confirm`. Elle ne retombe pas sur `DATABASE_URL`.

### Corrections du lot N

- La restauration retire désormais le mot de passe de l'argument `--dbname` et le transmet via l'environnement du processus.
- Les sauvegardes locales sont créées avec des permissions `0600`; les liens symboliques sont refusés et les fichiers partiels sont supprimés en cas d'échec de `pg_dump`.
- Le script de sauvegarde refuse toujours d'écraser un fichier sans `--overwrite`.

### Limites opérationnelles qui restent à traiter

- `pg_dump` ne sauvegarde que PostgreSQL. Les fichiers d'évidence sont dans un volume Docker séparé (`/data/evidence`) ; ils doivent faire l'objet d'une sauvegarde indépendante.
- Aucun stockage distant, chiffrement au repos des archives, rétention, rotation, contrôle d'accès externe ou journal d'archivage n'est implémenté par ces deux scripts.
- Une sauvegarde PostgreSQL et une sauvegarde du volume de preuves doivent être coordonnées et identifiées comme un même point de reprise.
- `pg_restore --clean` remplace les objets de la cible. La confirmation de commande n'est pas un substitut à une procédure d'autorisation et de validation de la cible.

## 3. Preuves et fichiers

- `src/evidence_vault.py` sépare les octets des métadonnées métier et construit des clés sous `evidence/{organization_id}/{evidence_id}/...`.
- L'adaptateur filesystem vérifie le préfixe tenant, résout le chemin sous la racine autorisée, crée les répertoires en `0700` et les fichiers en `0600`.
- La table `api_evidence` conserve notamment l'organisation, le dossier, le nom, le type, la taille, le SHA-256, la clé objet et les informations de vérification.
- Les volumes `review_defense_evidence` et `review_defense_staging_evidence` sont distincts des volumes PostgreSQL.

À clarifier avant une exploitation durable : sauvegarde/restauration conjointe des métadonnées et octets, vérification périodique des empreintes, suppression cohérente des fichiers et lignes SQL, stratégie de rétention et traitement des objets orphelins. Aucun processus de purge automatique n'a été identifié dans le parcours runtime documenté.

## 4. Cloisonnement multi-organisation

- Les repositories PostgreSQL installent `app.organization_id` avec `set_config(..., true)` dans la transaction tenant-scoped.
- Les migrations activent les politiques RLS sur les tables portant `organization_id`; la migration 020 applique `ENABLE` et `FORCE ROW LEVEL SECURITY` aux tables alors présentes.
- Les migrations 033 et 034 ajoutent explicitement `FORCE ROW LEVEL SECURITY` à des tables tenant-scoped ajoutées après la migration de fiabilité.
- Les transactions sans tenant existent pour des parcours précis d'identification avant résolution de l'organisation ; elles doivent rester limitées à ces usages.

La présence d'une politique RLS ne remplace pas le contrôle d'autorisation applicatif. Toute nouvelle table avec `organization_id` doit recevoir une politique `USING` et `WITH CHECK`, et être forcée lorsque le rôle applicatif est propriétaire de la table. Les tables d'identité globales, comme `users`, ne sont pas des tables tenant-scoped par nature : leur accès doit passer par les adhésions et les services d'identité.

## 5. Confidentialité, conservation et effacement

- `privacy_requests` et `privacy_consents` sont tenant-scoped et protégées par RLS.
- La suppression d'une organisation cascade sur plusieurs tables via les clés étrangères ; certaines relations utilisateur utilisent `RESTRICT` ou `SET NULL`.
- Le service de confidentialité valide les catégories et statuts de demandes et masque les secrets dans les exports.

L'existence d'un type de demande `ERASURE` ne prouve pas qu'un effacement complet et propagé est implémenté. Les durées de conservation par catégorie, les exceptions de gel, l'effacement des preuves du volume, la purge des sauvegardes expirées et la preuve d'exécution doivent être définis explicitement. Aucun délai de rétention global n'est déduit du code observé.

## 6. Actions opérationnelles à planifier

- Définir une destination de sauvegarde distincte du serveur applicatif, chiffrée et avec accès restreint.
- Définir une rétention par type de données et un calendrier de rotation des archives.
- Sauvegarder PostgreSQL et le volume de preuves avec un identifiant de point de reprise commun.
- Documenter les étapes de restauration, les contrôles d'intégrité et la procédure de retour arrière.
- Définir les délais de conservation, la purge des preuves et la gestion des objets orphelins.
- Maintenir `migrations/` comme source runtime unique tant que la migration de l'arborescence historique n'a pas été arbitrée.

## Périmètre de vérification

Revue limitée à la lecture des sources, SQL, manifests et scripts suivis dans Git. Aucun test, build, typecheck, workflow, accès à PostgreSQL, dump, restauration ou manipulation de données réelles n'a été effectué.
