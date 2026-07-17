import type { Env } from "./contracts";
import { authenticateBrowserSession } from "./session";

const TOKEN_PATTERN = /^[A-Za-z0-9_-]{43}$/;
const DEVICE_PATTERN = /^dev_[a-f0-9]{32}$/;
const WRITE_STATES = new Set(["trialing", "active", "past_due", "grace"]);

function json(status: number, body: unknown): Response {
  return Response.json(body, {
    status,
    headers: {
      "cache-control": "no-store",
      "content-security-policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
      "referrer-policy": "no-referrer",
      "x-content-type-options": "nosniff",
    },
  });
}

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary)
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replace(/=+$/, "");
}

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

function deviceId(bytes: Uint8Array): string {
  return `dev_${Array.from(bytes, (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("")}`;
}

async function browserAccount(
  request: Request,
  env: Env,
  now: Date,
): Promise<string | null> {
  const session = await authenticateBrowserSession(request, env.DB, now);
  return session?.accountId ?? null;
}

async function canWrite(db: D1Database, accountId: string): Promise<boolean> {
  const row = await db
    .prepare("SELECT state FROM entitlements WHERE account_id = ?")
    .bind(accountId)
    .first<{ state: string }>();
  return row !== null && WRITE_STATES.has(row.state);
}

export async function handlePairStart(request: Request, env: Env): Promise<Response> {
  const now = new Date();
  const accountId = await browserAccount(request, env, now);
  if (accountId === null) return json(401, { status: "unauthorized" });
  if (!(await canWrite(env.DB, accountId))) {
    return json(403, { status: "pro-required" });
  }
  const active = await env.DB.prepare(
    "SELECT COUNT(*) AS count FROM continuity_devices WHERE account_id = ? AND revoked_at IS NULL",
  )
    .bind(accountId)
    .first<{ count: number }>();
  if ((active?.count ?? 0) >= 5) return json(409, { status: "device-limit" });

  const pairingCode = base64Url(crypto.getRandomValues(new Uint8Array(32)));
  const createdAt = now.toISOString();
  const expiresAt = new Date(now.getTime() + 10 * 60 * 1000).toISOString();
  await env.DB.batch([
    env.DB.prepare("DELETE FROM continuity_pairing_grants WHERE expires_at <= ?").bind(
      createdAt,
    ),
    env.DB.prepare(
      `INSERT INTO continuity_pairing_grants
       (code_hash, account_id, created_at, expires_at)
       VALUES (?, ?, ?, ?)`,
    ).bind(await sha256(pairingCode), accountId, createdAt, expiresAt),
  ]);
  return json(201, { pairingCode, expiresIn: 600 });
}

type PairingBody = {
  pairingCode: string;
  label: string;
  keyAgreementPublicKey: string;
  wrappedMasterKey: Record<string, unknown>;
  clientVersion: string;
};

function validatePairingBody(value: unknown): PairingBody | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return null;
  const body = value as Record<string, unknown>;
  if (
    JSON.stringify(Object.keys(body).sort()) !==
    JSON.stringify([
      "clientVersion",
      "keyAgreementPublicKey",
      "label",
      "pairingCode",
      "wrappedMasterKey",
    ])
  ) return null;
  if (
    typeof body.pairingCode !== "string" ||
    !TOKEN_PATTERN.test(body.pairingCode) ||
    typeof body.label !== "string" ||
    body.label.length < 1 ||
    body.label.length > 64 ||
    /[\u0000-\u001f\u007f]/.test(body.label) ||
    typeof body.keyAgreementPublicKey !== "string" ||
    !TOKEN_PATTERN.test(body.keyAgreementPublicKey) ||
    typeof body.clientVersion !== "string" ||
    !/^[0-9A-Za-z][0-9A-Za-z.+-]{0,31}$/.test(body.clientVersion) ||
    typeof body.wrappedMasterKey !== "object" ||
    body.wrappedMasterKey === null ||
    Array.isArray(body.wrappedMasterKey)
  ) return null;
  const wrapped = body.wrappedMasterKey as Record<string, unknown>;
  const expectedWrapped = [
    "ciphertext",
    "device_public_key",
    "ephemeral_public_key",
    "nonce",
    "salt",
    "schema_version",
  ];
  if (JSON.stringify(Object.keys(wrapped).sort()) !== JSON.stringify(expectedWrapped)) {
    return null;
  }
  if (
    wrapped.schema_version !== "emulo.continuity-device-wrap/v1" ||
    wrapped.device_public_key !== body.keyAgreementPublicKey ||
    typeof wrapped.ephemeral_public_key !== "string" ||
    !TOKEN_PATTERN.test(wrapped.ephemeral_public_key) ||
    typeof wrapped.salt !== "string" ||
    !/^[A-Za-z0-9_-]{22}$/.test(wrapped.salt) ||
    typeof wrapped.nonce !== "string" ||
    !/^[A-Za-z0-9_-]{16}$/.test(wrapped.nonce) ||
    typeof wrapped.ciphertext !== "string" ||
    !/^[A-Za-z0-9_-]{64}$/.test(wrapped.ciphertext) ||
    JSON.stringify(wrapped).length > 2048
  ) return null;
  return body as PairingBody;
}

export async function handlePairComplete(request: Request, env: Env): Promise<Response> {
  if (!/^application\/json(?:\s*;|$)/i.test(request.headers.get("content-type") ?? "")) {
    return json(415, { status: "content-type-required" });
  }
  const declaredLength = Number(request.headers.get("content-length") ?? "0");
  if (Number.isFinite(declaredLength) && declaredLength > 8192) {
    return json(413, { status: "payload-too-large" });
  }
  let parsed: unknown;
  try {
    const raw = await request.text();
    if (raw.length > 8192) return json(413, { status: "payload-too-large" });
    parsed = JSON.parse(raw);
  } catch {
    return json(400, { status: "invalid-request" });
  }
  const body = validatePairingBody(parsed);
  if (body === null) return json(400, { status: "invalid-request" });
  const now = new Date();
  const consumed = await env.DB.prepare(
    `DELETE FROM continuity_pairing_grants
     WHERE code_hash = ? AND expires_at > ?
     RETURNING account_id`,
  )
    .bind(await sha256(body.pairingCode), now.toISOString())
    .first<{ account_id: string }>();
  if (consumed === null) return json(400, { status: "pairing-invalid" });
  if (!(await canWrite(env.DB, consumed.account_id))) {
    return json(403, { status: "pro-required" });
  }
  const active = await env.DB.prepare(
    "SELECT COUNT(*) AS count FROM continuity_devices WHERE account_id = ? AND revoked_at IS NULL",
  )
    .bind(consumed.account_id)
    .first<{ count: number }>();
  if ((active?.count ?? 0) >= 5) return json(409, { status: "device-limit" });

  const rawDeviceId = deviceId(crypto.getRandomValues(new Uint8Array(16)));
  const deviceToken = base64Url(crypto.getRandomValues(new Uint8Array(32)));
  const timestamp = now.toISOString();
  await env.DB.prepare(
    `INSERT INTO continuity_devices
     (device_id, account_id, label, key_agreement_public_key,
      wrapped_master_key, token_hash, client_version, created_at,
      last_seen_at, revoked_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)`,
  )
    .bind(
      rawDeviceId,
      consumed.account_id,
      body.label,
      body.keyAgreementPublicKey,
      JSON.stringify(body.wrappedMasterKey),
      await sha256(deviceToken),
      body.clientVersion,
      timestamp,
      timestamp,
    )
    .run();
  return json(201, { deviceId: rawDeviceId, deviceToken });
}

export async function authenticateDevice(
  request: Request,
  db: D1Database,
  _now = new Date(),
): Promise<{ accountId: string; deviceId: string } | null> {
  const authorization = request.headers.get("authorization");
  const match = /^Bearer ([A-Za-z0-9_-]{43})$/.exec(authorization ?? "");
  if (match === null) return null;
  const row = await db.prepare(
    `SELECT account_id, device_id FROM continuity_devices
     WHERE token_hash = ? AND revoked_at IS NULL`,
  )
    .bind(await sha256(match[1]))
    .first<{ account_id: string; device_id: string }>();
  return row === null ? null : { accountId: row.account_id, deviceId: row.device_id };
}

export async function handleListDevices(request: Request, env: Env): Promise<Response> {
  const accountId = await browserAccount(request, env, new Date());
  if (accountId === null) return json(401, { status: "unauthorized" });
  const rows = await env.DB.prepare(
    `SELECT device_id, label, client_version, created_at, last_seen_at, revoked_at
     FROM continuity_devices WHERE account_id = ? ORDER BY created_at, device_id`,
  )
    .bind(accountId)
    .all<{
      device_id: string;
      label: string;
      client_version: string;
      created_at: string;
      last_seen_at: string;
      revoked_at: string | null;
    }>();
  return json(200, {
    devices: rows.results.map((row) => ({
      deviceId: row.device_id,
      label: row.label,
      clientVersion: row.client_version,
      createdAt: row.created_at,
      lastSeenAt: row.last_seen_at,
      state: row.revoked_at === null ? "active" : "revoked",
    })),
  });
}

export async function handleRevokeDevice(
  request: Request,
  env: Env,
  rawDeviceId: string,
): Promise<Response> {
  if (!DEVICE_PATTERN.test(rawDeviceId)) return json(404, { status: "not-found" });
  const now = new Date();
  const accountId = await browserAccount(request, env, now);
  if (accountId === null) return json(401, { status: "unauthorized" });
  const result = await env.DB.prepare(
    `UPDATE continuity_devices SET revoked_at = COALESCE(revoked_at, ?)
     WHERE device_id = ? AND account_id = ?`,
  )
    .bind(now.toISOString(), rawDeviceId, accountId)
    .run();
  return result.meta.changes === 0
    ? json(404, { status: "not-found" })
    : new Response(null, { status: 204, headers: { "cache-control": "no-store" } });
}
