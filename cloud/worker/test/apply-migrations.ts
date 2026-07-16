import { env } from "cloudflare:workers";
import { applyD1Migrations } from "cloudflare:test";

import type { Env } from "../src/contracts";

type TestMigrations = Parameters<typeof applyD1Migrations>[1];
const testEnv = env as unknown as Env & { TEST_MIGRATIONS: TestMigrations };
await applyD1Migrations(testEnv.DB, testEnv.TEST_MIGRATIONS);
