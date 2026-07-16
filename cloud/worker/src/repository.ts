import type { NormalizedEntitlement } from "./contracts";

const ID_PATTERN = /^[A-Za-z0-9_-]{1,128}$/;
const HASH_PATTERN = /^[a-f0-9]{64}$/;
const UTC_PATTERN = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/;

export interface BillingEventMetadata {
  provider: "polar";
  eventId: string;
  eventType: string;
  payloadSha256: string;
  effectiveAt: string;
  receivedAt: string;
}

export type BillingWriteStatus =
  | "applied"
  | "duplicate"
  | "stale"
  | "unknown-account"
  | "customer-conflict";

export interface BillingWriteResult {
  status: BillingWriteStatus;
  eventId: string;
}

interface ExistingEntitlement {
  provider_effective_at: string;
  provider_event_id: string;
}

function validateMetadata(
  metadata: BillingEventMetadata,
  entitlement: NormalizedEntitlement,
): void {
  if (
    metadata.provider !== "polar" ||
    !ID_PATTERN.test(metadata.eventId) ||
    !/^[a-z][a-z0-9_.-]{0,127}$/.test(metadata.eventType) ||
    !HASH_PATTERN.test(metadata.payloadSha256) ||
    !UTC_PATTERN.test(metadata.effectiveAt) ||
    !UTC_PATTERN.test(metadata.receivedAt) ||
    metadata.effectiveAt !== entitlement.effectiveAt
  ) {
    throw new Error("billing event metadata is invalid");
  }
}

function isNewer(
  metadata: BillingEventMetadata,
  existing: ExistingEntitlement | null,
): boolean {
  if (existing === null) {
    return true;
  }
  return (
    metadata.effectiveAt > existing.provider_effective_at ||
    (metadata.effectiveAt === existing.provider_effective_at &&
      metadata.eventId > existing.provider_event_id)
  );
}

function eventInsert(
  db: D1Database,
  metadata: BillingEventMetadata,
  result: Exclude<BillingWriteStatus, "duplicate">,
): D1PreparedStatement {
  return db
    .prepare(
      `INSERT OR IGNORE INTO billing_events
       (provider, event_id, event_type, payload_sha256, effective_at, received_at, processing_result)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
    )
    .bind(
      metadata.provider,
      metadata.eventId,
      metadata.eventType,
      metadata.payloadSha256,
      metadata.effectiveAt,
      metadata.receivedAt,
      result,
    );
}

export async function recordBillingEvent(
  db: D1Database,
  metadata: BillingEventMetadata,
  entitlement: NormalizedEntitlement,
): Promise<BillingWriteResult> {
  validateMetadata(metadata, entitlement);
  const duplicate = await db
    .prepare(
      "SELECT event_id FROM billing_events WHERE provider = ? AND event_id = ?",
    )
    .bind(metadata.provider, metadata.eventId)
    .first<{ event_id: string }>();
  if (duplicate !== null) {
    return { status: "duplicate", eventId: metadata.eventId };
  }

  const account = await db
    .prepare("SELECT account_id FROM accounts WHERE account_id = ?")
    .bind(entitlement.accountId)
    .first<{ account_id: string }>();
  if (account === null) {
    await eventInsert(db, metadata, "unknown-account").run();
    return { status: "unknown-account", eventId: metadata.eventId };
  }

  const customer = await db
    .prepare(
      "SELECT account_id FROM billing_customers WHERE provider = ? AND provider_customer_id = ?",
    )
    .bind(entitlement.provider, entitlement.providerCustomerId)
    .first<{ account_id: string }>();
  if (customer !== null && customer.account_id !== entitlement.accountId) {
    await eventInsert(db, metadata, "customer-conflict").run();
    return { status: "customer-conflict", eventId: metadata.eventId };
  }

  const current = await db
    .prepare(
      "SELECT provider_effective_at, provider_event_id FROM entitlements WHERE account_id = ?",
    )
    .bind(entitlement.accountId)
    .first<ExistingEntitlement>();
  const status = isNewer(metadata, current) ? "applied" : "stale";

  await db.batch([
    eventInsert(db, metadata, status),
    db
      .prepare(
        `INSERT INTO billing_customers
         (provider, provider_customer_id, account_id, external_customer_id, updated_at)
         VALUES (?, ?, ?, ?, ?)
         ON CONFLICT(provider, provider_customer_id) DO UPDATE SET
           updated_at = excluded.updated_at
         WHERE billing_customers.account_id = excluded.account_id`,
      )
      .bind(
        entitlement.provider,
        entitlement.providerCustomerId,
        entitlement.accountId,
        entitlement.accountId,
        metadata.receivedAt,
      ),
    db
      .prepare(
        `INSERT INTO entitlements
         (account_id, state, product_code, provider, provider_subscription_id,
          provider_customer_id, provider_product_id, provider_effective_at,
          provider_event_id, current_period_end, grace_ends_at, recovery_ends_at,
          updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
         ON CONFLICT(account_id) DO UPDATE SET
           state = excluded.state,
           product_code = excluded.product_code,
           provider = excluded.provider,
           provider_subscription_id = excluded.provider_subscription_id,
           provider_customer_id = excluded.provider_customer_id,
           provider_product_id = excluded.provider_product_id,
           provider_effective_at = excluded.provider_effective_at,
           provider_event_id = excluded.provider_event_id,
           current_period_end = excluded.current_period_end,
           grace_ends_at = excluded.grace_ends_at,
           recovery_ends_at = excluded.recovery_ends_at,
           updated_at = excluded.updated_at
         WHERE excluded.provider_effective_at > entitlements.provider_effective_at
            OR (excluded.provider_effective_at = entitlements.provider_effective_at
                AND excluded.provider_event_id > entitlements.provider_event_id)`,
      )
      .bind(
        entitlement.accountId,
        entitlement.state,
        entitlement.productCode,
        entitlement.provider,
        entitlement.providerSubscriptionId,
        entitlement.providerCustomerId,
        entitlement.providerProductId,
        entitlement.effectiveAt,
        metadata.eventId,
        entitlement.currentPeriodEnd,
        entitlement.graceEndsAt,
        entitlement.recoveryEndsAt,
        metadata.receivedAt,
      ),
  ]);
  return { status, eventId: metadata.eventId };
}
