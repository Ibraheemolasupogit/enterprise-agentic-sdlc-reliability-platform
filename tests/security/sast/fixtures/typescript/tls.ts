// C5-M02 TLS verification controls. Synthetic; never executed.
import https from "node:https";

export function unsafeAgent() {
  // ruleid: morrow.ts.tls-verification-disabled
  return new https.Agent({ keepAlive: true, rejectUnauthorized: false });
}

export function unsafeGlobal() {
  // ruleid: morrow.ts.tls-verification-disabled
  process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
}

export function unsafeHostname() {
  // ruleid: morrow.ts.tls-verification-disabled
  return https.request({ host: "example.invalid", checkServerIdentity: () => undefined });
}

export function safeAgent(ca: string) {
  // ok: morrow.ts.tls-verification-disabled
  return new https.Agent({ keepAlive: true, rejectUnauthorized: true, ca });
}

const insecure = false;
export function constantAlias() {
  // Constant propagation resolves the alias in CE 1.185.0.
  // ruleid: morrow.ts.tls-verification-disabled
  return new https.Agent({ rejectUnauthorized: insecure });
}
