import {
  SignJWT,
  createLocalJWKSet,
  exportJWK,
  generateKeyPair,
  type JWTPayload,
} from "jose";
import { beforeAll, describe, expect, it } from "vitest";

import { verifyGoogleIdToken } from "../src/google-token";

const CLIENT_ID = "google-client-test.apps.googleusercontent.com";
const NONCE = "nonce_that_is_random_and_unique_1234567890";
const NOW = new Date("2026-07-17T12:00:00.000Z");

async function sha256(value: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

describe("Google ID token verification", () => {
  let privateKey: CryptoKey;
  let keySet: ReturnType<typeof createLocalJWKSet>;

  beforeAll(async () => {
    const pair = await generateKeyPair("RS256", { extractable: true });
    privateKey = pair.privateKey as CryptoKey;
    const publicJwk = await exportJWK(pair.publicKey);
    keySet = createLocalJWKSet({
      keys: [{ ...publicJwk, kid: "test-key", alg: "RS256", use: "sig" }],
    });
  });

  async function token(overrides: Partial<JWTPayload & { email_verified: boolean }> = {}) {
    const issuedAt = Math.floor(NOW.getTime() / 1000);
    const claims = {
      sub: "google-subject-123",
      nonce: NONCE,
      email_verified: true,
      iss: "https://accounts.google.com",
      aud: CLIENT_ID,
      iat: issuedAt,
      exp: issuedAt + 300,
      ...overrides,
    };
    return new SignJWT(claims)
      .setProtectedHeader({ alg: "RS256", kid: "test-key", typ: "JWT" })
      .sign(privateKey);
  }

  async function verify(value: string) {
    return verifyGoogleIdToken(value, {
      clientId: CLIENT_ID,
      nonceHash: await sha256(NONCE),
      now: NOW,
      keySet,
    });
  }

  it("returns only the stable Google subject for a valid signed token", async () => {
    expect(await verify(await token())).toEqual({ subject: "google-subject-123" });
  });

  it.each([
    ["wrong issuer", { iss: "https://attacker.example" }],
    ["wrong audience", { aud: "another-client" }],
    ["expired token", { exp: Math.floor(NOW.getTime() / 1000) - 10 }],
    ["wrong nonce", { nonce: "another_nonce_that_does_not_match" }],
    ["unverified email", { email_verified: false }],
    ["invalid subject", { sub: "contains a space" }],
  ])("rejects %s", async (_label, overrides) => {
    await expect(verify(await token(overrides))).rejects.toThrow(
      "Google ID token is invalid",
    );
  });

  it("rejects a missing subject", async () => {
    await expect(verify(await token({ sub: undefined }))).rejects.toThrow(
      "Google ID token is invalid",
    );
  });

  it("rejects a token signed by an untrusted key", async () => {
    const attacker = await generateKeyPair("RS256");
    const issuedAt = Math.floor(NOW.getTime() / 1000);
    const forged = await new SignJWT({
      sub: "google-subject-123",
      nonce: NONCE,
      email_verified: true,
      iss: "https://accounts.google.com",
      aud: CLIENT_ID,
      iat: issuedAt,
      exp: issuedAt + 300,
    })
      .setProtectedHeader({ alg: "RS256", kid: "attacker", typ: "JWT" })
      .sign(attacker.privateKey);

    await expect(verify(forged)).rejects.toThrow("Google ID token is invalid");
  });
});
