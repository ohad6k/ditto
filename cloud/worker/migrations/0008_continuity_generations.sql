CREATE TABLE continuity_generations (
  account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
  generation_id TEXT NOT NULL CHECK (
    length(generation_id) = 24 AND substr(generation_id, 1, 4) = 'gen_'
  ),
  parent_generation_id TEXT CHECK (
    parent_generation_id IS NULL OR
    (length(parent_generation_id) = 24 AND substr(parent_generation_id, 1, 4) = 'gen_')
  ),
  author_device_id TEXT NOT NULL REFERENCES continuity_devices(device_id),
  schema_version TEXT NOT NULL CHECK (
    schema_version = 'emulo.continuity-envelope/v1'
  ),
  created_at TEXT NOT NULL,
  received_at TEXT NOT NULL,
  nonce TEXT NOT NULL CHECK (length(nonce) = 16),
  ciphertext TEXT NOT NULL CHECK (length(ciphertext) BETWEEN 22 AND 262168),
  ciphertext_sha256 TEXT NOT NULL CHECK (length(ciphertext_sha256) = 64),
  ciphertext_bytes INTEGER NOT NULL CHECK (
    ciphertext_bytes BETWEEN 16 AND 196624
  ),
  head_advanced INTEGER NOT NULL DEFAULT 0 CHECK (head_advanced IN (0, 1)),
  upload_nonce TEXT NOT NULL UNIQUE CHECK (length(upload_nonce) = 64),
  PRIMARY KEY (account_id, generation_id)
);

CREATE INDEX continuity_generations_account_received_idx
  ON continuity_generations(account_id, received_at, generation_id);

CREATE TABLE continuity_heads (
  account_id TEXT PRIMARY KEY REFERENCES accounts(account_id) ON DELETE CASCADE,
  generation_id TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (account_id, generation_id)
    REFERENCES continuity_generations(account_id, generation_id)
);
