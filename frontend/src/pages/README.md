# Pages React — carte des écrans

Ce dossier contient les composants de page de l'application React compilée par Vite.
Le point d'entrée est `src/main.tsx` et les routes déclarées sont centralisées dans
`src/app/router.tsx`.

## Pages actives — site public

| Route | Composant | Responsabilité |
|---|---|---|
| `/` | `HomePage` | Accueil et présentation |
| `/produit` | `ProductPage` | Présentation du produit |
| `/fonctionnement` | `MethodPage` | Étapes de traitement |
| `/securite` | `SecurityPage` | Contrôles et validation humaine |
| `/tarifs` | `PricingPage` | Catalogue et parcours de paiement actif |
| `/contact` | `ContactPage` | Orientation et contact |

Ces pages composent les sections à partir de `src/components/public/muse/` et du
shell public partagé. Les redirections `/solutions` et `/ressources` sont déclarées
dans le routeur.

## Pages actives — compte et authentification

| Route | Composant | Responsabilité |
|---|---|---|
| `/login` | `LoginPage` | Connexion |
| `/register` | `RegisterPage` | Création d'espace |

## Pages actives — espace authentifié

Toutes les routes ci-dessous sont imbriquées sous `RequireAuth` et `AppShell`.

| Route | Composant | Responsabilité |
|---|---|---|
| `/app/dashboard` | `DashboardPage` | Vue d'ensemble |
| `/app/reviews` | `ReviewsPage` | Liste des avis |
| `/app/reviews/:id` | `ReviewDetailPage` | Détail d'un avis |
| `/app/cases` | `CasesPage` | Liste des dossiers |
| `/app/cases/:id` | `CaseDetailPage` | Détail d'un dossier |
| `/app/analysis` | `AnalysisPage` | Analyse |
| `/app/notifications` | `NotificationsPage` | Notifications |
| `/app/billing` | `BillingPage` | Facturation |
| `/app/settings` | `SettingsPage` | Paramètres |
| `/app/privacy` | `PrivacyPage` | Demandes relatives aux données |
| `/app/admin` | `AdminPage` | Membres, rôles et invitations |

La navigation masque le lien Administration selon le rôle présenté par le contexte
d'authentification. Ce masquage d'interface n'est pas une autorisation : les API
d'administration doivent vérifier les rôles et l'organisation côté serveur.

Les routes légales publiques (`/mentions-legales`, `/confidentialite`, `/cookies`,
`/cgu`, `/cgv`, `/accessibilite`, `/contact-juridique`) partagent
`LegalPage`, qui sélectionne le contenu selon le chemin.

## Fichiers conservés mais non raccordés au routeur

Les fichiers suivants ne sont pas importés par `src/app/router.tsx` actuellement :

- `MusePublicPage.tsx` : ancienne implémentation monolithique de plusieurs pages
  publiques. Elle recoupe les pages Muse modulaires, mais n'est pas une copie
  strictement identique.
- `PublicProductPage.tsx`, `PublicMethodPage.tsx`, `PublicSecurityPage.tsx`,
  `PublicPricingPage.tsx`, `PublicContactPage.tsx` et
  `PublicPageExperiences.tsx` : variantes publiques alternatives.
- `PricingPagePayPal.tsx` : ancien parcours tarifaire autonome exportant lui aussi
  un composant `PricingPage`. Le parcours actif est celui importé par le routeur
  depuis `PricingPage.tsx`; ne pas confondre les deux implémentations.

Ces fichiers sont conservés pour référence et comparaison. Ne pas les raccorder
ou les supprimer sans décision explicite sur le rendu cible, les styles et les
parcours de paiement. Ne pas créer de nouvelles variantes de pages dans ce dossier.

## Règles d'organisation

- Une page = un composant de composition d'écran ; les sections réutilisables vont
  dans `src/components/`.
- Les pages publiques utilisent `src/components/public/` et le shell public.
- Les écrans authentifiés utilisent `AppShell` et les services partagés de `src/`.
- Les appels API passent par `src/services/api/client.ts`.
- Toute modification de route doit être faite dans `src/app/router.tsx` et préserver
  les chemins existants sauf demande explicite.
- Les contrôles d'accès effectifs doivent être imposés par l'API, pas seulement par
  l'affichage conditionnel de la navigation.
