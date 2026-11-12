import { readFileSync, readdirSync, existsSync } from "node:fs";
import { resolve, join } from "node:path";
import { fileURLToPath } from "node:url";
import OidcReporter from "./oidc-reporter.mjs";

export function assertCaptureOff(
  config,
  env = process.env,
  args = process.argv,
) {
  const fail = () => {
    throw new Error("Unsafe OIDC capture configuration; refusing execution.");
  };
  if (
    [
      "DEBUG",
      "PWDEBUG",
      "DEBUGPWSERVER",
      "PLAYWRIGHT_TRACE",
      "PW_TEST_TRACE",
    ].some((k) => env[k]) ||
    args.some((a) => /^--(?:trace|reporter|debug|ui)(?:=|$)/.test(a)) ||
    config.preserveOutput !== "never"
  )
    fail();
  const reporters = config.reporter;
  if (
    !Array.isArray(reporters) ||
    reporters.length !== 1 ||
    reporters[0].length > 2 ||
    (reporters[0][1] && Object.keys(reporters[0][1]).length > 0) ||
    !/(?:^|\/)scripts\/oidc-reporter\.mjs$/.test(reporters[0][0])
  )
    fail();
  const check = (use) => {
    if (
      use.trace !== "off" ||
      use.video !== "off" ||
      use.screenshot !== "off" ||
      use.serviceWorkers !== "block" ||
      use.storageState ||
      use.ignoreHTTPSErrors ||
      use.recordHar ||
      ["recordHar", "recordVideo", "storageState", "ignoreHTTPSErrors"].some(
        (k) => use.contextOptions?.[k],
      )
    )
      fail();
  };
  check(config.use ?? {});
  for (const project of config.projects ?? [])
    check({ ...config.use, ...project.use });
}
export function assertSanitized(text, canaries) {
  if (canaries.some((c) => c && text.includes(c)))
    throw new Error("Sensitive auth canary detected; evidence rejected.");
}

async function main() {
  const { default: config } = await import("../playwright.oidc.config.ts");
  assertCaptureOff(config);
  for (const mutation of [
    "trace",
    "video",
    "screenshot",
    "storageState",
    "ignoreHTTPSErrors",
    "recordHar",
  ]) {
    let rejected = false;
    try {
      assertCaptureOff(
        { ...config, use: { ...config.use, [mutation]: "on" } },
        {},
        [],
      );
    } catch {
      rejected = true;
    }
    if (!rejected) throw new Error("Capture negative control did not fail.");
  }
  for (const change of [
    { ...config, reporter: [["list"]] },
    { ...config, preserveOutput: "always" },
    { ...config, projects: [{ use: { trace: "on" } }] },
  ]) {
    let rejected = false;
    try {
      assertCaptureOff(change, {}, []);
    } catch {
      rejected = true;
    }
    if (!rejected) throw new Error("Capture negative control did not fail.");
  }
  const privateVector = JSON.parse(
    readFileSync("api/fixtures/rfc7515-rsa.json", "utf8"),
  );
  const canaries = [
    "non-live-code-canary",
    "non-live-verifier-canary",
    "non-live-state-canary",
    "non-live-nonce-canary",
    "non-live-token-canary",
    "non-live-subject-canary",
    privateVector.d,
  ];
  for (const canary of canaries) {
    let rejected = false;
    try {
      assertSanitized(canary, canaries);
    } catch {
      rejected = true;
    }
    if (!rejected)
      throw new Error("Auth canary negative control did not fail.");
  }
  const output = [],
    original = console.log;
  try {
    console.log = (value) => output.push(String(value));
    const reporter = new OidcReporter();
    reporter.onError(new Error(canaries.join(" ")));
    reporter.onTestEnd(
      { title: "P14 " + canaries.join(" ") },
      { status: "failed", error: { message: canaries.join(" ") } },
    );
  } finally {
    console.log = original;
  }
  assertSanitized(output.join("\n"), canaries);
  for (const name of readdirSync("frontend/dist/assets").filter((n) =>
    n.endsWith(".js"),
  ))
    assertSanitized(
      readFileSync(join("frontend/dist/assets", name), "utf8"),
      canaries,
    );
  const folder = "test-results/oidc";
  if (
    existsSync(folder) &&
    readdirSync(folder).some((n) => n !== ".last-run.json")
  )
    throw new Error("Unexpected retained OIDC artifacts.");
  console.log(
    "PASS: OIDC capture-off profile, unsafe capture mutations, canary rejection, sanitized reporter and built-asset checks.",
  );
}
if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
)
  void main().catch(() => {
    console.error(
      "FAIL: OIDC capture guard rejected configuration or evidence.",
    );
    process.exitCode = 1;
  });
