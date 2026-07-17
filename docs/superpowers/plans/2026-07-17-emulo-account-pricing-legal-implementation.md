# Emulo Account, Pricing, And Legal Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a professional, consumer-ready Emulo account surface, truthful Free-versus-Pro pricing, real Emulo branding, and public Privacy, Terms, and Refund pages while checkout remains disabled.

**Architecture:** Keep the public site static under `site/` and keep the authenticated account state in the existing Cloudflare Worker. Serve the optimized real Emulo icon as a Worker data module, structurally replace the split account layout with a centered shell, and test every removed/internal phrase so it cannot regress. Legal pages describe the current identity/billing service and the approved future encrypted-sync boundary without claiming that sync is live.

**Tech Stack:** Static HTML/CSS, TypeScript Cloudflare Worker, Wrangler data modules, Vitest with Workers pool, Python `unittest`, existing Vercel and Cloudflare deployment paths.

---

## File Structure

- Modify `tests/test_site_pricing.py`: exact public pricing contract and forbidden-copy checks.
- Create `tests/test_site_legal.py`: public legal-page structure, operator, contact, provider, privacy, and cross-link tests.
- Modify `site/index.html`: professional pricing copy, annual saving, policy links, and real favicon.
- Create `site/privacy.html`: actual data-flow and user-rights policy.
- Create `site/terms.html`: open-source/service separation and subscription terms.
- Create `site/refunds.html`: approved 14-day initial/7-day renewal policy.
- Create `site/legal.css`: shared legal-page editorial styles.
- Copy `assets/emulo-oauth.png` to `cloud/worker/src/emulo-oauth.png`: optimized Worker-owned real icon.
- Create `cloud/worker/src/data-modules.d.ts`: PNG data-module TypeScript declaration.
- Modify `cloud/worker/wrangler.jsonc` and `cloud/worker/wrangler.production.jsonc`: declare `.png` `Data` modules.
- Modify `cloud/worker/src/account-ui.ts`: centered account/payment document, professional copy, provider area, and legal links.
- Modify `cloud/worker/src/index.ts`: serve `/emulo.png` with exact immutable headers and retire the old SVG route from rendered pages.
- Modify `cloud/worker/test/account-ui.test.ts`: exact state and forbidden-copy assertions.
- Modify `cloud/worker/test/authenticated-worker.test.ts`: live route/content-type/security-header assertions.

### Task 1: Freeze the professional pricing contract

**Files:**
- Modify: `tests/test_site_pricing.py`
- Modify: `site/index.html`

- [ ] **Step 1: Replace the beta pricing test with the approved contract**

```python
def test_approved_prices_and_annual_value_are_visible(self):
    pricing = self.html.split('id="pricing"', 1)[1].split("</section>", 1)[0]
    for text in ("$0", "$9", "$108", "$79", "Save 27%"):
        self.assertIn(text, pricing)
    self.assertIn("Get Emulo", pricing)
    self.assertIn("Choose monthly", pricing)
    self.assertIn("Choose annual", pricing)
    for rejected in ("Private beta", "Install from GitHub", "Open account", "Payment truth stays server-side"):
        self.assertNotIn(rejected, pricing)
```

- [ ] **Step 2: Add a test that the Free-versus-Pro boundary stays honest**

```python
def test_pricing_keeps_free_capable_and_does_not_claim_sync_is_live(self):
    pricing = self.html.split('id="pricing"', 1)[1].split("</section>", 1)[0]
    for text in ("Free and open source", "MIT", "local", "No subscription"):
        self.assertIn(text, pricing)
    self.assertNotIn("available today", pricing.lower())
    self.assertNotIn("unlimited", pricing.lower())
```

- [ ] **Step 3: Run the focused test and verify the old page fails**

Run: `python -m unittest tests.test_site_pricing -v`

Expected: FAIL because the page still contains `Private beta`, old action labels, and no `$108`/`Save 27%` presentation.

- [ ] **Step 4: Replace the pricing copy and annual row**

Use these exact customer-facing values in `site/index.html`:

```html
<span class="section-label">OPEN SOURCE + MANAGED CONTINUITY</span>
<h2>Start free. Add continuity when your workflows depend on it.</h2>
<p>Emulo stays useful on your machine. Emulo Pro adds the managed layer for people who want continuity without maintaining it themselves.</p>
```

Free card:

```html
<span class="price-label">Emulo</span>
<h3>Free and open source.</h3>
<div class="price-value">$0</div>
<a class="price-link" href="https://github.com/ohad6k/emulo">Get Emulo</a>
```

Pro rows:

```html
<div class="plan-row">
  <span><strong>$9</strong> / month</span>
  <a href="https://emulo-production.ohad1306.workers.dev/account">Choose monthly</a>
</div>
<div class="plan-row plan-row-featured">
  <span><s>$108</s> <strong>$79</strong> / year <em>Save 27%</em></span>
  <a href="https://emulo-production.ohad1306.workers.dev/account">Choose annual</a>
</div>
```

Delete the beta tag and the entire `billing-proof` paragraph. Do not add live encrypted-sync claims.

- [ ] **Step 5: Run focused tests**

Run: `python -m unittest tests.test_site_pricing -v`

Expected: all pricing tests PASS.

- [ ] **Step 6: Commit the pricing slice**

```powershell
git add tests/test_site_pricing.py site/index.html
git commit -m "feat: clarify Emulo free and Pro pricing"
```

### Task 2: Publish the legal baseline

**Files:**
- Create: `tests/test_site_legal.py`
- Create: `site/privacy.html`
- Create: `site/terms.html`
- Create: `site/refunds.html`
- Create: `site/legal.css`
- Modify: `site/index.html`

- [ ] **Step 1: Write failing legal-page tests**

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

class SiteLegalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {
            name: (SITE / name).read_text(encoding="utf-8")
            for name in ("privacy.html", "terms.html", "refunds.html")
        }

    def test_every_policy_has_consistent_identity_and_links(self):
        for html in self.pages.values():
            self.assertIn("Emulo", html)
            self.assertIn("Ohad Krispin", html)
            self.assertIn("Israel", html)
            self.assertIn("ohadkrispin@gmail.com", html)
            for href in ("/privacy.html", "/terms.html", "/refunds.html"):
                self.assertIn(f'href="{href}"', html)
            self.assertNotIn("registered company", html.lower())

    def test_privacy_describes_actual_minimized_data(self):
        html = self.pages["privacy.html"]
        for text in ("Google", "GitHub", "Cloudflare", "Polar", "Vercel", "browser session", "raw AI session logs"):
            self.assertIn(text, html)
        self.assertIn("never receives the decryption key", html)

    def test_terms_separate_open_source_and_pro(self):
        html = self.pages["terms.html"]
        for text in ("MIT License", "Emulo Pro", "Merchant of Record", "automatic renewal", "Israel"):
            self.assertIn(text, html)

    def test_refund_windows_are_exact(self):
        html = self.pages["refunds.html"]
        self.assertIn("14 days", html)
        self.assertIn("7 days", html)
        self.assertIn("does not automatically cancel", html)
        self.assertIn("mandatory consumer rights", html.lower())
```

- [ ] **Step 2: Run the legal tests and verify missing files fail**

Run: `python -m unittest tests.test_site_legal -v`

Expected: ERROR with `FileNotFoundError` for `site/privacy.html`.

- [ ] **Step 3: Create the shared legal layout**

Each page uses this structure and its relevant policy body:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f5f1e8">
  <link rel="icon" type="image/png" href="/assets/emulo.png">
  <link rel="stylesheet" href="/legal.css">
  <title>Privacy Policy | Emulo</title>
</head>
<body>
  <header class="legal-header"><a href="/"><img src="/assets/emulo.png" alt=""><span>EMULO</span></a></header>
  <main class="legal-document">
    <p class="legal-kicker">EMULO POLICY</p>
    <h1>Privacy Policy</h1>
    <p class="legal-updated">Last updated: July 17, 2026</p>
    <!-- complete policy sections from the approved design -->
  </main>
  <footer><a href="/privacy.html">Privacy</a><a href="/terms.html">Terms</a><a href="/refunds.html">Refunds</a></footer>
</body>
</html>
```

Use `Emulo, operated by Ohad Krispin in Israel` and `mailto:ohadkrispin@gmail.com`. State that synchronized artifacts are a Pro capability that is activated only when available; raw AI session logs are not uploaded by the account/sync service. State Polar is Merchant of Record, and include the approved 14-day/7-day refund windows.

- [ ] **Step 4: Add a minimal shared editorial stylesheet**

```css
:root { color-scheme: light; --paper:#f5f1e8; --ink:#171715; --muted:#69665f; --line:#d9d2c5; }
* { box-sizing: border-box; }
body { margin:0; background:var(--paper); color:var(--ink); font:16px/1.7 system-ui,sans-serif; }
.legal-header, .legal-document, footer { width:min(760px,calc(100% - 40px)); margin-inline:auto; }
.legal-header { padding:24px 0; border-bottom:1px solid var(--line); }
.legal-header a { display:inline-flex; align-items:center; gap:10px; color:inherit; text-decoration:none; font-weight:800; letter-spacing:.18em; }
.legal-header img { width:36px; height:36px; border-radius:10px; object-fit:cover; }
.legal-document { padding:72px 0 80px; }
h1 { max-width:12ch; margin:.2em 0; font:700 clamp(3rem,9vw,5.5rem)/.94 Georgia,serif; letter-spacing:-.05em; }
h2 { margin-top:2.4em; font-size:1.15rem; }
p,li { color:#35332f; }
footer { display:flex; gap:24px; padding:24px 0 48px; border-top:1px solid var(--line); }
footer a { color:inherit; }
```

- [ ] **Step 5: Add policy links to the public home footer**

```html
<a href="/privacy.html">Privacy</a> ·
<a href="/terms.html">Terms</a> ·
<a href="/refunds.html">Refunds</a>
```

- [ ] **Step 6: Run focused legal and pricing tests**

Run: `python -m unittest tests.test_site_legal tests.test_site_pricing -v`

Expected: all tests PASS.

- [ ] **Step 7: Commit the legal slice**

```powershell
git add tests/test_site_legal.py site/privacy.html site/terms.html site/refunds.html site/legal.css site/index.html
git commit -m "feat: publish Emulo customer policies"
```

### Task 3: Serve the real Emulo icon from the Worker

**Files:**
- Copy: `assets/emulo-oauth.png` to `cloud/worker/src/emulo-oauth.png`
- Create: `cloud/worker/src/data-modules.d.ts`
- Modify: `cloud/worker/wrangler.jsonc`
- Modify: `cloud/worker/wrangler.production.jsonc`
- Modify: `cloud/worker/src/index.ts`
- Modify: `cloud/worker/test/authenticated-worker.test.ts`

- [ ] **Step 1: Write the failing PNG route test**

```ts
const mark = await SELF.fetch("https://api.example/emulo.png");
expect(mark.status).toBe(200);
expect(mark.headers.get("content-type")).toBe("image/png");
expect(mark.headers.get("cache-control")).toBe("public, max-age=86400, immutable");
expect((await mark.arrayBuffer()).byteLength).toBeGreaterThan(100_000);
expect((await SELF.fetch("https://api.example/emulo.png", { method: "POST" })).status).toBe(405);
```

- [ ] **Step 2: Run the integration test and verify 404**

Run: `cd cloud/worker; npx vitest run test/authenticated-worker.test.ts`

Expected: FAIL because `/emulo.png` returns 404.

- [ ] **Step 3: Copy the optimized asset and declare the data module**

Run: `Copy-Item -LiteralPath assets/emulo-oauth.png -Destination cloud/worker/src/emulo-oauth.png`

Create `data-modules.d.ts`:

```ts
declare module "*.png" {
  const value: ArrayBuffer;
  export default value;
}
```

Add to both Wrangler configs:

```jsonc
"rules": [
  { "type": "Data", "globs": ["**/*.png"], "fallthrough": true }
]
```

- [ ] **Step 4: Add the exact Worker route**

At module scope in `index.ts`:

```ts
import emuloIcon from "./emulo-oauth.png";
```

Inside `fetch` before the account routes:

```ts
if (url.pathname === "/emulo.png") {
  if (request.method !== "GET") return json(405, { status: "method-not-allowed" });
  return new Response(emuloIcon, { headers: {
    "cache-control": "public, max-age=86400, immutable",
    "content-type": "image/png",
    "x-content-type-options": "nosniff",
  }});
}
```

- [ ] **Step 5: Run typecheck, focused test, and dry run**

Run: `cd cloud/worker; npm run typecheck; npx vitest run test/authenticated-worker.test.ts; npx wrangler deploy --dry-run --config wrangler.production.jsonc`

Expected: all commands exit 0 and the asset is bundled as a data module.

- [ ] **Step 6: Commit the icon route**

```powershell
git add cloud/worker/src/emulo-oauth.png cloud/worker/src/data-modules.d.ts cloud/worker/src/index.ts cloud/worker/wrangler.jsonc cloud/worker/wrangler.production.jsonc cloud/worker/test/authenticated-worker.test.ts
git commit -m "feat: serve the real Emulo account icon"
```

### Task 4: Replace the account page structure

**Files:**
- Modify: `cloud/worker/test/account-ui.test.ts`
- Modify: `cloud/worker/test/authenticated-worker.test.ts`
- Modify: `cloud/worker/src/account-ui.ts`

- [ ] **Step 1: Write the signed-out design contract**

```ts
it("renders the professional two-provider sign-in surface", async () => {
  const html = await body(renderAccountPage({ authenticated:false, environment:"sandbox", checkoutEnabled:false }));
  expect(html).toContain("Sign in to Emulo");
  expect(html).toContain("Continue with Google");
  expect(html).toContain("Continue with GitHub");
  expect(html).toContain('href="/privacy.html"');
  expect(html).toContain('href="/terms.html"');
  expect(html).toContain('href="/refunds.html"');
  for (const rejected of ["Private account", "Signed out", "Production", "View open source", "opaque, hashed browser session", "Connect your Emulo account"]) {
    expect(html).not.toContain(rejected);
  }
});
```

- [ ] **Step 2: Write authenticated copy contracts**

```ts
expect(await body(renderAccountPage(status("none")))).toContain("Your Emulo account is ready.");
expect(await body(renderAccountPage(status("none")))).toContain("Emulo Pro is not available for purchase yet.");
expect(await body(renderAccountPage(status("active")))).toContain("Manage subscription");
```

- [ ] **Step 3: Run focused tests and verify old UI fails**

Run: `cd cloud/worker; npx vitest run test/account-ui.test.ts test/authenticated-worker.test.ts`

Expected: FAIL on Google button, policy links, PNG favicon, and forbidden old copy.

- [ ] **Step 4: Replace the document and signed-out surface**

Use this shell in `account-ui.ts`:

```html
<body>
  <header class="brand-header"><a href="/account"><img src="/emulo.png" alt=""><span>EMULO</span></a></header>
  <main class="account-main">
    <section class="account-surface" data-account-state="signed-out">
      <h1>Sign in to Emulo</h1>
      <p class="lede">Access your account and manage Emulo Pro.</p>
      <div class="provider-actions">
        <a class="provider-button provider-google" href="/v1/auth/google/start">Continue with Google</a>
        <span class="provider-divider">or</span>
        <a class="provider-button provider-github" href="/v1/auth/github/start">Continue with GitHub</a>
      </div>
      <p class="identity-note">Emulo uses your sign-in provider only to verify your identity.</p>
    </section>
  </main>
  <footer class="account-footer"><a href="/privacy.html">Privacy</a><a href="/terms.html">Terms</a><a href="/refunds.html">Refunds</a></footer>
</body>
```

Keep the Google link visible even before the route is configured; the route itself will fail safely until the Google-auth plan is complete.

- [ ] **Step 5: Replace the CSS structure**

Use warm ivory `#f5f1e8`, ink `#171715`, muted `#69665f`, border `#d9d2c5`, a centered `min(460px, calc(100% - 32px))` surface, 48px provider buttons, visible `:focus-visible`, and a 390px media query. Remove `.identity-panel`, navy/teal variables, status pills, and split-grid rules. Preserve `prefers-reduced-motion`.

- [ ] **Step 6: Update favicon and state copy**

Use `<link rel="icon" type="image/png" href="/emulo.png">`. For disabled no-entitlement state use exactly `Your Emulo account is ready.` and `Emulo Pro is not available for purchase yet.` Active uses `Emulo Pro is active.` and `Manage subscription`.

- [ ] **Step 7: Run focused Worker tests**

Run: `cd cloud/worker; npx vitest run test/account-ui.test.ts test/authenticated-worker.test.ts`

Expected: all focused tests PASS.

- [ ] **Step 8: Commit the account redesign**

```powershell
git add cloud/worker/src/account-ui.ts cloud/worker/test/account-ui.test.ts cloud/worker/test/authenticated-worker.test.ts
git commit -m "feat: redesign the Emulo account experience"
```

### Task 5: Serve policies from the account origin

**Files:**
- Create: `cloud/worker/src/legal-pages.ts`
- Modify: `cloud/worker/src/index.ts`
- Modify: `cloud/worker/test/authenticated-worker.test.ts`

- [ ] **Step 1: Write failing account-origin policy route tests**

```ts
for (const path of ["/privacy.html", "/terms.html", "/refunds.html"]) {
  const response = await SELF.fetch(`https://api.example${path}`);
  expect(response.status).toBe(200);
  expect(response.headers.get("content-type")).toBe("text/html; charset=utf-8");
  expect(response.headers.get("content-security-policy")).toContain("default-src 'self'");
  expect(await response.text()).toContain("ohadkrispin@gmail.com");
}
```

- [ ] **Step 2: Run the integration test and verify 404**

Run: `cd cloud/worker; npx vitest run test/authenticated-worker.test.ts`

Expected: FAIL because policy routes do not exist.

- [ ] **Step 3: Create bounded Worker legal responses**

`legal-pages.ts` exports `renderWorkerPolicy(path)` and returns the same approved policy content in the account shell. It uses no inline script, external fonts, user-controlled values, or provider IDs. Return headers:

```ts
{
  "cache-control": "public, max-age=300",
  "content-security-policy": "default-src 'self'; img-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
  "content-type": "text/html; charset=utf-8",
  "referrer-policy": "no-referrer",
  "x-content-type-options": "nosniff",
}
```

- [ ] **Step 4: Route exact GET methods**

```ts
if (["/privacy.html", "/terms.html", "/refunds.html"].includes(url.pathname)) {
  if (request.method !== "GET") return json(405, { status: "method-not-allowed" });
  return renderWorkerPolicy(url.pathname);
}
```

- [ ] **Step 5: Run focused tests**

Run: `cd cloud/worker; npx vitest run test/authenticated-worker.test.ts`

Expected: PASS.

- [ ] **Step 6: Commit account-origin policies**

```powershell
git add cloud/worker/src/legal-pages.ts cloud/worker/src/index.ts cloud/worker/test/authenticated-worker.test.ts
git commit -m "feat: expose policies before Emulo sign-in"
```

### Task 6: Add privacy and regression scans

**Files:**
- Create: `tests/test_emulo_public_security.py`
- Modify: `cloud/worker/test/authenticated-worker.test.ts`

- [ ] **Step 1: Add a tracked public-file leak scan**

```python
import re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = [*ROOT.joinpath("site").glob("*.html"), ROOT / "site" / "legal.css"]

class EmuloPublicSecurityTests(unittest.TestCase):
    def test_public_files_contain_no_secret_shapes_or_provider_ids(self):
        text = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC)
        for value in ("ce99808b-4e11-4cec-bc31-d9654d558e08", "b6535378-b1bd-40ee-bd37-96a03abec2f2"):
            self.assertNotIn(value, text)
        self.assertNotRegex(text, re.compile(r"(?:polar_(?:oat|sk)|client_secret|webhook_secret|BEGIN PRIVATE KEY)", re.I))

    def test_public_copy_does_not_claim_unavailable_paid_features(self):
        text = (ROOT / "site" / "index.html").read_text(encoding="utf-8").lower()
        self.assertNotIn("encrypted sync is available", text)
        self.assertNotIn("payment successful", text)
```

- [ ] **Step 2: Add CSP assertions for account and payment documents**

Assert `default-src 'self'`, `script-src 'self'`, `style-src 'self'`, `img-src 'self'`, `frame-ancestors 'none'`, `base-uri 'none'`, and `form-action 'self'` on account/payment responses.

- [ ] **Step 3: Run security tests**

Run: `python -m unittest tests.test_emulo_public_security -v; cd cloud/worker; npx vitest run test/authenticated-worker.test.ts`

Expected: all tests PASS.

- [ ] **Step 4: Commit the security regression layer**

```powershell
git add tests/test_emulo_public_security.py cloud/worker/test/authenticated-worker.test.ts
git commit -m "test: guard Emulo public privacy boundaries"
```

### Task 7: Full verification and visual receipt

**Files:**
- Modify only if verification exposes a defect.

- [ ] **Step 1: Run all Python tests**

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS with only documented platform skips.

- [ ] **Step 2: Run all Worker tests and typecheck**

Run: `cd cloud/worker; npm test; npm run typecheck; npm run verify:production-config`

Expected: all commands exit 0; checkout remains disabled.

- [ ] **Step 3: Run the production dry run and dependency audit**

Run: `cd cloud/worker; npx wrangler deploy --dry-run --config wrangler.production.jsonc; npm audit --omit=dev --audit-level=high`

Expected: bundle succeeds and audit reports zero high/critical production vulnerabilities.

- [ ] **Step 4: Verify the worktree and diff**

Run: `git status --short; git diff --check; git log --oneline -8`

Expected: clean worktree, no whitespace errors, and one focused commit per task.

- [ ] **Step 5: Start a local Worker and inspect desktop/mobile**

Run: `cd cloud/worker; npx wrangler dev --local --port 8787`

Inspect `/account`, `/privacy.html`, `/terms.html`, `/refunds.html`, and `/v1/billing/complete` at desktop and 390px. Required receipt: real icon, centered account layout, both provider buttons, readable policy pages, no horizontal overflow, no old beta/technical copy.

- [ ] **Step 6: Stop before provider/deploy mutation**

Do not push, migrate production, deploy, install Google secrets, or enable checkout in this plan. Hand off to the Google-auth plan after local proof is complete.
