import { describe, expect, it } from "vitest";
import {
  InMemoryWebStorage,
  OidcClient,
  WebStorageStateStore,
} from "oidc-client-ts";
import { fixtureConfig, OidcProviderFixture } from "./oidc-provider.js";

async function grant() {
  const provider = new OidcProviderFixture();
  const client = new OidcClient({
    authority: fixtureConfig.authority,
    client_id: fixtureConfig.clientId,
    scope: fixtureConfig.scope,
    redirect_uri: fixtureConfig.publicOrigin + "/auth/callback",
    response_type: "code",
    response_mode: "query",
    metadata: provider.metadata(),
    stateStore: new WebStorageStateStore({ store: new InMemoryWebStorage() }),
  });
  const request = await client.createSigninRequest({
    nonce: crypto.randomUUID(),
  });
  const callback = new URL(provider.authorize(request.url));
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: fixtureConfig.clientId,
    redirect_uri: fixtureConfig.publicOrigin + "/auth/callback",
    code: callback.searchParams.get("code")!,
    code_verifier: request.state.code_verifier!,
  });
  return { provider, body, request };
}
describe("C3 Node-only simulated authorization server", () => {
  it("P01/P04: independently verifies real PKCE and enforces one-use authorization code", async () => {
    const { provider, body } = await grant();
    expect(
      (
        await provider.fetch(fixtureConfig.authority + "/token", {
          method: "POST",
          body,
        })
      ).status,
    ).toBe(200);
    expect(provider.proof.verifier).toBe(true);
    expect(
      (
        await provider.fetch(fixtureConfig.authority + "/token", {
          method: "POST",
          body,
        })
      ).status,
    ).toBe(400);
  });
  it.each(["code_verifier", "client_id", "redirect_uri", "code", "grant_type"])(
    "P04: denies wrong %s",
    async (field) => {
      const { provider, body } = await grant();
      body.set(field, "wrong-value");
      expect(
        (
          await provider.fetch(fixtureConfig.authority + "/token", {
            method: "POST",
            body,
          })
        ).status,
      ).toBe(400);
      expect(provider.proof.verifier).toBe(false);
    },
  );
  it("P01/P14: does not accept credentials or emit private JWK components", async () => {
    const { provider, body } = await grant();
    body.set("client_secret", "non-live-canary");
    expect(
      (await provider.fetch(fixtureConfig.authority + "/token", { body }))
        .status,
    ).toBe(400);
    const jwks = await (
      await provider.fetch(fixtureConfig.authority + "/jwks")
    ).json();
    expect(jwks.keys[0]).not.toHaveProperty("d");
    expect(jwks.keys[0]).not.toHaveProperty("p");
    await expect(
      provider.fetch("https://login.microsoftonline.com/not-authorized"),
    ).rejects.toThrow("Fixture denied external network.");
  });
  it("P01 negative control: nonce omission cannot satisfy the actual protocol fixture", async () => {
    const { provider, request } = await grant();
    const url = new URL(request.url);
    url.searchParams.delete("nonce");
    expect(() => provider.authorize(url.href)).toThrow(
      "Fixture authorization denied.",
    );
  });
});
