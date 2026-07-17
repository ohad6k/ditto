# Emulo Continuity Onboarding Architecture Plan

## Objective

Turn the already verified encrypted-continuity primitives into a complete customer workflow that a paying Emulo Pro user can operate safely from the account page and local companion. The workflow must cover first-device setup, recovery-kit creation, one-time device pairing, status, push, retry, pull, conflict reporting, device revocation, encrypted export discovery, and cloud-continuity deletion without exposing raw sessions, plaintext profiles, device credentials, the account master key, or the recovery secret.

Checkout remains disabled. This change makes the paid capability usable in the repository; it does not claim that Google, Cloudflare migrations, Polar production billing, or a live two-device deployment are proven.

## Product Path

1. A signed-in active Emulo Pro customer opens the account page and creates a short-lived pairing code.
2. On the first computer, the customer runs `emulo-autopilot continuity-init`. Emulo creates a local device key, a local account master key, and a portable encrypted recovery kit. The recovery secret is shown once and never written to disk.
3. The customer runs `emulo-autopilot continuity-connect`, enters the pairing code, and gives the device a recognizable label. The companion wraps the local master key to the device public key, completes pairing over an exact HTTPS origin, and stores the returned bearer credential only in a private local file.
4. The customer uses `continuity-status`, `continuity-push`, `continuity-retry`, and `continuity-pull` to inspect and move approved generations. Pull activates only a linear descendant. Divergence is reported as a conflict and never silently merged or overwritten.
5. On a second computer, the customer copies the nonsecret encrypted recovery-kit file, runs `continuity-recover`, and enters the recovery secret through a hidden prompt. Emulo generates a fresh device key, unwraps the shared master key locally, and then uses a new one-time account pairing code.
6. The account page lists devices, allows explicit revocation, exposes the encrypted export manifest, and offers cloud-continuity deletion only behind exact typed confirmation. Local files are never deleted by the cloud-delete action.

## User Answers Translated

- Audience: individual AI power users, including non-developers who may sign in with Google and developers who may sign in with GitHub.
- Paid value: managed encrypted continuity across devices. The local open-source mining, review, activation, history, rollback, export, and offline engine remain capable without a subscription.
- Privacy rule: raw sessions and approved artifact plaintext stay local. Hosted systems store only ciphertext and bounded routing metadata.
- Safety rule: preserve the intelligence and history Emulo has learned. Never silently overwrite a divergent local generation, downgrade the local engine, or couple local functionality to billing availability.
- Operational rule: checkout remains disabled until the complete live two-device, provider, billing, and deletion proof is captured and Ohad separately approves activation.
- Cost rule: the customer workflow uses the existing Cloudflare and Polar architecture and introduces no new paid provider.
- Scope rule: work only in `codex/emulo-autopilot-design`; do not touch `feat/antigravity-source` or the main checkout.

## Current Repo Evidence

- `emulo_autopilot/continuity_crypto.py` already implements AES-256-GCM envelopes, X25519/HKDF device wrapping, Scrypt recovery wrapping, secure private-material writes, strict schemas, and tamper/wrong-key rejection.
- `emulo_autopilot/continuity.py` already packages approved generations, pushes with an encrypted outbox, retries idempotently, pulls and validates remote chains, activates linear descendants, preserves conflicts, and provides a strict HTTPS device transport.
- `emulo_autopilot/store.py` already owns continuity envelope and pending directories plus imported-generation activation and rollback-preserving history.
- `cloud/worker/src/device-auth.ts` already supports browser-authenticated pairing-code creation, one-time pairing completion, a five-device cap, hashed device tokens, account-scoped listing, and revocation.
- `cloud/worker/src/continuity-routes.ts` already supports ciphertext upload/head/download, encrypted export manifests, and exact-confirmation cloud-continuity deletion.
- `cloud/worker/src/account-ui.ts` already renders authenticated entitlement states, but it does not expose pairing or device controls.
- `emulo_autopilot/cli.py` already offers local status, queue, history, review, activation, rollback, and lock recovery, but it does not expose continuity commands.
- The release evidence records 380 Python tests, 129 Worker tests, production guard/typecheck/audit/dry-run evidence, and a synthetic API-level two-device proof. It explicitly marks customer onboarding and live providers as remaining blockers.

## Architecture Boundaries

### Local plaintext and key boundary

Only the Python companion may see the account master key, device private key, recovery secret, decrypted approved generation, or imported artifacts. The browser account page never receives any of those values. The recovery secret is intentionally displayed once, then supplied only through a hidden local prompt. The encrypted recovery kit is portable but insufficient without that secret.

### Browser account boundary

The browser session may create a one-time pairing grant, list safe device metadata, revoke a device, request an encrypted export manifest, and delete hosted ciphertext. It must not complete pairing on behalf of the companion, see device bearer tokens, receive wrapped master keys during listing, or embed secrets in HTML, URLs, DOM data attributes, logs, or analytics.

### Device transport boundary

Pairing completion and sync use an exact HTTPS origin, no credentials in URLs, no redirects, bounded JSON bodies, bounded JSON responses, strict content types, and short timeouts. The device token is written with private-file semantics and sent only in an Authorization header.

### Billing boundary

The Worker remains the authority for write-capable entitlement. The CLI never trusts a local paid flag. Pairing and writes fail closed when the server denies entitlement. Local history, rollback, export of local data, and installed behavior continue.

### Provider/deploy boundary

Repository code cannot prove a Google client, Cloudflare secret, applied D1 migration, Worker deployment, Polar lifecycle, or real-money state. Those remain explicit provider actions after repository verification.

## Options Considered

### Option A: Browser-only onboarding

Put setup, recovery, pairing, and sync in the account page. This appears simpler for nontechnical customers but violates the encryption boundary because the browser would need local filesystem access or plaintext/key material. Browser storage also provides a weaker and less inspectable credential boundary. Rejected.

### Option B: Raw configuration-file onboarding

Document manual JSON files and curl calls around the existing primitives. This minimizes code but is error-prone, exposes credentials through shell history, and sells an internal API rather than a usable product. Rejected.

### Option C: Account-assisted local companion onboarding

Use the browser only for authenticated account controls and one-time grants; use the local companion for all keys, recovery, encryption, and sync. This matches the current architecture, preserves end-to-end encryption, and can be automated by tests. Chosen.

## Recommended Architecture

Add a focused local module, `emulo_autopilot/continuity_onboarding.py`, responsible for recovery-kit and credential-file schemas, local setup/recovery/connect orchestration, and safe status construction. Keep cryptographic primitives in `continuity_crypto.py` and data synchronization in `continuity.py`. Add only a public-key derivation helper and a pairing HTTP operation to those existing focused modules.

Extend `emulo_autopilot/cli.py` with continuity subcommands, but import Pro continuity modules lazily inside command branches. This preserves the open-source base installation when the optional `cryptography` dependency is absent. Commands return structured JSON. Errors are generic enough to avoid secret disclosure while remaining actionable.

Extend the active-account surface in `account-ui.ts` with one clear `Devices` section. JavaScript calls same-origin endpoints with browser cookies, renders the one-time code and expiration, refreshes the safe device list, and performs revocation. A separate danger section requires typing `delete-cloud-continuity` before the delete request is enabled. Checkout controls remain unchanged and disabled in committed production configuration.

## Workstream Map

1. Local onboarding schemas and secure files.
2. Pairing and device-transport boundary.
3. CLI workflow and safe status/push/pull.
4. Account pairing/device/deletion interface.
5. End-to-end repository proof and production-context update.

## Workstreams

### 1. Local onboarding schemas and secure files

Purpose: create a recoverable first-device experience without persisting the recovery secret.

Files: `emulo_autopilot/continuity_onboarding.py`, `emulo_autopilot/continuity_crypto.py`, `tests/test_continuity_onboarding.py`.

Tasks:

- Define exact versioned schemas for the portable encrypted recovery kit and private device credential file.
- Derive a device public key from a validated private key without duplicating X25519 serialization logic in the CLI.
- Implement first-device initialization with refusal to overwrite existing key, recovery-kit, or credential state.
- Generate the recovery secret, wrap the master key, atomically write private material and the nonsecret kit, and return the secret once without logging it.
- Implement recovery using a supplied secret and a fresh device key. Never persist the secret.
- Enforce safe parent directories, reject symlinks/nonfiles, use temporary files and replacement, set `0600` where meaningful, and validate exact schemas on every read.

Acceptance: first-device setup and second-device recovery yield the same master key but different device keys; recovery fails with a wrong secret; no file contains the recovery secret; existing state is never overwritten.

### 2. Pairing and device-transport boundary

Purpose: connect the local device to an authenticated account grant without exposing its bearer token.

Files: `emulo_autopilot/continuity.py`, `emulo_autopilot/continuity_onboarding.py`, `tests/test_continuity.py`, `tests/test_continuity_onboarding.py`.

Tasks:

- Factor strict HTTPS-origin validation and bounded JSON response parsing so pairing and sync share the same security behavior.
- Add a pairing completion request with `{pairingCode,label,keyAgreementPublicKey,wrappedMasterKey,clientVersion}`.
- Treat redirects, non-JSON responses, oversized bodies, malformed device IDs/tokens, and provider errors as failures.
- Store the returned token only in the private credential file; return only safe metadata to the caller.
- Refuse to replace a connected credential unless the customer explicitly removes/revokes it first.

Acceptance: pairing consumes a one-time code, writes a valid private credential, never prints the token, and rejects an unsafe origin or malformed response.

### 3. CLI workflow and sync controls

Purpose: expose the complete local customer path through clear commands while keeping base Emulo independent of Pro dependencies.

Files: `emulo_autopilot/cli.py`, `tests/test_autopilot_cli.py`, `tests/test_continuity_onboarding.py`.

Tasks:

- Add `continuity-init`, `continuity-recover`, `continuity-connect`, `continuity-status`, `continuity-push`, `continuity-retry`, and `continuity-pull`.
- Prompt for the recovery secret and pairing code rather than requiring secrets in process arguments. Tests inject the secret reader.
- Require an explicit device label and allow only the production origin by default, with an explicit HTTPS origin option for verified testing environments.
- Load device credentials and key material only inside the selected command.
- Map push/pull results to structured JSON. Present `conflict` with local and remote heads and a message explaining that neither branch was overwritten.
- Make status usable offline: local initialization/connection/pending/head values are reported even if the remote status cannot be reached.

Acceptance: ordinary non-Pro commands still import and run without `cryptography`; secrets and bearer tokens never appear in stdout/stderr; conflicts are explicit; pending writes survive outages.

### 4. Account pairing, devices, export, and deletion

Purpose: make browser-authenticated operations discoverable and one-action without turning the browser into a key holder.

Files: `cloud/worker/src/account-ui.ts`, `cloud/worker/test/account-ui.test.ts`, existing route tests where integration coverage is needed.

Tasks:

- On active Pro only, render a `Devices` section with `Create pairing code`, a bounded code display, expiry text, and setup instructions naming the local command.
- Load safe device metadata from `GET /v1/devices`; show label, creation time, last-seen time, and status without internal account IDs, public keys, wrapped keys, or bearer credentials.
- Add per-device `Revoke` with confirmation and a safe refresh.
- Add `Download encrypted export manifest` as a same-origin authenticated action that never labels ciphertext as a plaintext profile export.
- Add a separated `Delete cloud continuity` danger action disabled until the exact confirmation phrase is entered. Explain that local files remain.
- Keep all controls absent for signed-out and nonactive entitlement states. Preserve pricing/checkout behavior and the existing warm editorial account design.
- Render errors inline with actionable, nontechnical wording and no provider body.

Acceptance: active users can create a grant and manage devices; inactive/signed-out users cannot see controls; HTML/JS contains no secrets or provider IDs; keyboard, focus, 390-pixel layout, and reduced-motion behavior remain sound.

### 5. Repository proof and release boundary

Purpose: prove the customer workflow without confusing repository proof with live production proof.

Files: `tests/test_continuity_two_device.py`, Worker tests, `.viberaven/production-context.md`, `docs/superpowers/plans/2026-07-17-emulo-pro-continuity-release-evidence.md`.

Tasks:

- Run a CLI-level synthetic first-device, connect, push, second-device recover/connect/pull proof with exact Unicode and CRLF artifact bytes.
- Prove wrong recovery secret, code replay, revoked device, stale parent, divergence, outage/retry, malformed server response, symlink/overwrite protection, and no-secret output.
- Scan generated files and captured output for synthetic plaintext/token/recovery markers outside the explicitly local approved artifact and private test fixtures.
- Run the complete Python and Worker suites, TypeScript typecheck, production config guards, dependency audits, production dry-run bundle, and desktop/mobile account browser QA.
- Record repo receipts and retain open provider actions. Do not deploy or enable checkout.

Acceptance: all repository gates pass freshly, the worktree diff is scoped, checkout is still disabled, and the evidence document still states live provider proof is outstanding.

## Execution Tasks

- [ ] Add failing local onboarding tests for secure init, one-time recovery output, recovery, overwrite refusal, and private credential storage.
- [ ] Implement the minimal onboarding schemas and local operations.
- [ ] Add failing transport tests for secure pairing and malformed/redirect responses.
- [ ] Implement pairing completion and credential persistence.
- [ ] Add failing CLI tests for lazy imports, hidden input, secret-safe output, status, push/retry/pull, and conflict reporting.
- [ ] Implement the continuity CLI commands.
- [ ] Add failing account UI tests for active-only pairing/device/export/delete controls and secret/provider-ID absence.
- [ ] Implement the account controls and same-origin client behavior.
- [ ] Add the CLI-level synthetic two-device test and make it pass.
- [ ] Run focused then complete verification, browser QA, secret scans, and production dry run.
- [ ] Update production context and release evidence with exact receipts and remaining provider actions.
- [ ] Commit the scoped changes on the isolated branch without pushing or deploying.

## Implementation Sequence

Use strict red-green-refactor cycles. Start with pure local onboarding because later commands depend on its files. Add pairing transport next, then CLI wiring, then the account UI. Run focused tests after each minimal change and commit coherent checkpoints. Finish with an end-to-end CLI proof and the full release gates.

## Data, Auth, Provider, And Deploy Boundaries

- D1 receives no new plaintext field. Existing migrations remain unchanged in this workstream unless a failing test proves a missing bounded metadata field.
- Browser auth uses the existing opaque session cookie. Device operations use the existing random bearer credential and hash-only server storage.
- Recovery secrets, private keys, master keys, device tokens, raw sessions, and approved plaintext never enter account HTML, D1, logs, query strings, or provider dashboards.
- Google production activation, Cloudflare secrets, D1 migration application, Worker deploy, and Polar production lifecycle are outside this repository implementation.
- `PAID_CHECKOUT_ENABLED=false` is a release invariant until separate explicit approval.

## Test Matrix

| Path | Required proof |
| --- | --- |
| First-device happy path | Keys and kit created, secret returned once, permissions private |
| Second-device happy path | Same master key, fresh device key, exact artifact pull/activation |
| Unauthorized/inactive | Pairing/write denied by Worker, local engine still works |
| Wrong/lost secret | Recovery fails without changing existing files |
| Pairing replay/expiry | Server rejects; no credential file created |
| Unsafe transport | Non-HTTPS, redirects, malformed/oversized JSON rejected |
| Revoked device | Sync denied immediately; other device and local history survive |
| Cloud outage | Push enters pending queue; retry succeeds idempotently |
| Divergent history | Both generations preserved; no silent activation/overwrite |
| Cloud deletion | Exact confirmation required; hosted rows removed; local files remain |
| Entitlement ended | New cloud writes fail; bounded recovery read/local use remain |
| Regression | Existing local, auth, billing, legal, pricing, and config tests pass |

## Verification Plan

- Focused Python: `python -m pytest tests/test_continuity_onboarding.py tests/test_continuity.py tests/test_autopilot_cli.py tests/test_continuity_two_device.py -q`.
- Full Python: use the repository's existing full-suite command in the Pro-enabled environment and record passed/skipped counts.
- Focused Worker: `npm test -- account-ui.test.ts device-auth.test.ts continuity-routes.test.ts continuity-lifecycle.test.ts` from `cloud/worker`.
- Full Worker: `npm test`; `npm run typecheck`; production guard test command from package scripts.
- Supply chain: `npm audit --omit=dev`; clean temporary Python environment with `.[pro]` followed by `pip check`.
- Build: production Wrangler dry run and inspection that checkout remains false and Google remains unconfigured unless separately proven.
- Visual: desktop and 390-pixel authenticated active-account screenshots, keyboard/focus checks, console check, and horizontal-overflow measurement.
- Privacy: repository and generated-fixture scans for known recovery/token/plaintext markers.

## Rollout And Rollback

No deployment occurs in this workstream. The branch can be rolled back by reverting its onboarding commits because existing encryption/store/server primitives remain compatible and no new migration is planned. When later deploying, apply migrations before code, keep checkout disabled, test synthetic accounts first, and roll back the Worker on any auth, pairing, plaintext, conflict, or deletion mismatch. Never roll back D1 by destructive down migration; use forward correction and preserve ciphertext generations until verified deletion.

## Risks And Fallbacks

- Optional crypto import regression: keep all Pro imports lazy and test base commands without the extra.
- Secret disclosure through CLI output: centralize safe response construction and scan captured stdout/stderr.
- Credential overwrite or symlink attack: no implicit overwrite, exact regular-file checks, atomic writes, and private modes.
- Browser complexity: keep the account UI to one device section and one danger section; no browser-held keys.
- Confusing encrypted export with readable export: name it explicitly and keep local plaintext export in the open-source engine.
- Live provider mismatch: label it unknown until observed; checkout remains disabled.

## Open Questions

No repository-design question blocks implementation. Production Google configuration, applied migrations, production Worker deployment, Polar webhook lifecycle, and live two-device proof remain deliberately open provider actions.

## Decision Log

- Chosen: account-assisted local companion workflow.
- Chosen: hidden prompts for recovery secret and pairing code.
- Chosen: separate versioned recovery-kit and credential schemas.
- Chosen: active-Pro-only browser controls and exact-confirmation deletion.
- Rejected: browser-held encryption keys.
- Rejected: raw curl/config onboarding.
- Rejected: silent conflict merge or last-write-wins.
- Rejected: coupling local open-source behavior to subscription state.
- Rejected: deploy or checkout activation in the same change.

## VibeRaven Route

Record the auth, billing, storage, deletion, and provider boundaries in `.viberaven/production-context.md` after verification. Keep repo evidence separate from Cloudflare, Google, and Polar proof. Route live activation to `go-live` only after the repository workflow is complete and Ohad separately authorizes provider mutations.

## Next Skill

`production-context`
