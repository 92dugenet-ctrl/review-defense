-- Review Defense V6.40 / PayPal billing foundation
-- Numbered migration 023 follows the repository migration contract.

CREATE TABLE IF NOT EXISTS billing_customers (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    provider TEXT NOT NULL DEFAULT 'paypal',
    provider_customer_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (organization_id, provider)
);

CREATE TABLE IF NOT EXISTS plans (
    id BIGSERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    public_price_cents INTEGER NOT NULL,
    loyalty_floor_cents INTEGER NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'EUR',
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    plan_code TEXT NOT NULL REFERENCES plans(code),
    provider TEXT NOT NULL DEFAULT 'paypal',
    provider_subscription_id TEXT UNIQUE,
    status TEXT NOT NULL,
    public_price_cents INTEGER NOT NULL,
    current_price_cents INTEGER NOT NULL,
    continuous_months INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ,
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
    canceled_at TIMESTAMPTZ,
    paused_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS loyalty_history (
    id BIGSERIAL PRIMARY KEY,
    subscription_id BIGINT NOT NULL REFERENCES subscriptions(id),
    old_price_cents INTEGER,
    new_price_cents INTEGER NOT NULL,
    continuous_months INTEGER NOT NULL,
    reason TEXT NOT NULL,
    effective_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS one_off_orders (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    order_type TEXT NOT NULL,
    reference_id TEXT,
    amount_cents INTEGER NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'EUR',
    provider TEXT NOT NULL DEFAULT 'paypal',
    provider_order_id TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS credit_transactions (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    order_id BIGINT REFERENCES one_off_orders(id),
    transaction_type TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    balance_after_cents INTEGER NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS billing_events (
    id BIGSERIAL PRIMARY KEY,
    provider TEXT NOT NULL DEFAULT 'paypal',
    provider_event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    resource_id TEXT,
    organization_id BIGINT,
    payload_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'RECEIVED',
    processed_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO plans(code, public_price_cents, loyalty_floor_cents)
VALUES
    ('essential', 4900, 3700),
    ('professional', 8900, 6900),
    ('business', 15900, 11900)
ON CONFLICT (code) DO NOTHING;
