# src — backend actuellement exécuté

## Rôle

`src/` contient la base Python actuellement utilisée par l'application. Ce n'est pas simplement un ancien dossier à vider : ses modules sont importés par le point d'entrée de production.

## Chemin de démarrage

```text
scripts/start_production.sh
  └─ Gunicorn
      └─ wsgi:app
          ├─ src.api_server.create_app
          └─ src.seo_site (rendu des pages SEO)
```

## Organisation actuelle par responsabilité

| Groupe | Modules représentatifs |
|---|---|
| Composition API | `api_server.py`, `app.py`, `app_shell.py` |
| Identité et sécurité | `identity.py`, `identity_repository.py`, `mfa.py`, `recovery_email.py`, `security_hardening.py` |
| Dossiers | `case_*.py`, `decision_workspace.py`, `submission_workspace.py`, `outcome_workspace.py`, `escalation_workflow.py` |
| Avis et Google | `review_*.py`, `google_*.py`, `case_review*.py` |
| Analyse et preuves | `contradiction_*.py`, `evidence_*.py`, `policy_workspace.py` |
| Notifications | `notification_*.py`, `postgres_notification_worker.py`, `alert_workspace.py`, `ops_alerts.py` |
| Facturation | `billing*.py`, `paypal_client.py` |
| Persistance et plateforme | `database.py`, `postgres_*.py`, `deployment.py`, `production_config.py`, `observability.py`, `resilience.py` |
| SEO et pages publiques | `seo_*.py` |

Ce tableau sert de repère de lecture; il ne remplace pas l'analyse des imports et des consommateurs.

## Règles de maintenance

- Garder `wsgi.py` et `src.api_server.create_app` compatibles.
- Ne pas déplacer un module sur la seule base de son nom.
- Vérifier les imports directs et transitifs avant chaque extraction.
- Préserver les routes, payloads JSON, statuts, permissions et effets de persistance.
- Ne pas changer les ports, le démarrage, les migrations ou les intégrations dans un chantier de layout.
- Extraire un seul domaine à la fois et maintenir une compatibilité d'import pendant la transition.

## Relation avec backend/

`backend/` est la cible de classement par domaines. Un module n'est considéré migré que lorsque son implémentation de référence, ses imports, ses consommateurs et ses tests ont été basculés et vérifiés. Les copies présentes dans `backend/` ne doivent pas être activées ni synchronisées en bloc.
