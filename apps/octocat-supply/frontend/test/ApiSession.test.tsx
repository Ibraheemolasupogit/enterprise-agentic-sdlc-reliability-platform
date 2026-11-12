import { afterEach, describe, expect, it } from "vitest";
import { protectedApiPath } from "../src/api";
import { attempt, closeSessions } from "./oidcHarness";

afterEach(closeSessions);
describe("C3 protected API sessions", () => {
  it.each([401, 403, 503])(
    "P08/P10: preserves distinct status %s without automatic retries",
    async (status) => {
      const a = await attempt();
      await a.incoming.complete(a.callback);
      a.transport.mockResolvedValue(
        new Response(JSON.stringify({ message: "non-live-upstream-canary" }), {
          status,
        }),
      );
      const before = a.transport.mock.calls.length;
      await expect(a.incoming.client.createCart()).rejects.toMatchObject({
        status,
      });
      expect(a.transport.mock.calls.length - before).toBe(1);
      expect(a.incoming.getSnapshot().phase).toBe(
        status === 401 ? "signedOut" : "signedIn",
      );
    },
  );
  it("P10: same-subject reauthentication uses a fresh token, with no replay of the rejected mutation", async () => {
    const a = await attempt();
    await a.incoming.complete(a.callback);
    const old = a.incoming.request().token;
    a.transport.mockResolvedValue(new Response("{}", { status: 401 }));
    await expect(a.incoming.client.createCart()).rejects.toMatchObject({
      status: 401,
    });
    const b = await attempt({ accessClaims: { jti: "second-session" } });
    await b.incoming.complete(b.callback);
    expect(b.incoming.request().token !== old).toBe(true);
    b.transport.mockResolvedValue(new Response("{}", { status: 201 }));
    await b.incoming.client.createCart();
    const headers = new Headers(b.transport.mock.calls.at(-1)![1]?.headers);
    expect(
      headers.get("Authorization") === "Bearer " + b.incoming.request().token,
    ).toBe(true);
    expect(a.incoming.getSnapshot().phase).toBe("signedOut");
  });
  it("P12/P13: rejects a delayed response from a logged-out generation and cancels owned requests", async () => {
    const a = await attempt();
    await a.incoming.complete(a.callback);
    let release: (r: Response) => void = () => {};
    a.transport.mockImplementation(
      () =>
        new Promise((r) => {
          release = r;
        }),
    );
    const operation = a.incoming.client.createCart();
    const denied = expect(operation).rejects.toMatchObject({ status: 401 });
    const init = a.transport.mock.calls.at(-1)![1]!;
    expect(init.redirect).toBe("error");
    expect(init.credentials).toBe("omit");
    a.incoming.logout();
    expect(init.signal?.aborted).toBe(true);
    release(new Response("{}", { status: 201 }));
    await denied;
  });
  it("P13: keeps encoded cart IDs on the approved API and omits owner/cookie/token URL data", async () => {
    const a = await attempt();
    await a.incoming.complete(a.callback);
    a.transport.mockResolvedValue(new Response("{}", { status: 200 }));
    await a.incoming.client.setQuantity(
      "https://foreign.example.test/../other",
      1,
      2,
    );
    const [path, init] = a.transport.mock.calls.at(-1)!;
    expect(String(path).startsWith("/api/carts/https%3A%2F%2F")).toBe(true);
    expect(init?.body).toBe('{"quantity":2}');
    expect(init?.credentials).toBe("omit");
    for (const path of [
      "https://foreign.example.test/api/carts",
      "//foreign.example.test/api/carts",
      "/api/../outside",
      "/outside",
    ])
      expect(() => protectedApiPath(path)).toThrow();
  });
});
