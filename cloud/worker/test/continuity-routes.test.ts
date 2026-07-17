import { env } from "cloudflare:workers";
import { SELF } from "cloudflare:test";
import { beforeEach, describe, expect, it } from "vitest";

import { resolveOrCreateGitHubIdentity } from "../src/auth-store";
import type { Env } from "../src/contracts";

const testEnv = env as unknown as Env;
const ACCOUNT_ID = "acct_0123456789abcdef0123456789abcdef";
const OTHER_ACCOUNT_ID = "acct_ffffffffffffffffffffffffffffffff";
const DEVICE_ID = "dev_0123456789abcdef0123456789abcdef";
const OTHER_DEVICE_ID = "dev_ffffffffffffffffffffffffffffffff";
const DEVICE_TOKEN = "a".repeat(43);
const OTHER_DEVICE_TOKEN = "b".repeat(43);
const PLAIN_MARKER = "SYNTHETIC_RAW_SESSION_MUST_NEVER_REACH_D1";

async function sha256Hex(value: string | Uint8Array): Promise<string> {
  const bytes = typeof value === "string" ? new TextEncoder().encode(value) : value;
  const copy = new Uint8Array(bytes.byteLength);
  copy.set(bytes);
  const digest = await crypto.subtle.digest("SHA-256", copy.buffer);
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}

async function account(accountId: string, providerId: string) {
  await resolveOrCreateGitHubIdentity(testEnv.DB, {
    providerUserId: providerId,
    proposedAccountId: accountId,
    createdAt: "2026-07-17T12:00:00.000Z",
  });
}

async function entitlement(
  accountId: string,
  state = "active",
  recoveryEndsAt: string | null = null,
) {
  const customer = `customer_${accountId}`;
  await testEnv.DB.batch([
    testEnv.DB.prepare(
      `INSERT INTO billing_customers
       (provider, provider_customer_id, account_id, external_customer_id, updated_at)
       VALUES ('polar', ?, ?, ?, ?)`,
    ).bind(customer, accountId, accountId, "2026-07-17T12:01:00.000Z"),
    testEnv.DB.prepare(
      `INSERT INTO entitlements
       (account_id, state, product_code, provider, provider_subscription_id,
        provider_customer_id, provider_product_id, provider_effective_at,
        provider_event_id, current_period_end, grace_ends_at, recovery_ends_at,
        updated_at)
       VALUES (?, ?, 'founding-monthly', 'polar', ?, ?, ?, ?, ?, ?, NULL, ?, ?)`,
    ).bind(
      accountId,
      state,
      `subscription_${accountId}`,
      customer,
      testEnv.POLAR_MONTHLY_PRODUCT_ID,
      "2026-07-17T12:01:00.000Z",
      `event_${accountId}`,
      "2026-08-17T12:01:00.000Z",
      recoveryEndsAt,
      "2026-07-17T12:01:00.000Z",
    ),
  ]);
}

async function device(
  accountId: string,
  deviceId: string,
  token: string,
  revokedAt: string | null = null,
) {
  await testEnv.DB.prepare(
    `INSERT INTO continuity_devices
     (device_id, account_id, label, key_agreement_public_key,
      wrapped_master_key, token_hash, client_version, created_at,
      last_seen_at, revoked_at)
     VALUES (?, ?, 'Test device', ?, ?, ?, '0.3.8', ?, ?, ?)`,
  )
    .bind(
      deviceId,
      accountId,
      "A".repeat(43),
      JSON.stringify({ encrypted: "B".repeat(128) }),
      await sha256Hex(token),
      "2026-07-17T12:02:00.000Z",
      "2026-07-17T12:02:00.000Z",
      revokedAt,
    )
    .run();
}

async function envelope(
  generationId: string,
  parentGenerationId: string | null,
  authorDeviceId = DEVICE_ID,
) {
  const ciphertextBytes = new TextEncoder().encode(`${PLAIN_MARKER}:${generationId}`);
  return {
    schema_version: "emulo.continuity-envelope/v1",
    generation_id: generationId,
    parent_generation_id: parentGenerationId,
    author_device_id: authorDeviceId,
    created_at: "2026-07-17T12:03:00Z",
    nonce: base64Url(new Uint8Array(12).fill(7)),
    ciphertext: base64Url(ciphertextBytes),
    ciphertext_sha256: await sha256Hex(ciphertextBytes),
  };
}

function request(path: string, token: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  headers.set("authorization", `Bearer ${token}`);
  return SELF.fetch(`https://api.example${path}`, { ...init, headers });
}

async function upload(body: unknown, token = DEVICE_TOKEN) {
  return request("/v1/continuity/generations", token, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

describe("encrypted continuity generations", () => {
  beforeEach(async () => {
    await testEnv.DB.batch([
      testEnv.DB.prepare("DELETE FROM continuity_heads"),
      testEnv.DB.prepare("DELETE FROM continuity_generations"),
      testEnv.DB.prepare("DELETE FROM continuity_pairing_grants"),
      testEnv.DB.prepare("DELETE FROM continuity_devices"),
      testEnv.DB.prepare("DELETE FROM browser_sessions"),
      testEnv.DB.prepare("DELETE FROM oauth_identities"),
      testEnv.DB.prepare("DELETE FROM oauth_flows"),
      testEnv.DB.prepare("DELETE FROM entitlements"),
      testEnv.DB.prepare("DELETE FROM billing_events"),
      testEnv.DB.prepare("DELETE FROM billing_customers"),
      testEnv.DB.prepare("DELETE FROM accounts"),
    ]);
    await account(ACCOUNT_ID, "12345678");
    await entitlement(ACCOUNT_ID);
    await device(ACCOUNT_ID, DEVICE_ID, DEVICE_TOKEN);
  });

  it("stores an authenticated ciphertext generation and exposes its head", async () => {
    const first = await envelope("gen_00000000000000000001", null);
    const response = await upload(first);
    expect(response.status).toBe(201);
    expect(await response.json()).toMatchObject({
      status: "stored",
      generationId: first.generation_id,
      head: first.generation_id,
      headAdvanced: true,
      idempotent: false,
    });

    const head = await request("/v1/continuity/head", DEVICE_TOKEN);
    expect(head.status).toBe(200);
    expect(await head.json()).toEqual({ generationId: first.generation_id });

    const downloaded = await request(
      `/v1/continuity/generations/${first.generation_id}`,
      DEVICE_TOKEN,
    );
    expect(downloaded.status).toBe(200);
    expect(await downloaded.json()).toEqual(first);

    const rowText = JSON.stringify(
      await testEnv.DB.prepare("SELECT * FROM continuity_generations").first(),
    );
    expect(rowText).not.toContain(PLAIN_MARKER);
  });

  it("rejects digest mismatch, spoofed authors, and malformed envelopes", async () => {
    const badDigest = await envelope("gen_00000000000000000002", null);
    badDigest.ciphertext_sha256 = "0".repeat(64);
    expect((await upload(badDigest)).status).toBe(400);

    const spoofed = await envelope(
      "gen_00000000000000000003",
      null,
      OTHER_DEVICE_ID,
    );
    expect((await upload(spoofed)).status).toBe(403);

    expect((await upload({ ciphertext: "not-an-envelope" })).status).toBe(400);
    expect(
      await testEnv.DB.prepare("SELECT COUNT(*) AS count FROM continuity_generations").first(),
    ).toEqual({ count: 0 });
  });

  it("is idempotent for an exact replay and rejects generation ID reuse", async () => {
    const first = await envelope("gen_00000000000000000004", null);
    expect((await upload(first)).status).toBe(201);
    const replay = await upload(first);
    expect(replay.status).toBe(200);
    expect(await replay.json()).toMatchObject({ idempotent: true, headAdvanced: true });

    const replacementCiphertext = new Uint8Array(16).fill(9);
    const reused = { ...first, ciphertext: base64Url(replacementCiphertext) };
    reused.ciphertext_sha256 = await sha256Hex(replacementCiphertext);
    const response = await upload(reused);
    expect(response.status).toBe(409);
    expect(await response.json()).toEqual({ status: "generation-id-reused" });
  });

  it("preserves a divergent branch instead of overwriting the current head", async () => {
    const first = await envelope("gen_00000000000000000005", null);
    const second = await envelope("gen_00000000000000000006", first.generation_id);
    const divergent = await envelope("gen_00000000000000000007", first.generation_id);
    expect((await upload(first)).status).toBe(201);
    expect((await upload(second)).status).toBe(201);
    const conflict = await upload(divergent);
    expect(conflict.status).toBe(409);
    expect(await conflict.json()).toEqual({
      status: "conflict",
      currentHead: second.generation_id,
      storedGeneration: divergent.generation_id,
      headAdvanced: false,
    });
    expect(
      await (await request("/v1/continuity/head", DEVICE_TOKEN)).json(),
    ).toEqual({ generationId: second.generation_id });
    expect(
      (
        await request(
          `/v1/continuity/generations/${divergent.generation_id}`,
          DEVICE_TOKEN,
        )
      ).status,
    ).toBe(200);
  });

  it("advances only one child when two devices race from the same parent", async () => {
    const first = await envelope("gen_0000000000000000000c", null);
    const left = await envelope("gen_0000000000000000000d", first.generation_id);
    const right = await envelope("gen_0000000000000000000e", first.generation_id);
    expect((await upload(first)).status).toBe(201);

    const responses = await Promise.all([upload(left), upload(right)]);
    expect(responses.map((response) => response.status).sort()).toEqual([201, 409]);
    const head = await (
      await request("/v1/continuity/head", DEVICE_TOKEN)
    ).json<{ generationId: string }>();
    expect([left.generation_id, right.generation_id]).toContain(head.generationId);
    const rows = await testEnv.DB.prepare(
      `SELECT generation_id FROM continuity_generations
       WHERE account_id = ? ORDER BY generation_id`,
    )
      .bind(ACCOUNT_ID)
      .all<{ generation_id: string }>();
    expect(rows.results.map((row) => row.generation_id)).toEqual([
      first.generation_id,
      left.generation_id,
      right.generation_id,
    ]);
  });

  it("isolates accounts and rejects a revoked device", async () => {
    const first = await envelope("gen_00000000000000000008", null);
    expect((await upload(first)).status).toBe(201);
    await account(OTHER_ACCOUNT_ID, "87654321");
    await entitlement(OTHER_ACCOUNT_ID);
    await device(OTHER_ACCOUNT_ID, OTHER_DEVICE_ID, OTHER_DEVICE_TOKEN);
    expect(
      (
        await request(
          `/v1/continuity/generations/${first.generation_id}`,
          OTHER_DEVICE_TOKEN,
        )
      ).status,
    ).toBe(404);

    await testEnv.DB.prepare(
      "UPDATE continuity_devices SET revoked_at = ? WHERE device_id = ?",
    )
      .bind("2026-07-17T12:05:00.000Z", DEVICE_ID)
      .run();
    expect((await request("/v1/continuity/head", DEVICE_TOKEN)).status).toBe(401);
    expect((await upload(await envelope("gen_00000000000000000009", first.generation_id))).status).toBe(401);
  });

  it("blocks writes after entitlement loss but allows the bounded recovery window", async () => {
    const first = await envelope("gen_0000000000000000000a", null);
    expect((await upload(first)).status).toBe(201);
    await testEnv.DB.prepare(
      "UPDATE entitlements SET state = 'ended', recovery_ends_at = '2099-01-01T00:00:00.000Z' WHERE account_id = ?",
    )
      .bind(ACCOUNT_ID)
      .run();
    expect(
      (await upload(await envelope("gen_0000000000000000000b", first.generation_id))).status,
    ).toBe(403);
    expect((await request("/v1/continuity/head", DEVICE_TOKEN)).status).toBe(200);

    await testEnv.DB.prepare(
      "UPDATE entitlements SET recovery_ends_at = '2020-01-01T00:00:00.000Z' WHERE account_id = ?",
    )
      .bind(ACCOUNT_ID)
      .run();
    expect((await request("/v1/continuity/head", DEVICE_TOKEN)).status).toBe(403);
  });

  it("enforces the generation quota without accepting another ciphertext", async () => {
    await testEnv.DB.prepare(
      `WITH RECURSIVE sequence(value) AS (
         SELECT 1 UNION ALL SELECT value + 1 FROM sequence WHERE value < 500
       )
       INSERT INTO continuity_generations
       (account_id, generation_id, parent_generation_id, author_device_id,
        schema_version, created_at, received_at, nonce, ciphertext,
        ciphertext_sha256, ciphertext_bytes, head_advanced, upload_nonce)
       SELECT ?, 'gen_' || printf('%020x', value), NULL, ?,
              'emulo.continuity-envelope/v1', '2026-07-17T12:03:00Z',
              '2026-07-17T12:03:00.000Z', ?, ?, ?, 16, 0,
              printf('%064x', value)
       FROM sequence`,
    )
      .bind(
        ACCOUNT_ID,
        DEVICE_ID,
        base64Url(new Uint8Array(12)),
        base64Url(new Uint8Array(16)),
        "0".repeat(64),
      )
      .run();
    const response = await upload(await envelope("gen_ffffffffffffffffffff", null));
    expect(response.status).toBe(413);
    expect(await response.json()).toEqual({ status: "generation-quota" });
  });

  it("enforces exact methods, JSON content type, and request size", async () => {
    expect((await SELF.fetch("https://api.example/v1/continuity/head")).status).toBe(401);
    expect(
      (
        await request("/v1/continuity/generations", DEVICE_TOKEN, {
          method: "POST",
          body: "{}",
        })
      ).status,
    ).toBe(415);
    expect(
      (
        await request("/v1/continuity/generations", DEVICE_TOKEN, {
          method: "POST",
          headers: {
            "content-type": "application/json",
            "content-length": "300000",
          },
          body: "{}",
        })
      ).status,
    ).toBe(413);
    expect(
      (
        await request("/v1/continuity/head", DEVICE_TOKEN, { method: "POST" })
      ).status,
    ).toBe(405);
  });
});
