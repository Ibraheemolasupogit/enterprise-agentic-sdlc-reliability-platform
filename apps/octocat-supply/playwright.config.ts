import { defineConfig } from "@playwright/test";

const external = process.env.E2E_BASE_URL;
export default defineConfig({
  testDir: "./e2e",
  testIgnore: "**/oidc/**",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: external ?? "http://127.0.0.1:4173",
    browserName: "chromium",
    trace: "retain-on-failure",
  },
  webServer: external
    ? undefined
    : {
        command: "node scripts/e2e-server.mjs",
        url: "http://127.0.0.1:4173/health/ready",
        timeout: 30000,
        reuseExistingServer: false,
      },
});
