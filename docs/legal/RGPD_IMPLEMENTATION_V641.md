# Review Defense — RGPD approfondi V6.41

## Objectif

Le bloc RGPD approfondi ajoute un parcours technique permettant de :

- recevoir et tracer les demandes de droits ;
- distinguer les demandes personnelles des données métier de l'organisation ;
- produire un export des données de compte disponibles ;
- enregistrer les consentements optionnels lorsqu'ils sont utilisés ;
- permettre aux OWNER/ADMIN de suivre l'état des demandes ;
- conserver une traçabilité d'audit des opérations RGPD.

## Architecture

Le parcours reste aligné avec l'architecture cible :

**eCloud Serve → API Review Defense → PostgreSQL/Supabase → stockage privé R2 → sauvegardes séparées**

Les contrôles d'autorisation sont réalisés côté serveur. Les données RGPD restent tenant-scoped par `organization_id`.

## Endpoints

- `GET /v1/privacy/export` — export JSON des données personnelles de compte disponibles via l'API.
- `GET /v1/privacy/requests` — consultation des demandes de l'utilisateur.
- `POST /v1/privacy/requests` — création d'une demande de droit.
- `GET /v1/privacy/requests?scope=organization` — vue organisation réservée OWNER/ADMIN.
- `PATCH /v1/privacy/requests/{id}` — changement d'état réservé OWNER/ADMIN.
- `GET /v1/privacy/consents` — consultation des consentements optionnels enregistrés.
- `POST /v1/privacy/consents` — enregistrement d'un consentement optionnel ou de son retrait.

Types de demandes supportés :

**ACCESS · RECTIFICATION · ERASURE · RESTRICTION · OBJECTION · PORTABILITY**

États :

**RECEIVED → IN_REVIEW → COMPLETED / REJECTED**

## Base PostgreSQL

La migration `024_v641_rgpd_privacy_workflow.sql` crée :

- `privacy_requests`
- `privacy_consents`

Le numéro `024` est volontaire : la migration `002_v59_google_sync.sql` occupe déjà la version `002`. Le runner identifie les migrations par leur numéro, qui doit donc rester unique.

Les deux tables sont protégées par PostgreSQL Row Level Security et la variable de transaction `app.organization_id`.

## Contrôle humain

Une demande d'effacement ou de limitation ne déclenche pas une suppression irréversible automatique.

Le système enregistre la demande, permet son traitement par un utilisateur habilité et conserve la trace de l'évolution. Les obligations légales, les données nécessaires à la preuve, à la sécurité ou à la facturation peuvent nécessiter un traitement distinct.

## Export

L'export actuel est explicitement limité aux données personnelles de compte disponibles via ce parcours. Il ne prétend pas exporter automatiquement l'intégralité des données métier d'une organisation.

Avant lancement commercial, le périmètre exact des données exportables doit être rapproché du registre des traitements, du contrat client et des rôles responsable/sous-traitant.

## Points de finalisation avant production

1. Vérifier que la migration PostgreSQL est appliquée sur l'environnement cible.
2. Vérifier que le repository de production expose les opérations RGPD correspondantes.
3. Tester les demandes sur plusieurs organisations pour confirmer l'isolation RLS.
4. Tester export, rectification, effacement et limitation avec les données réelles de test.
5. Définir les durées finales de conservation et le traitement des sauvegardes.
6. Documenter les fournisseurs, localisations et transferts internationaux définitifs.
7. Faire valider juridiquement les textes avant commercialisation.
