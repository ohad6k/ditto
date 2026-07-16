import { cloudflareTest } from "@cloudflare/vitest-pool-workers";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    cloudflareTest({
      wrangler: { configPath: "./wrangler.jsonc" },
      miniflare: {
        bindings: {
          APP_ENV: "test",
          POLAR_MONTHLY_PRODUCT_ID: "prod_monthly_test",
          POLAR_YEARLY_PRODUCT_ID: "prod_yearly_test",
          POLAR_WEBHOOK_SECRET: "test-only-placeholder",
        },
      },
    }),
  ],
});
