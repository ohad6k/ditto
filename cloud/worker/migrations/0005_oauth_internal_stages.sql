DROP INDEX oauth_diagnostics_created_idx;

ALTER TABLE oauth_diagnostics RENAME TO oauth_diagnostics_v1;

CREATE TABLE oauth_diagnostics (
  diagnostic_id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider TEXT NOT NULL CHECK (provider = 'github'),
  stage TEXT NOT NULL CHECK (
    stage IN ('token_exchange', 'user_lookup', 'identity_write', 'session_write')
  ),
  status_code INTEGER CHECK (status_code BETWEEN 100 AND 599),
  error_code TEXT,
  created_at TEXT NOT NULL
);

INSERT INTO oauth_diagnostics
  (diagnostic_id, provider, stage, status_code, error_code, created_at)
SELECT diagnostic_id, provider, stage, status_code, error_code, created_at
FROM oauth_diagnostics_v1;

DROP TABLE oauth_diagnostics_v1;

CREATE INDEX oauth_diagnostics_created_idx
  ON oauth_diagnostics(created_at DESC);
