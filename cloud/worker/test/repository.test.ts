import { env } from "cloudflare:workers";
import { beforeEach, describe, expect, it } from "vitest";

import type { Env, NormalizedEntitlement } from "../src/contracts";
import { recordBillingEvent } from "../src/repository";

const ACCOUNT_ID = "acct_0123456789abcdef0123456789abcdef";
const testEnv = env as unknown as Env;

function entitlement(
  changes: Partial<NormalizedEntitlement> = {},
): NormalizedEntitlement {
  return {
    accountId: ACCOUNT_ID,
    state: "active",
    productCode: "founding-monthly",
    provider: "polar",
    providerSubscriptionId: "sub_123",
    providerCustomerId: "customer_123",
    providerProductId: "prod_monthly_test",
    effectiveAt: "2026-07-16T12:00:00.000Z",
    currentPeriodEnd: "2026-08-16T12:00:00.000Z",
    graceEndsAt: null,
    recoveryEndsAt: null,
    ...changes,
  };
}

function metadata(
  eventId: string,
  effectiveAt = "2026-07-16T12:00:00.000Z",
) {
  return {
    provider: "polar" as const,
    eventId,
    eventType: "subscription.updated",
    payloadSha256: "a".repeat(64),
    effectiveAt,
    receivedAt: "2026-07-16T12:00:01.000Z",
  };
}

async function currentEntitlement() {
  return testEnv.DB.prepare(
    "SELECT state, provider_event_id, provider_effective_at FROM entitlements WHERE account_id = ?",
  )
    .bind(ACCOUNT_ID)
    .first<{
      state: string;
      provider_event_id: string;
      provider_effective_at: string;
    }>();
}

describe("recordBillingEvent", () => {
  beforeEach(async () => {
    await testEnv.DB.batch([
      testEnv.DB.prepare("DELETE FROM entitlements"),
      testEnv.DB.prepare("DELETE FROM billing_events"),
      testEnv.DB.prepare("DELETE FROM billing_customers"),
      testEnv.DB.prepare("DELETE FROM accounts"),
      testEnv.DB.prepare(
        "INSERT INTO accounts (account_id, created_at) VALUES (?, ?)",
      ).bind(ACCOUNT_ID, "2026-07-16T11:00:00.000Z"),
    ]);
  });

  it("applies a verified event and stores no payload body", async () => {
    const result = await recordBillingEvent(
      testEnv.DB,
      metadata("evt_001"),
      entitlement(),
    );
    expect(result.status).toBe("applied");
    expect(await currentEntitlement()).toMatchObject({
      state: "active",
      provider_event_id: "evt_001",
    });
    const columns = await testEnv.DB.prepare("PRAGMA table_info(billing_events)")
      .all<{ name: string }>();
    expect(columns.results.map((column) => column.name)).not.toContain("payload");
    const stored = await testEnv.DB.prepare(
      "SELECT payload_sha256 FROM billing_events WHERE event_id = ?",
    )
      .bind("evt_001")
      .first<{ payload_sha256: string }>();
    expect(stored?.payload_sha256).toBe("a".repeat(64));
  });

  it("treats a repeated event ID as idempotent", async () => {
    await recordBillingEvent(testEnv.DB, metadata("evt_001"), entitlement());
    const duplicate = await recordBillingEvent(
      testEnv.DB,
      metadata("evt_001"),
      entitlement({ state: "ended" }),
    );
    expect(duplicate.status).toBe("duplicate");
    expect((await currentEntitlement())?.state).toBe("active");
    const count = await testEnv.DB.prepare(
      "SELECT COUNT(*) AS count FROM billing_events",
    ).first<{ count: number }>();
    expect(count?.count).toBe(1);
  });

  it("keeps the newest effective event when an older event arrives later", async () => {
    await recordBillingEvent(
      testEnv.DB,
      metadata("evt_new", "2026-07-16T13:00:00.000Z"),
      entitlement({
        state: "ended",
        effectiveAt: "2026-07-16T13:00:00.000Z",
      }),
    );
    const stale = await recordBillingEvent(
      testEnv.DB,
      metadata("evt_old", "2026-07-16T12:00:00.000Z"),
      entitlement(),
    );
    expect(stale.status).toBe("stale");
    expect(await currentEntitlement()).toMatchObject({
      state: "ended",
      provider_event_id: "evt_new",
    });
  });

  it("uses event ID as a deterministic equal-time tie break", async () => {
    await recordBillingEvent(testEnv.DB, metadata("evt_100"), entitlement());
    await recordBillingEvent(
      testEnv.DB,
      metadata("evt_200"),
      entitlement({ state: "past_due" }),
    );
    const stale = await recordBillingEvent(
      testEnv.DB,
      metadata("evt_050"),
      entitlement({ state: "ended" }),
    );
    expect(stale.status).toBe("stale");
    expect(await currentEntitlement()).toMatchObject({
      state: "past_due",
      provider_event_id: "evt_200",
    });
  });

  it("records safe metadata but grants nothing for an unknown account", async () => {
    const unknown = entitlement({
      accountId: "acct_ffffffffffffffffffffffffffffffff",
    });
    const result = await recordBillingEvent(
      testEnv.DB,
      metadata("evt_unknown"),
      unknown,
    );
    expect(result.status).toBe("unknown-account");
    expect(await testEnv.DB.prepare("SELECT * FROM entitlements").first()).toBeNull();
    const stored = await testEnv.DB.prepare(
      "SELECT processing_result FROM billing_events WHERE event_id = ?",
    )
      .bind("evt_unknown")
      .first<{ processing_result: string }>();
    expect(stored?.processing_result).toBe("unknown-account");
  });
});
