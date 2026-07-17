# Emulo Pro continuity release evidence

**Status:** repository implementation verified; **not production-launch ready**.

This record separates what is proven in the repository from provider and
operator work that has not happened. `PAID_CHECKOUT_ENABLED` must remain
`false` until every remaining gate below is evidenced and Ohad separately
approves activation.

## What is implemented and verified

- Local AES-256-GCM approved-generation encryption with authenticated metadata,
  fresh nonces, strict schemas, and bounded plaintext.
- X25519 + HKDF per-device master-key wrapping and Scrypt recovery wrapping.
- One-time pairing grants, five-device cap, hashed device credentials,
  account-scoped listing, and immediate revocation.
- Ciphertext-only generation storage with digest verification, a 500-generation
  and 64 MiB account cap, idempotent retries, and account isolation.
- Optimistic parent concurrency that preserves both branches and advances only
  one head instead of silently overwriting or merging.
- Local encrypted outbox retries, exact artifact import, conflict preservation,
  continued local learning, and append-only rollback after cloud access fails.
- Bounded post-subscription recovery reads, ciphertext export manifests, and
  confirmed account-scoped cloud-continuity deletion that does not purge local
  files.
- Provider-separated GitHub and Google OAuth code. Google is deliberately
  disabled by the committed `not-configured` client ID.
- Concrete Free versus Pro copy: open source keeps local mining, review,
  activation, history, rollback, export, and offline use; Pro adds managed
  encrypted continuity and device/recovery operations.

## Verification evidence from 2026-07-17

- Python: 380 tests passed, 3 Windows/platform skips.
- Worker: 129 tests passed across 14 files.
- Production configuration: 8 guards passed.
- TypeScript: `tsc --noEmit` passed.
- Production npm audit: 0 vulnerabilities.
- Clean temporary Python environment with `.[pro]`: no broken requirements.
- Cloudflare production dry run passed at 1,741.67 KiB / 318.03 KiB gzip.
- Dry run confirmed `PAID_CHECKOUT_ENABLED=false` and
  `GOOGLE_CLIENT_ID=not-configured`.
- Browser QA: desktop and 390 px mobile pricing render with zero horizontal
  overflow, readable Pro contrast, and no page or console errors.
- Synthetic two-device proof preserved exact Hebrew, emoji, and CRLF artifact
  bytes and retained local rollback while transport was unavailable.

## Data boundary proven by tests

The hosted service can receive account/provider identifiers, entitlement
metadata, device labels and public keys, ciphertext, ciphertext digests, byte
sizes, generation relationships, and timestamps.

It does not need raw session logs, prompt text, receipt evidence, local source
paths, plaintext profile/workflow content, device private keys, the account
master key, the recovery secret, model-provider tokens, or payment-card data.
Device bearer tokens and browser sessions are stored only as hashes.

## Remaining launch blockers

1. Build the user-facing local onboarding path for first-device setup, recovery
   kit confirmation, pairing, sync status, push, pull, conflicts, export, and
   deletion. The tested Python APIs are not yet a complete customer workflow.
2. Create and verify the Google production Web OAuth client with callback
   `https://emulo-production.ohad1306.workers.dev/v1/auth/google/callback`, add
   the client secret directly as a Cloudflare Worker secret, and commit only
   the nonsecret client ID.
3. Apply production D1 migrations through `0008_continuity_generations.sql` and
   deploy the reviewed Worker revision without enabling checkout.
4. Run a live synthetic account proof: both sign-in providers, webhook-confirmed
   entitlement, first and second device, encrypted push/pull, conflict,
   revocation, recovery export, cloud deletion, and negative cross-account
   tests. Capture URLs, request IDs, timestamps, and screenshots without secret
   values.
5. Verify the production Polar products, portal, refunds/terms/privacy links,
   transaction email, cancellation, renewal, and webhook replay behavior.
6. Obtain a separate explicit Ohad approval, then change checkout activation in
   a small isolated release. Roll back on any mismatch.

## Launch decision

**No-go today.** The repository foundation is strong and the paid value is now
specific, but accepting money before customer-facing onboarding and live
provider proof would sell an internal capability rather than a usable product.
