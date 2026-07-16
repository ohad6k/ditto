# Emulo Autopilot Worker

This directory contains the locally verified billing-integrity core for the
optional Emulo Autopilot cloud service. It does not deploy anything, create a
Polar checkout, or change access to the open-source local product.

Implemented and verified locally:

- `GET /healthz`
- `POST /v1/billing/webhooks/polar`
- official Polar Standard Webhooks signature and schema verification
- bounded request bodies and payload-free event metadata
- idempotent, newer-wins D1 entitlement convergence
- fail-closed handling for unknown products, accounts, customers, and states
- GitHub OAuth with single-use state, S256 PKCE, browser binding, and hashed
  browser sessions
- authenticated Polar sandbox checkout for the configured monthly/yearly plans
- authenticated customer-portal sessions tied to the Emulo account ID

`PAID_CHECKOUT_ENABLED` remains `false`. No Cloudflare Worker, GitHub OAuth App,
Polar product, token, webhook, or public checkout has been configured by these
repository changes.

## Local verification

Requires Node.js 24 or newer.

```powershell
npm ci
npm run db:migrate:local
npm run typecheck
npm test
```

Copy `.dev.vars.example` to `.dev.vars` only for local testing. Put real secret
values directly into that ignored file or enter them interactively with
`wrangler secret put`; never paste them into chat, source files, shell history,
screenshots, or issue text.

`wrangler.jsonc` contains deliberately unusable product placeholders. The
monthly and yearly product IDs must be replaced only after the Polar sandbox
products exist.

## Provider actions intentionally deferred

No provider action is complete merely because this code exists. The remaining
operator actions are:

1. In Cloudflare, create or bind the free-tier Worker and D1 database, apply all
   migrations, and keep `PAID_CHECKOUT_ENABLED=false`. Record the Worker URL,
   deployment ID, and D1 database ID as evidence; do not record a secret. Set
   the nonsecret `PUBLIC_BASE_URL` binding to the exact HTTPS Worker origin with
   a trailing slash.
2. In GitHub under Settings > Developer settings > OAuth Apps, create a dedicated
   Emulo sign-in app with the Worker origin as Homepage URL and the exact
   `/v1/auth/github/callback` Worker URL as Authorization callback URL. Set the
   nonsecret `GITHUB_CLIENT_ID` Worker binding to the app's client ID, then set
   the client secret interactively in Cloudflare; record only the client ID and
   a redacted settings screenshot.
3. In Polar Sandbox, create recurring products at $9/month and $79/year and place
   their nonsecret product IDs in the Worker configuration.
4. Create a least-privilege Polar Sandbox organization token for checkout and
   customer-session creation and set it interactively in Cloudflare. Never copy
   the value into chat or evidence.
5. In Polar Sandbox under Settings > Webhooks, add the deployed endpoint ending
   in `/v1/billing/webhooks/polar`, select Raw format, and subscribe only to
   `subscription.created`, `subscription.active`, `subscription.updated`,
   `subscription.canceled`, `subscription.uncanceled`,
   `subscription.past_due`, and `subscription.revoked`.
6. Set the webhook secret interactively in Cloudflare and retain only a redacted
   screenshot or successful `202` sandbox delivery as verification.

Do not configure a live webhook or public checkout until sandbox purchase,
cancellation, past-due, revocation, duplicate, and replay behavior pass end to
end. Polar retries failed deliveries, so the endpoint should be live and tested
before a webhook is enabled.
