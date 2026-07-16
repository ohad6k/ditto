PRAGMA foreign_keys = ON;

CREATE TABLE accounts (
  account_id TEXT PRIMARY KEY
    CHECK (length(account_id) = 37 AND substr(account_id, 1, 5) = 'acct_'),
  created_at TEXT NOT NULL
);

CREATE TABLE billing_customers (
  provider TEXT NOT NULL CHECK (provider = 'polar'),
  provider_customer_id TEXT NOT NULL,
  account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
  external_customer_id TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (provider, provider_customer_id),
  UNIQUE (provider, external_customer_id),
  CHECK (external_customer_id = account_id)
);

CREATE INDEX billing_customers_account_idx
  ON billing_customers(account_id);

CREATE TABLE billing_events (
  provider TEXT NOT NULL CHECK (provider = 'polar'),
  event_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL CHECK (length(payload_sha256) = 64),
  effective_at TEXT NOT NULL,
  received_at TEXT NOT NULL,
  processing_result TEXT NOT NULL CHECK (
    processing_result IN ('applied', 'stale', 'unknown-account', 'customer-conflict')
  ),
  PRIMARY KEY (provider, event_id)
);

CREATE INDEX billing_events_effective_idx
  ON billing_events(provider, effective_at);

CREATE TABLE entitlements (
  account_id TEXT PRIMARY KEY REFERENCES accounts(account_id) ON DELETE CASCADE,
  state TEXT NOT NULL CHECK (
    state IN ('none', 'trialing', 'active', 'past_due', 'grace', 'ended', 'refunded')
  ),
  product_code TEXT NOT NULL CHECK (
    product_code IN ('founding-monthly', 'founding-yearly')
  ),
  provider TEXT NOT NULL CHECK (provider = 'polar'),
  provider_subscription_id TEXT NOT NULL,
  provider_customer_id TEXT NOT NULL,
  provider_product_id TEXT NOT NULL,
  provider_effective_at TEXT NOT NULL,
  provider_event_id TEXT NOT NULL,
  current_period_end TEXT,
  grace_ends_at TEXT,
  recovery_ends_at TEXT,
  updated_at TEXT NOT NULL,
  UNIQUE (provider, provider_subscription_id),
  FOREIGN KEY (provider, provider_customer_id)
    REFERENCES billing_customers(provider, provider_customer_id)
);

CREATE INDEX entitlements_state_idx ON entitlements(state);
