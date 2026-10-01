# Politique cookies et traceurs — modèle et spécification

> **À publier seulement après un scan réel du site et de l'application.** La liste ci-dessous est une structure, pas l'affirmation que ces traceurs sont installés.

## 1. Information utilisateur — modèle public

Le site et l'application Review Défense peuvent utiliser des cookies ou technologies similaires. Certains sont nécessaires au fonctionnement, à la sécurité ou au maintien de votre choix. D'autres, par exemple pour mesurer l'audience ou personnaliser des contenus, peuvent nécessiter votre consentement préalable selon leur finalité et leur configuration.

Vous pouvez accepter, refuser ou paramétrer les traceurs soumis au consentement. Votre choix est conservé pendant [DURÉE À VALIDER] et peut être modifié à tout moment via le lien « Gérer mes cookies » disponible en bas de page.

## 2. Inventaire réel à effectuer

| Nom du traceur | Émetteur | Finalité | Type | Durée | Domaine | Consentement requis ? | Bloqué avant choix ? |
|---|---|---|---|---|---|---|---|
| [SESSION] | [ ] | Authentification | Strictement nécessaire si indispensable | [ ] | [ ] | À analyser | [ ] |
| [CSRF / SÉCURITÉ] | [ ] | Sécurité | Strictement nécessaire si indispensable | [ ] | [ ] | À analyser | [ ] |
| [ANALYTICS] | [ ] | Mesure d'audience | Selon configuration | [ ] | [ ] | À analyser | [ ] |
| [PIXEL / ADS] | [ ] | Publicité | Non essentiel | [ ] | [ ] | Oui en principe | Oui |
| [EMBED / SOCIAL] | [ ] | Contenu tiers | Selon technologie | [ ] | [ ] | À analyser | [ ] |

## 3. Exigences pour le gestionnaire de consentement

- Aucun traceur soumis au consentement ne doit être déposé ou lu avant un consentement valable.
- Proposer des choix compréhensibles et granulaires par finalité lorsque plusieurs finalités existent.
- Le refus doit être aussi simple que l'acceptation.
- Les cases ne doivent pas être précochées ; le silence ou la poursuite de navigation ne valent pas consentement.
- Enregistrer preuve, date, version de notice, finalités et choix.
- Permettre le retrait aussi simplement que l'acceptation.
- Ne pas assimiler l'acceptation des CGU à un consentement cookies.
- Ne pas déposer de traceur tiers au simple chargement d'une page si le consentement est requis.
- Vérifier le comportement sur sous-domaines, pages de paiement, app et mobile.
- Documenter les traceurs exemptés et la raison précise de l'exemption.

## 4. Procédure de contrôle

1. Scanner le site et l'application en navigation privée, avant choix, après refus, après acceptation et après retrait.
2. Inspecter cookies, localStorage, sessionStorage, pixels, requêtes réseau et scripts tiers.
3. Répéter sur toutes les pages et parcours authentifiés.
4. Vérifier que les préférences sont respectées après navigation et reconnexion.
5. Conserver captures, export HAR et version du gestionnaire.

Référence pratique : recommandations CNIL sur les cookies et traceurs. Le consentement doit être libre, spécifique, éclairé, univoque, préalable et retirable.
