# Emulo Pro Production Products Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind the verified private Polar production products to Emulo while keeping live checkout disabled and making customer-facing plan naming consistent with Emulo Pro.

**Architecture:** Polar remains the provider source of truth; the repository stores only the two nonsecret UUID product IDs. Existing production guards continue to reject partial configuration and committed checkout enablement. Customer UI copy changes only the paid-tier name and preserves entitlement behavior.

**Tech Stack:** Cloudflare Workers, TypeScript, Vitest, Node test runner, Wrangler, Polar production MCP.

---

### Task 1: Bind verified production product IDs

**Files:**
- Modify: `cloud/worker/wrangler.production.jsonc`
- Test: `cloud/worker/test/production-config-validation.node.mjs`

- [ ] **Step 1: Replace both placeholders with provider-verified UUIDs**

```json
"POLAR_MONTHLY_PRODUCT_ID": "ce99808b-4e11-4cec-bc31-d9654d558e08",
"POLAR_YEARLY_PRODUCT_ID": "b6535378-b1bd-40ee-bd37-96a03abec2f2"
```

Keep `"PAID_CHECKOUT_ENABLED": "false"` unchanged.

- [ ] **Step 2: Run the production configuration guard**

Run: `npm run verify:production-config`

Expected: exit `0`, production server accepted, product activation state configured, checkout still disabled.

### Task 2: Rename customer-facing paid access to Emulo Pro

**Files:**
- Modify: `cloud/worker/test/account-ui.test.ts`
- Modify: `cloud/worker/test/authenticated-worker.test.ts`
- Modify: `cloud/worker/src/account-ui.ts`

- [ ] **Step 1: Change expectations before implementation**

Replace `Founding Beta is active` with `Emulo Pro is active` and `Founding Beta activated` with `Emulo Pro activated` in both test files.

- [ ] **Step 2: Run focused tests and verify they fail**

Run: `npx vitest run test/account-ui.test.ts test/authenticated-worker.test.ts`

Expected: failures show the old Founding Beta headings.

- [ ] **Step 3: Apply the minimal copy change**

In `account-ui.ts`, change active headings to `Emulo Pro is active` and `Emulo Pro activated`. Change active explanatory copy from `founding access` or `founding plan` to `Emulo Pro access` or `Emulo Pro plan`. Do not change state handling, checkout behavior, or entitlement mapping.

- [ ] **Step 4: Re-run focused tests**

Run: `npx vitest run test/account-ui.test.ts test/authenticated-worker.test.ts`

Expected: both files pass.

### Task 3: Update the production handoff and context receipt

**Files:**
- Modify: `docs/release/emulo-polar-production-activation.md`
- Modify: `.viberaven/production-context.md`

- [ ] **Step 1: Update product names in the runbook**

Use `Emulo Pro Monthly` and `Emulo Pro Annual`; preserve prices, cadence, no-trial rule, and private rollout boundary.

- [ ] **Step 2: Record the provider receipt**

Add a compact production-context entry recording the Emulo organization ID, both product IDs, exact verified prices/cadences, private visibility, no trial, and the fact that checkout remained disabled. Leave production OAT, webhook, deploy, and real-money lifecycle as open actions.

### Task 4: Verify and publish the isolated branch

**Files:**
- Verify all files changed above.

- [ ] **Step 1: Run full Worker verification**

Run: `npm test`

Expected: all Vitest and production-config tests pass.

Run: `npm run typecheck`

Expected: exit `0`.

Run: `npm run verify:production-config`

Expected: exit `0` with checkout disabled.

Run: `npx wrangler deploy --dry-run --config wrangler.production.jsonc`

Expected: bundle succeeds without deploying.

- [ ] **Step 2: Review the diff and safety invariants**

Run: `git diff --check` and inspect `git diff`.

Expected: no whitespace errors, no secrets, no checkout enablement, no Sandbox identifiers.

- [ ] **Step 3: Commit and push**

```bash
git add cloud/worker/wrangler.production.jsonc cloud/worker/src/account-ui.ts cloud/worker/test/account-ui.test.ts cloud/worker/test/authenticated-worker.test.ts docs/release/emulo-polar-production-activation.md .viberaven/production-context.md docs/superpowers/plans/2026-07-17-emulo-pro-production-products.md
git commit -m "feat: connect Emulo Pro production products"
git push
```
