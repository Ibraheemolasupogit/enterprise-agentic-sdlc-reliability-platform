# M4C-C5 — G4 TypeScript syntax gate: implementation

Date: 2026-11-17 UTC. Base: `2b050a1` plus preserved uncommitted C5 work.
Authority: owner direction to implement the
[G4 assessment](m4c-c5-g4-typescript-syntax-gate-assessment.md) recommendation
using the pinned TypeScript 6.0.3. There was no change to `ci.yml`, the trial
workflow, dependencies, lockfiles, the scan image, GitHub settings or Azure, no
dispatch, and no commit or push. Machine-readable record:
[JSON](m4c-c5-g4-typescript-syntax-gate-implementation.json).

**Status:**

* **Locally:** implemented and verified on macOS. On Linux, the
  host-attestation path is verified through the hardened container.
* **Hosted trial:** not yet runnable, and it fails closed (see below).
* **G4:** remains open until it is verified on a hosted runner.
* **E04, E05, E06 and release:** remain NO-GO.

## What changed

* **Gate script** [`scripts/sast/ts_syntax_gate.mjs`](../../scripts/sast/ts_syntax_gate.mjs)
  (new):
  * loads the compiler **from the exact bytes it hashes**;
  * parses each target from the exact bytes it hashes (strict UTF-8, no
    symlinks, no path escape);
  * is syntax-only (no resolution, no default library, no emit);
  * prints only TS codes and positions, never message text.
* **Compiler pin** [`security/sast/typescript-gate.json`](../../security/sast/typescript-gate.json)
  (new):
  * it must equal the application lockfile entry: version, resolved URL and
    sha512 integrity;
  * the hashes of `package.json` and `lib/typescript.js` come from the registry
    tarball, whose sha512 equals the lock integrity;
  * all 140 files in that tarball are byte-identical to the installed package.
* **Harness** (`scripts/sast/feasibility.py`):
  * The gate runs after the Python `ast` gate and **before isolation, controls
    or any Semgrep run**.
  * It checks exactly the TypeScript files given to Semgrep: 42 source files
    and 7 annotated control fixtures must parse.
  * As a runtime **self-test**, the 2 malformed and 3 parser-gap TypeScript
    fixtures must be rejected.
  * Every validated file is **re-hashed after all Semgrep runs**.
* **Container mode** (no Node in the image):
  * the harness requires `--ts-nonce`;
  * it accepts only a host attestation for that nonce;
  * the attestation must have matching manifest, gate and compiler hashes, the
    exact target set, and unchanged per-file hashes.
* **Driver** (`scripts/sast/hosted_trial.py`):
  * `container-run` runs `--typescript-gate-only` on the **host before any
    container starts**. Gate exits 2, 3 and 4 pass through; anything else
    becomes 3. A failed gate never starts a container.
  * The in-container `run` passes the run nonce.
  * `run --node/--typescript-dir` work in auto mode only.
* **Tests:**
  * new `tests/security/sast/test_typescript_gate.py`;
  * two new G4 driver cases in `test_container_trial.py`;
  * E03 adapted, without weakening (below).

**Exit codes** keep the existing contract:

| Exit | Meaning for the gate |
| --- | --- |
| 2 | Compiler or Node unavailable, lockfile/manifest/compiler mismatch, bad, stale or foreign attestation, target-set mismatch, or CLI misuse |
| 3 | Syntax error (path, TS code, position), gate crash, timeout or inconsistent output, or a file changed during or after validation |
| 4 | Self-test failed: a malformed control was accepted |

## Results

| Check | Result |
| --- | --- |
| Full SAST suite, macOS, real engine | **77/77**: 15 workflow, 11 container/driver, 8 G2 guard, 14 G4 gate, 29 E03 |
| Without engine | 47 pass, 30 explicitly skipped |
| G4 gate tests | **14/14** (details below) |
| F3 34-case matrix, macOS | **34/34**. **T03 (original G4 gap) now exit 3** (TS1136); previously exit 0 (known miss). T02 is now caught by the gate before Semgrep |
| Real Docker, hardened `--network none` Linux container | 5 scenarios (below) |
| G2 environment and isolation guard (unchanged file) | **8/8 on macOS and 8/8 inside the hardened Linux container** |
| Harness on the real repository (macOS) | Exit 0: 49 files parsed, 5 malformed controls rejected; controls pass; 73 source targets, 0 findings |
| Repository checks, `git diff --check`, untracked whitespace, trial-workflow validator, `actionlint`, delivery tests, `node --check`, gitleaks | Pass |

The 14 G4 gate tests cover:

* **Positive:** the repository passes, the target set is exact, and the gate
  works inside the sandbox wrapper.
* **Syntax:** the 4 G4 cases are rejected, and TSX and test files are gated.
* **Mutation regression:** 210 mutants (42 files × 5 invalid endings); 0 missed
  and 0 false positives.
* **Compiler, lockfile and manifest:** compiler tampering, version change,
  symlink and absence; lockfile version, integrity or URL drift; manifest
  unsafe or missing.
* **Node:** missing, too old, garbage output, error output.
* **Forged results:** 7 cases, including self-test exit 4.
* **Race and attestation:** the post-scan re-check; attestation round-trip and
  9 tampering cases.
* **CLI and end-to-end:** CLI mode rules; and a malformed file stops the real
  harness with **exit 3 and zero Semgrep processes**.

Real-Docker scenarios on disposable copies, driving `container-run` with the
existing hardened image:

| Scenario | Result |
| --- | --- |
| Clean copy | **0**. Host gate passed; in-container harness verified the host attestation (49 files) and scanned |
| Malformed TypeScript | **3** on the host. **No container started** |
| Compiler not installed | **2** on the host. **No container started** |
| File changed after the host gate | **3** in the container: "typescript target changed after host validation" |
| Attestation with a foreign nonce | **2** in the container: "stale or foreign (nonce mismatch)" |

**E03 adaptations, with protections preserved:**

* The harness invocation passes the hash-verified compiler and Node (auto
  mode), or a host attestation (container mode).
* The engine parse-error canary test now uses a malformed `.jsx` file, which is
  not TypeScript-gated, so Semgrep's parse-error path is still exercised.
* The new `CanaryInTypeScriptGate` test shows a malformed `.tsx` canary stopping
  before Semgrep, with the canary absent from the console and every artifact.

## Race window

* **Bound at validation:** each file's SHA-256 is computed by Python before the
  Node gate runs, and by Node on the bytes it actually parses. The two must
  match.
* **Checked before the scan (container mode):** the in-container harness
  re-checks the hashes, and any added, removed or changed TypeScript file fails.
* **Checked after the scan (both modes):** all files are re-hashed after every
  Semgrep run.
* **Remaining race, documented:** a change that is reverted *within* the scan
  window (A to B and back to A, before the post-scan re-hash) is not
  detectable.

## Requirement for E04 (not implemented)

Before any mandatory SAST CI:

* the SAST job must **hard-depend (`needs:`) on the existing mandatory
  `lint`/`typecheck` job**, and must not run if that job fails;
* the job must provide the lock-pinned compiler for the host gate (`npm ci`
  from `apps/octocat-supply/package-lock.json`).

`ci.yml` is unchanged.

## Hosted trial impact (owner decision needed)

The dispatch-only trial workflow does not install the application lockfile. The
host gate will therefore **fail closed with exit 2** ("pinned compiler
unavailable") before any container starts. Running the trial again needs an
owner-authorised workflow step, such as a pinned `setup-node` plus
`npm ci --ignore-scripts` from the application lockfile. The workflow is
unchanged.

## Limits

* The Node gate itself was verified on macOS with Node 22.17.1. The pinned Node
  is 24.22.2. No Linux Node image existed locally and none was pulled.
* Linux evidence covers the host-attestation path through the hardened
  container, not a Linux-hosted Node gate.
* The E03 container-mode suite and the Linux 34-case matrix were not re-run.
  Container mode now needs per-case host attestations.
* JavaScript (`.js`, `.jsx`, `.mjs`, `.cjs`) is not syntax-gated, and
  `.d.mts`/`.d.cts` stay excluded.
* Type errors and early errors remain with the CI typecheck (the E04
  requirement).
* The host-side gate for container trials runs without network isolation,
  because hosted runners lack unprivileged user namespaces. It only parses
  local files.

## Changed files (G4 implementation)

* New:
  * `scripts/sast/ts_syntax_gate.mjs`;
  * `security/sast/typescript-gate.json`;
  * `tests/security/sast/test_typescript_gate.py`;
  * this document and its JSON record.
* Modified:
  * `scripts/sast/feasibility.py`;
  * `scripts/sast/hosted_trial.py`;
  * `tests/security/sast/test_container_trial.py`;
  * `tests/security/sast/test_robustness_e03.py`;
  * status lines in `README.md`, `AGENTS.md`, `docs/capability-status.md` and
    `docs/milestones/m4c-c5-sast-plan.md`.
* Unchanged (hash-checked):
  * `ci.yml` and the trial workflow;
  * the application `package.json` and lockfile;
  * both Python locks;
  * the Dockerfile, `toolchain.json`, `controls.json`;
  * the G2 guard test;
  * both SBOMs.
