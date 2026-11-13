// C5-M03 JWT trust controls. Synthetic; never executed.
import { decodeJwt, jwtVerify, type JWTVerifyOptions, type KeyLike } from "jose";

export function unsafeDecode(token: string) {
  // ruleid: morrow.ts.jwt-decoded-without-verification
  return decodeJwt(token).sub;
}

export async function unsafeNoOptions(token: string, key: KeyLike) {
  // ruleid: morrow.ts.jwt-verify-incomplete
  return jwtVerify(token, key);
}

export async function unsafeNoIssuer(token: string, key: KeyLike) {
  // ruleid: morrow.ts.jwt-verify-incomplete
  return jwtVerify(token, key, { algorithms: ["RS256"], audience: "api://morrow" });
}

export async function unsafeNoAudience(token: string, key: KeyLike) {
  // ruleid: morrow.ts.jwt-verify-incomplete
  return jwtVerify(token, key, { algorithms: ["RS256"], issuer: "https://issuer.invalid" });
}

export async function unsafeAlgorithmNone(token: string, key: KeyLike) {
  // ruleid: morrow.ts.jwt-verify-incomplete
  return jwtVerify(token, key, { algorithms: ["none"], issuer: "https://issuer.invalid", audience: "api://morrow" });
}

export async function safeVerify(token: string, key: KeyLike) {
  // ok: morrow.ts.jwt-verify-incomplete
  return jwtVerify(token, key, {
    algorithms: ["RS256"],
    issuer: "https://issuer.invalid",
    audience: "api://morrow",
    requiredClaims: ["sub", "exp", "iat"],
  });
}

const weakOptions: JWTVerifyOptions = { algorithms: ["RS256"] };
export async function missedConstructedOptions(token: string, key: KeyLike) {
  // todoruleid: morrow.ts.jwt-verify-incomplete
  return jwtVerify(token, key, weakOptions);
}
