// C5-M06 sensitive logging controls. Synthetic; never executed.
type User = { id_token: string; profile: { sub: string } };

export function unsafeToken(user: User) {
  // ruleid: morrow.ts.sensitive-value-logged
  console.log("signed in", user.id_token);
}

export function unsafeHeader(authorization: string) {
  // ruleid: morrow.ts.sensitive-value-logged
  console.error(`auth failed for ${authorization}`);
}

export function unsafeClaims(claims: Record<string, unknown>) {
  // ruleid: morrow.ts.sensitive-value-logged
  console.warn(JSON.stringify({ claims }));
}

export function safeCode(requestId: string, status: number) {
  // ok: morrow.ts.sensitive-value-logged
  console.log(JSON.stringify({ requestId, status, code: "AUTH_FAILED" }));
}

export function safeLiteral() {
  // ok: morrow.ts.sensitive-value-logged
  console.error("Token refresh failed; sign in again.");
}

export function missedRename(user: User) {
  const value = user.id_token;
  // todoruleid: morrow.ts.sensitive-value-logged
  console.log(value);
}
