# M4C-C5 — G4H hosted TypeScript gate verification: preparation

Date: 2026-11-17 UTC. Base: `2b050a1` plus preserved uncommitted C5 work.
Authority: owner direction to prepare hosted verification of the
[G4 gate](m4c-c5-g4-typescript-syntax-gate-implementation.md) by modifying
**only the existing non-blocking SAST trial workflow**. The changes were
**prepared, not dispatched**:

* no `ci.yml` change;
* no application dependency or lockfile change;
* no change to the G2/G5 risk acceptance;
* no GitHub setting change, Azure work, commit or push.

Machine-readable record: [JSON](m4c-c5-g4h-hosted-gate-preparation.json).

## Workflow changes

In `.github/workflows/c5-sast-hosted-trial.yml`, still `workflow_dispatch` only,
`contents: read`, non-blocking and outside `ci.yml`, the new steps are inserted
after the runner facts and **before any download, image build or container**:

1. **`actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38`**, the same
   pin `ci.yml` already reviewed, with only `node-version: "24.22.2"`. That
   equals `apps/octocat-supply/.node-version`. There is no cache, registry or
   token option.
2. **`npm ci --ignore-scripts`** in `apps/octocat-supply`. It installs from the
   existing lockfile with npm's integrity verification and no lifecycle scripts.
   The only environment settings are `NPM_CONFIG_AUDIT`, `NPM_CONFIG_FUND` and
   `NPM_CONFIG_UPDATE_NOTIFIER` (all `false`).
3. **TypeScript preflight:**
   `hosted_trial.py typescript-preflight --node "$(command -v node)"`. It
   requires the provisioned Node to report **exactly** `v24.22.2`, then runs the
   G4 gate on the host. The compiler is checked against the manifest, the lock
   version, the resolved URL, the sha512 integrity and the file hashes, and the
   self-test runs. **Any failure exits 2, 3 or 4 and the job stops before the
   wheel download, image build or any container.**
4. `container-run` passes the same `--node "$(command -v node)"`. The driver
   re-checks the exact Node version and re-runs the host gate with this run's
   nonce before the hardened container starts.

Unchanged:

* the confirmation guard;
* the hash-locked wheel download, container build, offline install and the
  hardened `--network none` scan container (still no Node in the image);
* the summary, which runs on `always()`;
* the **exact six-file artifact allowlist**. The attestation, raw reports and
  `node_modules` are never uploaded.

**Why `--node` is explicit:** the harness otherwise looks in fixed locations
such as `/usr/local/bin/node`. On GitHub runners that is the image's own
preinstalled Node, not the `setup-node` tool-cache Node, so the pinned binary is
passed explicitly and version-checked.

## Supporting changes

* **`scripts/sast/hosted_trial.py`:**
  * new `pinned_node`, which requires an absolute executable path reporting
    exactly the `.node-version`;
  * new `typescript-preflight` subcommand;
  * `container-run --node`, checked before the gate, before Docker and before
    the image ID is read.
* **`scripts/sast/check_trial_workflow.py`** (policy), which now requires:
  * exactly one pinned `setup-node` whose only option is `node-version` equal to
    `.node-version`;
  * exactly one npm command, `npm ci --ignore-scripts`, from
    `apps/octocat-supply`, with only the reviewed `NPM_CONFIG_*` settings;
  * a preflight and `container-run` that both pass the provisioned Node;
  * the order setup-node → npm ci → preflight → download → build → install →
    scan;
  * no `GITHUB_PATH`/`GITHUB_ENV` writes, and no `npx`, yarn, pnpm,
    `npm install`, `npm exec` or `npm run`;
  * an upload list of **exactly** the six reviewed files.
* **Tests:**
  * `test_trial_workflow.py`: 7 new G4H tests (22 in total). An existing
    step-swap test now locates steps by content instead of position, which keeps
    its original intent.
  * `test_container_trial.py`: 3 new driver tests (14 in total).

## Verification (local)

| Check | Result |
| --- | --- |
| `actionlint` 1.7.12 | Pass |
| Trial-workflow policy validator | PASS |
| Workflow tests | **22/22**: Node pin, version and options; npm weakening or extras; preflight and scan without the pinned Node; any reordering after container work starts; `GITHUB_PATH`/`GITHUB_ENV` injection; allowlist add, drop, reorder or private path |
| Driver tests | **14/14**: exact-version Node check; preflight failing closed with no gate run under an unpinned Node and no Docker call; `container-run` running nothing under an unpinned Node |
| Full SAST suite, real engine (macOS) | **87/87**. Without the engine: 57 pass, 30 explicitly skipped |
| Delivery tests, repository checks, `git diff --check`, untracked whitespace, gitleaks | Pass |
| Preflight on the real repository with the local Node v22.17.1 | **Exit 2**: "node runtime v22.17.1 differs from pinned v24.22.2". A relative `node` path also gives exit 2 |
| Simulated positive path (disposable copy pinned to the local Node) | Preflight exit 0 (49 parsed, 5 rejected). Real `container-run --node` with the hardened Linux container: host gate passed, **exit 0, clean** |

**Not verified locally:**

* **Node 24.22.2:** downloading the official binary was blocked by the
  permission system, and was not worked around.
* **`npm ci --ignore-scripts`:** not run, because it needs registry access.

Both are exercised only by the hosted run.

## Proposed hosted verification procedure (requires owner authorisation)

1. **Commit:** the owner reviews and commits the changed files, so that `main`
   contains them. Nothing is committed here.
2. **Dispatch:** from the GitHub Actions UI, dispatch `C5-F4R hosted SAST
   feasibility trial` with `confirm = run-c5-f4-hosted-trial` and a new
   `authorization_reference`. This is the only trigger.
3. **Expected step outcomes:**
   * `setup-node` reports Node **v24.22.2**;
   * `npm ci --ignore-scripts` succeeds with no lifecycle scripts run;
   * the preflight prints
     `typescript-preflight: ok (node 24.22.2; typescript gate: pass (49 files parsed, 5 malformed controls rejected; typescript 6.0.3, node v24.22.2) …)`;
   * download, build and install are as in run 43478654843;
   * `container-run` prints the host gate pass, and then the in-container
     harness reports `typescript gate: pass (host-attestation; 49 files parsed, 5 malformed controls rejected …; re-verified after scan)`
     and exit 0.
4. **Acceptance checks on the downloaded artifact,** verified against its
   digest:
   * exactly six files;
   * `container-run.json` `typescript_gate.exit` is 0;
   * `c5-summary.json` `typescript_syntax_gate` has `mode`
     `host-attestation`, `typescript` `6.0.3`, `node` `v24.22.2`, `accepted` 49,
     `rejected_controls` 5 and `compiler_sha256` `56917765…2e39`;
   * `hosted-trial.json` `input_sha256sum` matches the committed files;
   * no `sast-private` content is present.
5. **Failure handling:** any preflight failure ends the job before an image or
   container exists. The summary then reports missing evidence (exit 7).
   Record that as a fail-closed result, not a waiver.
6. **On success:** record G4 as **verified on the hosted runner** in a closeout
   document. G4 can then close for TypeScript. JavaScript stays out of scope,
   and E04 still needs the lint/typecheck `needs:` dependency.

## Limits and residual risk

* `npm ci` downloads the whole application dependency tree on the runner. Its
  integrity is enforced against the lockfile, and lifecycle scripts are
  disabled. It runs outside the scan container, as `ci.yml` already does.
* The trial timeout stays 20 minutes. The extra steps are expected to add a
  few minutes; this has not been measured on a hosted runner.
* The local positive path used Node 22.17.1 with a copy-local pin, not 24.22.2.
* G2 and G5 acceptances are unchanged. Mandatory CI (E04), E05, E06 and release
  remain NO-GO.

## Changed files (G4H)

* Modified:
  * `.github/workflows/c5-sast-hosted-trial.yml`;
  * `scripts/sast/hosted_trial.py`;
  * `scripts/sast/check_trial_workflow.py`;
  * `tests/security/sast/test_trial_workflow.py`;
  * `tests/security/sast/test_container_trial.py`;
  * status lines in `README.md`, `AGENTS.md`, `docs/capability-status.md` and
    `docs/milestones/m4c-c5-sast-plan.md`.
* New: this document and its JSON record.
* Unchanged:
  * `ci.yml`;
  * the application `package.json`, lockfile and `.node-version`;
  * `requirements-sast-*.txt`;
  * `security/sast/typescript-gate.json`;
  * the harness and gate script;
  * the Dockerfile;
  * both SBOMs and all G2/G5 decision records.
