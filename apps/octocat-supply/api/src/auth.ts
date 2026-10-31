import { createHash } from "node:crypto";
import {
  createRemoteJWKSet,
  jwtVerify,
  errors,
  type JWTVerifyGetKey,
} from "jose";
import { AppError } from "./errors.js";

export const anonymousOwner = "anonymous:v1";
export type Authenticate = (
  authorization: string | undefined,
) => Promise<string>;
export type OidcSettings = {
  issuer: string;
  audience: string;
  jwksUri: string;
  role: string;
  scope: string;
};

export function httpsUrl(value: string | undefined, name: string): string {
  if (!value) throw new Error(`${name} is required.`);
  const url = new URL(value);
  if (
    url.protocol !== "https:" ||
    url.username ||
    url.password ||
    url.hash ||
    url.search
  )
    throw new Error(
      `${name} must be a fixed HTTPS URL without credentials, query or fragment.`,
    );
  return value;
}

export function oidcSettings(env: NodeJS.ProcessEnv): OidcSettings {
  const issuer = httpsUrl(env.OIDC_ISSUER, "OIDC_ISSUER");
  const jwksUri = httpsUrl(env.OIDC_JWKS_URI, "OIDC_JWKS_URI");
  for (const key of [
    "OIDC_AUDIENCE",
    "OIDC_REQUIRED_ROLE",
    "OIDC_REQUIRED_SCOPE",
  ])
    if (!env[key] || env[key]!.length > 256 || /\s/.test(env[key]!))
      throw new Error(`${key} must be a single bounded value.`);
  return {
    issuer,
    jwksUri,
    audience: env.OIDC_AUDIENCE!,
    role: env.OIDC_REQUIRED_ROLE!,
    scope: env.OIDC_REQUIRED_SCOPE!,
  };
}

export function oidcAuthenticator(
  settings: OidcSettings,
  key?: JWTVerifyGetKey,
): Authenticate {
  // Only the configured HTTPS JWKS is trusted. Token jku/x5u never select a URL.
  const keys =
    key ??
    createRemoteJWKSet(new URL(settings.jwksUri), {
      timeoutDuration: 1000,
      cooldownDuration: 30000,
      cacheMaxAge: 300000,
    });
  return async (authorization) => {
    if (
      !authorization ||
      authorization.length > 8192 ||
      !/^Bearer [\w.-]+$/.test(authorization)
    )
      throw new AppError(
        401,
        "UNAUTHENTICATED",
        "A valid bearer token is required.",
      );
    try {
      const { payload } = await jwtVerify(authorization.slice(7), keys, {
        algorithms: ["RS256"],
        issuer: settings.issuer,
        audience: settings.audience,
        requiredClaims: ["sub", "exp", "iat"],
        maxTokenAge: "1 hour",
        clockTolerance: 5,
      });
      if (
        typeof payload.sub !== "string" ||
        !payload.sub ||
        payload.sub.length > 256
      )
        throw new Error("Invalid subject");
      const roles = payload.roles;
      if (
        !Array.isArray(roles) ||
        !roles.every((r) => typeof r === "string") ||
        !roles.includes(settings.role)
      )
        throw new AppError(
          403,
          "FORBIDDEN",
          "The required application role is missing.",
        );
      const scopes =
        typeof payload.scope === "string" ? payload.scope : payload.scp;
      if (
        typeof scopes !== "string" ||
        !scopes.split(" ").includes(settings.scope)
      )
        throw new AppError(
          403,
          "FORBIDDEN",
          "The required API scope is missing.",
        );
      return (
        "oidc:" +
        createHash("sha256")
          .update(JSON.stringify([settings.issuer, payload.sub]))
          .digest("hex")
      );
    } catch (error) {
      if (error instanceof AppError) throw error;
      if (
        error instanceof TypeError ||
        error instanceof errors.JWKSTimeout ||
        (error instanceof errors.JOSEError && error.code === "ERR_JOSE_GENERIC")
      )
        throw new AppError(
          503,
          "IDENTITY_UNAVAILABLE",
          "Identity verification is temporarily unavailable.",
        );
      throw new AppError(
        401,
        "UNAUTHENTICATED",
        "The bearer token could not be verified.",
      );
    }
  };
}

export const anonymousAuthenticator: Authenticate = async (authorization) => {
  if (authorization)
    throw new AppError(
      401,
      "AUTH_MODE_MISMATCH",
      "This local demo does not accept identity tokens.",
    );
  return anonymousOwner;
};
