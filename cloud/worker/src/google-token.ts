import {
  createRemoteJWKSet,
  jwtVerify,
  type JWTVerifyGetKey,
} from "jose";

const GOOGLE_JWKS = createRemoteJWKSet(
  new URL("https://www.googleapis.com/oauth2/v3/certs"),
  {
    timeoutDuration: 5_000,
    cooldownDuration: 30_000,
    cacheMaxAge: 60 * 60 * 1000,
  },
);
const GOOGLE_SUBJECT_PATTERN = /^[A-Za-z0-9._~-]{1,255}$/;

export interface GoogleTokenVerificationOptions {
  clientId: string;
  nonceHash: string;
  now?: Date;
  keySet?: JWTVerifyGetKey;
}

async function hexDigest(value: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

function equalHash(left: string, right: string): boolean {
  if (left.length !== right.length) return false;
  let difference = 0;
  for (let index = 0; index < left.length; index += 1) {
    difference |= left.charCodeAt(index) ^ right.charCodeAt(index);
  }
  return difference === 0;
}

export async function verifyGoogleIdToken(
  token: string,
  options: GoogleTokenVerificationOptions,
): Promise<{ subject: string }> {
  try {
    if (
      token.length < 64 ||
      token.length > 8_192 ||
      !/^[A-Za-z0-9._-]+$/.test(token) ||
      !/^[A-Za-z0-9._-]{8,256}$/.test(options.clientId) ||
      !/^[a-f0-9]{64}$/.test(options.nonceHash)
    ) {
      throw new Error("invalid input");
    }
    const { payload } = await jwtVerify(token, options.keySet ?? GOOGLE_JWKS, {
      algorithms: ["RS256"],
      audience: options.clientId,
      issuer: ["https://accounts.google.com", "accounts.google.com"],
      currentDate: options.now,
      clockTolerance: 5,
      maxTokenAge: "10m",
      requiredClaims: ["sub", "iat", "exp", "nonce", "email_verified"],
    });
    if (
      typeof payload.sub !== "string" ||
      !GOOGLE_SUBJECT_PATTERN.test(payload.sub) ||
      payload.email_verified !== true ||
      typeof payload.nonce !== "string" ||
      !equalHash(await hexDigest(payload.nonce), options.nonceHash)
    ) {
      throw new Error("invalid claims");
    }
    return { subject: payload.sub };
  } catch {
    throw new Error("Google ID token is invalid");
  }
}
