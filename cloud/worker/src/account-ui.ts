import type { AccountStatus, EntitlementSummary } from "./account-status";

const DOCUMENT_HEADERS = {
  "cache-control": "no-store",
  "content-security-policy":
    "default-src 'none'; img-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
  "content-type": "text/html; charset=utf-8",
  "referrer-policy": "no-referrer",
  "x-content-type-options": "nosniff",
};

const EMULO_MARK = `<svg width="320" viewBox="0 0 470 470" role="img" xmlns="http://www.w3.org/2000/svg">
<title>emulo mascot</title>
<desc>A friendly flat robot with double-stroke eyes, with a faded copy of itself behind it.</desc>
<ellipse cx="306" cy="392" rx="150" ry="20" fill="#0f766e" opacity="0.14"/>
<g opacity="0.28" transform="translate(30,-22)"><rect x="224" y="96" width="212" height="210" rx="52" fill="#14b8a6"/><rect x="306" y="60" width="10" height="40" rx="5" fill="#14b8a6"/><circle cx="311" cy="52" r="15" fill="#14b8a6"/></g>
<line x1="281" y1="92" x2="275" y2="58" stroke="#17303a" stroke-width="7" stroke-linecap="round"/>
<circle cx="273" cy="49" r="16" fill="#ff8a5c" stroke="#17303a" stroke-width="6"/>
<rect x="198" y="200" width="26" height="70" rx="13" fill="#0f9488" stroke="#17303a" stroke-width="6"/>
<rect x="428" y="200" width="26" height="70" rx="13" fill="#0f9488" stroke="#17303a" stroke-width="6"/>
<rect x="216" y="96" width="220" height="216" rx="54" fill="#14b8a6" stroke="#17303a" stroke-width="7"/>
<rect x="248" y="132" width="156" height="132" rx="28" fill="#f6f4ec" stroke="#17303a" stroke-width="6"/>
<g fill="#17303a"><g transform="rotate(14 296 178)"><rect x="282" y="158" width="11" height="40" rx="5.5"/><rect x="299" y="158" width="11" height="40" rx="5.5"/></g><g transform="rotate(14 360 178)"><rect x="346" y="158" width="11" height="40" rx="5.5"/><rect x="363" y="158" width="11" height="40" rx="5.5"/></g></g>
<circle cx="282" cy="228" r="12" fill="#ff8a5c" opacity="0.55"/><circle cx="370" cy="228" r="12" fill="#ff8a5c" opacity="0.55"/>
<path d="M298 224 Q326 250 354 224" fill="none" stroke="#17303a" stroke-width="6" stroke-linecap="round"/>
<rect x="262" y="312" width="46" height="24" rx="12" fill="#0f9488" stroke="#17303a" stroke-width="6"/><rect x="344" y="312" width="46" height="24" rx="12" fill="#0f9488" stroke="#17303a" stroke-width="6"/>
</svg>`;

const ACCOUNT_STYLES = `:root {
  color-scheme: light;
  --ink: #17303a;
  --ink-muted: #52656c;
  --paper: #f6f4ec;
  --paper-deep: #ebe7dc;
  --white: #fffefa;
  --teal: #0f9488;
  --teal-dark: #0f766e;
  --coral: #ff8a5c;
  --line: rgba(23, 48, 58, 0.16);
  --shadow: 0 28px 70px rgba(23, 48, 58, 0.14);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* { box-sizing: border-box; }

html { min-width: 320px; background: var(--paper); }

body {
  margin: 0;
  min-height: 100vh;
  color: var(--ink);
  background:
    linear-gradient(90deg, rgba(23, 48, 58, 0.035) 1px, transparent 1px) 0 0 / 48px 48px,
    var(--paper);
}

a { color: inherit; }

button, a { -webkit-tap-highlight-color: transparent; }

button { font: inherit; }

.site-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(420px, .95fr);
}

.identity-panel {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 100vh;
  padding: clamp(28px, 5vw, 72px);
  background: var(--ink);
  color: var(--paper);
}

.identity-panel::after {
  content: "";
  position: absolute;
  right: -18%;
  bottom: -20%;
  width: min(50vw, 680px);
  aspect-ratio: 1;
  border: 1px solid rgba(246, 244, 236, .13);
  border-radius: 50%;
  box-shadow: 0 0 0 44px rgba(246, 244, 236, .025), 0 0 0 88px rgba(246, 244, 236, .018);
  pointer-events: none;
}

.brand-lockup {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 14px;
  width: fit-content;
  text-decoration: none;
}

.brand-mark {
  width: 54px;
  height: 54px;
  object-fit: contain;
  border-radius: 18px;
  background: var(--paper);
}

.wordmark {
  font-size: 1.08rem;
  font-weight: 800;
  letter-spacing: .16em;
  text-transform: uppercase;
}

.identity-copy {
  position: relative;
  z-index: 1;
  max-width: 760px;
  padding: clamp(56px, 11vh, 140px) 0;
}

.eyebrow {
  margin: 0 0 20px;
  color: #67d7ca;
  font-size: .76rem;
  font-weight: 800;
  letter-spacing: .18em;
  text-transform: uppercase;
}

.identity-copy h1 {
  max-width: 12ch;
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(3rem, 7.2vw, 7.5rem);
  font-weight: 500;
  letter-spacing: -.065em;
  line-height: .89;
}

.identity-copy > p:last-child {
  max-width: 52ch;
  margin: 30px 0 0;
  color: rgba(246, 244, 236, .72);
  font-size: clamp(1rem, 1.45vw, 1.2rem);
  line-height: 1.65;
}

.identity-foot {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  color: rgba(246, 244, 236, .62);
  font-size: .84rem;
}

.environment-badge,
.state-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 6px 11px;
  border: 1px solid currentColor;
  border-radius: 999px;
  font-size: .72rem;
  font-weight: 850;
  letter-spacing: .1em;
  text-transform: uppercase;
}

.environment-badge::before,
.state-badge::before {
  content: "";
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.account-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(26px, 5vw, 72px);
}

.account-surface {
  width: min(100%, 570px);
  padding: clamp(30px, 5vw, 58px);
  border: 1px solid var(--line);
  border-top: 5px solid var(--teal);
  background: rgba(255, 254, 250, .92);
  box-shadow: var(--shadow);
}

.surface-kicker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 38px;
}

.surface-kicker > span:first-child {
  color: var(--ink-muted);
  font-size: .76rem;
  font-weight: 800;
  letter-spacing: .12em;
  text-transform: uppercase;
}

.state-badge { color: var(--teal-dark); }
.state-badge[data-tone="attention"] { color: #a04c26; }
.state-badge[data-tone="ended"] { color: var(--ink-muted); }

.account-surface h2 {
  max-width: 13ch;
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(2.25rem, 5vw, 4.3rem);
  font-weight: 500;
  letter-spacing: -.05em;
  line-height: .98;
}

.lede {
  margin: 24px 0 0;
  color: var(--ink-muted);
  font-size: 1.02rem;
  line-height: 1.65;
}

.plan-facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 34px 0 0;
  border-block: 1px solid var(--line);
}

.plan-fact { padding: 18px 0; }
.plan-fact + .plan-fact { padding-left: 22px; border-left: 1px solid var(--line); }
.plan-fact dt { color: var(--ink-muted); font-size: .72rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }
.plan-fact dd { margin: 7px 0 0; font-weight: 760; }

.action-stack { display: grid; gap: 12px; margin-top: 34px; }

.primary-action,
.secondary-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 52px;
  padding: 13px 20px;
  border: 1px solid var(--ink);
  border-radius: 0;
  cursor: pointer;
  font-weight: 820;
  text-decoration: none;
  transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease;
}

.primary-action { background: var(--ink); color: var(--paper); box-shadow: 6px 6px 0 var(--coral); }
.secondary-action { background: transparent; color: var(--ink); }
.primary-action:hover, .secondary-action:hover { transform: translate(-2px, -2px); }
.primary-action:focus-visible, .secondary-action:focus-visible { outline: 3px solid var(--coral); outline-offset: 4px; }
.primary-action:disabled, .secondary-action:disabled { cursor: wait; opacity: .62; transform: none; }

.plan-choice {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 14px;
  min-height: 74px;
  padding: 14px 16px;
  border: 1px solid var(--line);
}

.plan-choice strong, .plan-choice span { display: block; }
.plan-choice span { margin-top: 3px; color: var(--ink-muted); font-size: .84rem; }
.plan-choice button { min-width: 104px; }

.fine-print,
.action-status {
  color: var(--ink-muted);
  font-size: .82rem;
  line-height: 1.55;
}

.action-status { min-height: 1.4em; margin: 16px 0 0; }

.proof-line {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid var(--line);
  color: var(--ink-muted);
  font-size: .82rem;
  line-height: 1.55;
}

.proof-line::before { content: "✓"; color: var(--teal-dark); font-weight: 900; }

@media (max-width: 900px) {
  .site-shell { grid-template-columns: 1fr; }
  .identity-panel { min-height: auto; padding: 26px; }
  .identity-copy { padding: 64px 0 74px; }
  .identity-copy h1 { max-width: 10ch; font-size: clamp(3.4rem, 14vw, 6rem); }
  .identity-foot { align-items: flex-end; }
  .account-panel { padding: 28px 18px 54px; }
  .account-surface { margin-top: -1px; }
}

@media (max-width: 520px) {
  .identity-copy { padding: 54px 0 58px; }
  .identity-foot { display: grid; }
  .account-surface { padding: 28px 22px 32px; }
  .surface-kicker { align-items: flex-start; flex-direction: column; margin-bottom: 28px; }
  .plan-facts { grid-template-columns: 1fr; }
  .plan-fact + .plan-fact { padding-left: 0; border-top: 1px solid var(--line); border-left: 0; }
  .plan-choice { grid-template-columns: 1fr; }
  .plan-choice button { width: 100%; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; }
}`;

const ACCOUNT_SCRIPT = `const MAX_STATUS_ATTEMPTS = 12;
const STATUS_DELAY_MS = 1500;

function safePolarUrl(value) {
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value);
    const polarHost = url.hostname === "polar.sh" || url.hostname.endsWith(".polar.sh");
    return url.protocol === "https:" && polarHost ? url.toString() : null;
  } catch {
    return null;
  }
}

async function hostedAction(responsePromise) {
  const response = await responsePromise;
  const payload = await response.json();
  const url = response.ok ? safePolarUrl(payload.url) : null;
  if (url === null) throw new Error("hosted action unavailable");
  window.location.assign(url);
}

for (const form of document.querySelectorAll("[data-checkout-form]")) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button[data-plan]");
    const status = document.querySelector("#account-action-status");
    const plan = button?.dataset.plan;
    if (!(button instanceof HTMLButtonElement) || !(status instanceof HTMLElement) || (plan !== "monthly" && plan !== "yearly")) return;
    button.disabled = true;
    status.textContent = "Creating secure Polar checkout...";
    try {
      await hostedAction(fetch("/v1/billing/checkout", {
        method: "POST",
        credentials: "same-origin",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ plan }),
      }));
    } catch {
      status.textContent = "Checkout is unavailable. Please retry.";
      button.disabled = false;
    }
  });
}

for (const form of document.querySelectorAll("[data-portal-form]")) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button");
    const status = document.querySelector("#account-action-status");
    if (!(button instanceof HTMLButtonElement) || !(status instanceof HTMLElement)) return;
    button.disabled = true;
    status.textContent = "Opening your secure Polar portal...";
    try {
      await hostedAction(fetch("/v1/billing/portal", {
        method: "POST",
        credentials: "same-origin",
      }));
    } catch {
      status.textContent = "The billing portal is unavailable. Please retry.";
      button.disabled = false;
    }
  });
}

function updatePaymentSurface(root, state) {
  const title = root.querySelector("[data-status-title]");
  const copy = root.querySelector("[data-status-copy]");
  const badge = root.querySelector("[data-status-badge]");
  const action = root.querySelector("[data-status-action]");
  if (!(title instanceof HTMLElement) || !(copy instanceof HTMLElement) || !(badge instanceof HTMLElement) || !(action instanceof HTMLAnchorElement)) return false;

  root.dataset.paymentState = state;
  action.href = "/account";
  action.textContent = "Open Emulo account";
  if (state === "active" || state === "trialing") {
    badge.textContent = "Active";
    badge.dataset.tone = "";
    title.textContent = "Emulo Pro activated";
    copy.textContent = "Polar's signed confirmation is applied. Your Emulo Pro access is now active.";
    return true;
  }
  if (state === "past_due" || state === "grace") {
    badge.textContent = "Attention";
    badge.dataset.tone = "attention";
    title.textContent = "Billing needs attention";
    copy.textContent = "Polar confirmed a billing issue. Open your account to manage it; local Emulo stays yours.";
    return true;
  }
  if (state === "ended" || state === "refunded") {
    badge.textContent = "Paused";
    badge.dataset.tone = "ended";
    title.textContent = "Cloud continuity is paused";
    copy.textContent = "Polar no longer reports active access. Your local profiles and workflows remain yours.";
    return true;
  }
  return false;
}

function wait(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function pollPaymentStatus() {
  const root = document.querySelector('[data-payment-state="verifying"][data-authenticated="true"]');
  if (!(root instanceof HTMLElement)) return;
  for (let attempt = 0; attempt < MAX_STATUS_ATTEMPTS; attempt += 1) {
    try {
      const response = await fetch("/v1/account/status", {
        method: "GET",
        credentials: "same-origin",
        headers: { accept: "application/json" },
      });
      if (response.status === 401) {
        const title = root.querySelector("[data-status-title]");
        const copy = root.querySelector("[data-status-copy]");
        const badge = root.querySelector("[data-status-badge]");
        const action = root.querySelector("[data-status-action]");
        if (title instanceof HTMLElement) title.textContent = "Sign in to verify access";
        if (copy instanceof HTMLElement) copy.textContent = "Reconnect the account used at checkout, then Emulo can read the verified status.";
        if (badge instanceof HTMLElement) badge.textContent = "Reconnect";
        if (action instanceof HTMLAnchorElement) {
          action.href = "/v1/auth/github/start";
          action.textContent = "Continue with GitHub";
        }
        return;
      }
      if (response.ok) {
        const payload = await response.json();
        const state = payload?.entitlement?.state;
        if (typeof state === "string" && updatePaymentSurface(root, state)) return;
      }
    } catch {
      // Keep the truthful pending state and retry within the bounded window.
    }
    if (attempt + 1 < MAX_STATUS_ATTEMPTS) await wait(STATUS_DELAY_MS);
  }
  const title = root.querySelector("[data-status-title]");
  const copy = root.querySelector("[data-status-copy]");
  const badge = root.querySelector("[data-status-badge]");
  if (title instanceof HTMLElement) title.textContent = "Confirmation is still pending";
  if (copy instanceof HTMLElement) copy.textContent = "No active entitlement is visible yet. Your account page will show access as soon as a verified Polar confirmation arrives.";
  if (badge instanceof HTMLElement) badge.textContent = "Pending";
}

void pollPaymentStatus();`;

function htmlDocument(
  title: string,
  environment: "sandbox" | "production",
  surface: string,
): Response {
  const environmentLabel = environment === "sandbox" ? "Polar Sandbox" : "Production";
  return new Response(
    `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${title}</title>
  <meta name="description" content="Emulo carries your way of working across AI agents.">
  <link rel="icon" href="/emulo.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/account.css">
</head>
<body>
  <main class="site-shell">
    <section class="identity-panel" aria-labelledby="emulo-promise">
      <a class="brand-lockup" href="/account" aria-label="Emulo account home">
        <img class="brand-mark" src="/emulo.svg" alt="">
        <span class="wordmark">Emulo</span>
      </a>
      <div class="identity-copy">
        <p class="eyebrow">Personal operating alignment</p>
        <h1 id="emulo-promise">Your way of working, carried forward.</h1>
        <p>Emulo learns from completed sessions and keeps your agents aligned without uploading raw session logs.</p>
      </div>
      <footer class="identity-foot">
        <span>Open source stays capable. Autopilot adds continuity.</span>
        <span class="environment-badge">${environmentLabel}</span>
      </footer>
    </section>
    <section class="account-panel">${surface}</section>
  </main>
  <script src="/account.js" defer></script>
</body>
</html>`,
    { status: 200, headers: DOCUMENT_HEADERS },
  );
}

function productLabel(entitlement: EntitlementSummary): string {
  if (entitlement.productCode === "founding-yearly") return "Annual";
  if (entitlement.productCode === "founding-monthly") return "Monthly";
  return "Not started";
}

function activeSurface(entitlement: EntitlementSummary): string {
  return `<article class="account-surface" data-account-state="${entitlement.state}">
    <div class="surface-kicker"><span>Emulo account</span><span class="state-badge">Active</span></div>
    <h2>Emulo Pro is active</h2>
    <p class="lede">Your verified Polar subscription is connected. Autopilot controls remain in the local Emulo control center.</p>
    <dl class="plan-facts"><div class="plan-fact"><dt>Plan</dt><dd>${productLabel(entitlement)}</dd></div><div class="plan-fact"><dt>Access</dt><dd>Cloud continuity</dd></div></dl>
    <div class="action-stack"><form data-portal-form><button class="primary-action" type="submit">Manage subscription</button></form><a class="secondary-action" href="/account">Refresh account</a></div>
    <p id="account-action-status" class="action-status" aria-live="polite"></p>
    <p class="proof-line">This state comes from a verified Polar confirmation, not the checkout redirect.</p>
  </article>`;
}

function attentionSurface(entitlement: EntitlementSummary): string {
  return `<article class="account-surface" data-account-state="${entitlement.state}">
    <div class="surface-kicker"><span>Emulo account</span><span class="state-badge" data-tone="attention">Attention</span></div>
    <h2>Billing needs attention</h2>
    <p class="lede">Open Polar to resolve the subscription. Cloud continuity may enter a grace period, but local Emulo stays yours.</p>
    <dl class="plan-facts"><div class="plan-fact"><dt>Plan</dt><dd>${productLabel(entitlement)}</dd></div><div class="plan-fact"><dt>Local engine</dt><dd>Still available</dd></div></dl>
    <div class="action-stack"><form data-portal-form><button class="primary-action" type="submit">Open billing portal</button></form><a class="secondary-action" href="/account">Refresh account</a></div>
    <p id="account-action-status" class="action-status" aria-live="polite"></p>
  </article>`;
}

function endedSurface(entitlement: EntitlementSummary): string {
  return `<article class="account-surface" data-account-state="${entitlement.state}">
    <div class="surface-kicker"><span>Emulo account</span><span class="state-badge" data-tone="ended">Paused</span></div>
    <h2>Cloud continuity is paused</h2>
    <p class="lede">New cloud writes have stopped. Your local profiles and workflows remain yours, including local history and rollback.</p>
    <dl class="plan-facts"><div class="plan-fact"><dt>Previous plan</dt><dd>${productLabel(entitlement)}</dd></div><div class="plan-fact"><dt>Open source</dt><dd>Unaffected</dd></div></dl>
    <div class="action-stack"><form data-portal-form><button class="primary-action" type="submit">Review subscription</button></form><a class="secondary-action" href="/account">Refresh account</a></div>
    <p id="account-action-status" class="action-status" aria-live="polite"></p>
  </article>`;
}

function noneSurface(checkoutEnabled: boolean): string {
  const actions = checkoutEnabled
    ? `<div class="action-stack">
        <form class="plan-choice" data-checkout-form><div><strong>Annual founding plan</strong><span>$79/year · founding price</span></div><button class="primary-action" type="submit" data-plan="yearly">Choose annual</button></form>
        <form class="plan-choice" data-checkout-form><div><strong>Monthly founding plan</strong><span>$9/month · cancel in Polar</span></div><button class="secondary-action" type="submit" data-plan="monthly">Choose monthly</button></form>
      </div>`
    : `<div class="action-stack"><a class="primary-action" href="https://github.com/ohad6/emulo">Use Emulo open source</a></div>
       <p class="fine-print">Checkout is safely closed while the founding beta is prepared for production.</p>`;
  return `<article class="account-surface" data-account-state="none">
    <div class="surface-kicker"><span>Founding beta</span><span class="state-badge" data-tone="ended">Private</span></div>
    <h2>${checkoutEnabled ? "Choose your founding plan" : "Founding access is currently private"}</h2>
    <p class="lede">The open-source engine remains free and local. Autopilot will add managed continuity across agents and devices.</p>
    ${actions}
    <p id="account-action-status" class="action-status" aria-live="polite"></p>
    <p class="proof-line">Raw session logs stay local. Access activates only after a verified Polar confirmation.</p>
  </article>`;
}

export function renderAccountPage(status: AccountStatus): Response {
  if (!status.authenticated) {
    return htmlDocument(
      "Emulo account",
      status.environment,
      `<article class="account-surface" data-account-state="signed-out">
        <div class="surface-kicker"><span>Private account</span><span class="state-badge" data-tone="ended">Signed out</span></div>
        <h2>Connect your Emulo account</h2>
        <p class="lede">GitHub verifies your identity. Emulo requests no repository or email scope and never stores the temporary GitHub token.</p>
        <div class="action-stack"><a class="primary-action" href="/v1/auth/github/start">Continue with GitHub</a><a class="secondary-action" href="https://github.com/ohad6/emulo">View open source</a></div>
        <p class="proof-line">Your account session is stored as an opaque, hashed browser session.</p>
      </article>`,
    );
  }

  const entitlement = status.entitlement;
  if (entitlement.state === "active" || entitlement.state === "trialing") {
    return htmlDocument("Emulo account", status.environment, activeSurface(entitlement));
  }
  if (entitlement.state === "past_due" || entitlement.state === "grace") {
    return htmlDocument("Emulo account", status.environment, attentionSurface(entitlement));
  }
  if (entitlement.state === "ended" || entitlement.state === "refunded") {
    return htmlDocument("Emulo account", status.environment, endedSurface(entitlement));
  }
  return htmlDocument("Emulo account", status.environment, noneSurface(status.checkoutEnabled));
}

function paymentSurface(status: AccountStatus): string {
  if (!status.authenticated) {
    return `<article class="account-surface" data-payment-state="verifying" data-authenticated="false" aria-live="polite">
      <div class="surface-kicker"><span>Payment verification</span><span class="state-badge" data-tone="attention">Reconnect</span></div>
      <h2 data-status-title>Sign in to verify access</h2>
      <p class="lede" data-status-copy>Emulo enables cloud access only after a verified Polar confirmation. Reconnect the account used at checkout to read that status.</p>
      <div class="action-stack"><a class="primary-action" href="/v1/auth/github/start">Continue with GitHub</a><a class="secondary-action" href="/account">Return to account</a></div>
    </article>`;
  }
  if (status.entitlement.state === "active" || status.entitlement.state === "trialing") {
    return `<article class="account-surface" data-payment-state="active" data-authenticated="true" aria-live="polite">
      <div class="surface-kicker"><span>Payment verification</span><span class="state-badge" data-status-badge>Active</span></div>
      <h2 data-status-title>Emulo Pro activated</h2>
      <p class="lede" data-status-copy>Your verified Polar confirmation is applied. Emulo now recognizes the ${productLabel(status.entitlement).toLowerCase()} Emulo Pro plan.</p>
      <div class="action-stack"><a class="primary-action" data-status-action href="/account">Open Emulo account</a></div>
      <p class="proof-line">Access was confirmed from the signed webhook state stored by Emulo.</p>
    </article>`;
  }
  if (status.entitlement.state === "past_due" || status.entitlement.state === "grace") {
    return `<article class="account-surface" data-payment-state="${status.entitlement.state}" data-authenticated="true" aria-live="polite">
      <div class="surface-kicker"><span>Payment verification</span><span class="state-badge" data-tone="attention" data-status-badge>Attention</span></div>
      <h2 data-status-title>Billing needs attention</h2>
      <p class="lede" data-status-copy>Polar confirmed a billing issue. Open the account to manage it; local Emulo stays yours.</p>
      <div class="action-stack"><a class="primary-action" data-status-action href="/account">Open Emulo account</a></div>
    </article>`;
  }
  if (status.entitlement.state === "ended" || status.entitlement.state === "refunded") {
    return `<article class="account-surface" data-payment-state="${status.entitlement.state}" data-authenticated="true" aria-live="polite">
      <div class="surface-kicker"><span>Payment verification</span><span class="state-badge" data-tone="ended" data-status-badge>Paused</span></div>
      <h2 data-status-title>Cloud continuity is paused</h2>
      <p class="lede" data-status-copy>Polar no longer reports active access. Your local Emulo profiles and workflows remain yours.</p>
      <div class="action-stack"><a class="primary-action" data-status-action href="/account">Open Emulo account</a></div>
    </article>`;
  }
  return `<article class="account-surface" data-payment-state="verifying" data-authenticated="true" aria-live="polite">
    <div class="surface-kicker"><span>Payment verification</span><span class="state-badge" data-tone="attention" data-status-badge>Verifying</span></div>
    <h2 data-status-title>Waiting for Polar confirmation</h2>
    <p class="lede" data-status-copy>The payment page returned, but Emulo enables cloud access only after a verified Polar confirmation. This normally takes a few seconds.</p>
    <div class="action-stack"><a class="primary-action" data-status-action href="/account">Return to account</a></div>
    <p class="proof-line">The checkout redirect alone never grants access.</p>
  </article>`;
}

export function renderPaymentPage(status: AccountStatus): Response {
  return htmlDocument("Verify Emulo access", status.environment, paymentSurface(status));
}

export function unavailablePage(): Response {
  return htmlDocument(
    "Emulo account unavailable",
    "sandbox",
    `<article class="account-surface" data-account-state="unavailable">
      <div class="surface-kicker"><span>Emulo account</span><span class="state-badge" data-tone="attention">Unavailable</span></div>
      <h2>We could not load the account safely</h2>
      <p class="lede">No account or billing state was changed. Please retry in a moment.</p>
      <div class="action-stack"><a class="primary-action" href="/account">Retry account</a></div>
    </article>`,
  );
}

export function accountStyles(): Response {
  return new Response(ACCOUNT_STYLES, {
    status: 200,
    headers: {
      "cache-control": "public, max-age=300",
      "content-type": "text/css; charset=utf-8",
      "referrer-policy": "no-referrer",
      "x-content-type-options": "nosniff",
    },
  });
}

export function accountScript(): Response {
  return new Response(ACCOUNT_SCRIPT, {
    status: 200,
    headers: {
      "cache-control": "public, max-age=300",
      "content-type": "text/javascript; charset=utf-8",
      "referrer-policy": "no-referrer",
      "x-content-type-options": "nosniff",
    },
  });
}

export function emuloMark(): Response {
  return new Response(EMULO_MARK, {
    status: 200,
    headers: {
      "cache-control": "public, max-age=86400, immutable",
      "content-type": "image/svg+xml; charset=utf-8",
      "content-security-policy": "default-src 'none'; style-src 'none'; script-src 'none'",
      "x-content-type-options": "nosniff",
    },
  });
}
