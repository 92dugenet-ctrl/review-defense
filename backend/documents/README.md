# Documents — documents et preuves

## Responsabilité cible

Centraliser les contrats de gestion des documents et preuves : métadonnées, stockage, intégrité, extraction, OCR, accès et cycle de conservation.

## État observé

Ce dossier est actuellement un **emplacement réservé** : aucun module Python n'y est présent dans l'arborescence observée.

Des responsabilités connexes existent encore dans d'autres emplacements :
- `src/evidence_vault.py`
- `src/evidence_extraction.py`
- `src/evidence_ocr.py`
- miroirs transitoires sous `backend/analysis/`

## Frontières à préserver

- Autorisation par organisation et dossier avant toute lecture.
- Intégrité, traçabilité et métadonnées des fichiers.
- Contrat de stockage objet et configuration d'infrastructure.
- Séparation entre document source, texte extrait et faits dérivés.

## Règle de migration

Ne pas déplacer les implémentations depuis `src/` dans cette étape. Définir d'abord le contrat de stockage et les consommateurs, puis extraire les composants un par un sans changer les chemins de stockage ni les permissions.
