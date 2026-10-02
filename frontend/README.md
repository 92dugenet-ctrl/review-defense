# Review Defense — espace client et administration

Le répertoire `frontend/` contient le site public et l’espace applicatif client/admin.

## Espace applicatif

- `workspace.html` : point d’entrée servi sur les routes espace.
- `workspace.js` : authentification, navigation par rôle, appels API, listes, fiches détaillées et actions.
- `workspace.css` : interface responsive et continuité visuelle avec le site public.

## Intégration backend

L’interface consomme les contrats HTTP versionnés sous `/v1` : authentification et profil, avis, dossiers, preuves, file de traitement, escalades SLA, approbations, équipe, notifications, soumissions et catalogue de facturation.

Les permissions de navigation sont une aide d’interface uniquement : le backend reste l’autorité pour authentifier, autoriser et valider chaque mutation. Les actions de décision, d’approbation, de gel et de soumission restent soumises aux garde-fous serveur et à une confirmation explicite.

## Parcours

1. Analyser et consulter les avis.
2. Créer et suivre un dossier.
3. Ajouter et vérifier les preuves.
4. Préparer les faits, contradictions et checklist.
5. Enregistrer les décisions, validations et soumissions autorisées.
6. Suivre les notifications et les échéances SLA.

## Vérifications

La CI doit exécuter la vérification syntaxique de `workspace.js`, les tests backend et les tests d’intégration PostgreSQL. Une validation navigateur sur les routes `/connexion`, `/inscription`, `/client` et `/admin` reste nécessaire avant mise en production.

## Limites fonctionnelles connues

L’interface n’exécute pas une action externe de publication de réponse à un avis. Elle expose uniquement les opérations réellement proposées par le backend. Les notifications créées dans la file ne signifient pas qu’un email ou webhook a été délivré.
