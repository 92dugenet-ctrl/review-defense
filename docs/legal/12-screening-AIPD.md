# Pré-évaluation AIPD — analyse d'impact RGPD

> Cette fiche est un screening initial, pas une AIPD complète. Une AIPD est requise lorsque le traitement est susceptible d'engendrer un risque élevé pour les droits et libertés. La décision de ne pas en réaliser doit être motivée.

## 1. Traitement examiné

- Nom : traitement de contenus d'avis, dossiers et pièces justificatives.
- Responsable : [CLIENT / REVIEW DÉFENSE SELON FLUX].
- Description : [FONCTIONNALITÉS EXACTES].
- Données : [AVIS, IDENTIFIANTS, CONTENUS, PIÈCES, LOGS, DONNÉES SENSIBLES ÉVENTUELLES].
- Personnes : [CLIENTS, AUTEURS D'AVIS, SALARIÉS, PERSONNES CITÉES].
- Volumétrie : [NOMBRE DE CLIENTS / DOSSIERS / PERSONNES].
- Durée : [DURÉES].
- Destinataires : [LISTE].

## 2. Critères de risque à examiner

Répondre OUI / NON / INCONNU et justifier :
- Évaluation ou notation systématique de personnes ?
- Décisions automatisées produisant des effets juridiques ou similaires significatifs ?
- Surveillance systématique ?
- Données sensibles ou hautement personnelles ?
- Traitement à grande échelle ?
- Croisement de jeux de données ?
- Personnes vulnérables ?
- Usage innovant d'une technologie ?
- Exclusion d'un droit, service ou contrat ?
- Traitement systématique de contenus libres pouvant révéler santé, opinions, religion, infractions ou autres données sensibles ?
- Analyse automatisée des auteurs d'avis ou inférence de leur identité ?

## 3. Analyse des scénarios de risque

Pour chaque scénario : menace, vulnérabilité, personnes exposées, gravité, vraisemblance, niveau de risque initial, mesure de réduction, risque résiduel, responsable et échéance.

Scénarios à examiner :
- accès inter-clients ou erreur de cloisonnement ;
- fuite de pièces justificatives ;
- exposition d'avis ou d'informations sensibles dans un prompt ou un outil tiers ;
- réutilisation non autorisée pour entraînement ou amélioration ;
- compte compromis ou invitation mal attribuée ;
- suppression incomplète dans fichiers, logs et sauvegardes ;
- erreur de qualification conduisant à un signalement injustifié ;
- décision automatisée ou profilage non prévu.

## 4. Mesures et décision

Mesures : minimisation, masquage, restriction des champs libres, accès par rôle, MFA, chiffrement, stockage privé, séparation des tenants, revue humaine, transparence, contrôle fournisseur, purge et gestion des incidents.

Décision :
- [AIPD REQUISE / NON REQUISE].
- Motifs détaillés : [ ].
- Consultation DPO / conseil : [ ].
- Consultation préalable de la CNIL si le risque résiduel élevé ne peut être atténué : [À ÉVALUER].
- Validation par le responsable : [NOM / DATE].

## 5. Revue

Revoir l'analyse avant toute nouvelle fonctionnalité, nouveau fournisseur, changement de finalité, augmentation importante des volumes ou incident significatif.
