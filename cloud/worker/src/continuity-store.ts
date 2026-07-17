export const MAX_GENERATIONS = 500;
export const MAX_ACCOUNT_CIPHERTEXT_BYTES = 64 * 1024 * 1024;

const WRITE_STATES = new Set(["trialing", "active", "past_due", "grace"]);

export type StoredGeneration = {
  account_id: string;
  generation_id: string;
  parent_generation_id: string | null;
  author_device_id: string;
  schema_version: string;
  created_at: string;
  received_at: string;
  nonce: string;
  ciphertext: string;
  ciphertext_sha256: string;
  ciphertext_bytes: number;
  head_advanced: number;
  upload_nonce: string;
};

type EntitlementRow = {
  state: string;
  recovery_ends_at: string | null;
};

async function entitlement(
  db: D1Database,
  accountId: string,
): Promise<EntitlementRow | null> {
  return db
    .prepare("SELECT state, recovery_ends_at FROM entitlements WHERE account_id = ?")
    .bind(accountId)
    .first<EntitlementRow>();
}

export async function canWriteContinuity(
  db: D1Database,
  accountId: string,
): Promise<boolean> {
  const row = await entitlement(db, accountId);
  return row !== null && WRITE_STATES.has(row.state);
}

export async function canReadContinuity(
  db: D1Database,
  accountId: string,
  now = new Date(),
): Promise<boolean> {
  const row = await entitlement(db, accountId);
  if (row === null) return false;
  if (WRITE_STATES.has(row.state)) return true;
  return (
    row.recovery_ends_at !== null &&
    Number.isFinite(Date.parse(row.recovery_ends_at)) &&
    Date.parse(row.recovery_ends_at) > now.getTime()
  );
}

export async function currentHead(
  db: D1Database,
  accountId: string,
): Promise<string | null> {
  const row = await db
    .prepare("SELECT generation_id FROM continuity_heads WHERE account_id = ?")
    .bind(accountId)
    .first<{ generation_id: string }>();
  return row?.generation_id ?? null;
}

export async function generation(
  db: D1Database,
  accountId: string,
  generationId: string,
): Promise<StoredGeneration | null> {
  return db
    .prepare(
      `SELECT account_id, generation_id, parent_generation_id, author_device_id,
              schema_version, created_at, received_at, nonce, ciphertext,
              ciphertext_sha256, ciphertext_bytes, head_advanced, upload_nonce
       FROM continuity_generations
       WHERE account_id = ? AND generation_id = ?`,
    )
    .bind(accountId, generationId)
    .first<StoredGeneration>();
}

export async function quotaAvailable(
  db: D1Database,
  accountId: string,
  incomingBytes: number,
): Promise<boolean> {
  const row = await db
    .prepare(
      `SELECT COUNT(*) AS generation_count,
              COALESCE(SUM(ciphertext_bytes), 0) AS ciphertext_bytes
       FROM continuity_generations WHERE account_id = ?`,
    )
    .bind(accountId)
    .first<{ generation_count: number; ciphertext_bytes: number }>();
  return (
    (row?.generation_count ?? 0) < MAX_GENERATIONS &&
    (row?.ciphertext_bytes ?? 0) + incomingBytes <= MAX_ACCOUNT_CIPHERTEXT_BYTES
  );
}

export type GenerationInsert = {
  generationId: string;
  parentGenerationId: string | null;
  authorDeviceId: string;
  schemaVersion: string;
  createdAt: string;
  receivedAt: string;
  nonce: string;
  ciphertext: string;
  ciphertextSha256: string;
  ciphertextBytes: number;
  uploadNonce: string;
};

export async function insertAndAdvance(
  db: D1Database,
  accountId: string,
  value: GenerationInsert,
): Promise<StoredGeneration> {
  const insert = db
    .prepare(
      `INSERT OR IGNORE INTO continuity_generations
       (account_id, generation_id, parent_generation_id, author_device_id,
        schema_version, created_at, received_at, nonce, ciphertext,
        ciphertext_sha256, ciphertext_bytes, head_advanced, upload_nonce)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)`,
    )
    .bind(
      accountId,
      value.generationId,
      value.parentGenerationId,
      value.authorDeviceId,
      value.schemaVersion,
      value.createdAt,
      value.receivedAt,
      value.nonce,
      value.ciphertext,
      value.ciphertextSha256,
      value.ciphertextBytes,
      value.uploadNonce,
    );
  const advance = value.parentGenerationId === null
    ? db
        .prepare(
          `INSERT OR IGNORE INTO continuity_heads (account_id, generation_id, updated_at)
           SELECT ?, ?, ?
           WHERE EXISTS (
             SELECT 1 FROM continuity_generations
             WHERE account_id = ? AND generation_id = ? AND upload_nonce = ?
           )`,
        )
        .bind(
          accountId,
          value.generationId,
          value.receivedAt,
          accountId,
          value.generationId,
          value.uploadNonce,
        )
    : db
        .prepare(
          `UPDATE continuity_heads SET generation_id = ?, updated_at = ?
           WHERE account_id = ? AND generation_id = ?
             AND EXISTS (
               SELECT 1 FROM continuity_generations
               WHERE account_id = ? AND generation_id = ? AND upload_nonce = ?
             )`,
        )
        .bind(
          value.generationId,
          value.receivedAt,
          accountId,
          value.parentGenerationId,
          accountId,
          value.generationId,
          value.uploadNonce,
        );
  const mark = db
    .prepare(
      `UPDATE continuity_generations SET head_advanced = 1
       WHERE account_id = ? AND generation_id = ? AND upload_nonce = ?
         AND EXISTS (
           SELECT 1 FROM continuity_heads
           WHERE account_id = ? AND generation_id = ?
         )`,
    )
    .bind(
      accountId,
      value.generationId,
      value.uploadNonce,
      accountId,
      value.generationId,
    );
  await db.batch([insert, advance, mark]);
  const stored = await generation(db, accountId, value.generationId);
  if (stored === null) throw new Error("continuity generation insert failed");
  return stored;
}

export async function touchDevice(
  db: D1Database,
  deviceId: string,
  timestamp: string,
): Promise<void> {
  await db
    .prepare(
      `UPDATE continuity_devices SET last_seen_at = ?
       WHERE device_id = ? AND revoked_at IS NULL`,
    )
    .bind(timestamp, deviceId)
    .run();
}
