import { env } from "cloudflare:workers";
import { SELF } from "cloudflare:test";
import { beforeEach, describe, expect, it } from "vitest";

import {
  createBrowserSession,
  resolveOrCreateGitHubIdentity,
} from "../src/auth-store";
import type { Env } from "../src/contracts";

const testEnv = env as unknown as Env;
const ACCOUNT_ID = "acct_0123456789abcdef0123456789abcdef";
const SESSION_TOKEN = "i".repeat(43);

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

function authenticatedHeaders(): HeadersInit {
  return { cookie: `__Host-emulo_session=${SESSION_TOKEN}` };
}

describe("authenticated Worker integration", () => {
  beforeEach(async () => {
    await testEnv.DB.batch([
      testEnv.DB.prepare("DELETE FROM browser_sessions"),
      testEnv.DB.prepare("DELETE FROM oauth_identities"),
      testEnv.DB.prepare("DELETE FROM oauth_flows"),
      testEnv.DB.prepare("DELETE FROM entitlements"),
      testEnv.DB.prepare("DELETE FROM billing_events"),
      testEnv.DB.prepare("DELETE FROM billing_customers"),
      testEnv.DB.prepare("DELETE FROM accounts"),
    ]);
    await resolveOrCreateGitHubIdentity(testEnv.DB, {
      providerUserId: "12345678",
      proposedAccountId: ACCOUNT_ID,
      createdAt: "2026-07-16T12:00:00.000Z",
    });
    await createBrowserSession(testEnv.DB, {
      sessionHash: await sha256(SESSION_TOKEN),
      accountId: ACCOUNT_ID,
      createdAt: "2026-07-16T12:00:00.000Z",
      expiresAt: "2099-07-16T13:00:00.000Z",
    });
  });

  it("serves a truthful signed-out account and pending-payment page", async () => {
    const account = await SELF.fetch("https://api.example/account");
    expect(account.status).toBe(200);
    expect(account.headers.get("cache-control")).toBe("no-store");
    const accountBody = await account.text();
    expect(accountBody).toContain("Continue with GitHub");
    expect(accountBody).not.toContain("account is connected");

    const script = await SELF.fetch("https://api.example/account.js");
    expect(script.status).toBe(200);
    expect(script.headers.get("content-type")).toBe(
      "text/javascript; charset=utf-8",
    );
    expect(await script.text()).toContain('fetch("/v1/billing/checkout"');

    const complete = await SELF.fetch(
      "https://api.example/v1/billing/complete",
    );
    expect(complete.status).toBe(200);
    const body = await complete.text();
    expect(body).toContain("verified Polar confirmation");
    expect(body).not.toContain("access is active");
  });

  it("returns no-store authenticated status without identifiers", async () => {
    const signedOut = await SELF.fetch("https://api.example/v1/account/status");
    expect(signedOut.status).toBe(401);
    expect(signedOut.headers.get("cache-control")).toBe("no-store");
    expect(await signedOut.json()).toEqual({ status: "unauthenticated" });

    const signedIn = await SELF.fetch("https://api.example/v1/account/status", {
      headers: authenticatedHeaders(),
    });
    expect(signedIn.status).toBe(200);
    expect(signedIn.headers.get("cache-control")).toBe("no-store");
    const body = await signedIn.text();
    expect(JSON.parse(body)).toMatchObject({
      authenticated: true,
      environment: "sandbox",
      checkoutEnabled: false,
      entitlement: { state: "none", productCode: null },
    });
    expect(body).not.toMatch(/accountId|account_id|provider|subscription|customer/i);
  });

  it("keeps checkout disabled through the public Worker route", async () => {
    const response = await SELF.fetch(
      "https://api.example/v1/billing/checkout",
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ plan: "yearly" }),
      },
    );
    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({ status: "checkout-disabled" });
  });

  it("keeps exact methods on account and billing routes", async () => {
    expect(
      (
        await SELF.fetch("https://api.example/account", { method: "POST" })
      ).status,
    ).toBe(405);
    expect(
      (
        await SELF.fetch("https://api.example/account.js", { method: "POST" })
      ).status,
    ).toBe(405);
    expect(
      (
        await SELF.fetch("https://api.example/v1/billing/complete", {
          method: "POST",
        })
      ).status,
    ).toBe(405);
    expect(
      (
        await SELF.fetch("https://api.example/v1/account/status", {
          method: "POST",
        })
      ).status,
    ).toBe(405);
    expect(
      (
        await SELF.fetch("https://api.example/v1/billing/portal", {
          method: "GET",
        })
      ).status,
    ).toBe(405);
  });
});
