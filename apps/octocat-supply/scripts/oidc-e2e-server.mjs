// Test-only loopback bridge. Never used by the application/container entrypoint.
import { createServer } from "node:http";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { Buffer } from "node:buffer";
import { createRemoteJWKSet, customFetch } from "jose";
import {
  OidcProviderFixture,
  fixtureConfig,
} from "../test/fixtures/oidc-provider.ts";
import { Store } from "../api/src/database.ts";
import { createApp } from "../api/src/app.ts";
import { oidcAuthenticator } from "../api/src/auth.ts";

const folder = mkdtempSync(join(tmpdir(), "morrow-oidc-browser-"));
const dist = resolve("frontend/dist");
readFileSync(join(dist, "index.html"));
let store, app, provider, statuses;
function reset(options = {}) {
  store?.close();
  rmSync(join(folder, "fixture.sqlite"), { force: true });
  rmSync(join(folder, "fixture.sqlite-wal"), { force: true });
  rmSync(join(folder, "fixture.sqlite-shm"), { force: true });
  store = new Store(join(folder, "fixture.sqlite"));
  store.migrate();
  store.seed();
  provider = new OidcProviderFixture();
  provider.options = options;
  statuses = [];
  const settings = {
    issuer: fixtureConfig.authority,
    audience: "morrow-api",
    jwksUri: fixtureConfig.authority + "/jwks",
    role: "Demo.User",
    scope: "cart",
  };
  const keys = createRemoteJWKSet(new URL(settings.jwksUri), {
    cooldownDuration: 0,
    timeoutDuration: 1000,
    [customFetch]: (url, init) => provider.fetch(url, init),
  });
  app = createApp(store, {
    origins: [fixtureConfig.publicOrigin],
    authenticate: oidcAuthenticator(settings, keys),
  });
}
reset();
const send = (res, status, body) => {
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Cache-Control": "no-store",
  });
  res.end(JSON.stringify(body));
};
const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, "http://127.0.0.1:4175");
    if (url.pathname === "/health/fixture")
      return send(res, 200, { status: "ready" });
    if (url.pathname.startsWith("/api/")) {
      res.once("finish", () =>
        statuses.push({
          method: req.method,
          status: res.statusCode,
          bearer: !!req.headers.authorization,
          cookie: !!req.headers.cookie,
        }),
      );
      return app(req, res);
    }
    if (url.pathname.startsWith("/__fixture/")) {
      if (url.pathname === "/__fixture/stats")
        return send(res, 200, {
          counts: provider.counts,
          proof: provider.proof,
          statuses,
        });
      const chunks = [];
      let size = 0;
      for await (const chunk of req) {
        size += chunk.length;
        if (size > 16384) throw new Error();
        chunks.push(chunk);
      }
      const options = JSON.parse(Buffer.concat(chunks).toString() || "{}");
      if (url.pathname === "/__fixture/reset") {
        reset(options);
        return send(res, 200, {});
      }
      if (url.pathname === "/__fixture/options") {
        provider.options = { ...provider.options, ...options };
        return send(res, 200, {});
      }
      if (url.pathname === "/__fixture/ownership") {
        if (!/^[a-f0-9-]{36}$/.test(options.cart ?? "")) throw new Error();
        if (options.actor && !["alice", "bob"].includes(options.actor))
          throw new Error();
        const tokens = await provider.tokens(
          "non-live-ownership-nonce",
          options.actor ?? "bob",
        );
        const headers = {
          Authorization: "Bearer " + tokens.access_token,
          "Content-Type": "application/json",
        };
        const results = [];
        for (const [method, path, body] of [
          ["GET", "/api/carts/" + options.cart],
          ["PUT", "/api/carts/" + options.cart + "/items/1", '{"quantity":1}'],
          ["DELETE", "/api/carts/" + options.cart + "/items/1"],
          ["DELETE", "/api/carts/" + options.cart],
        ])
          results.push(
            (
              await fetch("http://127.0.0.1:4175" + path, {
                method,
                headers,
                body,
              })
            ).status,
          );
        return send(res, 200, { statuses: results });
      }
      return send(res, 404, {});
    }
    if (url.pathname.startsWith("/__issuer/")) {
      const virtual =
        fixtureConfig.authority +
        url.pathname.slice("/__issuer".length) +
        url.search;
      if (url.pathname === "/__issuer/authorize") {
        const callback = provider.authorize(virtual);
        // A new navigation stays inside Playwright's routing fence; an HTTP
        // redirect can bypass routing for the remainder of that request chain.
        res.writeHead(200, {
          "Content-Type": "text/html",
          "Cache-Control": "no-store",
          "Referrer-Policy": "no-referrer",
        });
        return res.end(
          '<!doctype html><meta http-equiv="refresh" content="0;url=' +
            callback.replaceAll("&", "&amp;").replaceAll('"', "&quot;") +
            '">',
        );
      }
      const chunks = [];
      for await (const chunk of req) chunks.push(chunk);
      const headers = Object.fromEntries(
        Object.entries(req.headers).filter(([, v]) => typeof v === "string"),
      );
      const response = await provider.fetch(virtual, {
        method: req.method,
        headers,
        body:
          req.method === "POST" ? Buffer.concat(chunks).toString() : undefined,
      });
      res.writeHead(response.status, {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Access-Control-Allow-Origin": fixtureConfig.publicOrigin,
        Vary: "Origin",
      });
      return res.end(await response.text());
    }
    if (url.pathname === "/auth-config.json")
      return send(res, 200, fixtureConfig);
    const name = url.pathname.startsWith("/assets/")
      ? url.pathname.slice(1)
      : "index.html";
    const path = resolve(dist, name);
    if (!path.startsWith(dist + "/")) throw new Error();
    const body = readFileSync(path);
    res.writeHead(200, {
      "Content-Type": name.endsWith(".js")
        ? "text/javascript"
        : name.endsWith(".css")
          ? "text/css"
          : "text/html",
      "Cache-Control": "no-store",
      "Referrer-Policy": "no-referrer",
      "X-Content-Type-Options": "nosniff",
      "Content-Security-Policy":
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self' https://issuer.example.test; base-uri 'none'; frame-ancestors 'none'",
    });
    res.end(body);
  } catch {
    send(res, 503, { code: "SIMULATED_DEPENDENCY_UNAVAILABLE" });
  }
});
server.listen(4175, "127.0.0.1");
const stop = () =>
  server.close(() => {
    store.close();
    rmSync(folder, { recursive: true, force: true });
  });
process.once("SIGTERM", stop);
process.once("SIGINT", stop);
