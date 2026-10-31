import { readFileSync } from "node:fs";
import {
  createLocalJWKSet,
  createRemoteJWKSet,
  customFetch,
  importJWK,
  SignJWT,
  type JWTPayload,
} from "jose";
import request from "supertest";
import { describe, expect, it } from "vitest";
import {
  oidcAuthenticator,
  anonymousAuthenticator,
  oidcSettings,
} from "../src/auth.js";
import { createApp } from "../src/app.js";
import { Store, migrations } from "../src/database.js";
import { runtimeSettings } from "../src/runtime.js";

const privateJwk = JSON.parse(
  readFileSync(
    new URL("../fixtures/rfc7515-rsa.json", import.meta.url),
    "utf8",
  ),
);
const publicJwk = {
  kty: privateJwk.kty,
  n: privateJwk.n,
  e: privateJwk.e,
  kid: "test-one",
  alg: "RS256",
  use: "sig",
};
const key = await importJWK(privateJwk, "RS256");
const config = {
  issuer: "https://issuer.example.test",
  audience: "morrow-api",
  jwksUri: "https://issuer.example.test/jwks",
  role: "Demo.User",
  scope: "cart",
};
const verify = oidcAuthenticator(
  config,
  createLocalJWKSet({ keys: [publicJwk] }),
);
async function token(overrides: JWTPayload = {}, kid = "test-one") {
  const now = Math.floor(Date.now() / 1000);
  return new SignJWT({
    iss: config.issuer,
    aud: config.audience,
    sub: "alice",
    iat: now,
    exp: now + 300,
    roles: ["Demo.User"],
    scope: "cart",
    ...overrides,
  })
    .setProtectedHeader({ alg: "RS256", kid })
    .sign(key);
}

describe("OIDC signature/claims and anonymous namespace boundaries", () => {
  it("upgrades M2 carts without assigning an authenticated owner or changing old migrations", () => {
    const store = new Store(":memory:");
    try {
      store.migrate(migrations.slice(0, 2));
      const id = "c18eb8c7-276c-4330-83fe-e842c7e5fb2e";
      store.db.prepare("INSERT INTO carts(id) VALUES(?)").run(id);
      const history = store.db
        .prepare("SELECT * FROM schema_migrations ORDER BY version")
        .all();
      store.migrate();
      store.seed();
      expect(store.cart(id).items).toEqual([]);
      expect(
        store.db.prepare("SELECT owner_key FROM carts WHERE id=?").get(id)
          ?.owner_key,
      ).toBe("anonymous:v1");
      expect(
        store.db
          .prepare(
            "SELECT * FROM schema_migrations WHERE version<=2 ORDER BY version",
          )
          .all(),
      ).toEqual(history);
      expect(() => store.cart(id, "oidc:" + "a".repeat(64))).toThrow();
    } finally {
      store.close();
    }
  });
  it("uses only a verified issuer/subject, independent of principal headers", async () => {
    const a = await verify("Bearer " + (await token()));
    expect(a).toMatch(/^oidc:[a-f0-9]{64}$/);
    expect(await verify("Bearer " + (await token({ sub: "bob" })))).not.toBe(a);
    expect(await anonymousAuthenticator(undefined)).not.toBe(a);
    await expect(
      anonymousAuthenticator("Bearer ignored"),
    ).rejects.toMatchObject({ status: 401 });
  });
  it.each([
    { iss: "https://attacker.example.test" },
    { aud: "other" },
    { exp: 1 },
    { nbf: 9999999999 },
    { iat: 1 },
    { roles: [] },
    { scope: "read" },
    { sub: "" },
  ])("rejects invalid claims %j", async (claims) => {
    await expect(
      verify("Bearer " + (await token(claims))),
    ).rejects.toMatchObject({ status: expect.any(Number) });
  });
  it("rejects absent/oversized/tampered tokens and refreshes a rotated JWKS kid", async () => {
    await expect(verify(undefined)).rejects.toMatchObject({ status: 401 });
    const unsigned =
      Buffer.from('{"alg":"none"}').toString("base64url") +
      "." +
      Buffer.from('{"sub":"alice"}').toString("base64url") +
      ".";
    await expect(verify("Bearer " + unsigned)).rejects.toMatchObject({
      status: 401,
    });
    await expect(verify("Bearer " + "x".repeat(9000))).rejects.toMatchObject({
      status: 401,
    });
    const signed = await token();
    const parts = signed.split(".");
    parts[1] = Buffer.from('{"sub":"mallory"}').toString("base64url");
    await expect(verify("Bearer " + parts.join("."))).rejects.toMatchObject({
      status: 401,
    });
    let kid = "test-one",
      calls = 0;
    const keys = createRemoteJWKSet(new URL(config.jwksUri), {
      cooldownDuration: 0,
      [customFetch]: async () => {
        calls++;
        return new Response(JSON.stringify({ keys: [{ ...publicJwk, kid }] }));
      },
    });
    const remote = oidcAuthenticator(config, keys);
    await remote("Bearer " + (await token()));
    kid = "test-two";
    await remote("Bearer " + (await token({}, kid)));
    expect(calls).toBe(2);
  });
  it("fails closed with a safe dependency error when the trusted JWKS is unavailable", async () => {
    const keys = createRemoteJWKSet(new URL(config.jwksUri), {
      [customFetch]: async () => {
        throw new TypeError("sensitive upstream detail");
      },
    });
    await expect(
      oidcAuthenticator(config, keys)("Bearer " + (await token())),
    ).rejects.toMatchObject({
      status: 503,
      code: "IDENTITY_UNAVAILABLE",
      message: "Identity verification is temporarily unavailable.",
    });
  });
  it("isolates all cart methods across authenticated users and anonymous mode", async () => {
    const store = new Store(":memory:");
    store.migrate();
    store.seed();
    try {
      const app = createApp(store, { authenticate: verify });
      const alice = "Bearer " + (await token()),
        bob = "Bearer " + (await token({ sub: "bob" }));
      const id = (
        await request(app)
          .post("/api/carts")
          .set("Authorization", alice)
          .send({})
          .expect(201)
      ).body.id;
      await request(app)
        .put(`/api/carts/${id}/items/1`)
        .set("Authorization", alice)
        .send({ quantity: 2 })
        .expect(200);
      for (const [method, path] of [
        ["get", `/api/carts/${id}`],
        ["delete", `/api/carts/${id}`],
        ["delete", `/api/carts/${id}/items/1`],
      ] as const)
        await request(app)[method](path).set("Authorization", bob).expect(404);
      await request(app)
        .put(`/api/carts/${id}/items/1`)
        .set("Authorization", bob)
        .send({ quantity: 1 })
        .expect(404);
      await request(app)
        .get(`/api/carts/${id}`)
        .set("X-MS-CLIENT-PRINCIPAL", "alice")
        .expect(401);
      const anonymous = createApp(store);
      await request(anonymous).get(`/api/carts/${id}`).expect(404);
      const anonId = (
        await request(anonymous).post("/api/carts").send({}).expect(201)
      ).body.id;
      await request(app)
        .get(`/api/carts/${anonId}`)
        .set("Authorization", alice)
        .expect(404);
      await request(app)
        .post("/api/carts")
        .set("Authorization", alice)
        .send({ owner: "bob" })
        .expect(400);
      expect(
        (
          await request(app)
            .get(`/api/carts/${id}`)
            .set("Authorization", alice)
            .expect(200)
        ).body.totalMinor,
      ).toBe(25998);
    } finally {
      store.close();
    }
  });
  it("rejects incomplete/unsafe cloud configuration without opening a database or authenticating", () => {
    expect(runtimeSettings({}).auth).toBe("anonymous");
    for (const env of [
      { APP_ENV: "cloud" },
      { AUTH_MODE: "mixed" },
      { DATABASE_BACKEND: "sql" },
      { AUTH_MODE: "oidc" },
    ])
      expect(() => runtimeSettings(env)).toThrow();
    expect(() => oidcSettings({ OIDC_ISSUER: "http://untrusted" })).toThrow();
  });
});
