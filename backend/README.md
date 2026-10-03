# Backend — organisation par domaine

Les sous-répertoires de `backend/` organisent progressivement les responsabilités métier : API, identité, organisations, permissions, avis, dossiers, analyse, documents, notifications et facturation.

## Source d'exécution actuelle

- `wsgi.py` importe `src.api_server.create_app`.
- `src/api_server.py` reste le point de composition HTTP actif.
- Les services et adaptateurs exécutés par l'application restent ceux importés depuis `src/`.

Les modules présents dans `backend/` ne deviennent pas automatiquement la source d'exécution du seul fait de leur emplacement. Avant tout déplacement ou remplacement : cartographier imports et consommateurs, préserver les contrats API, puis faire une extraction limitée à un domaine. Ne pas synchroniser les fichiers par copie aveugle et ne pas supprimer les versions historiques sans preuve d'absence d'usage.
