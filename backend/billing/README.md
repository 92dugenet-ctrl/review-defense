# Billing — facturation et paiements

## Responsabilité cible

Regrouper le catalogue d'offres, les règles de facturation et l'adaptateur de paiement. Le domaine Billing orchestre les opérations de paiement sans exposer les secrets ni déléguer les décisions d'accès à l'interface.

## Fichiers présents

- `billing_catalog.py` : catalogue et définition des offres.
- `billing_service.py` : orchestration de la facturation.
- `paypal_client.py` : client d'intégration PayPal.

## Dépendances sensibles

- Identifiant d'organisation et abonnement associé.
- Webhooks, idempotence, état de paiement et synchronisation.
- Secrets et configuration PayPal sandbox / production.
- Droits d'accès aux fonctionnalités et états d'abonnement.

## Source exécutée

Le runtime utilise encore les modules correspondants de `src/`. Les fichiers de ce dossier sont l'organisation cible et ne constituent pas une activation de la nouvelle arborescence.

## Règle d'extraction

Préserver les URLs de retour, contrats webhook, validations de signature, clés d'idempotence, statuts et comportement de souscription. Ne jamais déplacer de secret dans le code ou la documentation.
