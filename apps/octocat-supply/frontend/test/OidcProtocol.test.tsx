import { afterEach, describe, expect, it, vi } from "vitest";
import { InMemoryWebStorage, UserManager } from "oidc-client-ts";
import { captureCallback } from "../src/oidcSession";
import { parseAuthConfig, trustedMetadata } from "../src/idToken";
import {
  fixtureConfig,
  type ProviderOptions,
} from "../../test/fixtures/oidc-provider";
import { attempt, closeSessions, session } from "./oidcHarness";

afterEach(closeSessions);
describe("C3 actual client protocol", () => {
  it("P01/P04: uses real S256/state/nonce, consumes once and never persists tokens", async () => {
    const a = await attempt();
    expect(
      a.callback.startsWith(fixtureConfig.publicOrigin + "/auth/callback?"),
    ).toBe(true);
    const first = a.incoming.complete(a.callback);
    expect(a.incoming.complete(a.callback)).toBe(first);
    await first;
    expect(a.incoming.getSnapshot().phase).toBe("signedIn");
    expect(a.provider.proof).toEqual({
      s256: true,
      nonce: true,
      publicClient: true,
      verifier: true,
    });
    expect(a.provider.counts.token).toBe(1);
    expect(sessionStorage.length).toBe(0);
    expect(localStorage.length).toBe(0);
    const replay = session();
    await replay.complete(a.callback);
    expect(replay.getSnapshot().phase).toBe("signedOut");
    expect(a.provider.counts.token).toBe(1);
    const b = await attempt();
    const one = a.provider.lastAuthorization!.searchParams;
    const two = b.provider.lastAuthorization!.searchParams;
    expect(one.get("nonce") !== two.get("nonce")).toBe(true);
    expect(one.get("state") !== two.get("state")).toBe(true);
    expect(one.get("code_challenge") !== two.get("code_challenge")).toBe(true);
  });
  it.each([
    ["missing state", (u: URL) => u.searchParams.delete("state")],
    ["wrong state", (u: URL) => u.searchParams.set("state", "wrong")],
    ["duplicate state", (u: URL) => u.searchParams.append("state", "wrong")],
    ["duplicate code", (u: URL) => u.searchParams.append("code", "wrong")],
    [
      "duplicate error",
      (u: URL) => {
        u.searchParams.delete("code");
        u.searchParams.append("error", "denied");
        u.searchParams.append("error", "denied");
      },
    ],
    ["code plus error", (u: URL) => u.searchParams.set("error", "denied")],
    [
      "fragment",
      (u: URL) => {
        u.hash = "access_token=non-live-canary";
      },
    ],
    [
      "foreign origin",
      (u: URL) => {
        u.hostname = "foreign.example.test";
      },
    ],
    [
      "wrong path",
      (u: URL) => {
        u.pathname = "/other";
      },
    ],
    ["no code", (u: URL) => u.searchParams.delete("code")],
  ] as const)(
    "P03: closes and cleans %s callback before exchange",
    async (_label, mutate) => {
      const a = await attempt();
      const url = new URL(a.callback);
      mutate(url);
      await a.incoming.complete(url.href);
      expect(a.incoming.getSnapshot().phase).toBe("signedOut");
      expect(a.provider.counts.token).toBe(0);
      expect(sessionStorage.length).toBe(0);
      expect(location.href).toBe(fixtureConfig.publicOrigin + "/");
    },
  );
  it.each(["expired", "future", "corrupt", "missing"])(
    "P03: rejects %s transaction",
    async (kind) => {
      const a = await attempt();
      const key = Object.keys(sessionStorage).find((k) =>
        k.endsWith(":pending"),
      )!;
      const p = JSON.parse(sessionStorage.getItem(key)!);
      if (kind === "expired") p.created -= 300001;
      if (kind === "future") p.created += 10000;
      if (kind === "missing") sessionStorage.removeItem(key);
      else
        sessionStorage.setItem(
          key,
          kind === "corrupt" ? "broken" : JSON.stringify(p),
        );
      await a.incoming.complete(a.callback);
      expect(a.incoming.getSnapshot().phase).toBe("signedOut");
      expect(a.provider.counts.token).toBe(0);
      expect(sessionStorage.length).toBe(0);
    },
  );
  it("P03/P04: rejects unsolicited and another context's callback, preserving unrelated storage", async () => {
    const a = await attempt();
    const otherStorage = new InMemoryWebStorage();
    otherStorage.setItem("unrelated", "keep");
    const other = session(otherStorage);
    await other.complete(a.callback);
    expect(other.getSnapshot().phase).toBe("signedOut");
    expect(otherStorage.getItem("unrelated")).toBe("keep");
    expect(a.provider.counts.token).toBe(0);
    await a.incoming.complete(a.callback);
    expect(a.incoming.getSnapshot().phase).toBe("signedIn");
  });
  it("P03: unavailable redirect storage fails closed without a memory fallback", async () => {
    const storage = new InMemoryWebStorage();
    vi.spyOn(storage, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    const a = await attempt({}, storage);
    expect(a.outgoing.getSnapshot().phase).toBe("signedOut");
    expect(a.provider.counts.authorize).toBe(0);
  });
  it.each([
    ["consent denial", { denial: "access_denied" }],
    ["login required", { denial: "login_required" }],
    ["invalid grant", { invalidGrant: true }],
    ["malformed JSON", { malformedTokenResponse: true }],
    ["missing ID token", { tokenFields: { id_token: "" } }],
    ["missing access token", { tokenFields: { access_token: "" } }],
    ["wrong type", { tokenFields: { token_type: "MAC" } }],
    ["nonpositive lifetime", { tokenFields: { expires_in: 0 } }],
    ["invalid lifetime", { tokenFields: { expires_in: "invalid" } }],
    [
      "refresh token",
      { tokenFields: { refresh_token: "non-live-refresh-canary" } },
    ],
    ["token outage", { outage: "token" }],
  ] satisfies [string, ProviderOptions][])(
    "P05: safely rejects %s",
    async (_label, options) => {
      const a = await attempt(options);
      await a.incoming.complete(a.callback);
      expect(a.incoming.getSnapshot().phase).toBe("signedOut");
      expect(a.incoming.getSnapshot().error).toBe(
        "Sign-in could not be verified. Start a new sign-in.",
      );
      expect(sessionStorage.length).toBe(0);
      expect(a.provider.counts.token).toBeLessThanOrEqual(1);
    },
  );
  it("P06: userLoaded is not acceptance; rejects wrong issuer before any signed-in publication", async () => {
    const a = await attempt({
      idClaims: { iss: "https://foreign.example.test" },
    });
    const loaded = vi.spyOn(UserManager.prototype, "storeUser");
    const phases: string[] = [];
    a.incoming.subscribe(() => phases.push(a.incoming.getSnapshot().phase));
    await a.incoming.complete(a.callback);
    expect(loaded).toHaveBeenCalled();
    expect(phases.includes("signedIn")).toBe(false);
    expect(a.incoming.getSnapshot().phase).toBe("signedOut");
    expect(() => a.incoming.request()).toThrow();
  });
  it.each([
    ["issuer", { issuer: "https://foreign.example.test" }],
    ["missing token", { token_endpoint: undefined }],
    ["missing JWKS", { jwks_uri: undefined }],
    ["HTTP", { token_endpoint: "http://issuer.example.test/token" }],
    [
      "foreign endpoint",
      { token_endpoint: "https://foreign.example.test/token" },
    ],
    ["plain PKCE", { code_challenge_methods_supported: ["plain"] }],
    ["implicit", { response_types_supported: ["id_token token"] }],
    ["fragment mode", { response_modes_supported: ["fragment"] }],
  ])(
    "P02: rejects %s metadata before navigation or exchange",
    async (_label, metadata) => {
      const a = await attempt({ metadata });
      expect(a.outgoing.getSnapshot().phase).toBe("signedOut");
      expect(a.provider.counts.authorize).toBe(0);
      expect(a.provider.counts.token).toBe(0);
      expect(() =>
        trustedMetadata(a.provider.metadata(), fixtureConfig),
      ).toThrow();
    },
  );
  it.each([
    { publicOrigin: "https://foreign.example.test" },
    { authority: "http://issuer.example.test" },
    { scope: "openid offline_access cart" },
    { clientId: "x ".repeat(200) },
    { authority: "https://login.microsoftonline.com/common/v2.0" },
  ])("P02: rejects untrusted configuration", (change) => {
    expect(() => parseAuthConfig({ ...fixtureConfig, ...change })).toThrow();
  });
  it("P03: snapshots and scrubs callback before asynchronous bootstrap", () => {
    history.replaceState(
      {},
      "",
      "/auth/callback?code=non-live-code&state=non-live-state",
    );
    const captured = captureCallback();
    expect(captured?.includes("code=")).toBe(true);
    expect(location.href).toBe(fixtureConfig.publicOrigin + "/auth/callback");
  });
});
