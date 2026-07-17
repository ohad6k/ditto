import { env } from "cloudflare:workers";
import { SELF } from "cloudflare:test";
import { beforeEach, describe, expect, it } from "vitest";

import {
  createBrowserSession,
  resolveOrCreateGitHubIdentity,
} from "../src/auth-store";
import { authenticateDevice } from "../src/device-auth";
import type { Env } from "../src/contracts";

const testEnv = env as unknown as Env;
const ACCOUNT_ID = "acct_0123456789abcdef0123456789abcdef";
const OTHER_ACCOUNT_ID = "acct_ffffffffffffffffffffffffffffffff";
const SESSION_TOKEN = "s".repeat(43);
const OTHER_SESSION_TOKEN = "t".repeat(43);
const PUBLIC_KEY = "A".repeat(43);

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

async function createAccount(accountId: string, providerId: string, token: string) {
  await resolveOrCreateGitHubIdentity(testEnv.DB, {
    providerUserId: providerId,
    proposedAccountId: accountId,
    createdAt: "2026-07-17T12:00:00.000Z",
  });
  await createBrowserSession(testEnv.DB, {
    sessionHash: await sha256(token),
    accountId,
    createdAt: "2026-07-17T12:00:00.000Z",
    expiresAt: "2099-07-17T13:00:00.000Z",
  });
}

async function activate(accountId = ACCOUNT_ID) {
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
       VALUES (?, 'active', 'founding-monthly', 'polar', ?, ?, ?, ?, ?, ?, NULL, NULL, ?)`,
    ).bind(
      accountId,
      `subscription_${accountId}`,
      customer,
      testEnv.POLAR_MONTHLY_PRODUCT_ID,
      "2026-07-17T12:01:00.000Z",
      `event_${accountId}`,
      "2026-08-17T12:01:00.000Z",
      "2026-07-17T12:01:00.000Z",
    ),
  ]);
}

function wrappedKey(publicKey = PUBLIC_KEY) {
  return {
    schema_version: "emulo.continuity-device-wrap/v1",
    device_public_key: publicKey,
    ephemeral_public_key: "B".repeat(43),
    salt: "C".repeat(22),
    nonce: "D".repeat(16),
    ciphertext: "E".repeat(64),
  };
}

async function startPairing(token = SESSION_TOKEN) {
  return SELF.fetch("https://api.example/v1/devices/pair/start", {
    method: "POST",
    headers: { cookie: `__Host-emulo_session=${token}` },
  });
}

async function completePairing(code: string, label = "Ohad laptop") {
  return SELF.fetch("https://api.example/v1/devices/pair/complete", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      pairingCode: code,
      label,
      keyAgreementPublicKey: PUBLIC_KEY,
      wrappedMasterKey: wrappedKey(),
      clientVersion: "0.3.8",
    }),
  });
}

describe("continuity device authentication", () => {
  beforeEach(async () => {
    await testEnv.DB.batch([
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
    await createAccount(ACCOUNT_ID, "12345678", SESSION_TOKEN);
  });

  it("requires browser authentication and a write-capable Pro entitlement", async () => {
    expect(
      (
        await SELF.fetch("https://api.example/v1/devices/pair/start", {
          method: "POST",
        })
      ).status,
    ).toBe(401);
    expect((await startPairing()).status).toBe(403);

    await activate();
    const response = await startPairing();
    expect(response.status).toBe(201);
    expect(response.headers.get("cache-control")).toBe("no-store");
    const body = await response.json<{ pairingCode: string; expiresIn: number }>();
    expect(body.pairingCode).toMatch(/^[A-Za-z0-9_-]{43}$/);
    expect(body.expiresIn).toBe(600);
    const stored = await testEnv.DB.prepare(
      "SELECT code_hash FROM continuity_pairing_grants",
    ).first<{ code_hash: string }>();
    expect(stored?.code_hash).toHaveLength(64);
    expect(stored?.code_hash).not.toBe(body.pairingCode);
  });

  it("consumes a pairing code once and returns a one-time device credential", async () => {
    await activate();
    const start = await (await startPairing()).json<{ pairingCode: string }>();
    const response = await completePairing(start.pairingCode);
    expect(response.status).toBe(201);
    const body = await response.json<{ deviceId: string; deviceToken: string }>();
    expect(body.deviceId).toMatch(/^dev_[a-f0-9]{32}$/);
    expect(body.deviceToken).toMatch(/^[A-Za-z0-9_-]{43}$/);
    const stored = await testEnv.DB.prepare(
      `SELECT account_id, token_hash, wrapped_master_key
       FROM continuity_devices WHERE device_id = ?`,
    )
      .bind(body.deviceId)
      .first<{ account_id: string; token_hash: string; wrapped_master_key: string }>();
    expect(stored?.account_id).toBe(ACCOUNT_ID);
    expect(stored?.token_hash).toHaveLength(64);
    expect(stored?.token_hash).not.toBe(body.deviceToken);
    expect(stored?.wrapped_master_key).not.toContain("approved artifact plaintext");
    expect((await completePairing(start.pairingCode)).status).toBe(400);
  });

  it("does not consume a valid grant when a different code is presented", async () => {
    await activate();
    const start = await (await startPairing()).json<{ pairingCode: string }>();
    expect((await completePairing("x".repeat(43))).status).toBe(400);
    expect((await completePairing(start.pairingCode)).status).toBe(201);
  });

  it("lists safe device metadata and never returns wrapped keys or tokens", async () => {
    await activate();
    const start = await (await startPairing()).json<{ pairingCode: string }>();
    await completePairing(start.pairingCode);
    const response = await SELF.fetch("https://api.example/v1/devices", {
      headers: { cookie: `__Host-emulo_session=${SESSION_TOKEN}` },
    });
    expect(response.status).toBe(200);
    const text = await response.text();
    expect(JSON.parse(text).devices).toHaveLength(1);
    expect(text).toContain("Ohad laptop");
    expect(text).not.toMatch(/wrapped|token|publicKey/i);
  });

  it("revokes only an owned device and rejects its bearer token afterward", async () => {
    await activate();
    await createAccount(OTHER_ACCOUNT_ID, "87654321", OTHER_SESSION_TOKEN);
    await activate(OTHER_ACCOUNT_ID);
    const start = await (await startPairing()).json<{ pairingCode: string }>();
    const paired = await (await completePairing(start.pairingCode)).json<{
      deviceId: string;
      deviceToken: string;
    }>();

    expect(
      (
        await SELF.fetch(`https://api.example/v1/devices/${paired.deviceId}`, {
          method: "DELETE",
          headers: { cookie: `__Host-emulo_session=${OTHER_SESSION_TOKEN}` },
        })
      ).status,
    ).toBe(404);
    expect(
      await authenticateDevice(
        new Request("https://api.example/v1/sync/head", {
          headers: { authorization: `Bearer ${paired.deviceToken}` },
        }),
        testEnv.DB,
        new Date("2026-07-17T12:05:00.000Z"),
      ),
    ).toMatchObject({ accountId: ACCOUNT_ID, deviceId: paired.deviceId });

    expect(
      (
        await SELF.fetch(`https://api.example/v1/devices/${paired.deviceId}`, {
          method: "DELETE",
          headers: { cookie: `__Host-emulo_session=${SESSION_TOKEN}` },
        })
      ).status,
    ).toBe(204);
    expect(
      await authenticateDevice(
        new Request("https://api.example/v1/sync/head", {
          headers: { authorization: `Bearer ${paired.deviceToken}` },
        }),
        testEnv.DB,
        new Date("2026-07-17T12:06:00.000Z"),
      ),
    ).toBeNull();
  });

  it("enforces exact methods and JSON content type", async () => {
    await activate();
    expect(
      (await SELF.fetch("https://api.example/v1/devices/pair/start")).status,
    ).toBe(405);
    expect(
      (
        await SELF.fetch("https://api.example/v1/devices/pair/complete", {
          method: "POST",
          body: "{}",
        })
      ).status,
    ).toBe(415);
    expect(
      (
        await SELF.fetch("https://api.example/v1/devices", { method: "POST" })
      ).status,
    ).toBe(405);
  });
});
