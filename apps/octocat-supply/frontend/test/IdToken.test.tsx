import { afterEach, describe, expect, it } from "vitest";
import { attempt, closeSessions } from "./oidcHarness";
import type { ProviderOptions } from "../../test/fixtures/oidc-provider";

afterEach(closeSessions);
describe("C3 cryptographic ID-token gate", () => {
  it.each([
    ["signature", { badSignature: true }],
    ["algorithm", { idHeader: { alg: "none" } }],
    ["key", { idHeader: { kid: "unknown" } }],
    ["issuer", { idClaims: { iss: "https://foreign.example.test" } }],
    ["absent issuer", { idClaims: { iss: undefined } }],
    ["audience", { idClaims: { aud: "wrong" } }],
    ["absent audience", { idClaims: { aud: undefined } }],
    ["subject", { idClaims: { sub: "" } }],
    ["absent subject", { idClaims: { sub: undefined } }],
    ["nonce", { idClaims: { nonce: "wrong" } }],
    ["absent nonce", { idClaims: { nonce: undefined } }],
    ["expiry", { idClaims: { exp: 1 } }],
    ["absent expiry", { idClaims: { exp: undefined } }],
    ["future issued time", { idClaims: { iat: 9999999999 } }],
    ["absent issued time", { idClaims: { iat: undefined } }],
    ["not before", { idClaims: { nbf: 9999999999 } }],
    ["authorized party", { idClaims: { azp: "wrong" } }],
    [
      "extra audience",
      { idClaims: { aud: ["morrow-spa", "other"], azp: "morrow-spa" } },
    ],
  ] satisfies [string, ProviderOptions][])(
    "P06: rejects invalid %s without publishing or calling the API",
    async (_label, options) => {
      const a = await attempt(options);
      const phases: string[] = [];
      a.incoming.subscribe(() => phases.push(a.incoming.getSnapshot().phase));
      await a.incoming.complete(a.callback);
      expect(phases.includes("signedIn")).toBe(false);
      expect(a.incoming.getSnapshot().phase).toBe("signedOut");
      expect(() => a.incoming.request()).toThrow();
      expect(sessionStorage.length).toBe(0);
    },
  );
  it("P06: ignores token-controlled key URLs and consults only the trusted JWKS", async () => {
    const a = await attempt({
      idHeader: {
        jku: "https://foreign.example.test/jwks",
        x5u: "https://foreign.example.test/key",
      },
    });
    await a.incoming.complete(a.callback);
    expect(a.incoming.getSnapshot().phase).toBe("signedIn");
    expect(a.provider.counts.jwks).toBe(1);
    expect(
      a.transport.mock.calls.every(
        ([input]) =>
          new URL(String(input)).origin === "https://issuer.example.test",
      ),
    ).toBe(true);
  });
});
