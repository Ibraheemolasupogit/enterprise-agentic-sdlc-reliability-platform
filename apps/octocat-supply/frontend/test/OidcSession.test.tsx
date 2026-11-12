import { act, render, screen } from "@testing-library/react";
import { StrictMode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import AuthApp from "../src/AuthApp";
import { userStorageKey } from "../src/oidcSession";
import { fixtureConfig } from "../../test/fixtures/oidc-provider";
import { attempt, closeSessions, session } from "./oidcHarness";

afterEach(closeSessions);
const response = (status: number, body: object = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
describe("C3 session lifecycle", () => {
  it.each(["timer", "resume"])(
    "P10: expires memory tokens via %s before dispatch",
    async (kind) => {
      vi.useFakeTimers({ toFake: ["Date", "setTimeout", "clearTimeout"] });
      const a = await attempt();
      await a.incoming.complete(a.callback);
      expect(a.incoming.getSnapshot().phase).toBe("signedIn");
      const detach = a.incoming.attach();
      if (kind === "timer") await vi.advanceTimersByTimeAsync(301000);
      else {
        vi.setSystemTime(Date.now() + 301000);
        document.dispatchEvent(new Event("visibilitychange"));
      }
      expect(a.incoming.getSnapshot().phase).toBe("signedOut");
      expect(() => a.incoming.request()).toThrow();
      expect(a.incoming.getSnapshot().error).toBe(
        "Your session expired. Sign in again.",
      );
      detach();
    },
  );
  it.each(["metadata", "token", "jwks"] as const)(
    "P05/P09: bounds %s outage without accepting a late callback",
    async (kind) => {
      vi.useFakeTimers();
      // Native AbortSignal.timeout uses the host clock, independently of Vitest.
      // Route only this public timer primitive through the controlled test clock.
      vi.spyOn(AbortSignal, "timeout").mockImplementation((ms) => {
        const controller = new AbortController();
        setTimeout(
          () => controller.abort(new DOMException("Timed out", "TimeoutError")),
          ms,
        );
        return controller.signal;
      });
      const a = await attempt();
      a.provider.options.hang = kind;
      const completion = a.incoming.complete(a.callback);
      await vi.waitFor(() =>
        expect(a.provider.counts[kind]).toBe(kind === "metadata" ? 2 : 1),
      );
      await vi.advanceTimersByTimeAsync(kind === "jwks" ? 1250 : 5250);
      await completion;
      expect(a.incoming.getSnapshot().phase).toBe("signedOut");
      expect(sessionStorage.length).toBe(0);
      expect(() => a.incoming.request()).toThrow();
    },
  );
  it("P05/P12: aggregate deadline closes the session even if an unabortable verification response arrives late", async () => {
    vi.useFakeTimers();
    const a = await attempt();
    let started = false;
    let release: () => void = () => {};
    const barrier = new Promise<void>((r) => {
      release = r;
    });
    a.transport.mockImplementation(async (input, init) => {
      if (String(input).endsWith("/jwks")) {
        started = true;
        await barrier;
      }
      return a.provider.fetch(input, init);
    });
    const operation = a.incoming.complete(a.callback);
    await vi.waitFor(() => expect(started).toBe(true));
    await vi.advanceTimersByTimeAsync(15250);
    expect(a.incoming.getSnapshot().phase).toBe("signedOut");
    expect(sessionStorage.length).toBe(0);
    release();
    await operation;
    expect(() => a.incoming.request()).toThrow();
    expect(a.incoming.getSnapshot().phase).toBe("signedOut");
  });
  it("P12: logout while callback is pending cannot restore a user or API token", async () => {
    const a = await attempt();
    let release: () => void = () => {};
    const barrier = new Promise<void>((r) => {
      release = r;
    });
    let tokenStarted = false;
    a.transport.mockImplementation(async (input, init) => {
      if (String(input).endsWith("/token")) {
        tokenStarted = true;
        await barrier;
      }
      return a.provider.fetch(input, init);
    });
    const completion = a.incoming.complete(a.callback);
    await vi.waitFor(() => expect(tokenStarted).toBe(true));
    a.incoming.logout();
    release();
    await completion;
    expect(a.incoming.getSnapshot().phase).toBe("signedOut");
    expect(() => a.incoming.request()).toThrow();
    expect(sessionStorage.length).toBe(0);
  });
  it("P11: isolates hashed client/user namespaces and never claims anonymous references", async () => {
    localStorage.setItem("morrow-demo-cart", "anonymous-reference");
    const a = await attempt();
    await a.incoming.complete(a.callback);
    const alice = a.incoming.getSnapshot().storageKey!;
    a.incoming.logout();
    const b = await attempt({ actor: "bob" });
    await b.incoming.complete(b.callback);
    expect(b.incoming.getSnapshot().storageKey !== alice).toBe(true);
    expect(alice).toMatch(/^morrow-oidc-cart:v2:[a-f0-9]{64}$/);
    expect(localStorage.getItem("morrow-demo-cart")).toBe(
      "anonymous-reference",
    );
    expect(b.provider.counts.token).toBe(1);
  });
  it("P12: a cancelled callback cannot erase a newer sign-in's pending state", async () => {
    const a = await attempt();
    let release: () => void = () => {};
    let started = false;
    const barrier = new Promise<void>((r) => {
      release = r;
    });
    a.transport.mockImplementation(async (input, init) => {
      if (String(input).endsWith("/token")) {
        started = true;
        await barrier;
      }
      return a.provider.fetch(input, init);
    });
    const completion = a.incoming.complete(a.callback);
    await vi.waitFor(() => expect(started).toBe(true));
    a.incoming.logout();
    const b = await attempt({ actor: "bob" });
    const pending = sessionStorage.length;
    expect(pending).toBeGreaterThan(0);
    release();
    await completion;
    expect(sessionStorage.length).toBe(pending);
    await b.incoming.complete(b.callback);
    expect(b.incoming.getSnapshot().phase).toBe("signedIn");
  });
  it("P12: component unmount during exchange prevents protected API calls and late restoration", async () => {
    const a = await attempt();
    let release: () => void = () => {};
    let started = false;
    let protectedCalls = 0;
    const barrier = new Promise<void>((r) => {
      release = r;
    });
    a.transport.mockImplementation(async (input, init) => {
      if (String(input) === "/auth-config.json")
        return response(200, fixtureConfig);
      if (String(input).startsWith("/api/")) {
        protectedCalls++;
        return response(200, { items: [], total: 0 });
      }
      if (String(input).endsWith("/token")) {
        started = true;
        await barrier;
      }
      return a.provider.fetch(input, init);
    });
    const view = render(<AuthApp callbackUrl={a.callback} />);
    await vi.waitFor(() => expect(started).toBe(true));
    await act(async () => view.unmount());
    await act(async () => {
      release();
      await new Promise((r) => setTimeout(r, 10));
    });
    expect(protectedCalls).toBe(0);
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });
  it.each([200, 404, 503])(
    "P11: migrates a legacy reference only after actual API approval status %s",
    async (status) => {
      const legacy = userStorageKey({
        profile: { iss: fixtureConfig.authority, sub: "id-alice" },
      } as Parameters<typeof userStorageKey>[0]);
      const id = "c18eb8c7-276c-4330-83fe-e842c7e5fb2e";
      localStorage.setItem(legacy, id);
      const a = await attempt();
      let apiCalls = 0;
      a.transport.mockImplementation(async (input, init) => {
        if (String(input).startsWith("/api/")) {
          apiCalls++;
          return response(status, { id });
        }
        return a.provider.fetch(input, init);
      });
      await a.incoming.complete(a.callback);
      expect(apiCalls).toBe(1);
      if (status === 503) {
        expect(a.incoming.getSnapshot().phase).toBe("restore");
        expect(localStorage.getItem(legacy)).toBe(id);
        a.transport.mockImplementation(async (input, init) =>
          String(input).startsWith("/api/")
            ? response(200, { id })
            : a.provider.fetch(input, init),
        );
        await a.incoming.retryRestore();
      }
      expect(a.incoming.getSnapshot().phase).toBe("signedIn");
      expect(localStorage.getItem(legacy)).toBeNull();
      expect(localStorage.getItem(a.incoming.getSnapshot().storageKey!)).toBe(
        status === 404 ? null : id,
      );
    },
  );
  it("P03: cleans a callback even if runtime configuration cannot load", async () => {
    history.replaceState(
      {},
      "",
      "/auth/callback?code=non-live-code&state=non-live-state",
    );
    sessionStorage.setItem(
      "morrow-oidc-state:v1:old:pending",
      "non-live-state",
    );
    sessionStorage.setItem("unrelated", "keep");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("non-live-code")),
    );
    render(<AuthApp />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "shop is closed",
    );
    expect(location.href).toBe(fixtureConfig.publicOrigin + "/");
    expect(sessionStorage.getItem("unrelated")).toBe("keep");
    expect(sessionStorage.length).toBe(1);
  });
  it("P04/P12: StrictMode effect replay processes once, unmount clears access", async () => {
    const a = await attempt();
    const api = vi.fn(async () => response(200, { items: [], total: 0 }));
    a.transport.mockImplementation(async (input, init) =>
      String(input) === "/auth-config.json"
        ? response(200, fixtureConfig)
        : String(input).startsWith("/api/")
          ? api()
          : a.provider.fetch(input, init),
    );
    const view = render(
      <StrictMode>
        <AuthApp callbackUrl={a.callback} />
      </StrictMode>,
    );
    expect(await screen.findByText("Signed in")).toBeInTheDocument();
    expect(a.provider.counts.token).toBe(1);
    await act(async () => view.unmount());
    expect(sessionStorage.length).toBe(0);
    const reloaded = session();
    expect(() => reloaded.request()).toThrow();
  });
});
