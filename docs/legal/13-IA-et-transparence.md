# Inventaire IA, transparence et contrôle humain

> À compléter à partir du code, des appels réseau, des contrats fournisseurs et des fonctions réellement activées. Ne pas affirmer qu'un modèle est utilisé ou non sans audit de l'ensemble des environnements.

## 1. Inventaire des systèmes

| Fonction | Modèle / fournisseur | Rôle de Review Défense | Données envoyées | Région | Réutilisation fournisseur | Base / DPA | Classe AI Act |
|---|---|---|---|---|---|---|---|
| Extraction / classification d'avis | [CODE LOCAL OU MODÈLE] | [FOURNISSEUR / DÉPLOYEUR] | [ ] | [ ] | [ ] | [ ] | [À QUALIFIER] |
| Suggestion de réponse | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| OCR / extraction de pièces | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Assistant conversationnel | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

## 2. Contrôles RGPD

- Déterminer la finalité et la base légale de chaque usage.
- Minimiser les données et éviter l'envoi de données identifiantes lorsque non nécessaire.
- Vérifier les paramètres de rétention, d'entraînement et de revue humaine du fournisseur.
- Encadrer le fournisseur par contrat et clauses de sous-traitance lorsque requis.
- Évaluer les transferts hors EEE.
- Informer les utilisateurs des usages pertinents.
- Prévoir un mécanisme de correction et de validation humaine.
- Ne pas prendre de décision produisant des effets juridiques ou similaires significatifs uniquement sur une sortie automatisée sans analyse de l'article 22.

## 3. AI Act

Pour chaque système, qualifier si Review Défense est fournisseur, déployeur ou les deux, identifier la catégorie de risque et les obligations correspondantes. L'AI Act prévoit une application échelonnée ; les obligations de transparence de l'article 50 commencent à s'appliquer le 2 août 2026. Examiner notamment l'information des personnes lorsqu'elles interagissent directement avec un système d'IA et les obligations de marquage/détection de certains contenus générés ou manipulés par IA, lorsque les cas visés sont concernés.

Évaluer aussi les obligations de maîtrise de l'IA des personnes intervenant pour l'entreprise, la documentation technique, les instructions d'utilisation, la supervision humaine et la conservation des preuves selon le rôle et la catégorie du système.

## 4. Règles produit minimales

- Identifier clairement les suggestions produites par IA.
- Indiquer que la sortie peut être erronée et doit être vérifiée.
- Conserver une trace de la validation humaine pour toute action externe.
- Ne pas présenter une analyse automatisée comme une qualification juridique définitive.
- Ne pas envoyer de contenu client à un modèle externe sans base légale, information, instruction et garanties contractuelles adéquates.
- Prévoir un interrupteur ou une configuration de désactivation si l'usage n'est pas nécessaire au service.

## 5. Preuves à conserver

Inventaire de modèles, versions, fournisseurs, régions, DPA, prompts types, tests de biais/erreurs pertinents, notices utilisateurs, captures des interfaces, procédures de validation, journal des actions et revues périodiques.
