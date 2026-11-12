// Node-only simulated protocol responder. Published key provenance/rights:
// api/fixtures/README.md (RFC 7515 A.2); never import into a production entry.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { createHash } from "node:crypto";
import { importJWK, SignJWT, type JWTPayload } from "jose";

export const fixtureConfig = {
  mode: "oidc" as const,
  authority: "https://issuer.example.test",
  clientId: "morrow-spa",
  scope: "openid cart",
  publicOrigin: "https://shop.example.test",
};
export const publishedJwk = JSON.parse(
  readFileSync(resolve("api/fixtures/rfc7515-rsa.json"), "utf8"),
);
export const publicJwk = {
  kty: publishedJwk.kty,
  n: publishedJwk.n,
  e: publishedJwk.e,
  kid: "fixture-rsa",
  alg: "RS256",
  use: "sig",
};
let signingKey: ReturnType<typeof importJWK> | undefined;
export type ProviderOptions = {
  actor?: "alice" | "bob";
  idClaims?: JWTPayload;
  accessClaims?: JWTPayload;
  idHeader?: Record<string, string>;
  badSignature?: boolean;
  metadata?: Record<string, unknown>;
  tokenFields?: Record<string, unknown>;
  denial?: string;
  invalidGrant?: boolean;
  malformedTokenResponse?: boolean;
  outage?: "metadata" | "token" | "jwks";
  hang?: "metadata" | "token" | "jwks";
};
type Grant = {
  client: string;
  redirect: string;
  challenge: string;
  nonce: string;
  actor: string;
  used: boolean;
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

export class OidcProviderFixture {
  options: ProviderOptions = {};
  readonly counts = { metadata: 0, authorize: 0, token: 0, jwks: 0 };
  readonly grants = new Map<string, Grant>();
  lastAuthorization?: URL;
  proof = { s256: false, nonce: false, publicClient: false, verifier: false };
  metadata() {
    return {
      issuer: fixtureConfig.authority,
      authorization_endpoint: fixtureConfig.authority + "/authorize",
      token_endpoint: fixtureConfig.authority + "/token",
      jwks_uri: fixtureConfig.authority + "/jwks",
      response_types_supported: ["code"],
      response_modes_supported: ["query"],
      code_challenge_methods_supported: ["S256"],
      id_token_signing_alg_values_supported: ["RS256"],
      ...this.options.metadata,
    };
  }
  authorize(raw: string) {
    const url = new URL(raw),
      q = url.searchParams;
    this.counts.authorize++;
    if (
      url.origin !== fixtureConfig.authority ||
      url.pathname !== "/authorize" ||
      ["client_id", "redirect_uri", "state", "nonce", "code_challenge"].some(
        (k) => q.getAll(k).length !== 1 || !q.get(k),
      ) ||
      q.get("client_id") !== fixtureConfig.clientId ||
      q.get("redirect_uri") !== fixtureConfig.publicOrigin + "/auth/callback" ||
      q.get("response_type") !== "code" ||
      q.get("response_mode") !== "query" ||
      q.get("code_challenge_method") !== "S256" ||
      !q.get("scope")?.split(" ").includes("openid") ||
      q.get("scope")?.split(" ").includes("offline_access") ||
      q.has("client_secret")
    )
      throw new Error("Fixture authorization denied.");
    this.lastAuthorization = url;
    this.proof.s256 = true;
    this.proof.nonce = true;
    const callback = new URL(q.get("redirect_uri")!);
    callback.searchParams.set("state", q.get("state")!);
    if (this.options.denial)
      callback.searchParams.set("error", this.options.denial);
    else {
      const code = "fixture-code-" + this.counts.authorize;
      this.grants.set(code, {
        client: q.get("client_id")!,
        redirect: q.get("redirect_uri")!,
        challenge: q.get("code_challenge")!,
        nonce: q.get("nonce")!,
        actor: this.options.actor ?? "alice",
        used: false,
      });
      callback.searchParams.set("code", code);
    }
    return callback.href;
  }
  async tokens(nonce: string, actor = this.options.actor ?? "alice") {
    const now = Math.floor(Date.now() / 1000);
    const { alg: requestedAlg, ...header } = this.options.idHeader ?? {};
    let id = await new SignJWT({
      iss: fixtureConfig.authority,
      sub: "id-" + actor,
      aud: fixtureConfig.clientId,
      iat: now,
      exp: now + 300,
      nonce,
      ...this.options.idClaims,
    })
      .setProtectedHeader({
        alg: "RS256",
        kid: publicJwk.kid,
        ...header,
      })
      .sign(await (signingKey ??= importJWK(publishedJwk, "RS256")));
    if (requestedAlg && requestedAlg !== "RS256") {
      const parts = id.split(".");
      parts[0] = Buffer.from(
        JSON.stringify({ alg: requestedAlg, kid: publicJwk.kid, ...header }),
      ).toString("base64url");
      id = parts.join(".");
    }
    if (this.options.badSignature) {
      const parts = id.split(".");
      parts[2] = (parts[2][0] === "a" ? "b" : "a") + parts[2].slice(1);
      id = parts.join(".");
    }
    const access = await new SignJWT({
      iss: fixtureConfig.authority,
      sub: "api-" + actor,
      aud: "morrow-api",
      iat: now,
      exp: now + 300,
      roles: ["Demo.User"],
      scope: "cart",
      ...this.options.accessClaims,
    })
      .setProtectedHeader({ alg: "RS256", kid: publicJwk.kid })
      .sign(await (signingKey ??= importJWK(publishedJwk, "RS256")));
    return {
      id_token: id,
      access_token: access,
      token_type: "Bearer",
      expires_in: 300,
      scope: fixtureConfig.scope,
      ...this.options.tokenFields,
    };
  }
  fetch = async (
    input: RequestInfo | URL,
    init: RequestInit = {},
  ): Promise<Response> => {
    const url = new URL(input instanceof Request ? input.url : String(input));
    if (url.origin !== fixtureConfig.authority)
      throw new Error("Fixture denied external network.");
    const route = url.pathname.endsWith("/.well-known/openid-configuration")
      ? "metadata"
      : url.pathname === "/token"
        ? "token"
        : url.pathname === "/jwks"
          ? "jwks"
          : undefined;
    if (!route) throw new Error("Fixture endpoint is not allowed.");
    this.counts[route]++;
    if (this.options.outage === route)
      throw new TypeError("Non-live upstream detail must not escape.");
    if (this.options.hang === route)
      return new Promise((_resolve, reject) => {
        const signal =
          init.signal ?? (input instanceof Request ? input.signal : undefined);
        if (signal?.aborted)
          reject(new DOMException("Fixture cancelled", "AbortError"));
        else
          signal?.addEventListener(
            "abort",
            () => reject(new DOMException("Fixture cancelled", "AbortError")),
            { once: true },
          );
      });
    if (route === "metadata") return json(this.metadata());
    if (route === "jwks") return json({ keys: [publicJwk] });
    const body = new URLSearchParams(String(init.body ?? ""));
    const grant = this.grants.get(body.get("code") ?? "");
    const verifier = body.get("code_verifier") ?? "";
    if (
      !grant ||
      grant.used ||
      this.options.invalidGrant ||
      body.get("grant_type") !== "authorization_code" ||
      body.get("client_id") !== grant.client ||
      body.get("redirect_uri") !== grant.redirect ||
      !/^[A-Za-z0-9._~-]{43,128}$/.test(verifier) ||
      createHash("sha256").update(verifier).digest("base64url") !==
        grant.challenge ||
      body.has("client_secret") ||
      new Headers(init.headers).has("Authorization")
    )
      return json({ error: "invalid_grant" }, 400);
    grant.used = true;
    this.proof.publicClient = true;
    this.proof.verifier = true;
    if (this.options.malformedTokenResponse)
      return new Response("not-json", {
        headers: { "Content-Type": "application/json" },
      });
    return json(await this.tokens(grant.nonce, grant.actor as "alice" | "bob"));
  };
}
