# M4C-C5 — E03 robustness completion (M07–M14)

Date: 2026-11-13 UTC. Base: `2b050a1` plus the uncommitted, preserved
[F4R execution closeout](m4c-c5-f4r-hosted-trial-execution.md). Authority: owner
direction for **E03 robustness completion only**, local and offline. Status:
**E03 met locally (macOS arm64 native; Linux x86_64 in the hardened Docker
`--network none` container, emulated)**.

There was no hosted dispatch or rerun, no CI integration, no GitHub setting
change, no dependency, rule or application change, no Azure, and no commit or
push. Destructive tests ran only on disposable copies: Python `TemporaryDirectory`
copies inside the tests, and confirmed `mktemp -d` scratch directories for the
Docker evidence checks.

## Decision

| Gate | Result |
| --- | --- |
| **E03 robustness (C5-M07–M14 fail closed; safe controls pass)** | **GO: met locally on both platforms** |
| E04 mandatory CI, E05 independent coverage review, E06 governance | NO-GO / Blocked (unchanged) |
| C5-A1/A2, release, Azure | NO-GO (unchanged) |

## Outstanding E03 items at the start of this slice

Per the F4R closeout, these were exercised with the real engine before this slice:

| Control | What it covers |
| --- | --- |
| M07 | Malformed source |
| M08 | Inventory, suppression and path checks |
| M09 | Rule and catalogue tampering |
| M10 | Engine, version and hash checks |
| M13 | Egress isolation |

Outstanding were:

* **M11** (timeout, crash, killed process, partial, empty, truncated or malformed
  JSON, skipped target) and **M12** (forged exit 0, errors, findings, coverage
  mismatch). These had been covered by driver-level mocks only.
* **M14** (canary capture), which had not been exercised.

## Method

New local test module:
[`tests/security/sast/test_robustness_e03.py`](../../tests/security/sast/test_robustness_e03.py).
It lives outside `tests/delivery`, so CI discovery is unchanged. It needs
`C5_SEMGREP` and skips explicitly otherwise.

* Each class copies the repository to a temporary directory and loads the
  harness or driver **from that copy**, so canaries never touch the working tree.
* The **real** harness runs end to end: preflight (lock, `pip check`, RECORD,
  engine hash), inventory, catalogue, `ast` gate, isolation and the real Semgrep
  1.185.0 engine.
* For M11/M12 only the engine's completed process is intercepted **after** the
  real engine produced it, and is then broken or forged. The harness's own
  validators must reject it with a fixed, distinguishable reason.
* For M14, canaries are planted in real source and identifiers, in a real TSX
  parse-error snippet, in token-like environment variables, and injected into
  every result field of the real report. Each case has a **positive control**
  (the canary must appear in the private raw report).

## Gaps found and fixed (red, then green)

The new tests first **failed** against the F3–F4R harness and driver. All failures
were fail-closed (non-zero), but each broke the distinct-exit-code contract or
leaked attacker-controlled text.

| # | Gap (proved by a failing test) | Fix (tightening only) |
| --- | --- | --- |
| 1 | A forged result with an **unknown rule ID** was accepted: exit 1 "findings", and the forged ID (carrying a canary) was printed and written to the published summary | `validate_complete` now requires every result's `check_id` to be in the executed catalogue → exit 3 |
| 2 | A forged result with a **path outside the targets** crashed the harness with an uncaught `KeyError` naming the path (as a subprocess: exit 1 = "findings") | Every result path must be a scanned target, and `start.line` must be a positive integer → exit 3 |
| 3 | **Unexpected internal exceptions** escaped (Python exit 1 = "findings") | `feasibility.main()` maps any unexpected exception to exit 3 and prints only the exception **type** |
| 4 | The trial **driver** crashed with exit 1 when it could not write its own evidence (stale-evidence scenario), and an in-container exit 7 would have been folded into 6 | `hosted_trial.main()` maps unexpected exceptions to **7** (evidence could not be produced, type name only). `container-run` passes an in-container 7 through |

Changed: `scripts/sast/feasibility.py` (result-integrity validation and the
internal-error wrapper) and `scripts/sast/hosted_trial.py` (driver wrapper and
7 pass-through). These are SAST harness tooling, not rules, dependencies or
application code. Nothing was weakened: every earlier check, threshold and exit
code is unchanged.

## Results

**Real-engine E03 suite: 28/28 on macOS (auto isolation) and 28/28 on Linux in
container mode.** On Linux the whole suite ran inside the hardened
`--network none`, uid 1001, capability-free, no-new-privileges, read-only
container.

| Case | Expected = actual |
| --- | --- |
| Baseline (no forging) | 0 clean |
| **M11** empty output; truncated JSON; non-JSON text; `[]` shape; killed (-9) with partial output | 3 (malformed/empty JSON or unexpected shape) |
| M11 timeout | 3 ("engine exceeded 120s deadline") |
| M11 crash exit 2 with a valid report | 3 (exit contradicts findings) |
| M11 skipped target; unparsed target | 3 (scanned paths differ; target not parsed) |
| M11 engine errors; skipped rules; version change | 3 |
| M11 unexpected internal error (canary in message) | 3 "unexpected internal error (RuntimeError)"; canary not printed |
| **M12** forged exit 0 with a finding; forged exit 1 without findings | 3 (contradiction) |
| M12 extra scanned path; rule-catalogue forgery; nondeterministic repeat | 3 |
| M12 forged result outside targets (canary path); unknown rule (canary rule); line 0 | 3; canaries not printed |
| M12 controls report wiped to "clean" | 4 control-failure |
| M12 malformed-controls report forged clean | 4 control-failure |
| M12 residual: consistent source forgery | 0. **Pinned as a documented limit** (see below) |
| **M14** real canary findings (Python `shell=True`, TS token logging) | 1 findings, printed as rule, path and line only |
| M14 injected canaries in `lines`, `message`, `metavars`, `dataflow_trace`, `fix` of every real result | Raw private report contains them (positive control). Console, `c5-summary.json` and `hosted-trial.json` do not |
| M14 environment canaries (`GITHUB_TOKEN`, `SEMGREP_APP_TOKEN`, `OTEL_EXPORTER_OTLP_ENDPOINT`) | Absent from every engine environment, the console and the artifacts |
| M14 real parse-error snippet (TSX error message echoes the canary) | 3. Canary is in the raw report only (positive control), not in the console or published files |
| M14 raw report storage | Directory 0700, files 0600. Trial upload list = six explicit `artifacts/sast/*.json`, with no `sast-private`. `ci.yml` uploads only `artifacts/m3`/`m4b` |
| Engine observation | Semgrep CE 1.185.0 without login emits `"lines": "requires login"` and no metavariables, and the rules' messages are fixed text. This is an extra layer that is **not relied upon**; the injected-canary test proves the harness allowlist independently |

**Real Docker evidence checks** (through `hosted_trial.py container-run` on
disposable copies):

| Scenario | Result |
| --- | --- |
| Evidence path blocked (a directory sits in place of `hosted-trial.json`) | **7**, "missing or unreadable" |
| Stale record claiming "clean, exit 0" with a foreign nonce, made read-only | **7**, "in-container driver could not produce evidence". The stale record was never accepted |
| Same, with the host unable to write its own record | **7**, "unexpected internal error (PermissionError)" (was exit 1 before fix 4) |
| Clean positive run through the updated driver | **0**: 70 targets, 0 findings, isolation verified |

**Preserved and regression results:**

| Check | Result |
| --- | --- |
| F3 34-case mutation matrix (fresh disposable snapshot, updated harness) | **34/34 macOS** (default mode), **34/34 Linux** (container mode, runner inside the hardened container) |
| SAST local test suite | **52/52** with the real engine (15 workflow, 9 container/driver including two new E03 driver cases, 28 E03). Without `C5_SEMGREP`: 24 pass and 28 are explicitly skipped |
| Trial workflow validator, `actionlint` 1.7.12, delivery tests, repository checks, gitleaks | Pass. Final values are in the [JSON record](m4c-c5-e03-robustness.json) |

## Remaining limitations

* **Consistent forgery is not detectable.** An attacker who controls the engine
  binary or its complete output (report and exit together) for the source scan
  is indistinguishable from a clean run. Mitigations: the `semgrep-core` hash,
  RECORD verification of every installed file, offline hash-locked install, and
  real controls that must detect seeded issues in the same run. Same-change
  tampering of harness and tests remains a governance (C5-A2) issue.
* M11 kill, timeout and crash cases are simulated by intercepting the real
  engine's process result, not by killing a live engine process. Engine OOM or
  hang inside Docker maps to driver exit 6 (mocked, F4R).
* Paths are published by design (bounded to scanned targets after fix 2). A
  secret embedded in a *file name* would still be published.
* Linux results are emulated (Rosetta). The hosted acceptance (run 43478654843)
  used the **pre-E03** harness and driver hashes. Fixes 1–4 are verified
  locally only, and any future hosted run would re-verify them.
* Open and not waived: **G2** (five MODERATE advisories), **G4**
  (engine-accepted malformed TS), **G5** (native-library notices and SBOM), and
  **governance** (C5-A2/E06). E04 and E05 are not started.

## Changed files (E03)

* New:
  * `tests/security/sast/test_robustness_e03.py`;
  * this document and its JSON record.
* Modified:
  * `scripts/sast/feasibility.py` (fixes 1–3);
  * `scripts/sast/hosted_trial.py` (fix 4);
  * `tests/security/sast/test_container_trial.py` (two driver E03 cases);
  * status lines in `README.md`, `AGENTS.md`, `docs/capability-status.md` and
    `docs/milestones/m4c-c5-sast-plan.md`.
* Unchanged: workflows (`ci.yml`, trial), rules, locks, catalogue, Dockerfile,
  toolchain, fixtures, application and earlier evidence.
