import {
  cloudflareTest,
  readD1Migrations,
} from "@cloudflare/vitest-pool-workers";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

process.env.POLAR_WEBHOOK_SECRET ??= "test-only-placeholder";

export default defineConfig({
  plugins: [
    cloudflareTest(async () => ({
      wrangler: { configPath: "./wrangler.jsonc" },
      miniflare: {
        bindings: {
          APP_ENV: "test",
          POLAR_MONTHLY_PRODUCT_ID: "prod_monthly_test",
          POLAR_YEARLY_PRODUCT_ID: "prod_yearly_test",
          POLAR_WEBHOOK_SECRET: "test-only-placeholder",
          TEST_MIGRATIONS: await readD1Migrations(
            fileURLToPath(new URL("./migrations", import.meta.url)),
          ),
        },
      },
    })),
  ],
  test: {
    setupFiles: ["./test/apply-migrations.ts"],
  },
});
