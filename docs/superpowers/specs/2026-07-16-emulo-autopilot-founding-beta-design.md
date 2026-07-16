# Emulo Autopilot Founding Beta Design

**Date:** 2026-07-16
**Status:** Ready for founder review
**Owner:** Ohad
**Implementation branch:** `codex/emulo-autopilot-design`
**Product target:** Solo AI-agent power users

## 1. Decision

Build **Emulo Autopilot**, a paid managed layer around Emulo's strong open-source core.

The open-source product remains capable, local-first, portable, and useful without an account. Autopilot earns its subscription by removing repeated maintenance: it notices completed sessions, stages evidence-backed improvements, validates them, propagates approved changes across supported agents, synchronizes encrypted artifacts across devices, and makes every change inspectable and reversible.

The founding beta will use **Polar first** because Ohad already has an account and Polar supports Israeli payouts. Billing remains behind a provider-neutral interface so Paddle can be added or substituted later without changing product entitlements.

This is a product and revenue system, not a promise that a specific star or revenue number will occur. The 10,000-star target is the growth north star. Public claims and launch timing remain gated by inspectable benchmark evidence and real user outcomes.

## 2. User problem and promise

AI power users install models, MCP servers, rules, and skills, but those tools are generic. Each operator speaks, debugs, plans, verifies, and ships differently. Their useful corrections and workflows stay trapped in past sessions, and every new agent must be taught again.

Emulo's category is **personal operating alignment**:

- skills teach an agent a general capability;
- memory recalls facts and prior context;
- Emulo learns how one specific operator works and keeps that operating style available across agents.

The founding-beta promise is:

> Emulo learns from completed sessions, safely improves your personal workflows, and keeps every supported agent aligned without uploading raw session logs.

The promise does not include autonomous external actions, guaranteed performance gains, or invisible use of paid model allowances.

## 3. Product principles

1. **Do not weaken open source.** Core mining, local history, validation, adapters, exports, and manual automation remain open.
2. **Raw evidence stays local.** Session logs, source code, local paths, provider credentials, and receipt bodies never enter the Emulo cloud.
3. **Every learned change has provenance.** A user can see what changed, why it changed, which local receipts support it, and how to undo it.
4. **Learning must be conservative.** Silence, engagement, or model confidence alone never becomes a personal rule.
5. **Reversibility precedes automation.** No automatic activation exists until atomic writes, version history, conflict handling, and rollback pass tests.
6. **Provider use is visible.** Emulo never silently drives Claude, Codex, or another subscription in a background loop. Deterministic local work can run unattended; model-assisted synthesis runs in an explicit supported agent context and produces a local receipt.
7. **No cost before revenue.** The beta uses free infrastructure and hard application caps. It does not enable a paid provider plan until recurring revenue safely covers it and Ohad explicitly approves the upgrade.
8. **Proof drives growth.** Distribution links to benchmark methodology, reproducible workflows, and honest user outcomes rather than hype-only claims.

## 4. Scope

### 4.1 Founding beta includes

- a local companion that detects new completed sessions without copying them;
- deterministic local extraction of user-authored signals;
- model-assisted candidate synthesis inside an explicit user-controlled agent run;
- a local candidate ledger with evidence hashes and local-only receipt references;
- separate rule, correction, preference, and workflow candidate types;
- policy-based classification into auto-activatable, review-required, and rejected candidates;
- regression validation before activation;
- atomic propagation to supported agent adapters;
- local version history, conflict detection, and one-command rollback;
- client-side encrypted artifact sync;
- a lightweight control center for state, queue, devices, agents, versions, and billing status;
- Polar checkout, signed webhook processing, entitlements, cancellation, and customer-portal access;
- full export, account disconnect, local-only mode, and cloud deletion.

### 4.2 Explicitly excluded

- uploading or remotely processing raw session logs;
- a hosted model or bundled model tokens;
- team administration, seats, or shared company profiles;
- a community pattern marketplace;
- unattended external actions such as posting, emailing, merging, deploying, or purchasing;
- automatic security, financial, legal, medical, credential, permission, or destructive-action rules;
- a mobile application;
- lifetime pricing;
- usage-based billing;
- paid advertising;
- replacing the benchmark or video work currently owned by Claude.

## 5. Free and paid boundary

### 5.1 Emulo Open Source

The free product keeps the intelligence and ownership:

- full local session discovery and mining;
- manual and command-driven profile updates;
- local rule, correction, preference, and workflow generation;
- regression validation;
- every supported agent adapter;
- local history and rollback;
- scriptable local automation hooks;
- complete data export and portable open formats;
- no account requirement.

### 5.2 Emulo Autopilot

The paid product sells continuity, orchestration, and recovery:

- completion detection and queued processing through the local companion;
- one control center across agents and devices;
- end-to-end encrypted artifact sync;
- managed device pairing and health status;
- one-action propagation across installed agents;
- managed encrypted version retention and recovery;
- conflict assistance and clear drift warnings;
- priority founding-beta support.

Autopilot may make the open engine easier and more continuous, but it must not make a user's local profile hostage to billing. When an entitlement ends, cloud sync stops after a grace period; local artifacts, local history, export, manual updates, and installed agent behavior continue to work.

## 6. System boundaries

The founding beta is one vertical product composed of small, replaceable units.

### 6.1 Open-source local engine

The existing `emulo.py` behavior remains the compatibility anchor. New behavior is introduced behind explicit commands and versioned formats. Existing mining and install paths must not change accidentally.

Responsibilities:

- discover supported session sources;
- read only user-authored text according to existing source rules;
- redact before a model can read selected content;
- generate deterministic hashes and local receipts;
- validate candidate schemas;
- compile active artifacts;
- install through host-specific adapters;
- maintain atomic local generations and rollback.

### 6.2 Local companion

A separate process, not a growing monolith inside `emulo.py`, coordinates automation.

Responsibilities:

- watch supported source roots using checkpoints, not permanent file locks;
- identify sessions that are stable and complete;
- request deterministic extraction;
- place model-assisted work in a visible queue;
- apply policy and validation results;
- serve a loopback-only control API;
- encrypt and synchronize approved artifacts;
- expose health without exposing raw evidence.

The companion must remain useful offline. Cloud or billing failure cannot block local mining, local review, local installs, or rollback.

### 6.3 Agent bridge

Each supported agent receives a thin bridge that can process queued candidate synthesis during a user-active session. The bridge records:

- provider and model label when available;
- prompt-contract version;
- input artifact digest;
- output artifact digest;
- start and completion time;
- failure class.

It does not claim exact token cost or subscription consumption unless the provider supplies a verifiable receipt.

### 6.4 Encrypted control plane

The initial server is a Cloudflare Worker with D1. It stores identity, entitlements, device metadata, sync indexes, and encrypted artifact chunks. It never receives decryption keys or raw local evidence.

Server-readable fields are deliberately narrow:

- account ID and verified sign-in identity;
- entitlement state and provider references;
- device IDs, labels, public keys, last-seen time, and client version;
- artifact IDs, type, encrypted byte size, ciphertext digest, generation, and timestamps;
- service-limit counters and security audit metadata.

The server cannot read profile text, workflow text, local evidence, local filenames, or receipt bodies.

### 6.5 Control center

The first control center is served by the local companion and uses the cloud only for authentication, encrypted sync, and billing state. This avoids sending the profile decryption key to a hosted browser application.

It shows:

- whether Autopilot is healthy;
- sessions discovered and processed;
- pending candidates and their policy class;
- active profile/workflow generation;
- installed agent status;
- devices and last synchronization;
- rollback points;
- subscription and customer-portal link.

It never renders raw receipt text unless the user explicitly opens a local evidence view.

## 7. End-to-end data flow

1. A source session becomes stable according to its adapter's completion rule.
2. The companion records a local checkpoint and asks the open engine to extract user-authored signals.
3. The engine redacts locally, creates content-addressed receipts, and emits a bounded local candidate packet.
4. Deterministic signals are evaluated locally. If synthesis is needed, the packet waits for an explicit supported-agent run.
5. The agent bridge produces candidates bound to the packet digest and prompt-contract version.
6. Strict local schema and evidence validation rejects invented, unbound, contradictory, or unsafe candidates.
7. The policy engine assigns each surviving candidate to safe auto-activation, user review, or rejection.
8. Regression checks run against the current active generation and representative fixtures.
9. The activation engine atomically writes a new generation and propagates it through adapters. A failed adapter causes rollback or a clearly partial, non-promoted generation; it never reports success silently.
10. The sync client encrypts only approved profile and workflow artifacts plus bounded metadata. The server receives ciphertext.
11. Other paired devices download, verify, decrypt locally, detect conflicts, and activate only after their own validation.

## 8. Learning and activation policy

### 8.1 Candidate types

- **Directive:** an explicit persistent instruction about how the agent should work.
- **Correction:** an explicit rejection or correction of previous agent behavior.
- **Preference:** an expressed choice that can be contextual rather than universal.
- **Workflow:** a repeated multi-step procedure with a recognizable trigger and verifiable completion rule.
- **Retirement:** evidence that an active item is obsolete or harmful.

### 8.2 Safe auto-activation

A candidate may auto-activate only when all conditions hold:

- it is based on explicit user-authored language;
- equivalent evidence appears in at least three distinct completed sessions across at least two time strata;
- no unresolved contradiction exists in newer or equally forceful evidence;
- the candidate is scoped to the contexts supported by its evidence;
- it does not match a prohibited high-risk category;
- it passes strict schema, Unicode, privacy, duplication, size, and regression checks;
- it changes only Emulo-managed regions or generated artifacts;
- the previous generation is durable and one-command rollback has been verified;
- the user has enabled safe auto-activation globally.

The initial default is **review-required**. Safe auto-activation is enabled only after the user has successfully reviewed and rolled back at least one synthetic demonstration or real low-risk change.

### 8.3 Always review

The following never auto-activate in the founding beta:

- inferred preferences without explicit language;
- a rule supported by fewer than three sessions;
- universal wording derived from contextual evidence;
- retirement of an active item;
- security, credentials, permissions, destructive commands, purchases, legal/medical/financial behavior, or external communication;
- a change that modifies a user-owned file outside an Emulo-managed block;
- a candidate with a contradiction, failed regression, missing receipt, unknown schema, or model-only rationale.

### 8.4 Always reject

Reject any candidate based on assistant text presented as user evidence, secret material, source-code content, fabricated receipts, path traversal, unsupported encodings, hidden control envelopes, or evidence whose digest cannot be reproduced.

## 9. Versioning, conflicts, and rollback

Every activation creates an immutable local generation containing:

- parent generation ID;
- active artifact digests;
- candidate decisions;
- adapter results;
- validation receipt;
- creation source and timestamp.

Writes use temporary files, `fsync` where supported, atomic replacement, and post-write verification. User-owned content around managed blocks is byte-preserved, including CRLF and Hebrew/mixed-Unicode round trips.

Sync uses optimistic concurrency on the encrypted generation parent. Divergent generations are not silently merged. The control center presents both branches, their locally decrypted summaries, and the options to keep local, keep remote, or create a reviewed merge generation.

Rollback creates a new generation that points to a previously valid artifact set. History remains append-only; rollback never erases the failed generation.

## 10. Encryption and account recovery

### 10.1 Keys

- The client generates an account master key locally using an operating-system cryptographic random source.
- Artifact payloads use authenticated encryption with a fresh nonce per payload.
- Each device has a separate signing and key-agreement identity.
- The master key is wrapped separately for each paired device.
- The server stores wrapped keys and public material only.
- Authentication cookies, Polar entitlements, and GitHub identity never become encryption keys.

The implementation plan must select mature, audited platform cryptography rather than custom primitives and must include cross-platform test vectors.

### 10.2 Recovery

The first device displays a one-time recovery secret that the user must confirm before the first cloud artifact upload is allowed. A second device is added by local pairing approval or the recovery secret. Emulo cannot recover encrypted content without one of those paths.

Losing all device keys and the recovery secret means losing cloud recovery. The product must state this plainly. Local artifacts remain available on any intact device and can initialize a new encrypted account generation.

### 10.3 Deletion

Account deletion immediately revokes sessions, deletes device and entitlement mappings, and queues all encrypted blobs for bounded deletion. The client can export before deletion. Deleting the cloud account does not remove local files without a second explicit local purge command.

## 11. Authentication and authorization

The beta uses GitHub OAuth for account sign-in and a separate device-pairing flow. Every server request requires an authenticated account and verifies ownership of the requested device, artifact, or entitlement record.

Security requirements:

- state and PKCE for OAuth where supported;
- secure, HTTP-only, same-site cookies for browser sessions;
- short-lived client access tokens and rotating refresh credentials;
- no bearer token in URLs;
- constant-time webhook signature verification through Polar's supported Standard Webhooks implementation;
- replay protection and stored webhook event IDs;
- idempotent entitlement transitions;
- strict CORS limited to the production control origin and loopback integration;
- rate limits on login, pairing, sync, and webhook endpoints;
- logs redact authorization, checkout, device, and ciphertext data by default.

## 12. Billing and entitlements

### 12.1 Provider strategy

Use Polar's hosted checkout and customer portal first. Do not build custom card handling. Do not paste provider secrets into chat, commit them, or expose them to the browser.

The billing module exposes a provider-neutral contract:

- create checkout session;
- verify signed webhook;
- normalize customer, order, and subscription events;
- resolve current entitlement;
- create customer-portal session or link;
- record refund and cancellation state.

Polar identifiers live only in the billing adapter and normalized mapping table. Product code consumes Emulo entitlement states, not Polar-specific states.

### 12.2 Entitlement state machine

Normalized states are:

- `none`;
- `trialing`;
- `active`;
- `past_due`;
- `grace`;
- `ended`;
- `refunded`.

The checkout redirect never grants access. Only a verified, idempotently processed webhook or a server-to-server reconciliation can change entitlement. Duplicate and out-of-order events must converge to the provider's newest effective state.

`past_due` keeps local features and grants a seven-day sync grace period. `ended` disables new cloud writes but permits a 30-day encrypted export/recovery window. The exact retention policy must be displayed before purchase and may only become shorter with explicit customer notice.

### 12.3 Pricing

Founding Beta, first 50 paying customers:

- **$9 per month**;
- **$79 per year**, highlighted as the default;
- founding price protected for the first twelve months;
- cancel through Polar's customer portal;
- no lifetime deal and no fake countdown.

Standard price after demonstrated retention and reliability:

- **$15 per month**;
- **$120 per year**.

Price moves only after real evidence: at least ten paying users, at least six completing a second successful weekly learning cycle, no unresolved data-loss incident, and support load sustainable by one founder.

As of 2026-07-16, Polar lists a free Starter plan at 5% + $0.50 per transaction. Organizations created before 2026-05-27 may retain an Early Member rate, but the implementation and forecast must assume Starter until Ohad verifies the exact organization receipt. Annual pricing is emphasized because fixed transaction fees consume a smaller share of the payment.

## 13. Zero-out-of-pocket infrastructure

Initial infrastructure:

- Cloudflare Workers Free for API and static assets;
- Cloudflare D1 Free for identity, entitlement, device, sync index, and bounded ciphertext chunks;
- GitHub OAuth;
- Polar sandbox during development and Polar Starter only when a customer pays;
- provider-native logs within the free retention window;
- no R2, paid email service, purchased domain, paid monitoring, or hosted model.

Current published limits checked on 2026-07-16:

- Workers Free: 100,000 requests/day, 10 ms CPU per HTTP request, 50 subrequests/request;
- D1 Free: 5 million rows read/day, 100,000 rows written/day, 5 GB total storage;
- D1 Free database: 500 MB; maximum string, BLOB, or row: 2 MB.

The application uses lower internal founding-beta caps:

- 50 paid accounts;
- 5 devices/account;
- 25 MB encrypted cloud storage/account;
- 1,000 artifact generations/account, with local history remaining uncapped by cloud policy;
- 5,000 authenticated API requests/account/day;
- 256 KB maximum encrypted chunk and 5 MB maximum logical artifact bundle;
- no server-side scanning, compression, model inference, or decryption.

The Worker route is fail-closed. When an internal or provider limit is approached, new registrations and nonessential sync writes pause with a clear status. Existing local operation continues. No automatic provider upgrade or metered-overage switch is permitted.

## 14. API and storage model

The exact paths may change in the implementation plan, but boundaries do not.

### 14.1 Server endpoints

- `GET /v1/auth/github/start`
- `GET /v1/auth/github/callback`
- `POST /v1/devices/pair/start`
- `POST /v1/devices/pair/complete`
- `GET /v1/devices`
- `DELETE /v1/devices/{id}`
- `GET /v1/sync/head`
- `POST /v1/sync/generations`
- `GET /v1/sync/generations/{id}`
- `POST /v1/billing/checkout`
- `POST /v1/billing/webhooks/polar`
- `POST /v1/billing/portal`
- `GET /v1/entitlement`
- `POST /v1/account/export-manifest`
- `DELETE /v1/account`

### 14.2 D1 tables

- `accounts`
- `oauth_identities`
- `sessions`
- `devices`
- `device_wrapped_keys`
- `sync_generations`
- `sync_chunks`
- `billing_customers`
- `billing_events`
- `entitlements`
- `usage_counters`
- `deletion_jobs`

Ciphertext is chunked below D1's row and statement limits. Every chunk is content-addressed and authenticated by the client. Indexes must make account ownership, generation lookup, webhook replay checks, and quota checks point queries.

## 15. Failure behavior

- **Cloud unavailable:** queue encrypted sync locally; continue all local work.
- **Billing unavailable:** do not grant new entitlement; preserve existing cached entitlement through its bounded verification window.
- **Model bridge unavailable or quota exhausted:** keep deterministic candidate packets queued; do not substitute a hidden provider or claim learning completed.
- **Invalid model output:** reject without changing active artifacts.
- **Adapter write failure:** preserve the prior valid generation and report exact adapter state.
- **Conflicting device updates:** preserve both branches and require explicit resolution.
- **Lost decryption key:** offer pairing, recovery-secret restore, or local reinitialization; never imply server recovery is possible.
- **Free-tier limit reached:** fail closed for affected cloud action, pause registration/nonessential sync, and keep local features operational.
- **Webhook signature or replay failure:** return an error, record only safe metadata, and make no entitlement change.
- **Unsupported client version:** permit export and local operation; block incompatible cloud mutations with an upgrade explanation.

## 16. Verification strategy

Implementation follows test-driven development and keeps the current 270-test baseline green.

### 16.1 Local engine and companion

- synthetic session completion and partial-file tests;
- user-only extraction and control-envelope rejection;
- deterministic candidate and receipt hashing;
- Hebrew and mixed-Unicode round trips;
- CRLF preservation;
- path traversal, symlink, and junction rejection;
- crash and power-loss simulations around atomic activation;
- adapter partial-failure and rollback tests;
- candidate-policy tables covering every safe/review/reject rule;
- model-output hallucination and receipt-binding rejection;
- offline queue and resume tests.

### 16.2 Cryptography and sync

- cross-platform known-answer vectors;
- nonce uniqueness and tamper rejection;
- proof that server fixtures contain no plaintext profile/workflow strings;
- device revocation and stale-token rejection;
- divergent-generation conflict tests;
- lost-key and recovery flows;
- export and account-deletion verification;
- chunk boundary, ordering, duplication, truncation, and quota tests.

### 16.3 Billing

- Polar sandbox checkout, activation, renewal, cancellation, past-due, revocation, and refund;
- signature failure and replay tests;
- duplicate and out-of-order webhook tests;
- checkout redirect cannot unlock features;
- cached entitlement expiry and grace behavior;
- customer portal path;
- provider contract tests independent of Polar.

### 16.4 Product proof

- install on a clean machine or clean user profile;
- two supported agent hosts;
- two devices for pairing and sync;
- a full session-to-candidate-to-activation-to-rollback recording;
- a cloud outage during local operation;
- a billing cancellation without local data loss;
- privacy scan of logs, network payloads, D1 records, and packaged artifacts;
- external pilot receipts from users other than Ohad.

No public claim may convert synthetic tests into user outcomes or treat clone/download counts as active users.

## 17. Fast gated sprint

The target is five focused working days after Claude hands off the occupied benchmark, video, and learning-loop paths. This is a sequencing target, not permission to skip a gate.

### Day 0: specification and isolation

- commit this design in an isolated worktree;
- receive Ohad's written-spec approval;
- produce a bite-sized implementation plan;
- inventory Claude's final diff before touching overlapping files.

### Day 1: local transaction foundation

- freeze versioned candidate, generation, and receipt schemas;
- implement atomic local generation store and rollback tests;
- introduce narrow command/module seams without breaking the one-file CLI contract.

### Day 2: companion vertical slice

- detect completed sessions;
- build deterministic extraction queue;
- connect one explicit agent bridge;
- implement safe policy and one adapter end to end;
- demonstrate activation and rollback offline.

### Day 3: encrypted sync vertical slice

- implement local key management and device identity;
- deploy development Worker/D1 on free limits;
- pair two devices and sync encrypted generations;
- verify conflict, tamper, outage, and recovery behavior.

### Day 4: Polar and control center

- configure Polar sandbox products;
- implement checkout, signed webhooks, entitlements, and portal;
- expose queue, agents, devices, versions, rollback, and billing in the local control center;
- run the full sandbox billing matrix.

### Day 5: private founding-beta gate

- clean-install and privacy review;
- end-to-end proof recording;
- invite a very small set of explicit testers without promotional obligation;
- stage pricing, onboarding, support, and launch copy;
- do not open paid checkout publicly until the launch gates pass.

If a gate fails, work stays on that gate. Features are cut before safety checks are cut. The first cuts are visual polish, multi-device convenience beyond pairing, and secondary agent adapters, not rollback, encryption, privacy, or billing integrity.

## 18. Launch and growth gates

### 18.1 Private beta gate

All must pass:

- current open-source tests remain green;
- new local, sync, security, and billing tests pass;
- one clean install completes without manual repository edits;
- one complete learning cycle and rollback works on two supported agents;
- server and network inspection find no raw logs or plaintext artifacts;
- cloud outage does not block local operation;
- Polar sandbox lifecycle is verified end to end;
- no unresolved data-loss or privilege-boundary defect.

### 18.2 Paid founding-beta gate

All must pass:

- at least three non-founder testers complete onboarding;
- at least two activate or deliberately reject a real candidate with the reason captured;
- every tester can export and rollback without founder intervention;
- pricing and limitations are shown before checkout;
- support, refund, privacy, terms, and deletion paths are live;
- Ohad approves the exact public checkout switch.

### 18.3 Proof-led distribution

Distribution remains staged until the benchmark proof is publishable. Every public beat must add a distinct reason to care: measured benchmark evidence, a real workflow, a user outcome, a meaningful capability, or an honest lesson.

Channel rules remain fixed:

- no Hacker News projection or automation;
- Reddit uses few, spaced, native confession-format posts and no duplicate copy or bumping;
- X uses number-first proof and approved scheduling only;
- YouTube carries the evergreen two-condition demonstration;
- Product Hunt is one timed spike after benchmark and paid onboarding are ready;
- directory work is maintenance, not the primary growth engine;
- outreach is one-to-one, useful-first, and manually approved by Ohad;
- no public posting, email, outreach, or launch execution without Ohad's exact approval.

The product loop is:

1. inspectable proof earns attention;
2. open source earns trust and adoption;
3. Autopilot removes recurring maintenance for power users;
4. successful learning cycles create demonstrable workflows and testimonials;
5. those outcomes become the next non-repetitive distribution assets.

## 19. Success measures

### 19.1 Product measures

- onboarding completion;
- first completed-session detection;
- time to first valid candidate;
- candidate activation, edit, rejection, and rollback rates;
- successful propagation by adapter;
- weekly learning-cycle completion;
- sync and recovery success;
- privacy or integrity incidents;
- support minutes per active customer.

### 19.2 Revenue measures

- checkout started and completed;
- monthly versus annual selection;
- trial-to-paid conversion if a trial is later introduced;
- first and second renewal;
- refund, chargeback, cancellation, and failed-payment recovery;
- gross revenue, provider fees, and payout receipts.

### 19.3 Growth measures

- GitHub stars by dated source event;
- unique repository visitors and clones from GitHub's exact traffic window;
- verified package downloads only from a named provider and time window;
- benchmark page visitors and outbound install clicks;
- clean installs that reach a locally recorded first successful action;
- Discord joins and active participants;
- user-authored tutorials, workflows, issues, and testimonials.

No visitor, conversion, download, star, or revenue total is forecast unless it is built bottom-up from sourced per-channel evidence. Unknowns remain unknown.

## 20. Stop and expansion rules

Pause paid expansion when any of these occurs:

- plaintext personal artifacts or raw logs reach the server;
- rollback or export cannot recover the last valid local state;
- billing grants access from an unverified redirect or webhook;
- support or refund behavior is unclear;
- a distribution action triggers a platform spam warning;
- a public claim cannot be reproduced from its cited evidence.

Expand only from repeated demand:

- add a second billing provider after Polar becomes a business risk or Paddle is verified and materially better;
- add hosted model inference only when customers request it, unit economics are positive, and it is separately consented and metered;
- add teams only after multiple paying users ask to share bounded artifacts;
- add community pattern contribution only through its separate privacy design;
- raise price only after the retention and reliability gate in Section 12.3.

## 21. Current provider evidence

These sources were checked on 2026-07-16 and must be rechecked before production launch because provider terms and limits can change:

- [Cloudflare Workers limits](https://developers.cloudflare.com/workers/platform/limits/)
- [Cloudflare Workers and D1 pricing](https://developers.cloudflare.com/workers/platform/pricing/)
- [Cloudflare D1 limits](https://developers.cloudflare.com/d1/platform/limits/)
- [Polar pricing](https://polar.sh/resources/pricing)
- [Polar supported countries](https://polar.sh/docs/merchant-of-record/supported-countries)
- [Polar Merchant of Record](https://polar.sh/docs/merchant-of-record/introduction)
- [Polar webhook setup](https://polar.sh/docs/integrate/webhooks/endpoints)
- [Polar webhook events](https://polar.sh/docs/integrate/webhooks/events)
- [Polar customer portal](https://polar.sh/docs/features/customer-portal/introduction)
- [Polar account reviews](https://polar.sh/docs/merchant-of-record/account-reviews)

Polar handles international sales-tax obligations as Merchant of Record, but that does not settle Ohad's Israeli business registration, income tax, bookkeeping, or personal tax obligations. Those remain a separate professional/legal check before meaningful revenue.

## 22. Changelog

- Replaced the earlier 30-day rollout with a five-day gated sprint.
- Switched the first billing implementation from Paddle-first to Polar-first because the Polar account is ready and Israel is supported.
- Preserved a provider-neutral billing boundary so Paddle remains a later option.
- Separated deterministic unattended work from visible model-assisted work to avoid hidden subscription consumption.
- Made the free/open-source boundary explicit and prohibited local data lockout after cancellation.
- Added hard internal caps and fail-closed behavior below current free-tier limits.
- Preserved Claude's ownership of active benchmark, video, and learning-loop work until handoff and diff review.
- Kept public distribution staged and approval-gated, with no spam-prone automation.
