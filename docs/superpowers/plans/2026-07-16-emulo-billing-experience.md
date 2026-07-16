# Emulo Billing Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Emulo's placeholder account and payment pages with a branded, authenticated, webhook-truthful founding-beta experience while preserving the disabled-by-default checkout gate.

**Architecture:** A new account-status module authenticates the hashed browser session and maps the normalized D1 entitlement to a provider-neutral view model. A separate UI module renders signed-out, account, and payment-verification surfaces and owns the CSP-compatible stylesheet and small same-origin client script. `index.ts` remains the route composition root; Polar checkout, portal, and webhook handlers remain the only provider-facing modules.

**Tech Stack:** TypeScript 7, Cloudflare Workers, D1, Vitest Workers pool, Polar SDK, semantic HTML, vanilla CSS and JavaScript.

---

## File map

- Create `cloud/worker/src/account-status.ts`: authenticated entitlement read and safe view model.
- Create `cloud/worker/src/account-ui.ts`: HTML shell, account/receipt renderers, stylesheet, client script, and approved Emulo SVG response.
- Create `cloud/worker/test/account-status.test.ts`: direct status-domain tests.
- Modify `cloud/worker/src/index.ts`: route account/status/UI assets through the new modules.
- Modify `cloud/worker/test/authenticated-worker.test.ts`: public route and rendered-state integration tests.
- Modify `cloud/worker/README.md`: describe truthful status and safe deployment behavior.
- Update `.viberaven/production-context.md`: preserve external proof and open production actions.

### Task 1: Provider-neutral account status

**Files:**
- Create: `cloud/worker/test/account-status.test.ts`
- Create: `cloud/worker/src/account-status.ts`

- [ ] **Step 1: Write the failing status tests**

Create authenticated and unauthenticated requests using the existing auth-store helpers. The tests must assert:

```ts
expect(await resolveAccountStatus(signedOut, testEnv, NOW)).toEqual({
  authenticated: false,
  environment: "sandbox",
  checkoutEnabled: false,
});

expect(await resolveAccountStatus(signedIn, testEnv, NOW)).toMatchObject({
  authenticated: true,
  entitlement: { state: "none", productCode: null },
});

expect(active.entitlement).toEqual({
  state: "active",
  productCode: "founding-monthly",
  currentPeriodEnd: "2026-08-16T12:00:00.000Z",
  graceEndsAt: null,
  recoveryEndsAt: null,
});
expect(JSON.stringify(active)).not.toMatch(/provider|subscription|customer|account_id/);
```

Also insert a `past_due` row and prove its bounded lifecycle timestamps are preserved. Inject a D1 failure and prove `resolveAccountStatus` rejects without serializing diagnostics itself.

- [ ] **Step 2: Run the focused test and observe RED**

Run:

```powershell
npx vitest run test/account-status.test.ts
```

Expected: FAIL because `../src/account-status` does not exist.

- [ ] **Step 3: Implement the minimum status module**

Export these provider-neutral types and resolver:

```ts
export interface EntitlementSummary {
  state: EntitlementState;
  productCode: ProductCode | null;
  currentPeriodEnd: string | null;
  graceEndsAt: string | null;
  recoveryEndsAt: string | null;
}

export type AccountStatus =
  | {
      authenticated: false;
      environment: "sandbox" | "production";
      checkoutEnabled: false;
    }
  | {
      authenticated: true;
      environment: "sandbox" | "production";
      checkoutEnabled: boolean;
      entitlement: EntitlementSummary;
    };

export async function resolveAccountStatus(
  request: Request,
  env: Env,
  now = new Date(),
): Promise<AccountStatus>;
```

Authenticate with `authenticateBrowserSession`. Use one prepared query selecting only `state`, `product_code`, `current_period_end`, `grace_ends_at`, and `recovery_ends_at`. Map no row to state `none` with null plan/timestamps. Derive environment only from `POLAR_SERVER === "production"`; derive checkout availability from `PAID_CHECKOUT_ENABLED === "true"` and configured environment.

- [ ] **Step 4: Run focused tests and observe GREEN**

Run `npx vitest run test/account-status.test.ts`.

Expected: all account-status tests pass with no warnings.

- [ ] **Step 5: Commit the status boundary**

```powershell
git add cloud/worker/src/account-status.ts cloud/worker/test/account-status.test.ts
git commit -m "feat: expose safe Emulo account status"
```

### Task 2: Truthful account/status routes

**Files:**
- Modify: `cloud/worker/test/authenticated-worker.test.ts`
- Modify: `cloud/worker/src/index.ts`

- [ ] **Step 1: Write failing route tests**

Add integration tests that prove:

```ts
const signedOut = await SELF.fetch("https://api.example/v1/account/status");
expect(signedOut.status).toBe(401);
expect(signedOut.headers.get("cache-control")).toBe("no-store");

const account = await SELF.fetch("https://api.example/account");
expect(account.status).toBe(200);
expect(await account.text()).toContain("Continue with GitHub");
expect(await account.text()).not.toContain("account is connected");
```

Create a live browser session and assert authenticated status JSON contains the normalized state but not `accountId`, `providerCustomerId`, `providerSubscriptionId`, or provider errors. Add method checks for POST to `/v1/account/status` returning `405`.

- [ ] **Step 2: Run the integration test and observe RED**

Run `npx vitest run test/authenticated-worker.test.ts`.

Expected: FAIL because the status route is missing and the account page still makes an unconditional connected-account claim.

- [ ] **Step 3: Add the status route and authenticated page composition**

In `index.ts`, resolve account status for `/account` and `/v1/billing/complete`. Add:

```ts
if (url.pathname === "/v1/account/status") {
  if (request.method !== "GET") return json(405, { status: "method-not-allowed" });
  const status = await resolveAccountStatus(request, env);
  return status.authenticated
    ? json(200, status)
    : json(401, { status: "unauthenticated" });
}
```

All responses must keep `Cache-Control: no-store`. Catch unexpected status-read failures at the Worker boundary and return a bounded unavailable page/JSON without exception text.

- [ ] **Step 4: Run the focused route tests and observe GREEN**

Run `npx vitest run test/authenticated-worker.test.ts`.

Expected: status/auth method and privacy assertions pass.

- [ ] **Step 5: Commit route behavior**

```powershell
git add cloud/worker/src/index.ts cloud/worker/test/authenticated-worker.test.ts
git commit -m "feat: make Emulo account state authenticated"
```

### Task 3: Branded Emulo account and receipt structure

**Files:**
- Create: `cloud/worker/src/account-ui.ts`
- Modify: `cloud/worker/src/index.ts`
- Modify: `cloud/worker/test/authenticated-worker.test.ts`

- [ ] **Step 1: Write failing structural UI tests**

Test the rendered pages for semantic and state-specific markers:

```ts
expect(accountBody).toContain('class="brand-mark"');
expect(accountBody).toContain('href="/emulo.svg"');
expect(accountBody).toContain('href="/account.css"');
expect(accountBody).toContain('data-account-state="signed-out"');
expect(accountBody).toContain("Your way of working, carried forward.");

expect(completeBody).toContain('data-payment-state="verifying"');
expect(completeBody).toContain('aria-live="polite"');
expect(completeBody).not.toContain("Payment successful");
```

Add route tests for `/account.css`, `/account.js`, and `/emulo.svg`, including exact content types, immutable/no-store caching as appropriate, and method `405` responses.

- [ ] **Step 2: Run UI integration tests and observe RED**

Run `npx vitest run test/authenticated-worker.test.ts`.

Expected: FAIL because the new structural markers and assets do not exist.

- [ ] **Step 3: Implement the UI module**

Export:

```ts
export function renderAccountPage(status: AccountStatus): Response;
export function renderPaymentPage(status: AccountStatus): Response;
export function accountStyles(): Response;
export function accountScript(): Response;
export function emuloMark(): Response;
export function unavailablePage(): Response;
```

Use a structural split layout rather than a dashboard grid. The left identity panel contains the approved Emulo mark, category statement, privacy promise, and explicit environment badge. The right action panel contains exactly one state-driven primary action and concise plan facts. Use the existing `assets/emulo.svg` artwork as the source for the inline/static SVG response.

Required CSS qualities:

- system/serif editorial display pairing with no external font request;
- ink, warm paper, teal, and coral palette grounded in the approved mascot;
- visible keyboard focus and minimum 44 px controls;
- fluid layout from 320 px through desktop;
- no generic gradient background or repeated rounded-card grid;
- `prefers-reduced-motion` branch that removes transitions;
- high-contrast status chips for sandbox, active, attention, and ended states.

Required copy behavior:

- signed out: `Continue with GitHub`;
- none and checkout disabled: explain private founding beta without a dead purchase promise;
- active: `Founding Beta is active` plus monthly/annual label and `Manage subscription`;
- past due/grace: `Billing needs attention` and preserve local-open-source availability;
- ended/refunded: cloud continuity stopped, local Emulo remains owned by the user;
- verifying receipt: `Waiting for Polar confirmation` until D1 says otherwise.

- [ ] **Step 4: Wire asset/UI routes in `index.ts`**

Serve `/account.css`, `/account.js`, and `/emulo.svg` from the Worker module. Keep a strict CSP:

```text
default-src 'none'; img-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'
```

Set `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and `Cache-Control: no-store` on account documents. The SVG may use immutable public caching because it contains no state.

- [ ] **Step 5: Run UI tests and observe GREEN**

Run `npx vitest run test/authenticated-worker.test.ts`.

Expected: semantic structure, truthful copy, route, cache, CSP, and method assertions pass.

- [ ] **Step 6: Commit the structural redesign**

```powershell
git add cloud/worker/src/account-ui.ts cloud/worker/src/index.ts cloud/worker/test/authenticated-worker.test.ts
git commit -m "feat: redesign Emulo founding beta account"
```

### Task 4: Checkout, portal, and webhook-confirmation interactions

**Files:**
- Modify: `cloud/worker/src/account-ui.ts`
- Modify: `cloud/worker/test/authenticated-worker.test.ts`

- [ ] **Step 1: Write failing interaction-contract tests**

Assert the script contains same-origin calls for checkout, portal, and status, plus bounded polling and state markers:

```ts
expect(script).toContain('fetch("/v1/billing/checkout"');
expect(script).toContain('fetch("/v1/billing/portal"');
expect(script).toContain('fetch("/v1/account/status"');
expect(script).toContain("MAX_STATUS_ATTEMPTS");
expect(script).toContain("credentials: \"same-origin\"");
```

Assert checkout forms appear only when the authenticated status allows checkout and entitlement is not active. Assert active state renders portal but not plan-purchase forms.

- [ ] **Step 2: Run the focused test and observe RED**

Run `npx vitest run test/authenticated-worker.test.ts`.

Expected: FAIL because portal handling, account status polling, and conditional state rendering are missing.

- [ ] **Step 3: Implement minimal interactions**

The client script must:

- submit only `monthly` or `yearly` from fixed `data-plan` attributes;
- POST JSON with same-origin credentials;
- disable only the initiating control while awaiting a result;
- navigate only when the response is `ok` and contains an HTTPS URL;
- POST to the portal route from `data-portal-form`;
- on `data-payment-state="verifying"`, poll status at most 12 times with a 1.5 second delay;
- stop on `active`, `past_due`, `grace`, `ended`, or `refunded`;
- update heading, body, badge, and primary link through text content and fixed DOM attributes, never `innerHTML` from JSON;
- render a pending fallback after the bounded attempt limit.

- [ ] **Step 4: Run focused tests and observe GREEN**

Run `npx vitest run test/authenticated-worker.test.ts test/polar-client.test.ts`.

Expected: UI interaction contract and existing checkout/portal ownership tests pass.

- [ ] **Step 5: Commit interaction behavior**

```powershell
git add cloud/worker/src/account-ui.ts cloud/worker/test/authenticated-worker.test.ts
git commit -m "feat: confirm Emulo billing state from webhooks"
```

### Task 5: Documentation and full local verification

**Files:**
- Modify: `cloud/worker/README.md`
- Modify: `.viberaven/production-context.md`

- [ ] **Step 1: Update documentation**

Document `/v1/account/status`, the signed-out/account/receipt behavior, and the exact invariant:

```text
The completion URL is a verification surface, not an access grant. Only an
authenticated status read of a D1 entitlement written by a verified Polar
webhook may display an active founding-beta state.
```

Correct stale provider notes by separating completed sandbox evidence from pending production actions. Do not include secrets, account IDs, provider customer IDs, subscription IDs, event IDs, or raw payloads.

- [ ] **Step 2: Run complete verification**

From `cloud/worker`:

```powershell
npm run typecheck
npm test
npx wrangler deploy --dry-run --outdir .wrangler-dry-run
```

From the worktree root:

```powershell
git diff --check
git status --short
git diff -- cloud/worker .viberaven/production-context.md docs/superpowers
```

Expected: zero type errors, zero test failures, successful Worker bundle, no whitespace errors, no unexpected files, no secret values, and no unrelated branch changes.

- [ ] **Step 3: Commit docs and verification memory**

```powershell
git add cloud/worker/README.md .viberaven/production-context.md docs/superpowers
git commit -m "docs: record Emulo billing experience boundary"
```

### Task 6: Safe deploy and live sandbox verification

**Files:**
- No production source change expected.

- [ ] **Step 1: Prove the safe deployment configuration**

Run:

```powershell
rg -n 'PAID_CHECKOUT_ENABLED|POLAR_SERVER' cloud/worker/wrangler.jsonc
```

Expected: checkout is `false`; server is `sandbox`.

- [ ] **Step 2: Deploy while preserving secrets**

From `cloud/worker`:

```powershell
npx wrangler deploy --keep-vars
```

Record the Worker version ID and public URL, not secret values.

- [ ] **Step 3: Verify unauthenticated and fail-closed live routes**

Verify:

- `/account` returns a branded signed-out surface;
- `/account.css`, `/account.js`, and `/emulo.svg` return exact content types;
- `/v1/account/status` returns `401` without a session;
- POST `/v1/billing/checkout` returns `503 checkout-disabled`;
- unsigned POST `/v1/billing/webhooks/polar` returns `403 rejected`.

- [ ] **Step 4: Verify authenticated state in the browser**

Use the existing GitHub browser session or sign in again. Confirm the account page displays `Founding Beta is active`, `Monthly`, `Sandbox`, and the portal action. Open the completion URL and confirm it reads the existing active D1 entitlement instead of remaining on a generic submitted screen. Capture redacted screenshots with no query codes or identifiers.

- [ ] **Step 5: Query bounded D1 proof**

Run count/state-only queries proving one active sandbox entitlement and applied lifecycle events. Do not print account, customer, subscription, product, or event identifiers.

### Task 7: Production Polar activation runbook

**Files:**
- Create: `docs/release/emulo-polar-production-activation.md`

- [ ] **Step 1: Verify current official Polar production requirements**

Use only Polar's official documentation/dashboard evidence for current production organization, product, webhook, token, portal, fee, tax, and payout requirements. Mark anything dashboard-only as unknown until Ohad provides a redacted receipt or a connected provider tool proves it.

- [ ] **Step 2: Write exact owner/provider actions**

The runbook must separate:

- repository/config changes the agent can make;
- Polar dashboard actions requiring Ohad's authenticated account or 2FA;
- Cloudflare secret entry that must occur interactively and never in chat;
- evidence required before enabling checkout;
- the private real purchase/refund lifecycle;
- the rollback command that disables checkout without disabling webhooks for existing customers.

- [ ] **Step 3: Stop at the live-money gate if owner evidence is missing**

Do not create charges, refund real payments, change payout/KYC settings, publish a checkout, or enable the production gate without explicit approval at that exact stage. The completed goal may be marked blocked only after the same owner/provider evidence gap persists across three goal turns and no other in-scope progress remains.

## Final completion gate

- [ ] Branded account and receipt surfaces are deployed and observed live.
- [ ] Active copy is derived only from an authenticated D1 entitlement.
- [ ] Checkout stays disabled until a separately approved production window.
- [ ] Full Worker tests and typecheck pass freshly.
- [ ] Sandbox lifecycle, portal access, and fail-closed routes have fresh evidence.
- [ ] Production provider actions are either proven or clearly isolated as owner-only, with no secrets requested in chat.
- [ ] No main-checkout, benchmark, video, antigravity, or unrelated work was changed.
