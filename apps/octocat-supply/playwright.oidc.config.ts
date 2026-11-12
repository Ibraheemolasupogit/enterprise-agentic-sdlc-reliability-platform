import { defineConfig } from "@playwright/test";
import { assertCaptureOff } from "./scripts/verify-auth-capture.mjs";

const config = defineConfig({
  testDir: "./e2e/oidc",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  outputDir: "./test-results/oidc",
  reporter: [["./scripts/oidc-reporter.mjs"]],
  preserveOutput: "never",
  use: {
    browserName: "chromium",
    trace: "off",
    screenshot: "off",
    video: "off",
    serviceWorkers: "block",
  },
  webServer: {
    command: "node --import tsx scripts/oidc-e2e-server.mjs",
    url: "http://127.0.0.1:4175/health/fixture",
    timeout: 30000,
    reuseExistingServer: false,
  },
});
assertCaptureOff(config);
export default config;
