-- V6.42 Billing identifier integrity: PayPal identifiers are globally unique.
CREATE UNIQUE INDEX IF NOT EXISTS uq_billing_paypal_order_global
  ON billing_transactions(paypal_order_id) WHERE paypal_order_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_billing_paypal_subscription_global
  ON billing_transactions(paypal_subscription_id) WHERE paypal_subscription_id IS NOT NULL;
