import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { setTimeout as delay } from "node:timers/promises";

const root = fileURLToPath(new URL("../", import.meta.url));
const project = process.env.COMPOSE_PROJECT_NAME ?? "morrow-supply-m2";
assert.match(project, /^morrow-supply-m2(?:-clean)?$/);
const base = "http://127.0.0.1:8080";
const results = { started: new Date().toISOString(), project, checks: [] };
function compose(args, port = "3000") {
  const result = spawnSync(
    "docker",
    ["compose", "-p", project, "-f", "compose.yaml", ...args],
    {
      cwd: root,
      env: { ...process.env, API_PORT: port },
      encoding: "utf8",
      timeout: 60000,
    },
  );
  assert.equal(
    result.status,
    0,
    result.stderr || result.error?.message || result.stdout,
  );
  return result.stdout.trim();
}
async function response(path, options = {}) {
  return fetch(base + path, {
    ...options,
    signal: AbortSignal.timeout(5000),
    headers: { "Content-Type": "application/json" },
  });
}
async function json(path, options = {}) {
  const result = await response(path, options);
  assert.ok(result.ok, `${path} returned ${result.status}`);
  return result.json();
}
async function wait(path, status) {
  for (let attempt = 0; attempt < 60; attempt++) {
    try {
      if ((await response(path)).status === status) return;
    } catch {
      /* Child is starting. */
    }
    await delay(500);
  }
  throw new Error(`${path} did not reach ${status}`);
}
let cartId;
let faulted = false;
try {
  await wait("/health/ready", 200);
  const products = await json("/api/products");
  assert.equal(products.total, 12);
  const oversized = await response("/api/carts", {
    method: "POST",
    body: JSON.stringify({ data: "x".repeat(17000) }),
  });
  assert.equal(oversized.status, 413);
  assert.equal((await oversized.json()).code, "BODY_TOO_LARGE");
  const created = await json("/api/carts", { method: "POST", body: "{}" });
  cartId = created.id;
  await json(`/api/carts/${cartId}/items/1`, {
    method: "PUT",
    body: '{"quantity":2}',
  });
  const before = await json(`/api/carts/${cartId}/items/2`, {
    method: "PUT",
    body: '{"quantity":3}',
  });
  assert.equal(before.totalMinor, 28796);
  results.checks.push(
    "frontend → API → SQLite / 12 fixtures / pricing and discount passed",
  );

  const oldContainer = compose(["ps", "-q", "api"]);
  const inspect = spawnSync(
    "docker",
    ["inspect", oldContainer, "--format", "{{json .NetworkSettings.Ports}}"],
    { encoding: "utf8" },
  );
  assert.equal(inspect.status, 0);
  assert.ok(
    Object.values(JSON.parse(inspect.stdout)).every((value) => value === null),
    "API must have no host-published ports",
  );
  compose(["up", "-d", "--force-recreate", "--no-deps", "api"]);
  await wait("/health/ready", 200);
  const newContainer = compose(["ps", "-q", "api"]);
  assert.notEqual(oldContainer, newContainer);
  const after = await json(`/api/carts/${cartId}`);
  assert.deepEqual(after.items, before.items);
  assert.equal(after.totalMinor, before.totalMinor);
  results.checks.push(
    "API container replacement retained cart/items/pricing in named volume; API is unpublished",
  );

  compose([
    "exec",
    "-T",
    "api",
    "node",
    "-e",
    "fetch('http://127.0.0.1:3001',{signal:AbortSignal.timeout(1000)}).then(()=>process.exit(1)).catch(e=>process.exit(e.cause?.code==='ECONNREFUSED'?0:1))",
  ]);
  faulted = true;
  compose(["up", "-d", "--force-recreate", "--no-deps", "frontend"], "3001");
  await wait("/", 200);
  const staticStatus = (await response("/")).status;
  const journey = await response("/api/products");
  const readiness = await response("/health/ready");
  assert.equal(staticStatus, 200);
  assert.equal(journey.status, 503);
  assert.equal(readiness.status, 503);
  const error = await journey.json();
  assert.equal(error.code, "UPSTREAM_UNAVAILABLE");
  assert.ok(error.requestId);
  results.fault = {
    actor: "local deterministic test script",
    observedAt: new Date().toISOString(),
    requestId: error.requestId,
    correctPort: 3000,
    wrongPort: 3001,
    staticStatus,
    journeyStatus: journey.status,
    readinessStatus: readiness.status,
  };
  results.checks.push(
    "actual wrong-port fault: static route healthy, API journey/readiness failed safely",
  );
} finally {
  if (faulted)
    compose(["up", "-d", "--force-recreate", "--no-deps", "frontend"]);
  await wait("/health/ready", 200);
  if (cartId) {
    const recoveryResponse = await response(`/api/carts/${cartId}`);
    assert.equal(recoveryResponse.status, 200);
    const recovered = await recoveryResponse.json();
    assert.equal(recovered.totalMinor, 28796);
    results.recovery = {
      verifiedAt: new Date().toISOString(),
      requestId: recoveryResponse.headers.get("x-request-id"),
      status: recoveryResponse.status,
      totalMinor: recovered.totalMinor,
    };
    assert.equal(
      (await response(`/api/carts/${cartId}`, { method: "DELETE" })).status,
      204,
    );
    assert.equal((await response(`/api/carts/${cartId}`)).status, 404);
  }
}
results.checks.push(
  "configuration restored; fresh request verified recovery; only test cart removed",
);
results.finished = new Date().toISOString();
mkdirSync(new URL("../test-results/", import.meta.url), { recursive: true });
writeFileSync(
  new URL("../test-results/container-smoke.json", import.meta.url),
  JSON.stringify(results, null, 2) + "\n",
);
console.log(JSON.stringify(results, null, 2));
