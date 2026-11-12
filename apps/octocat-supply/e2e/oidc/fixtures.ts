import { test as base, expect, type BrowserContext } from "@playwright/test";
import type { ProviderOptions } from "../../test/fixtures/oidc-provider";
import { assertCaptureOff } from "../../scripts/verify-auth-capture.mjs";

const bridge = "http://127.0.0.1:4175";
export const appOrigin = "https://shop.example.test";
export const test = base.extend<{
  simulated: {
    reset(options?: ProviderOptions): Promise<void>;
    options(options: ProviderOptions): Promise<void>;
    stats(): Promise<{
      counts: { token: number };
      proof: Record<string, boolean>;
      statuses: { status: number; cookie: boolean }[];
    }>;
    route(context: BrowserContext): Promise<void>;
    ownership(cart: string, actor?: "alice" | "bob"): Promise<number[]>;
  };
}>({
  simulated: [
    async ({ request, context }, use, testInfo) => {
      assertCaptureOff({
        use: testInfo.project.use,
        preserveOutput: testInfo.config.preserveOutput,
        reporter: testInfo.config.reporter,
      });
      let blocked = 0;
      async function route(target: BrowserContext) {
        await target.route("**/*", async (route) => {
          const req = route.request(),
            url = new URL(req.url());
          const issuer = url.origin === "https://issuer.example.test";
          if (url.origin !== appOrigin && !issuer) {
            blocked++;
            await route.abort("blockedbyclient");
            return;
          }
          try {
            const response = await route.fetch({
              url:
                bridge +
                (issuer ? "/__issuer" : "") +
                url.pathname +
                url.search,
              maxRedirects: 0,
            });
            await route.fulfill({ response });
          } catch {
            await route.abort("failed");
          }
        });
      }
      await route(context);
      const control = async (path: string, options: object) => {
        const r = await request.post(bridge + path, { data: options });
        expect(r.ok()).toBe(true);
      };
      await control("/__fixture/reset", {});
      await use({
        reset: async (options = {}) => control("/__fixture/reset", options),
        options: async (options) => control("/__fixture/options", options),
        stats: async () =>
          (await request.get(bridge + "/__fixture/stats")).json(),
        route,
        ownership: async (cart, actor) => {
          const r = await request.post(bridge + "/__fixture/ownership", {
            data: { cart, actor },
          });
          return (await r.json()).statuses;
        },
      });
      const diagnostics = await (
        await request.get(bridge + "/__fixture/stats")
      ).json();
      testInfo.annotations.push({
        type: "oidc-counts",
        description: [
          diagnostics.counts.metadata,
          diagnostics.counts.authorize,
          diagnostics.counts.token,
          diagnostics.counts.jwks,
          Number(diagnostics.proof.s256),
          Number(diagnostics.proof.nonce),
        ].join(","),
      });
      expect(blocked).toBe(0);
      expect(testInfo.attachments).toHaveLength(0);
    },
    { auto: true },
  ],
});
export { expect };
