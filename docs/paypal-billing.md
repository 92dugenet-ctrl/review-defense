# Review Defense — PayPal Billing

## Target

PayPal is the primary payment provider for the first commercial billing implementation.

PayPal REST APIs use OAuth 2.0. Sandbox and production use separate API endpoints. Sandbox credentials are isolated from live money.

## Environment

Required server-side variables:

- `PAYPAL_ENV=sandbox`
- `PAYPAL_CLIENT_ID`
- `PAYPAL_CLIENT_SECRET`

Optional:

- `PAYPAL_WEBHOOK_ID`
- `PAYPAL_RETURN_URL`
- `PAYPAL_CANCEL_URL`

Never expose the client secret to the frontend.

## Functional rules

The application owns:

- plan catalog;
- loyalty pricing;
- subscription entitlement state;
- audit prices;
- defense-step prices;
- credit ledger;
- billing-event idempotency.

PayPal owns:

- payment authorization/capture;
- subscription/payment transaction state;
- provider-side transaction identifiers.

## Subscription rule

A cancellation at period end keeps the entitlement active until the provider confirms the subscription has actually ended.

A new subscription after cancellation starts at the then-current public price. Previous loyalty pricing is not restored automatically.

## Defense rule

Each additional defense step requires:

1. Review Defense recommends the next step.
2. Review Defense displays the exact incremental price.
3. Customer explicitly validates the paid step.
4. PayPal payment is created/captured.
5. A verified provider event activates the step.
6. Work proceeds.

Payment never triggers an external Google action automatically.

## Webhook rule

Every provider event is persisted using its provider event ID as an idempotency key. Duplicate deliveries must be harmless.

## Launch sequence

1. Create PayPal Developer application.
2. Create Sandbox Business and Personal accounts.
3. Configure credentials in the deployment secret store.
4. Register webhook endpoint and store its identifier.
5. Run subscription, one-off, cancellation, failed-payment and duplicate-webhook tests.
6. Only after Sandbox certification, switch credentials/endpoints to production.
