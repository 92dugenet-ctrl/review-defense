-- V6.41 PayPal billing ledger
CREATE TABLE IF NOT EXISTS billing_transactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  offer_id text NOT NULL,
  kind text NOT NULL,
  status text NOT NULL,
  currency text NOT NULL DEFAULT 'EUR',
  amount numeric(12,2),
  paypal_order_id text,
  paypal_subscription_id text,
  paypal_event_id text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, paypal_order_id),
  UNIQUE (paypal_event_id)
);
CREATE INDEX IF NOT EXISTS idx_billing_org_created ON billing_transactions(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_paypal_sub ON billing_transactions(paypal_subscription_id);
ALTER TABLE billing_transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY billing_transactions_org_isolation ON billing_transactions
  USING (organization_id::text = current_setting('app.organization_id', true));

-- V6.42 Billing identifier integrity: PayPal identifiers are globally unique.
CREATE UNIQUE INDEX IF NOT EXISTS uq_billing_paypal_order_global
  ON billing_transactions(paypal_order_id) WHERE paypal_order_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_billing_paypal_subscription_global
  ON billing_transactions(paypal_subscription_id) WHERE paypal_subscription_id IS NOT NULL;
