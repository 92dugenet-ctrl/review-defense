# Politique de conservation, archivage et effacement

> **Ne pas appliquer les durées proposées sans les valider.** Une durée doit être liée à une finalité, un point de départ, une justification et un mécanisme d'effacement testable. Les durées comptables légales ne s'appliquent pas automatiquement à toutes les données d'un compte.

## Matrice à compléter

| Catégorie | Base / finalité | Durée active | Archivage intermédiaire | Déclencheur d'effacement | Système / preuve |
|---|---|---|---|---|---|
| Compte utilisateur | Gestion du service | Durée du compte | [DURÉE] si litige/obligation | Fermeture + délai | PostgreSQL / ticket |
| Sessions et jetons | Authentification | Durée de session | Aucun ou [ ] | Expiration/révocation | Base / purge |
| MFA et récupération | Sécurité | Tant que nécessaire | [ ] | Désactivation/expiration | Base / purge |
| Avis et dossiers client | Exécution du service | Durée contractuelle | [DURÉE JUSTIFIÉE] | Fin du contrat + demande/instruction | Base |
| Pièces justificatives | Dossier client | [DURÉE] | [ ] | Fin du contrat / instruction | Volume evidence |
| Historique et audit métier | Traçabilité | [DURÉE] | [ ] | Expiration définie | Base |
| Logs sécurité | Sécurité | [DURÉE PAR LOG] | [ ] | Rotation | Logs / SIEM |
| Factures et pièces comptables | Obligations comptables/fiscales | Selon exigence | Selon exigence | Fin du délai légal | Comptabilité |
| Support | Gestion des demandes | [DURÉE] | [ ] | Clôture + délai | Outil support |
| Demandes RGPD | Obligation / preuve | [DURÉE] | [ ] | Échéance justifiée | Table privacy_requests |
| Prospects | Prospection | [DURÉE] | Liste d'opposition minimale | Dernier contact / opposition | CRM |
| Consentements | Preuve du choix | Durée nécessaire à la preuve | [ ] | Fin de nécessité | Table / CMP |
| Sauvegardes | Continuité | Cycle [ ] | [ ] | Rotation automatique | Backup provider |

## Règles d'effacement

- Distinguer suppression logique, suppression des données actives, purge des index/cache, purge des fichiers, et expiration des sauvegardes.
- Ne pas promettre une suppression immédiate des sauvegardes si le système les conserve pendant un cycle technique ; expliquer le délai exact et empêcher la restauration de réintroduire des données devant être supprimées.
- Définir une procédure de gel en cas de litige ou d'obligation légale, avec périmètre et durée documentés.
- La suppression d'un compte ne doit pas entraîner la destruction de données dont le client est responsable sans vérifier le contrat, le rôle et les instructions.
- Documenter l'effacement des jetons Google, clés et identifiants d'intégration lors de la déconnexion.
- Tester périodiquement la restauration d'une sauvegarde et l'application des suppressions après restauration.

## Contrôles techniques à réaliser

1. Lister toutes les tables contenant des données personnelles et les clés de liaison.
2. Lister les fichiers et métadonnées du volume `/data/evidence`.
3. Identifier les journaux Docker, Caddy, Gunicorn, PostgreSQL et outils externes.
4. Identifier sauvegardes, snapshots, réplications, exports manuels et environnements de test.
5. Définir un job de purge idempotent, journalisé, contrôlé et testé.
6. Prévoir un rapport d'effacement par compte/organisation et une attestation au client lorsque nécessaire.
