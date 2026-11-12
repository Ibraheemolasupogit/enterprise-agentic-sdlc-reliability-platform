// Execute adversarial contracts on disposable copies, never edit the worktree.
import {
  cpSync,
  mkdtempSync,
  readFileSync,
  writeFileSync,
  rmSync,
  symlinkSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const root = resolve(".");
const folder = mkdtempSync(join(tmpdir(), "morrow-c3-mutations-"));
const mutations = [
  {
    name: "nonce-omission",
    file: "frontend/src/oidcSession.ts",
    from: "manager.signinRedirect({ nonce })",
    to: "manager.signinRedirect({})",
    test: "frontend/test/OidcProtocol.test.tsx",
    expected: "P01/P04",
  },
  {
    name: "id-verification-bypass",
    file: "frontend/src/oidcSession.ts",
    from: "const verified = await initialized.verify(user, pending.nonce);",
    to: "const verified = {issuer:this.config.authority, subject:String(user.profile.sub), expiresAt:user.expires_at};",
    test: "frontend/test/IdToken.test.tsx",
    expected: "P06",
  },
  {
    name: "early-session-publication",
    file: "frontend/src/oidcSession.ts",
    from: "const user = await manager.signinRedirectCallback(raw);",
    to: 'const user = await manager.signinRedirectCallback(raw); this.publish({phase:"signedIn"});',
    test: "frontend/test/OidcProtocol.test.tsx",
    expected: "P06",
  },
  {
    name: "external-api-target",
    file: "frontend/src/api.ts",
    from: 'if (\n    !path.startsWith("/api/") ||',
    to: 'if (false && (\n    !path.startsWith("/api/") ||',
    test: "frontend/test/ApiSession.test.tsx",
    expected: "P13",
    finish: true,
  },
];
try {
  for (const mutation of mutations) {
    const dir = join(folder, mutation.name);
    for (const path of [
      "frontend",
      "test",
      "api/fixtures",
      "vitest.config.ts",
      "tsconfig.tests.json",
      "package.json",
    ])
      cpSync(join(root, path), join(dir, path), {
        recursive: true,
        filter: (p) => !p.includes("/frontend/dist"),
      });
    symlinkSync(join(root, "node_modules"), join(dir, "node_modules"), "dir");
    const file = join(dir, mutation.file);
    let code = readFileSync(file, "utf8");
    if (!code.includes(mutation.from))
      throw new Error("Mutation no longer matches reviewed source.");
    code = code.replace(mutation.from, mutation.to);
    if (mutation.finish)
      code = code.replace(
        '!new URL(path, location.origin).pathname.startsWith("/api/")\n  )',
        '!new URL(path, location.origin).pathname.startsWith("/api/")\n  ))',
      );
    writeFileSync(file, code);
    const report = join(dir, "result.json");
    const result = spawnSync(
      process.execPath,
      [
        join(root, "node_modules/vitest/vitest.mjs"),
        "run",
        "--project",
        "web",
        mutation.test,
        "--reporter=json",
        "--outputFile",
        report,
      ],
      { cwd: dir, encoding: "utf8", timeout: 60000 },
    );
    // A compile/discovery/setup error is not evidence of assertion sensitivity.
    const data = JSON.parse(readFileSync(report, "utf8"));
    const failed = data.testResults
      .flatMap((t) => t.assertionResults)
      .filter(
        (a) => a.status === "failed" && a.fullName.includes(mutation.expected),
      );
    if (result.status !== 1 || !failed.length)
      throw new Error(
        "Mutation did not fail its intended behavioral assertion.",
      );
    console.log(
      JSON.stringify({
        mutation: mutation.name,
        rejected: true,
        failedContract: mutation.expected,
        assertions: failed.length,
      }),
    );
  }
} finally {
  rmSync(folder, { recursive: true, force: true });
}
