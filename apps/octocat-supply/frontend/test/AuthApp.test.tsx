import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import AuthApp, { parseAuthConfig, userStorageKey } from "../src/AuthApp";
import { createClient } from "../src/api";
import type { User } from "oidc-client-ts";

afterEach(() => vi.unstubAllGlobals());
describe("browser identity boundaries", () => {
  it("never falls back to anonymous when runtime authentication config is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<AuthApp />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "shop is closed",
    );
    expect(
      screen.queryByRole("button", { name: "Add Demo Feeder" }),
    ).toBeNull();
  });
  it("rejects missing/insecure provider configuration and separates remembered carts by issuer/subject", () => {
    expect(() => parseAuthConfig({ mode: "oidc" })).toThrow();
    expect(() =>
      parseAuthConfig({
        mode: "oidc",
        authority: "http://issuer",
        publicOrigin: "https://shop.test",
        clientId: "public-client",
        scope: "openid cart",
      }),
    ).toThrow();
    const alice = {
      profile: { iss: "https://issuer.test", sub: "alice" },
    } as User;
    const bob = { profile: { iss: "https://issuer.test", sub: "bob" } } as User;
    expect(userStorageKey(alice)).not.toBe(userStorageKey(bob));
    expect(userStorageKey(alice)).not.toBe("morrow-demo-cart");
  });
  it("adds bearer tokens only through the configured client and never sends owner fields", async () => {
    const fetch = vi
      .fn()
      .mockImplementation(async () => new Response("{}", { status: 201 }));
    vi.stubGlobal("fetch", fetch);
    await createClient(async () => "non-live-test-token").createCart();
    expect(fetch).toHaveBeenCalledWith(
      "/api/carts",
      expect.objectContaining({
        body: "{}",
        headers: expect.objectContaining({
          Authorization: "Bearer non-live-test-token",
        }),
      }),
    );
    fetch.mockClear();
    await createClient().createCart();
    expect(fetch.mock.calls[0][1].headers).not.toHaveProperty("Authorization");
    const expired = createClient(async () => {
      throw new Error("expired");
    });
    fetch.mockClear();
    await expect(expired.createCart()).rejects.toThrow("expired");
    expect(fetch).not.toHaveBeenCalled();
  });
});
