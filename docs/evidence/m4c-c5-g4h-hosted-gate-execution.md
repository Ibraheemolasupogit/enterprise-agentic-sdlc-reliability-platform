# M4C-C5 — G4H hosted TypeScript gate verification: execution and G4 closeout

Date: 2026-11-18 UTC. Commit: `2e0bd258a6b217572e86355a460d86dc5b479ce2`
(`origin/main`).

Authority:

* the owner's per-run authorisation **"C5-G4H U1E run-1 2026-11-18"**,
  executed under the adopted toolchain ([U1E](m4c-c5-u1e-adoption-decision.md));
* the owner's decision on 2026-11-18 to **close G4 for TypeScript only**, based
  on this run.

Preparation: [G4H preparation](m4c-c5-g4h-hosted-gate-preparation.md).
Machine-readable record: [JSON](m4c-c5-g4h-hosted-gate-execution.json).

**Result: PASS, clean, exit 0. G4 is CLOSED for TypeScript. JavaScript remains
out of scope.**

* **Unchanged:** G2 and G5 remain **OPEN**. E04, E05, E06, release and
  redistribution remain **NO-GO**. The G5D and U1E decisions are unchanged.
* **Not done:** no commit, push, release or `ci.yml` change. The trial workflow
  received only the owner-approved cache hardening, applied after Run 1 (see the
  configuration comparison below).

## Pre-dispatch confirmation (2026-11-18T20:38:46Z)

| Check | Result |
| --- | --- |
| HEAD and `origin/main` | Both `2e0bd258a6b2…`; working tree clean |
| Concurrent trial | None in progress |
| Unchanged since `268bc75` | Workflow, driver and container |
| Consistency | 237/237 |
| OSV (335 SBOM v3 packages) | Only the 6 known **MODERATE** G2 GHSAs; no new, HIGH or CRITICAL advisory |
| CISA KEV (catalogue 2026.11.18) | 0 hits across 15 CVEs |
| Upstream | Semgrep 1.186.0 is the latest release |
| Stop conditions | G5D section 6 and U1E E5: none triggered |
| Expiry | 2026-12-17: valid |

## Run identity

| Item | Value |
| --- | --- |
| Run | **44393309563**, attempt 1. Dispatched once at 20:39:24Z; no retry; the only new trial run |
| Commit and ref | `2e0bd258a6b217572e86355a460d86dc5b479ce2`, `refs/heads/main`, event `workflow_dispatch` |
| Inputs | `confirm=run-c5-f4-hosted-trial`; `authorization_reference="C5-G4H U1E run-1 2026-11-18"` (recorded in `hosted-trial.json`) |
| Duration | Job 20:39:30Z → 20:41:26Z (about 2 minutes; timeout 20). All 13 workflow steps succeeded |
| Runner | GitHub-hosted, Ubuntu 24.04.5 LTS, image `ubuntu24/20261111.370`, kernel `7.0.0-1017-azure`, x86_64. `GITHUB_TOKEN`: `contents: read`, `metadata: read` |
| Artifact | `c5-f4r-hosted-sast-trial-44393309563-1`, ID 14469048127, 12,466 bytes. GitHub digest `sha256:388dc3baca1ba774e1a708514791aed36b45fca9d10ce0928af60c4cdf4e0cf8`. The downloaded archive's SHA-256 is **equal**. Retention is 7 days (expires about 2026-11-25) |

## Verification against the acceptance criteria

| Criterion | Result |
| --- | --- |
| Artifact contents | **Exactly the six allowlisted files.** No private report, raw engine output, `secret_hash`, Pro/Secrets fields, canary or credential pattern |
| `input_sha256sum` (11 trial inputs) | **Equal to the expected list for `2e0bd25`.** It includes `toolchain.json` `91f9a3d0…603d`, `requirements-sast-linux.txt` `a6472b78…fc25`, `feasibility.py` `f7690a9a…d0`, the workflow `0fc6f22d…b4b`, `ts_syntax_gate.mjs` `a91e8b91…e29` and `typescript-gate.json` `3f46c454…b67` |
| Node and `npm ci` | `setup-node` gave **`node: v24.22.2`**, npm 11.19.1. Node came from the runner image tool cache (`/opt/hostedtoolcache/node/24.22.2`). `npm ci --ignore-scripts` added 367 packages; no lifecycle scripts ran |
| Host TypeScript preflight (before any download, image or container) | `typescript-preflight: ok (node 24.22.2; … 49 files parsed, 5 malformed controls rejected; typescript 6.0.3, node v24.22.2)` |
| In-container TypeScript gate | **`host-attestation`**: pass, 49 accepted, 5 malformed controls rejected, TypeScript 6.0.3, Node v24.22.2, compiler `56917765…2e39`, re-verified after the scan. In `container-run.json`, the TypeScript gate exit is 0 |
| Semgrep | Version **1.186.0**; `semgrep_core_sha256` `dcaa53ef…1e68`, the U1E adopted hash |
| Toolchain | 67 distributions match `requirements-sast-linux.txt`; `pip check` passes; **3,310** RECORD files verified. Install stages venv, pip-install and pip-check are all 0. Image `sha256:6221d763…3b99`, amd64, user 1001:1001 |
| Isolation | `docker --network none` verified: only `lo` up (kernel fallback tunnels down), non-local IPv4/IPv6 unreachable, DNS fails, non-root, no capabilities, NoNewPrivs, seccomp filter, read-only root. Hardening flags: `--rm --platform linux/amd64 --pull never --network none --user 1001:1001 --read-only --cap-drop ALL --security-opt no-new-privileges=true --ipc none --pids-limit 512 --memory 3g --memory-swap 3g --cpus 2 --tmpfs /tmp:rw,nosuid,nodev,noexec,size=512m` |
| Controls | Pass: **59/64 as expected** (5 known misses, 0 missed); 23 catalogued fixtures; malformed fixtures rejected; **parser-gap drift 0** (all 4 still `engine_rejected: false`) |
| Source | **Clean: 73 targets, 0 findings.** 5 repetitions of 4.07, 3.94, 4.55, 7.35 and 4.37 s. Harness exit 0 in 31.4 s; peak child RSS 292,076 KiB. The inventory classified 265 files at `2e0bd25` |
| Non-blocking | `hosted-trial.json` has `non_blocking: true`. The workflow is dispatch-only and not referenced by `ci.yml` |
| Caching | **No cache written.** "Cache mode: write" is the job-level cache permission printed for every job. `setup-node` showed only its default `package-manager-cache: true` input, with no restore or save lines, and its post step logged only cleanup. The repository's Actions cache count is **0** after the run |

**Preserved copies** (session scratch only; not committed and not
redistributed):

| File | SHA-256 |
| --- | --- |
| `artifact.zip` | `388dc3ba…0cf8` |
| `job.log` | `3bed9cb1a754258ad4f8f01f8724b004bfa5589303b3d1122aca454d8cf2470c` |
| `c5-summary.json` | `f343efe652f4db5b6c2d8a102224e11f616f7f9ddfe7e7b78956c6f9e9f40359` |
| `container-image.json` | `64bbc00d169ad60aa118d41d5fdcecc63b137c32e7f70126836c27049790457a` |
| `container-install.json` | `a1997ab55ccea66703164ac188ac0e253c5289076c3d9968c966ff54f9a4d628` |
| `container-run.json` | `06d39d53e7a79bd0904dbed6498ce20058d49f161404aa883da518ab84db2b2b` |
| `hosted-runner-facts.json` | `a854182614f79ceadc6d0c9c0da076725ac545708e7be6ddd97b0b48395a65c2` |
| `hosted-trial.json` | `6ea5a9d3088984f05b228adba75fb01538558693fcf322b40686a7ef75e06556` |

## G4 closeout (owner decision, 2026-11-18)

**G4 is CLOSED for TypeScript.** The original G4 gap was malformed TypeScript
silently accepted by the engine. It is now closed by the pinned TypeScript
6.0.3 syntax gate, which:

* runs before any Semgrep process;
* uses a lock-verified compiler;
* has a runtime self-test;
* re-hashes every validated file after the scan;
* in container mode, accepts only a nonce-bound host attestation.

This is verified locally (G4 implementation; LT-U1 S4 14/14, including the
end-to-end test) and now on a GitHub-hosted runner with the pinned Node
24.22.2 (this run).

**Not covered by the closure:**

* JavaScript (`.js`, `.jsx`, `.mjs`, `.cjs`) is **not** syntax-gated and remains
  **out of scope**. `.d.mts`/`.d.cts` stay excluded.
* Type errors and early errors are not syntax errors. They remain with the CI
  typecheck. The **E04 requirement** is unchanged: the SAST job must hard-depend
  (`needs:`) on the mandatory lint/typecheck job.
* The documented race is unchanged: a change reverted within the scan window
  (A → B → A) is not detectable.

## Limitations and residual risks

* **Single hosted run.** `--repeat 5` applied to the source scan only.
* **Node origin.** Node 24.22.2 came from the GitHub runner image's tool cache.
  The driver verified that the version is exactly the pin, but provenance rests
  on the runner image.
* **Network during the host gate.** The host-side TypeScript gate on the runner
  runs without network isolation (hosted runners lack unprivileged user
  namespaces). It only parses local files.
* **Implicit caching default.** `setup-node` v6 enables package-manager caching
  by default; it did not engage here. The workflow does not disable it
  explicitly **in Run 1's configuration**. The hardening below was approved and
  applied after Run 1.
* **CI context.** Mandatory CI at `2e0bd25` (run 44380044262) **passed**
  because GitHub **withdrew** GHSA-fc5q-39xc-vjpf (picomatch) at
  2026-11-18T15:38:56Z, not because of a repository change. `npm audit` still
  reports **9 moderate** minimatch findings (GHSA-g3hv-75wg-m249), below the
  unchanged `--audit-level=high` threshold, and not waived.
* **Unchanged decisions:** G2 (V1, V2) and G5 (V3–V6, V8) are open, under the
  U1E conditional acceptance until 2026-12-17. G5D section 7 (minimum before
  E04) is unmet.
* **Artifact retention.** The artifact expires after 7 days. This record and
  the scratch copies hold the hashes.

## Run 1 configuration vs. hardened configuration

Run 1 verified the workflow **as committed at `2e0bd25`**. The hardening below
was approved and applied **after** Run 1 (2026-11-18, uncommitted at the time
of writing). Run 1's evidence and hashes are **unchanged** and remain the G4
closure evidence for `2e0bd25`.

| Item | Run 1 verified configuration (`2e0bd25`) | Hardened configuration (current working tree) |
| --- | --- | --- |
| `setup-node` `with:` | `node-version: "24.22.2"` only (the action's default `package-manager-cache: true` applied; no cache engaged) | `node-version: "24.22.2"` and **`package-manager-cache: false`** |
| Trial workflow SHA-256 | `0fc6f22dafec175426ff4dff1d910077dbbe182a86dfc155c60300cdf7fabb4b` (in Run 1's `input_sha256sum`) | `d445ce5c19e76e54226bb57db7d4fbbac5002384c48a0a1687b4b6b9342bf684` |
| `check_trial_workflow.py` SHA-256 | `587a54ed099f5f11ab3a97609070e5b93b87c40806b7ffeb3ef53ef50d0ea6d0` | `cb9c134b8faa6edb7c0618d57d5c1c088017ec9356527db576f046c7e9e887b4` |
| `test_trial_workflow.py` SHA-256 | `5059309ec4bfbf6a20166e5479963bd3b5328f8734b7be30c4993928845dc2c9` | `aa9a71a36e97d11c96118c3c293dd062ca5749ee0133067acd67a0ffae59f0a5` |
| Other 10 trial inputs | As in Run 1's `input_sha256sum` | **Identical** to Run 1 |
| Verified on a hosted runner | **Yes** (Run 1) | **No.** Validated locally only; the next owner-authorised trial confirms it |

## Hardening (APPLIED 2026-11-18, owner-approved; originally proposed below)

**Aim:** make the "no caching" property explicit, rather than relying on the
absence of a root `package.json` for `setup-node`'s default.

Patch: scratch `g4h-hardening.patch`, SHA-256
`9f4c690133379736d499c40699d3acea04bece32e31f6d1972ea5450ba7b7241`. It
changes three files:

1. **`.github/workflows/c5-sast-hosted-trial.yml`:** adds
   `package-manager-cache: false` under the pinned `setup-node` step's `with:`.
   That `setup-node` version (`24997072…`) already lists the input, as Run 1's
   log shows.
2. **`scripts/sast/check_trial_workflow.py`:** the validator now requires
   `with == {"node-version": <.node-version>, "package-manager-cache": "false"}`.
   It loads YAML with `BaseLoader`, so `false` is the string `"false"`. Every
   other key, including `cache`, `registry-url`, `token` and `check-latest`,
   is still rejected.
3. **`tests/security/sast/test_trial_workflow.py`:** the current-layout test
   expects the new `with`. The loose-setup-node test also rejects the key being
   removed, and the values `"true"`, `""`, `"False "`, `"0"` and `"npm"`.

**Prototype validation** (disposable copy, before applying):

| Check | Result |
| --- | --- |
| `actionlint` and the validator (hardened workflow with hardened validator) | Pass |
| Trial-workflow tests | Pass |
| Engine-free SAST suite, `env -i`, compiler available | 88 run: 58 pass, 30 skipped |
| Hardened validator against the **current** workflow | **Rejected**: "package-manager-cache: false" required |
| **Current** validator against the hardened workflow | **Rejected** (its exact-`with` rule). The two files must change together |

**Effect on hashes and bindings:**

| File | Current SHA-256 | Hardened SHA-256 | Bound where |
| --- | --- | --- | --- |
| Trial workflow | `0fc6f22d…b4b` | `d445ce5c19e76e54226bb57db7d4fbbac5002384c48a0a1687b4b6b9342bf684` | A **hosted-trial input** (`INPUT_HASHES`). Also point-in-time records: G4H preparation JSON, A1 X1 table (withdrawn), U1 JSON "unchanged" list, and Run 1's immutable `input_sha256sum` |
| `check_trial_workflow.py` | `587a54ed…6d0` | `cb9c134b8faa6edb7c0618d57d5c1c088017ec9356527db576f046c7e9e887b4` | G4H preparation JSON and A1 X1 table (point-in-time). Not a trial input |
| `test_trial_workflow.py` | `5059309e…c2c9` | `aa9a71a36e97d11c96118c3c293dd062ca5749ee0133067acd67a0ffae59f0a5` | G4H preparation JSON (point-in-time) |

* **No live binding breaks.** The U1E section 3 hashes (toolchain, locks,
  harness, guard, controls, rules, SBOM v3, inventory) do not include these
  files. The U1 consistency checks do not cover them. The historical records
  stay accurate for their dates and need no edit.
* **What changes:** the **next** trial's expected `input_sha256sum`. The
  workflow entry becomes `d445ce5c…f684`, and the next per-run authorisation
  must use the updated list.
* **G5D stop condition 4** (hardening or allowlist change *without owner
  review*) is not tripped, provided the owner reviews and approves the patch.
  The change narrows behaviour and does not alter the harness, isolation or
  allowlist.

**Is another hosted trial necessary?** (assessed before applying; still valid)

* **Not for the G4 closure.** The hardening touches neither the gate, the
  harness, the toolchain nor the container. Run 1 remains the closure evidence
  for commit `2e0bd25`.
* **For the hardened workflow itself:** it has not run on a hosted runner. The
  change is one documented input that this `setup-node` version accepts, and
  local validation passes. A hosted confirmation is **recommended but not
  required**. The next owner-authorised trial would provide it: check that the
  `setup-node` input echo shows `package-manager-cache: false`, that there are
  no cache restore or save lines, and that the repository cache count stays 0.

## Changed files (this record)

* **New:** this document and its JSON record.
* **Modified (status lines only):** `AGENTS.md`, `README.md`,
  `docs/capability-status.md` and `docs/milestones/m4c-c5-sast-plan.md`.
* **Modified by the approved hardening:** `.github/workflows/c5-sast-hosted-trial.yml`,
  `scripts/sast/check_trial_workflow.py` and
  `tests/security/sast/test_trial_workflow.py`. These are exactly the reviewed
  patch (SHA-256 `9f4c6901…7241`), and the resulting hashes equal the reviewed
  prototype.
* **Not changed:** `ci.yml`, the driver, the harness, the container, the
  toolchain and locks, U1E, all G2/G5/E04–E06 decisions, and Run 1's evidence
  and hashes.
