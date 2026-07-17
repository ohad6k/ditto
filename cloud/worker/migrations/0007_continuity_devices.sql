CREATE TABLE continuity_pairing_grants (
  code_hash TEXT PRIMARY KEY CHECK (length(code_hash) = 64),
  account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  CHECK (
    expires_at > created_at
    AND unixepoch(expires_at) - unixepoch(created_at) <= 600
  )
);

CREATE INDEX continuity_pairing_grants_expiry_idx
  ON continuity_pairing_grants(expires_at);

CREATE TABLE continuity_devices (
  device_id TEXT PRIMARY KEY CHECK (
    length(device_id) = 36 AND substr(device_id, 1, 4) = 'dev_'
  ),
  account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
  label TEXT NOT NULL CHECK (length(label) BETWEEN 1 AND 64),
  key_agreement_public_key TEXT NOT NULL CHECK (length(key_agreement_public_key) = 43),
  wrapped_master_key TEXT NOT NULL CHECK (length(wrapped_master_key) BETWEEN 100 AND 2048),
  token_hash TEXT NOT NULL UNIQUE CHECK (length(token_hash) = 64),
  client_version TEXT NOT NULL CHECK (length(client_version) BETWEEN 1 AND 32),
  created_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  revoked_at TEXT
);

CREATE INDEX continuity_devices_account_idx
  ON continuity_devices(account_id, revoked_at, created_at);
