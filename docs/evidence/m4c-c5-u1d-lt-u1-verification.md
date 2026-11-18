# M4C-C5 — U1D: LT-U1 local verification of Semgrep 1.186.0 (second, fresh run)

Date: 2026-11-18 UTC, from 15:38:48Z to 15:48:51Z. Base: commit `268bc75`,
plus the uncommitted C5-U1/U1B/U1C work, including the owner-approved G2 guard
fixes.

Plan: [U1B section 4](m4c-c5-u1b-pre-execution-assurance.md). Previous run:
[U1C](m4c-c5-u1c-lt-u1-execution.md), stopped at S2. Machine-readable record:
[JSON](m4c-c5-u1d-lt-u1-verification.json).

**Result: ALL STAGES S0–S8 PASSED.** There were no retries, no failed gates and
no security deviations.

* **Verified locally:** Semgrep CE 1.186.0, on macOS arm64 and in the hardened
  Linux `--network none` container on this workstation.
* **Not adopted.** No hosted dispatch, commit, push or release.
* **Unchanged:** G5D D1–D6. G2, G4 and G5 remain **OPEN**. E04, E05, E06,
  release and redistribution remain **NO-GO**. Mandatory CI stays red
  (picomatch), not waived.

## Authorisation

* **Owner authorisation:** one fresh LT-U1 run, expiring 2026-11-20.
* **Owner decision for this run only:** the existing G2 findings (V1, V2) and
  the G5 findings V3–V6 and V8 are accepted under the documented hardened
  controls.
* That decision is now **consumed**. It is not adoption and not a waiver.

## Stage results

| Stage | Expected | Result |
| --- | --- | --- |
| **S0** (no engine) | Clean recheck; 237/237; engine-free suite OK; snapshot | **PASS.** OSV: 335 unique queries, only the 6 known **MODERATE** G2 GHSAs, **0 new, 0 HIGH/CRITICAL**. CISA KEV 2026.11.17 (1,782 entries): **0 hits** across 15 CVEs. Upstream: Semgrep 1.186.0 and `cryptography` 50.0.2 are the latest; the `semgrep/ocaml` `5.4.0-semgrep` head is `eb2978e6` (already reviewed). Consistency **237/237**. Suite 88 run: 58 pass, 30 skipped (engine). No sensitive variables in the parent shell; no hosted run in progress; the hardened image is present; no C5 containers running. Snapshot: HEAD, `git status`, SHA-256 of 261 files |
| **S1** hardened harness (macOS) | Exit 0 and as catalogued | **PASS, exit 0.** Isolation: `sandbox-exec` deny `network*`, loopback probe **EPERM**. Toolchain: 67 distributions match the lock, `pip check` passes, **3,224** RECORD files verified. Inventory 261 files; `ast` gate 22 files. TypeScript gate **49 parsed / 5 rejected**, re-verified after the scan. Controls **59/64 as expected** (5 known misses, 0 missed; 23 fixtures; malformed rejected). **Parser-gap drift 0** (all 4 still `engine_rejected: false`). Source: **73 targets, 0 findings** |
| **S2** G2 guard (LT-U1 environment) | 9/9 | **PASS, 9/9.** The U1C failure is resolved |
| **S3** E03, real engine | 29/29, 0 skipped | **PASS, 29/29, 0 skipped** (172.8 s). M11 failure handling, M12 forged reports and M14 canary capture all pass. No canary in the console |
| **S4** G4, including end-to-end | 14/14, 0 skipped | **PASS, 14/14, 0 skipped**, including `HarnessEndToEnd`: malformed TypeScript stops with **zero Semgrep processes** |
| **S5** F3 fail-closed matrix | 34/34 | **PASS, 34/34 as expected.** B00=0; C01–C24=2; T01–T03=3; F01=1; K01–K02=4; P01–P03=2. Runner SHA-256 `bd0f88e0…3007` verified |
| **S6** full SAST suite, real engine | 88/88, 0 skipped | **PASS, 88/88, 0 skipped** (193.3 s). The plan stated 87; one test was added by the owner-approved G2 guard fix |
| **S7** Linux hardened container | Exit 0, `host-attestation` | **PASS, exit 0.** Isolation verified: only `lo` up, non-local IPv4/IPv6 unreachable, DNS fails, non-root, no capabilities, NoNewPrivs, seccomp, read-only root. Toolchain: 67 distributions match the Linux lock, **3,310** RECORD files; `semgrep-core` `dcaa53ef…1e68` (manifest). TypeScript gate: host gate passes, then in-container **`host-attestation`** 49/5, re-verified after the scan. Controls 59/64, parser-gap drift 0. Source **73 targets, 0 findings**. `container-run.json`: result `clean`, docker exit 0, full hardening flag set recorded |
| **S8** post-run integrity | Unchanged | **PASS.** HEAD, `git status` and **all 261 working-tree file hashes are unchanged** from S0. No writes under the repository, `artifacts/`, the application `node_modules` or `/tmp` since S0. No C5 container left. Consistency 237/237. No `secret_hash`, Pro, Secrets or canary content in any artifact |

## Environment and controls

* **Command environment:** every command ran under `env -i` with:
  * `PATH=/usr/bin:/bin` (S7 adds `/usr/local/bin` for the Docker CLI only,
    with `DOCKER_HOST=unix:///var/run/docker.sock`);
  * a new empty scratch `HOME` per stage;
  * `TMPDIR` inside the run directory;
  * `LANG`/`LC_ALL=C.UTF-8`;
  * only the named `C5_*`/`F3_*` variables.
* **Engine and venvs:**
  * macOS venv: offline hash-locked install from C5-U1 (re-verified by every
    harness preflight);
  * Linux venv: from C5-U1 `container-install` (re-verified in the container);
  * image `c5f4r-sast-runtime:local`
    (`sha256:e7dfbbf428d4372a6756cea9e0fc15988ae091b4c8bc99c5025cdd2c4f6484dc`).
* **Inputs:** every scan and test ran on disposable copies in the session
  scratch directory. The repository was only read.
* **G2/G5 controls:** preserved. The flags and environment were pinned and
  checked by the G2 guard; network isolation was verified by the harness in
  every run; nothing was redistributed or uploaded.

**Output hashes** (kept in scratch, not committed):

| File | SHA-256 |
| --- | --- |
| S0 OSV | `3acf5b1cb38d12eb7e449695751086bab14eb63920c39e7ae52380f240f66243` |
| S0 tree | `8be50c3d0fa83dfa78cc1729813ca78eacf31d1fcf1938f66c5085069802ff0b` |
| S1 console | `9aaf2072bb783edf1d5aab829c4d14020cabc4a725fa871291c3359f48575ca7` |
| S1 summary | `c99a9e0cfeda7f74afb5819ea3f809336ed4d9c81721aa2af5e6d0bb4b1cfdcd` |
| S2 | `f85d455b86cf1d7be38039b75103f4e696e5a8caa27bfc4c26e81f2e99c80eb7` |
| S3 | `ba287e38a987f6332c1732f6411c1a09d4ebc0e5b6405effda778825ec2bc8a1` |
| S4 | `60a778f2e00dd0cb01b8236cc031579d63d501829b8b5ecca3e075c6cc5db549` |
| S5 | `3ce0ba7c992b2297d7098d9eee32389fe89b8b851e224ebe59bf4659def0e15e` |
| S7 console | `451f7bdeccfd9203c998ef0c33004abc7e8d371d97869558e33580303eaaecfc` |
| S7 summary | `477db8855a9cb8f408fc83274a5c74ef200c5b6300d24d7891f33a76b34cf841` |
| S7 `container-run.json` | `943e66af51f91b24c3cc7be498032c9ed59eb06b32289f862c4906229f11a4c4` |
| S7 runner | `c6c67ba5b921e26fda0b442a248fcf4808b1dbf54c2103ec210e953818fdd1fe` |

## Remaining risks and limits

* **Local only.** S7 ran on Docker Desktop on this workstation (`linux/amd64`),
  not on a GitHub-hosted runner. Hosted behaviour of 1.186.0, including the G4H
  steps (`setup-node` 24.22.2 and `npm ci`), is **unverified**.
* **Node and repetitions.** Node v22.17.1 was used for the TypeScript gate. The
  hosted preflight enforces v24.22.2. The scans used `--repeat 1`.
* **E03 ran in auto mode only** (macOS sandbox). Container-mode E03 was not in
  scope.
* **One guard test still inherits the caller environment:**
  `test_engine_invocation_platform_wrapper`. The `PATH` pin is covered by five
  other tests.
* **Findings carried forward:** G2 (V1, V2), V3–V6 and V8 are present in
  1.186.0, **open and not waived**. G5D section 7 (minimum before E04) is still
  unmet.
* **macOS `libtree-sitter`** identity remains as recorded in v2 (inferred;
  byte-identical to 1.185.0).
* **Mandatory CI** is red (GHSA-fc5q-39xc-vjpf, picomatch), not waived.
* **The run-scoped coverage decision is consumed.** Any further engine
  execution, or any use of 1.186.0, needs a new owner decision.

## GO/NO-GO after LT-U1

| Decision | Status | Remaining criteria |
| --- | --- | --- |
| Adopt 1.186.0 and SBOM v3 | **NO-GO (technically ready for owner decision)** | Every technical criterion in U1B section 8 is now met. It needs a recorded owner decision renewing the conditional G2, V3–V6 and V8 acceptance for the 1.186.0 hashes (a new decision record; G5D is not edited), and the A6 path choice (B recommended) |
| G4H hosted dispatch on 1.186.0 | **NO-GO** | Adoption, then commit and push by the owner, a same-day recheck and per-run authorisation |
| E04, release, redistribution | **NO-GO** | G5D section 7, green mandatory CI without waiver, and governance |
