# Emulo Google OAuth Implementation Plan

> Execute with strict test-first changes. Checkout remains disabled throughout.

**Goal:** Add production-grade Google sign-in beside GitHub without merging accounts by email, persisting provider tokens, or weakening the current session and billing boundaries.

**Architecture:** Extend the existing D1 identity model to allow `github` and `google`, bind every OAuth flow to its provider, and store a one-time Google nonce hash with the flow. A Google-specific module performs the Authorization Code + PKCE exchange and verifies the returned ID token with Google's remote JWKS using pinned `jose`. Both providers issue the same opaque browser session and resolve to separate internal Emulo accounts.

**Current evidence:** Google documents `https://accounts.google.com/o/oauth2/v2/auth`, `https://oauth2.googleapis.com/token`, and a JWKS-backed signed ID token. The accepted identity key is the stable, case-sensitive `sub`, not email. Required validation is signature, `iss`, `aud`, `exp`, and the one-time `nonce`; Emulo additionally requires `email_verified=true`.

## Task 1: Provider-bound auth persistence

**Files:**
- Add: `cloud/worker/migrations/0006_google_oauth.sql`
- Modify: `cloud/worker/src/auth-store.ts`
- Modify: `cloud/worker/test/auth-store.test.ts`

1. Add failing tests for provider-bound flow consumption, Google nonce storage as a hash, Google subject validation, and provider-separated identities.
2. Add a forward-only migration that rebuilds `oauth_flows`, `oauth_identities`, and `oauth_diagnostics` for the two allowlisted providers while preserving existing GitHub rows and account IDs.
3. Generalize flow and identity APIs around an explicit `OAuthProvider` union.
4. Run the focused store tests and commit.

## Task 2: Shared OAuth safety primitives

**Files:**
- Add: `cloud/worker/src/oauth-core.ts`
- Modify: `cloud/worker/src/github-auth.ts`
- Modify: `cloud/worker/test/github-auth.test.ts`

1. Add failing regression tests proving GitHub flows are tagged `github` and cannot consume Google state.
2. Extract base URL validation, hashing, PKCE helpers, browser binding, safe responses, session issuance, and safe diagnostics without changing GitHub behavior.
3. Run GitHub and store tests and commit.

## Task 3: Google token verification

**Files:**
- Modify: `cloud/worker/package.json`
- Modify: `cloud/worker/package-lock.json`
- Add: `cloud/worker/src/google-token.ts`
- Add: `cloud/worker/test/google-token.test.ts`

1. Pin `jose@6.2.3` and prove it imports in the Worker test runtime.
2. Add failing signed-token tests for valid claims, invalid signature, wrong issuer, wrong audience, expired token, wrong nonce, missing/invalid subject, and unverified email.
3. Verify only `RS256` tokens against Google's remote JWKS; require `sub`, `iat`, `exp`, `nonce`, and `email_verified`.
4. Return only the validated Google `sub`; never return or persist the raw token.
5. Run focused token tests, type-check, and commit.

## Task 4: Google Authorization Code flow and routes

**Files:**
- Add: `cloud/worker/src/google-auth.ts`
- Add: `cloud/worker/test/google-auth.test.ts`
- Modify: `cloud/worker/src/contracts.ts`
- Modify: `cloud/worker/src/index.ts`
- Modify: `cloud/worker/vitest.config.ts`
- Modify: `cloud/worker/wrangler.jsonc`
- Modify: `cloud/worker/wrangler.production.jsonc`

1. Add failing start-route tests for the exact callback, minimal `openid email profile` scope, state, PKCE S256, nonce, and secure flow cookie.
2. Add failing callback tests for consent denial, malformed/replayed/cross-provider state, wrong browser binding, bad token exchange, failed ID-token verification, identity/session write failures, and the successful no-token-storage path.
3. Implement server-side token exchange and identity/session issuance.
4. Add exact GET-only routes for `/v1/auth/google/start` and `/v1/auth/google/callback`.
5. Keep Google config fail-closed and optional until the provider client exists; GitHub remains independently operational.
6. Run focused integration tests and commit.

## Task 5: Configuration, privacy, and release gates

**Files:**
- Modify: `cloud/worker/scripts/validate-production-config.mjs`
- Modify: `cloud/worker/test/production-config-validation.node.mjs`
- Modify: `tests/test_emulo_public_security.py`
- Modify: `.viberaven/production-context.md`

1. Add failing guards that reject Google secrets in public vars, reject partial Google activation, and preserve `PAID_CHECKOUT_ENABLED=false`.
2. Add repository scans proving no Google token/client secret is rendered, logged, or committed.
3. Record the exact provider action still required: create a Google Web client, authorize the production callback, set the Cloudflare secret, then add only the nonsecret client ID.
4. Run all Python and Worker tests, type-check, audit, production-config validation, and a production dry-run.
5. Browser-check the Google button and the safe unconfigured response. Do not deploy, enable checkout, or claim live Google sign-in without a real provider receipt.

