# Consolidation des branches — 2026-10-02

## Périmètre

- Branche cible : `develop`.
- `main` n'a pas été modifiée.
- Aucune branche source n'a été supprimée.
- Les branches historiques n'ont pas été copiées en bloc : les versions présentes sur `develop` sont souvent plus récentes et remplacent déjà leurs anciennes implémentations.
- Les fichiers identiques, les ajouts déjà présents et les fonctionnalités portées dans une architecture plus récente sont considérés comme intégrés.

## Branches sans commits propres par rapport à develop

Les branches ci-dessous sont en retard sur `develop` et n'apportent aucun commit unique à réintégrer :

- `audit/phase-zero-2026-10-02`
- `baseline/v6.40-core`
- `certify-business-chain-run`
- `consolidation/code-unification-20261002`
- `content/front-copy-hourly-2026-10-01`
- `feat/v6-40-white-blue-premium`
- `freeze/infrastructure-v6.40`
- `frontend-cycle-4`
- `restore/services-before-production-refactor`
- `restore/services-last-known-good`
- `ux/v640-premium-landing`

## Branches divergentes examinées

| Branche | Éléments examinés et décision |
|---|---|
| `archive/pre-core-reset-2026-09-28` | Les scripts E2E et tests frontend sont identiques à `develop`. Les versions de `app.js` et `public.js` sont plus anciennes ; le CSS public est identique. Pas de remplacement. |
| `audit/muse-modular-20260930` | Les composants Muse et pages ajoutés sont présents sur `develop`. Le workflow CI de la branche est antérieur au workflow actuel ; conservation de la version actuelle. |
| `audit/public-routes-cleanup` | Le CSS public et les routes de style sont déjà présents. Le workflow et l'ancien index React sont antérieurs à l'architecture actuelle. |
| `automation/revue-defense-006` | `frontend/assets/dossier-timeline.css` est identique à `develop`. |
| `chore/public-site-coherent-audit` | Les trois visuels SVG sont identiques à ceux de `develop`. Les anciennes pages monolithiques ont été remplacées par les pages et composants Muse actuels. |
| `content/front-copy-2026-09-30` | Les pages fonctionnement, ressources et services sont identiques. Les autres versions sont antérieures ; la branche contient notamment la faute « Tarifss », absente de `develop`. |
| `feat/about-editorial-muse-layout` | `frontend/about.html` est identique à `develop`. |
| `feat/frontend-consistent-layout` | Ancienne version de `public.js`, remplacée par une version plus complète sur `develop`. |
| `feat/frontend-short-home` | Ancienne version de `public.css` et des assets marketing ; les règles et pages actuelles sont plus complètes. |
| `feature/client-monitoring-hub` | Le hub client, le profil, les documents et le parcours Google sont présents dans les versions actuelles de `frontend/assets/app.js` et `frontend/workspace.js`. Les routes backend et le stockage ont évolué sur `develop`. La migration du hub a été renumérotée pour éviter le conflit de numéro. |
| `feature/paypal-billing-v1` | Les primitives de facturation, le client PayPal, les tests et la documentation sont présents dans les versions actuelles. Les migrations et scripts historiques ne doivent pas remplacer la chaîne de migrations actuelle. Les suppressions historiques ne sont pas réappliquées aveuglément. |
| `fix/v6-40-e2e-dashboard-assertion` | L'ancien script E2E est plus court et a été remplacé par une version plus complète sur `develop`. |
| `frontend/client-admin-workspace` | Les fichiers workspace et leurs contrats de test sont présents sur `develop`. Les versions actuelles sont plus complètes ; les symboles/fonctions de la branche sont déjà couverts. |
| `processing-architecture-staging` | `src/processing_jobs.py` et la migration 029 sont identiques à `develop`. Le test présent sur `develop` conserve la correction de syntaxe déjà apportée. |
| `tmp-commercial-rebuild` | Le CSS public et le script E2E sont identiques. Le hero vidéo est déjà présent dans la version actuelle de `public.js`, qui contient davantage de code. |
| `ui/v6-40-premium-console` | Le CSS de console premium est déjà repris sur `develop`, avec des règles supplémentaires. |
| `work/lot-a-foundation-20261002` | Les trois fichiers d'authentification et de client API examinés sont identiques à `develop`. |

## Conclusion de consolidation

À la date de cet audit, les apports utiles identifiés dans les branches secondaires sont déjà présents dans `develop`, soit à l'identique, soit sous une implémentation plus récente. Aucun remplacement en bloc n'a été effectué afin de préserver les versions plus complètes de `develop`.

Les branches sources restent disponibles pour une dernière revue avant toute suppression future. Cette opération n'a pas modifié `main` et n'a supprimé aucune branche.
