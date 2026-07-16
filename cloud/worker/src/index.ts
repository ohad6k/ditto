import type { Env } from "./contracts";
import { beginGitHubOAuth, completeGitHubOAuth } from "./github-auth";
import { handlePolarWebhook } from "./polar";
import { handlePolarCheckout, handlePolarPortal } from "./polar-client";

function json(status: number, body: Record<string, string>): Response {
  return Response.json(body, {
    status,
    headers: {
      "cache-control": "no-store",
    },
  });
}

function page(title: string, message: string): Response {
  return new Response(
    `<!doctype html><meta charset="utf-8"><title>${title}</title><main><h1>${title}</h1><p>${message}</p></main>`,
    {
      status: 200,
      headers: {
        "cache-control": "no-store",
        "content-security-policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        "content-type": "text/html; charset=utf-8",
        "referrer-policy": "no-referrer",
        "x-content-type-options": "nosniff",
      },
    },
  );
}

export default {
  async fetch(request, env, _context?): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/healthz") {
      if (request.method !== "GET") {
        return json(405, { status: "method-not-allowed" });
      }
      return json(200, {
        service: "emulo-autopilot-api",
        status: "ok",
      });
    }
    if (url.pathname === "/account") {
      if (request.method !== "GET") {
        return json(405, { status: "method-not-allowed" });
      }
      return page(
        "Emulo account",
        "Your browser account is connected. Billing and Autopilot controls remain in the local Emulo control center.",
      );
    }
    if (url.pathname === "/v1/billing/complete") {
      if (request.method !== "GET") {
        return json(405, { status: "method-not-allowed" });
      }
      return page(
        "Payment submitted",
        "Emulo enables cloud access only after a verified Polar confirmation. You can return to the local control center.",
      );
    }
    if (url.pathname === "/v1/billing/webhooks/polar") {
      if (request.method !== "POST") {
        return json(405, { status: "method-not-allowed" });
      }
      return handlePolarWebhook(request, env);
    }
    if (url.pathname === "/v1/auth/github/start") {
      if (request.method !== "GET") {
        return json(405, { status: "method-not-allowed" });
      }
      return beginGitHubOAuth(env);
    }
    if (url.pathname === "/v1/auth/github/callback") {
      if (request.method !== "GET") {
        return json(405, { status: "method-not-allowed" });
      }
      return completeGitHubOAuth(request, env);
    }
    if (url.pathname === "/v1/billing/checkout") {
      if (request.method !== "POST") {
        return json(405, { status: "method-not-allowed" });
      }
      return handlePolarCheckout(request, env);
    }
    if (url.pathname === "/v1/billing/portal") {
      if (request.method !== "POST") {
        return json(405, { status: "method-not-allowed" });
      }
      return handlePolarPortal(request, env);
    }
    return json(404, { status: "not-found" });
  },
} satisfies ExportedHandler<Env>;
