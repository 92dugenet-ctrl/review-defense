# PayPal — Review Defense Sandbox / FR + EN

## 🇫🇷 Français

### Objectif

Ce dossier prépare PayPal **avant l'intégration du checkout dans Review Defense**.

Le script `scripts/paypal/setup_sandbox.py` utilise l'API REST PayPal Sandbox pour créer :

- le produit **Review Defense** ;
- **Essential — 49 € / mois** ;
- **Professional — 89 € / mois** ;
- **Business — 159 € / mois**.

Il ne modifie pas le frontend et n'active aucun paiement réel.

### Sécurité

Le Client Secret doit rester côté serveur et dans les variables d'environnement. Il ne doit jamais être ajouté à GitHub, au frontend, à un commit ou au fichier `paypal-sandbox-config.json`.

Variables prévues :

```text
PAYPAL_ENVIRONMENT=sandbox
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_HOME_URL=https://review-defense.com
PAYPAL_PRODUCT_ID=
PAYPAL_PLAN_ESSENTIAL_ID=
PAYPAL_PLAN_PROFESSIONAL_ID=
PAYPAL_PLAN_BUSINESS_ID=
```

### Exécution

Depuis la racine du projet :

```bash
python scripts/paypal/setup_sandbox.py
```

Le script génère localement :

```text
paypal-sandbox-config.json
```

Ce fichier contient les IDs PayPal utiles à l'étape suivante et est explicitement exclu de Git.

### Fidélité

Les tarifs de fidélité Review Defense restent :

| Formule | Départ | 4–6 mois | 7–12 mois | Année 2 | Année 3+ |
|---|---:|---:|---:|---:|---:|
| Essential | 49 € | 46 € | 43 € | 40 € | 37 € |
| Professional | 89 € | 84 € | 79 € | 74 € | 69 € |
| Business | 159 € | 149 € | 139 € | 129 € | 119 € |

Le provisioning ne transforme pas ces paliers en modification globale du prix du plan PayPal. La gestion individualisée sera faite lors de l'intégration des abonnements, afin d'éviter de modifier involontairement le tarif d'autres clients.

### Ce qui reste volontairement pour l'intégration suivante

- PayPal JavaScript SDK / boutons ;
- création et capture des Orders pour les achats ponctuels ;
- création des Subscriptions ;
- association compte Review Defense ↔ client PayPal ;
- webhooks et vérification des signatures ;
- historique des paiements ;
- remboursements ;
- annulation / suspension ;
- pages de succès et d'annulation ;
- interface bilingue FR/EN ;
- emails bilingues ;
- passage Sandbox → Live.

---

## 🇬🇧 English

### Purpose

This folder prepares PayPal **before the PayPal Checkout integration is added to Review Defense**.

The `scripts/paypal/setup_sandbox.py` script uses the PayPal REST Sandbox API to create:

- the **Review Defense** product;
- **Essential — €49 / month**;
- **Professional — €89 / month**;
- **Business — €159 / month**.

It does not modify the frontend and does not activate real payments.

### Security

The Client Secret must remain server-side and inside environment variables. Never commit it to GitHub, expose it to the frontend, put it in a commit, or write it to `paypal-sandbox-config.json`.

Expected variables:

```text
PAYPAL_ENVIRONMENT=sandbox
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_HOME_URL=https://review-defense.com
PAYPAL_PRODUCT_ID=
PAYPAL_PLAN_ESSENTIAL_ID=
PAYPAL_PLAN_PROFESSIONAL_ID=
PAYPAL_PLAN_BUSINESS_ID=
```

### Run

From the repository root:

```bash
python scripts/paypal/setup_sandbox.py
```

The script generates locally:

```text
paypal-sandbox-config.json
```

This contains the PayPal IDs needed for the next stage and is explicitly excluded from Git.

### Loyalty pricing

The Review Defense loyalty schedule remains:

| Plan | Starting | 4–6 months | 7–12 months | Year 2 | Year 3+ |
|---|---:|---:|---:|---:|---:|
| Essential | €49 | €46 | €43 | €40 | €37 |
| Professional | €89 | €84 | €79 | €74 | €69 |
| Business | €159 | €149 | €139 | €129 | €119 |

Provisioning does not turn these tiers into a global PayPal plan-price mutation. Individualized pricing will be handled during subscription integration so another customer's price is not changed accidentally.

### Intentionally deferred to the integration phase

- PayPal JavaScript SDK / buttons;
- Orders creation and capture for one-off purchases;
- Subscriptions creation;
- Review Defense account ↔ PayPal customer mapping;
- webhooks and signature verification;
- payment history;
- refunds;
- cancellation / suspension;
- success and cancel pages;
- FR/EN interface;
- bilingual emails;
- Sandbox → Live transition.

### Official PayPal references

- REST authentication: https://developer.paypal.com/api/rest/authentication
- Product creation: https://developer.paypal.com/api/catalog-products/v1/products-create/
- PayPal REST API requests: https://developer.paypal.com/api/make-api-requests/
- Sandbox accounts: https://developer.paypal.com/sandbox-testing/accounts


### Provisioning via GitHub Actions

Le dépôt contient aussi `.github/workflows/paypal-sandbox-provision.yml`.

Dans **Settings → Secrets and variables → Actions → New repository secret**, ajoute :

- `PAYPAL_CLIENT_ID`
- `PAYPAL_CLIENT_SECRET`

Tu peux aussi fournir les IDs déjà existants si le provisioning a déjà été exécuté :

- `PAYPAL_PRODUCT_ID`
- `PAYPAL_PLAN_ESSENTIAL_ID`
- `PAYPAL_PLAN_PROFESSIONAL_ID`
- `PAYPAL_PLAN_BUSINESS_ID`

Ensuite : **Actions → PayPal Sandbox Provisioning → Run workflow**.

Le workflow ne s'exécute que manuellement et reste limité au Sandbox. Le résultat est fourni comme artefact temporaire pendant 7 jours. Les secrets sont gérés par GitHub Actions et ne sont pas écrits dans le dépôt.

### Provisioning through GitHub Actions

The repository also contains `.github/workflows/paypal-sandbox-provision.yml`.

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

- `PAYPAL_CLIENT_ID`
- `PAYPAL_CLIENT_SECRET`

You can also provide existing IDs if provisioning has already been run:

- `PAYPAL_PRODUCT_ID`
- `PAYPAL_PLAN_ESSENTIAL_ID`
- `PAYPAL_PLAN_PROFESSIONAL_ID`
- `PAYPAL_PLAN_BUSINESS_ID`

Then: **Actions → PayPal Sandbox Provisioning → Run workflow**.

The workflow is manual-only and restricted to Sandbox. The result is uploaded as a temporary artifact for 7 days. GitHub Actions manages the secrets and they are never written to the repository.
