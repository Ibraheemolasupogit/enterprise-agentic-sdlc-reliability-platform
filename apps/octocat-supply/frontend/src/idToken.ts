import { createRemoteJWKSet, customFetch, jwtVerify } from "jose";
import type { OidcMetadata, User } from "oidc-client-ts";

export type OidcConfig = {
  mode: "oidc";
  authority: string;
  clientId: string;
  scope: string;
  publicOrigin: string;
};
export type AuthConfig = { mode: "anonymous" } | OidcConfig;
const invalid = () => new Error("Identity response could not be verified.");

export function parseAuthConfig(value: unknown): AuthConfig {
  if (!value || typeof value !== "object" || !("mode" in value))
    throw invalid();
  if (value.mode === "anonymous") return { mode: "anonymous" };
  const v = value as Record<string, unknown>;
  for (const key of ["authority", "clientId", "scope", "publicOrigin"])
    if (typeof v[key] !== "string" || !v[key] || v[key].length > 2048)
      throw invalid();
  const authority = new URL(v.authority as string);
  const origin = new URL(v.publicOrigin as string);
  const scopes = (v.scope as string).split(" ");
  if (
    v.mode !== "oidc" ||
    authority.protocol !== "https:" ||
    authority.username ||
    authority.password ||
    authority.search ||
    authority.hash ||
    origin.origin !== v.publicOrigin ||
    origin.protocol !== "https:" ||
    origin.origin !== location.origin ||
    (v.clientId as string).length > 256 ||
    /\s/.test(v.clientId as string) ||
    !scopes.includes("openid") ||
    scopes.includes("offline_access") ||
    scopes.some((s) => !s || /\s/.test(s)) ||
    (authority.hostname === "login.microsoftonline.com" &&
      /^\/(common|organizations|consumers)(\/|$)/i.test(authority.pathname))
  )
    throw invalid();
  return {
    mode: "oidc",
    authority: v.authority as string,
    clientId: v.clientId as string,
    scope: v.scope as string,
    publicOrigin: v.publicOrigin as string,
  };
}

export function trustedMetadata(
  value: unknown,
  config: OidcConfig,
): Partial<OidcMetadata> {
  if (!value || typeof value !== "object") throw invalid();
  const v = value as Record<string, unknown>;
  if (v.issuer !== config.authority) throw invalid();
  const result: Partial<OidcMetadata> = { issuer: config.authority };
  for (const name of [
    "authorization_endpoint",
    "token_endpoint",
    "jwks_uri",
  ] as const) {
    if (typeof v[name] !== "string") throw invalid();
    const url = new URL(v[name]);
    if (
      url.origin !== new URL(config.authority).origin ||
      url.protocol !== "https:" ||
      url.username ||
      url.password ||
      url.hash ||
      url.search
    )
      throw invalid();
    result[name] = url.href;
  }
  for (const [name, expected] of [
    ["response_types_supported", "code"],
    ["response_modes_supported", "query"],
    ["code_challenge_methods_supported", "S256"],
    ["id_token_signing_alg_values_supported", "RS256"],
  ] as const)
    if (
      v[name] !== undefined &&
      (!Array.isArray(v[name]) || !v[name].includes(expected))
    )
      throw invalid();
  return result;
}

export function idTokenVerifier(
  config: OidcConfig,
  metadata: Partial<OidcMetadata>,
) {
  const keys = createRemoteJWKSet(new URL(metadata.jwks_uri!), {
    timeoutDuration: 1000,
    cacheMaxAge: 300000,
    cooldownDuration: 30000,
    [customFetch]: (input, init) =>
      fetch(input, { ...init, redirect: "error", credentials: "omit" }),
  });
  return async (user: User, nonce: string) => {
    if (
      !user.id_token ||
      !user.access_token ||
      user.access_token.length > 8185 ||
      !/^[\w.-]+$/.test(user.access_token) ||
      user.token_type?.toLowerCase() !== "bearer" ||
      user.refresh_token ||
      !Number.isFinite(user.expires_at) ||
      user.expires_at! <= Date.now() / 1000
    )
      throw invalid();
    const { payload } = await jwtVerify(user.id_token, keys, {
      algorithms: ["RS256"],
      issuer: config.authority,
      audience: config.clientId,
      requiredClaims: ["sub", "exp", "iat", "nonce"],
      clockTolerance: 5,
    });
    if (
      typeof payload.sub !== "string" ||
      !payload.sub ||
      payload.sub.length > 256 ||
      payload.nonce !== nonce ||
      !nonce ||
      !Number.isFinite(payload.iat) ||
      payload.iat! > Date.now() / 1000 + 5 ||
      !Number.isFinite(payload.exp) ||
      (payload.azp !== undefined && payload.azp !== config.clientId) ||
      (Array.isArray(payload.aud) &&
        (payload.azp !== config.clientId ||
          payload.aud.some((a) => a !== config.clientId)))
    )
      throw invalid();
    return {
      issuer: config.authority,
      subject: payload.sub,
      expiresAt: Math.min(payload.exp!, user.expires_at!),
    };
  };
}
