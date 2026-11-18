# M4C-C5 — U1C: LT-U1 local verification of Semgrep 1.186.0 (execution record)

Date: 2026-11-18 UTC. Start 11:09:31Z; stopped 11:12:51Z. Base: commit
`268bc75`, plus the uncommitted C5-U1/U1B work.

Plan: [U1B section 4](m4c-c5-u1b-pre-execution-assurance.md). Machine-readable
record: [JSON](m4c-c5-u1c-lt-u1-execution.json).

**Result: STOPPED AT S2 (FAIL). S0 and S1 passed; S3–S7 were not run.** As the
authorisation requires, the failed stage was **not retried**.

The failure is in the G2 guard **test**, and it depends on the caller's
environment (section 3). It is not an engine, harness or control failure.
Nevertheless, LT-U1 does **not** verify 1.186.0, and **1.186.0 is not
adopted**.

* **Not done:** hosted dispatch, adoption, commit, push or release.
* **Unchanged:** G5D D1–D6. G2, G4 and G5 remain **OPEN**. E04, E05, E06,
  release and redistribution remain **NO-GO**. Mandatory CI stays red
  (picomatch), not waived.

## Authorisation and preconditions

| # | Precondition (U1B section 5) | Status |
| --- | --- | --- |
| 1 | Owner authorisation for one LT-U1 execution, expiring 2026-11-20 | **Given** (owner instruction, 2026-11-18) |
| 2 | Owner decision on 1.186.0 coverage | **Given before S1**: G2 (V1, V2) and V3–V6, V8 accepted **for this single LT-U1 local run only** under the existing G5D controls, and ALSA-2026:98475 recorded as not applicable to 1.186.0. This is not adoption and not a waiver |
| 3 | `libtree-sitter` identity resolved | **Satisfied** (U1B R1) |
| 4 | Same-day OSV and upstream recheck | **Clean** (S0) |
| 5 | Hashes match the record | 237/237 (S0) |
| 6 | Minimal environment | `env -i` with `PATH=/usr/bin:/bin`, `HOME` set to a new empty scratch directory, and `LANG`/`LC_ALL=C.UTF-8`. The parent shell had no `SEMGREP_*`, `OTEL_*`, proxy or token variables |
| 7 | Clean state | HEAD, `git status` and the SHA-256 of all 259 working-tree files were snapshotted. No hosted run was in progress |

## Stage results

| Stage | Result | Detail |
| --- | --- | --- |
| **S0** (no engine) | **PASS** | OSV: 335 unique queries for the v3 components; only the 6 known MODERATE G2 GHSAs; **no new advisory, no HIGH/CRITICAL**. CISA KEV catalogue 2026.11.17 (1,782 entries): **0 hits** across the 15 CVE identifiers in scope. Upstream: Semgrep latest is 1.186.0, `cryptography` latest is 50.0.2, and the `semgrep/ocaml` `5.4.0-semgrep` head is `eb2978e6` (the already-reviewed CI-only commit). Consistency 237/237. Engine-free suite: 87 run, 57 pass, 30 skipped |
| **S1** hardened harness | **PASS (exit 0)** | Run on a disposable copy with the scratch venv installed offline from the hash-locked macOS wheels. Details below |
| **S2** G2 guard | **FAIL (exit 1)** | 7/8 pass. `NegativePolicy.test_every_mutation_is_rejected`, subtest `mutation='tool PATH widened'`: **"Drift not raised"** (section 3) |
| S3 E03 | **Not run** | Stopped at S2 |
| S4 G4 end-to-end | **Not run** | Stopped at S2 |
| S5 F3 matrix | **Not run** | Stopped at S2 |
| S6 full suite | **Not run** | Stopped at S2 |
| S7 Linux container | **Not run** | Stopped at S2 |
| S8 (post-stop integrity, read-only) | **PASS** | HEAD, `git status` and all 259 file hashes are unchanged from S0. No writes under `artifacts/` or the application `node_modules` since S0. No C5 container running. Consistency 237/237 |

**S1 harness details** (Semgrep CE **1.186.0**, macOS arm64, CPython 3.12.8):

* **isolation:** macOS `sandbox-exec` with deny `network*`; the loopback probe
  got **EPERM**;
* **toolchain:** 67 distributions match `requirements-sast-macos.txt`; `pip
  check` passes; **3,224** installed files match their RECORD hashes;
  `semgrep-core` SHA-256 is `8a41e91c…cd46`, equal to the manifest;
* **inventory:** 259 files classified; the `ast` gate checked 22 Python files;
* **TypeScript gate:** pass; 49 files parsed and 5 malformed controls rejected;
  TypeScript 6.0.3, Node v22.17.1; re-verified after the scan;
* **controls:** pass, **59/64 as expected**:
  * 5 known misses and **0 MISSED**, identical to the 1.185.0 hosted baseline
    (run 43478654843);
  * 23 catalogued fixtures; malformed fixtures all rejected;
* **parser gaps:** **drift = 0**. All 4 fixtures are still accepted by the
  engine (`engine_rejected: false`), so the 1.185.0 parser-gap behaviour is
  unchanged in 1.186.0;
* **source:** clean, **73 targets, 0 findings**;
* **output:** no `secret_hash`, Pro or Secrets fields in any artifact.

**Output hashes** (kept in the session scratch directory, not committed):

| File | SHA-256 |
| --- | --- |
| S1 console | `ee25c5f0d7f5a7ede7dc4139a6d13417605980fe3abd31b24eaa66c42a14c57d` |
| S1 summary | `f9f389715dc4600ed73c004eb6e6af32966801b228cb2fd782cf927253f89535` |
| S2 console | `610cfc1669233b4c9ea0052f81a27e1ea0705435a315694d505248573389edde` |
| S0 OSV record | `f1eeec123d4b3e7db0b3269a52052c1f07ae8fd6de7265b67df7ef2d4a7efb44` |
| S0 tree snapshot | `ef3c500f6cfc7dcabd04f31d0d0e6eff672b62779f7e2215509d94620230b976` |

## S2 failure analysis (read-only; not retried)

**What the case does.** The mutation "tool PATH widened" replaces the harness's
pinned tool `PATH` (`"/usr/bin:/bin"`) with `os.environ.get("PATH", "")`. The
guard builds the mutated harness's environment with
`mock.patch.dict(os.environ, environ, clear=False)`, so the mutated harness
inherits the **caller's** `PATH`.

**Why it was not detected.** LT-U1 ran every command under `env -i
PATH=/usr/bin:/bin`, which is **exactly the pinned value**. The "widened"
`PATH` therefore equals the pinned one, there is no drift to detect, and
`check_tool_env` correctly raises nothing.

**Corroboration.** In S0, under the normal shell `PATH`, the same test passed:
the full suite was OK and the G2 guard was 8/8.

**Classification:** a **test-design defect** (the mutation's effect depends on
the caller's environment), exposed by the stricter LT-U1 environment.

* **Not affected:** the engine; the harness's tool-environment control (the
  pinned `PATH` is unchanged); the U1 changes (the mutation line and the
  harness's `tool_env` were not modified by U1).
* **What it means:** the mutation test is **vacuous** whenever the caller's
  `PATH` is `/usr/bin:/bin`. In that environment the guard cannot prove that a
  harness inheriting the caller's `PATH` would be caught.

**Proposed fix (not implemented; needs owner approval).** Make the mutation
independent of the caller: run that case with a distinct caller `PATH` in the
injected environment (for example `{"PATH": "/c5g2/bin:/usr/bin:/bin", "X":
"C5G2CANARY"}`), so that inheriting it always differs from the pin. Optionally,
also assert that the mutated source produces a different environment before
expecting `Drift`.

This strengthens the test and weakens nothing. The other 7 tests and the other
G2 mutation cases passed in the LT-U1 environment.

## Fix applied after the stop (owner-directed, 2026-11-18; no engine)

`tests/security/sast/test_g2_mitigation_guard.py` (SHA-256
`2ff0e830080ed7839d3e2fdc20d4a8d3ee2c2e893a9281aa404cab82efeedc24`):

* **Distinct caller `PATH`.** The mutation loop now injects
  `MUTATION_CALLER_ENV = {"X": "C5G2CANARY", "PATH": CALLER_PATH}`, with
  `CALLER_PATH` set to the guard's existing hostile value
  `/c5g2/bin:/usr/bin:/bin`. It no longer inherits the test runner's `PATH`.
* **Non-vacuity assertions.** The test asserts `CALLER_PATH` differs from the
  pinned `/usr/bin:/bin`. For the "tool PATH widened" mutation, it also asserts
  that the mutated tool and engine `PATH` equal the caller value and differ
  from the pin, **before** expecting `Drift`.
* **New positive control:** `test_pinned_path_ignores_distinct_caller_path`.
  The unmutated harness keeps the pinned `PATH` (tool and engine) under the
  distinct caller `PATH`.
* **Preserved:** every existing mutation, synthetic override, hostile-environment
  check, the flag and environment pins, and the `rejected >= len - 1` bound.
  No assertion was removed or relaxed. The harness is unchanged.

**Engine-free validation:**

| Check | Result |
| --- | --- |
| G2 guard, normal shell | 9/9 |
| G2 guard, LT-U1 environment (`env -i PATH=/usr/bin:/bin`, empty `HOME`) | 9/9 (previously 7/8) |
| G2 guard, unusual caller `PATH` (`/usr/local/bin:/usr/bin:/bin:/sbin`) | 9/9 |
| SAST suite, normal shell and LT-U1 environment | 88 run: 58 pass, 30 skipped (engine). Semgrep was never invoked |

**Negative controls** (disposable copies; all failed as intended):

| Control | Result |
| --- | --- |
| (a) Pre-fix loop under `env -i` | Reproduces the original "Drift not raised" |
| (b) Caller `PATH` forced equal to the pin | Fails the new `CALLER_PATH != pin` assertion |
| (c) Ineffective PATH mutation | Fails the non-vacuity assertion |
| (d) Real harness with its PATH pin removed | Caught by 4 tests: the mutation anchor, the no-`os.environ` source check, the hostile-environment test and the new positive control |

**Observation (not changed, out of scope):**
`PositivePolicy.test_engine_invocation_container_mode` also uses the caller's
`PATH`. Under a caller `PATH` equal to the pin it cannot tell a pinned `PATH`
from an inherited one. In control (d) it passed, but the new positive control
and three other tests caught the weakening. Applying the same distinct caller
environment to that test is optional further hardening.

## Follow-up: container-mode positive test (owner-directed, 2026-11-18; no engine)

`PositivePolicy.test_engine_invocation_container_mode` now uses the same
deterministic caller environment (`MUTATION_CALLER_ENV`). It asserts that
`CALLER_PATH` differs from the pin and that the tool and engine `PATH` equal the
pin, then applies the unchanged `check_engine` and `check_tool_env`. Guard
SHA-256: `0ac3de5d0016ff3fab094d5bf4463cf2994d39c4b719e0c7aa19ea9aa513f286`.

| Check | Result |
| --- | --- |
| This test, unchanged harness, normal shell and LT-U1 environment | Pass |
| This test, disposable copy with the harness `PATH` pin removed, both environments | **Fails** (`'/c5g2/bin:/usr/bin:/bin' != '/usr/bin:/bin'`) |
| Whole guard against the pin-removed copy, LT-U1 environment | **5 tests fail** (was 4): the mutation anchor, the source check, container mode, the hostile environment and the new positive control |
| G2 guard, both environments | 9/9 |
| SAST suite, both environments | 88 run: 58 pass, 30 skipped (engine). Semgrep never invoked |

Every line the change removed was replaced by a strict superset. No control was
removed or relaxed. The harness is unchanged.

**Remaining observation (unchanged, out of scope):**
`test_engine_invocation_platform_wrapper` (macOS sandbox wrapper shape) still
inherits the caller environment. Against the pin-removed copy in the LT-U1
environment it passes, so on its own it does not prove the `PATH` pin. That pin
is covered by the five tests above.

## Residual risks and limits

* **Unverified on 1.186.0:**
  * E03 (29 tests: M11 failure handling, M12 forged reports, M14 canary
    capture);
  * the F3 34-case fail-closed matrix;
  * the G4 end-to-end test (malformed TypeScript stops before any Semgrep
    process);
  * the full suite with the engine;
  * the Linux hardened-container scan.
* **The S1 evidence is a single run** (`--repeat 1`). It shows the 1.186.0
  harness path is clean on macOS only.
* **The G2 guard's PATH mutation case is vacuous under a caller `PATH` of
  `/usr/bin:/bin`** until it is fixed.
* **The coverage decision for 1.186.0** (precondition 2) was **scoped to this
  LT-U1 run** and has now been consumed. Any further engine execution needs a
  new owner decision.
* **The 1.186.0 engine was executed once** (S1), under network isolation on a
  disposable copy. No toolchain artifact was uploaded or redistributed.
* **Unchanged from earlier records:** G2, V3–V6 and V8 are present in 1.186.0
  and not waived. Mandatory CI is red (picomatch).

## Next steps (owner decisions)

1. Approve the G2 guard test fix in section 3 (a test-only change).
2. Authorise a **new** LT-U1 execution from S0. The scoped coverage decision
   must be restated. S1 may be repeated within that run, because a restarted
   run re-executes every stage.
3. Adoption, the A6 path choice, hosted dispatch, E04, release and
   redistribution remain **NO-GO** until those results exist.
