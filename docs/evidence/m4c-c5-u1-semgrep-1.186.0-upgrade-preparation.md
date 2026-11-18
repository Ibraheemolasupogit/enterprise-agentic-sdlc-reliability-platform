# M4C-C5 — U1: controlled Semgrep CE 1.185.0 → 1.186.0 upgrade (preparation)

Date: 2026-11-18 UTC. Base: commit `268bc75`, plus the uncommitted, proposed
[G5D addendum A1](m4c-c5-g5d-addendum-a1.md).

Authority: owner direction to prepare a controlled upgrade **without executing
the Semgrep engine** until the applicable security gate permits it.

Machine-readable record: [JSON](m4c-c5-u1-semgrep-1.186.0-upgrade-preparation.json).

**Status: PREPARED, NOT ADOPTED, NOT EXECUTED.**

* **Not run:** the Semgrep engine (`semgrep`, `pysemgrep` or `semgrep-core`);
  the harness; any engine-backed test; any hosted dispatch.
* **Not done:** commit, push or release.
* **Unchanged:**
  * the original [G5D decision](m4c-c5-g5d-security-risk-decision.md) (D1–D6);
  * SBOM v1 (frozen) and SBOM v2 (adopted baseline);
  * all earlier evidence;
  * `ci.yml`, the trial workflow and the application dependencies.
* **Still open or NO-GO:**
  * G2, G4 and G5 remain **OPEN**;
  * E04, E05, E06, release and redistribution remain **NO-GO**;
  * mandatory CI stays **red** on the picomatch finding (section 7), not waived.

## 1. Gate analysis: what is permitted while scans are blocked

**Current gate:**

* [G5D addendum A1](m4c-c5-g5d-addendum-a1.md) records ALSA-2026:98475 as CVSS
  HIGH, which trips G5D section 6 stop condition 1 ("BLOCK all scanning").
* Exception X1 is proposed but **not approved**.
* So no scan may run.

**Effect of the upgrade itself:**

* Stop condition 7 ("the lock, the engine or the SBOM no longer match their
  recorded hashes") means that changing the pins takes the toolchain **outside
  the G5D acceptance**. G5D accepted the 1.185.0 hashes only.
* Using 1.186.0 for any scan therefore needs a **new owner decision**, even
  after the 1.185.0 block is resolved.

| Activity | Permitted now? | Basis |
| --- | --- | --- |
| Reading upstream metadata; hashing, downloading and statically parsing wheels in the session scratch directory (ELF, Mach-O, DWARF, symbols, strings) | **Yes, done** | Not scanning; nothing redistributed (stop condition 6) |
| Editing pins, the manifest, inventories, SBOM candidates, tests and documentation | **Yes, done** | Preparation; G5D stays unchanged |
| OSV and upstream advisory queries | **Yes, done** | Read-only research |
| CycloneDX schema validation | **Yes, done** | `jsonschema` library import; no engine |
| Offline `pip install` into a scratch venv (macOS), and the driver's `container-install` in the hardened `--network none` container (Linux); then `pip check`, distribution set, RECORD and `semgrep-core` hash checks | **Yes, done** | Installation and integrity checks only. Wheels run no code at install time. `container-install` runs only `venv`, `pip install` and `pip check` |
| Unit tests with `C5_SEMGREP` unset (engine tests skip), `actionlint`, validators, repository checks, gitleaks | **Yes, done** | No engine execution |
| `semgrep --version`, the harness (`feasibility.py`), `hosted_trial.py run` or `container-run`, the E03 real-engine suite, the F3 34-case matrix, the G4 end-to-end harness test | **No, not run** | Engine execution is scanning, or a prerequisite of it |
| Hosted dispatch | **No** | No authorisation; X1 is pending and covers 1.185.0 only |

## 2. Exact pins and verified hashes

| Item | 1.185.0 (previous) | 1.186.0 (prepared) |
| --- | --- | --- |
| Tag object / commit | `18866f41…` / `9240f708…` | `fbdca2da09575dffcc69b8245626567e2ab34c57` / `a5844e7c2d9d04548f86048f525d467a00742656`. The tag is **unsigned**, as before |
| PyPI release | — | Published 2026-11-18 and not yanked. `Requires-Dist`, `License-Expression` (LGPL-2.1-or-later) and `Requires-Python` (>=3.10) are **identical** to 1.185.0 |
| Linux wheel (`manylinux_2_34_x86_64`) | `0eb6aaad…c02b` | `54ebaf79adf4e5855c54d5e4457d8d03f27cc6bf73d79642281790b833d92e4f` (PyPI digest equals local SHA-256) |
| macOS wheel (`macosx_11_0_arm64`) | `d54c7dc2…f1b4` | `94b473227b1abe89d104bf87a50e257b3c47f0e09483e4290babc99c01e3aea8` (PyPI digest equals local SHA-256) |
| `semgrep-core`, Linux | `38fd0879…672d` (reproduced) | `dcaa53ef689d5e0145e6d418016ed40561a11ad6fa2c9472a760ed8131131e68` |
| `semgrep-core`, macOS | `4bfb5ad1…e9f5` (reproduced) | `8a41e91cef264cef399853606e0600c34bb11145afc10fc181e96cc92795cd46` |
| `requirements-sast-linux.txt` | `8d7d13b6…8b15` | `a6472b7823e8e1c6442a05516b99c198be2244340867c410723bc41c9d42fc25` |
| `requirements-sast-macos.txt` | `ca6756ce…7cefa` | `c7381523700084a16ffa3cc9f51de277d72c490e83046cb510ec2630e21e74f2` |
| Other 66 lock entries | — | **Unchanged**: same `Requires-Dist`, so the existing hash-pinned versions still satisfy it |

The previous `semgrep-core` hashes were reproduced from re-downloaded,
hash-locked 1.185.0 wheels. That confirms the hashing method against the
recorded values.

**Install verification (no engine execution):**

| Platform | Result |
| --- | --- |
| macOS arm64, CPython 3.12, offline `--require-hashes` | 67/67 wheels; `pip check` clean; installed set equals the lock (67); **3,224** RECORD-hashed files, **0** mismatches; `semgrep-core` and lock hashes equal the manifest |
| Linux x86_64, hardened container (`c5f4r-sast-runtime:local`, `--network none`, uid 1001, all capabilities dropped, read-only root), driver `container-install` on a disposable copy | Exit 0: offline install and `pip check` clean; installed set equals the lock (67); **3,310** RECORD-hashed files, **0** mismatches; `semgrep-core` and lock hashes equal the manifest |

## 3. Changed behaviour, isolation and telemetry review

**Python changes:** 14 files in the Python package changed (a 585-line diff).
`semdep` is unchanged.

| Change | Security relevance | Control and result |
| --- | --- | --- |
| `SEMGREP_METRICS_URL` is now read (metrics endpoint configurable; default unchanged) | A redirected metrics destination | Metrics stay off (`--metrics=off`, `SEMGREP_SEND_METRICS=off`). The engine environment is an exact allowlist, so the variable cannot reach the engine. The scan container has no network. **The G2 guard now tests this explicitly** (section 4) |
| `--compute-secret-hash` and an optional `secret_hash` output field (Secrets only) | A new Secrets-product surface | Not used: `--oss-only`, local rules, no Secrets. **Now a forbidden argument in the G2 guard.** The optional output field does not appear for CE rules (not yet confirmed by an engine run) |
| MCP telemetry and logs redact error messages and supply-chain results; MCP tracing honours `SEMGREP_SEND_METRICS=off` | A privacy improvement | MCP stays forbidden (`mcp` is a forbidden subcommand) |
| `semgrep_metrics.actor` field; `SecretHash` and `Sha1` output types | Interface additions only | None needed |
| Cross-module inlining in release binaries | A performance change; the engine binary differs | Same 84 opam build directories (`time_now` no longer has its own DWARF unit). The opam lockfiles are **byte-identical** between tags. C/C++ code is now compiled by GCC 11.5.0-**17**, previously -14 |
| No change to `extract()`/`traceparent` or the OpenTelemetry propagation paths | G2 V2 path | Unchanged: the G2 analysis carries over |

Isolation and hardening are unchanged:

* harness flags and engine environment;
* `--network none` container hardening;
* the Dockerfile;
* the six-file artifact allowlist;
* `ci.yml` and the trial workflow.

`feasibility.py` changed only `ENGINE_VERSION` ("1.185.0" to "1.186.0"). That
constant is the report-version check, so a stale 1.185.0 venv now **fails
closed** (lock and core hash mismatch, then version mismatch).

## 4. Compatibility tests (strengthened, not weakened)

`tests/security/sast/test_g2_mitigation_guard.py` (8 tests, all passing)
gains four checks:

* `--compute-secret-hash` added to the forbidden engine arguments;
* `SEMGREP_METRICS_URL` added to the credential-or-hostile pattern and to the
  hostile caller environment, which must never reach the engine;
* two harness-mutation cases, "metrics endpoint redirected" and "secret hash
  computation enabled", which are both rejected;
* two synthetic-override cases (the 1.186.0 metrics endpoint and the
  secret-hash flag), which are both rejected.

No assertion was removed or relaxed.

No other test hard-codes the engine version or hashes: the G2 guard reads
`ENGINE_VERSION` from the harness.

Fixture comments that describe observed **1.185.0** engine behaviour (the
parser-gap fixtures, the `tls.ts` constant propagation, and the E03 source-line
observation) are left unchanged. They are historical observations, and they
can only be re-confirmed by an engine run (section 8).

## 5. SBOM v3 and inventory

**New files:**

* [`security/sast/sbom/semgrep-toolchain-1.186.0.v3-candidate.cdx.json`](../../security/sast/sbom/semgrep-toolchain-1.186.0.v3-candidate.cdx.json)
  (SHA-256 `7d534e90ad6fe45e2cd664ee786f56cc780a0f235566aec4e7ae7696d63424ca`, regenerated by U1B with signed-RPM and reproducible-build identities);
* [`security/sast/native-libraries-1.186.0.json`](../../security/sast/native-libraries-1.186.0.json)
  (`2e7cb870…ceaa`, regenerated by U1B).

**Preserved unchanged:** v1 (`499477a2…3d81`), v2 (`70a38b40…8fe7`) and
`native-libraries.json` (`f70a8718…e866`).

**How v3 was derived:** from v2, by scratch script `u1_sbom_v3.py` (SHA-256
`5e9f0f7692659323b95b1ae04d1693f49231ec3b938722c60ded42611a3b4591`, U1B revision). The
script asserts the v2 hash and changes only what 1.186.0 evidence supports.

| Area | v3 change |
| --- | --- |
| `semgrep` wheels (2) | Version, package URL, hash and wheel name changed; bom-refs renamed in components and dependencies |
| `semgrep-core` (2) | Version and hash changed; Linux build-id `5d369e89…` and GCC -17 build note added |
| Linux bundled libraries | **17 changed.** **16 are CONFIRMED** against signed AlmaLinux RPMs ([U1B](m4c-c5-u1b-pre-execution-assurance.md)): source RPM, RPM hash and URL, signer, and the full signed `License` tag. `libtree-sitter` is **CONFIRMED** as tree-sitter 0.26.3 by a reproducible build (U1B R1). **9 unchanged**, carried over only after their hash and build-id matched v2 |
| macOS bundled dylibs (7) | **Byte-identical** to 1.185.0; carried over unchanged (V8 libdwarf unchanged) |
| Static components | Linux `cxx-std-headers` is now GCC 11.5.0-17 (561 instantiations, unchanged; no `from_chars`, parallel mode, `__gnu_pbds` or aligned `new`). `time_now` is annotated. The OCaml runtime fork commit `4046c817` is unchanged |
| Vulnerabilities | 29 → **23**. The 6 ALSA entries were removed because their affected Linux libraries are now at patched builds (OSV: 0 AlmaLinux advisories). ALSA-2026:98475 does not apply to v3. The other 23 are unchanged, still `in_triage` (21) or `not_affected` (2), and annotated "unchanged in 1.186.0" |
| Metadata | New serial number; status "CANDIDATE v3 (C5-U1) … adoption requires owner decision" |

**Validation:**

* **Schema:** CycloneDX 1.6.2 schema (same copies and hashes as G5D),
  `jsonschema` 4.25.1 and `referencing` 0.37.0.
  * v3: **0 errors**.
  * v2: still 0 errors.
  * Negative controls on mutated v3 copies: bad analysis state, bad hash
    algorithm, bad component type, missing `bomFormat` and bad serial number.
    **5 of 5 rejected.**
* **OSV reassessment of v3:** 335 unique package queries (PyPI 67, AlmaLinux 9
  19, opam 102, crates.io 147). Hits: `mcp` 1.29.0 (4 GHSA) and
  `opentelemetry-api` 1.37.0 (2 GHSA, including GHSA-mf5v). **No OSV
  advisory is missing from v3.** The other 17 v3 entries come from fork,
  commit-range or manual research (OSEC ×9, OpenSSL in `cryptography` ×6,
  libdwarf, PCRE2), and their components are byte-identical or on the same
  fork commit.
* **Not queryable through OSV purl lookups:** the `semgrep/ocaml` fork,
  tree-sitter, the EPEL `libunwind`, Homebrew and OpenSSL-in-wheel components,
  and 135 components without a purl. The coverage limits are the same as G5C.

## 6. G2 and G5 reassessment under 1.186.0

| Finding | Under 1.186.0 |
| --- | --- |
| G2 V1 (`mcp` 1.29.0, 4 GHSA), G2 V2 (`opentelemetry-api` 1.37.0, including GHSA-mf5v) | **Unchanged.** Same pins; OPEN, not waived |
| V3–V5 (OCaml 5.4.0 fork `4046c817`: OSEC Marshal, `Str`/`map_file`, `runtime_events`) | **Unchanged**: same fork commit |
| V6 (OpenSSL in `cryptography` 50.0.2) | **Unchanged**: same wheel; no newer `cryptography` release |
| V7 (6 ALSA, plus ALSA-2026:98475 recorded in A1) | **Remediated by 1.186.0**: patched AlmaLinux builds, and OSV returns 0 advisories for the bundled versions. All 16 rebuilt AlmaLinux libraries are verified against signed RPMs, and `libtree-sitter` by reproducible build (U1B) |
| V8 (libdwarf, macOS) | **Unchanged**: byte-identical dylib |
| G5 licensing and redistribution | Unchanged obligations; redistribution **NO-GO** |
| G5D section 7 (minimum before E04) | **Still not met.** Item 1 needs `mcp` ≥ 1.30.0, `opentelemetry-api` ≥ 1.45.2 and the OCaml OSEC fixes; 1.186.0 delivers only the rebuilt AlmaLinux libraries |

## 7. Mandatory CI (unchanged, visible)

* Mandatory CI run 44216318120 at `268bc75` stays **failed**:
  `npm audit --audit-level=high` reports GHSA-fc5q-39xc-vjpf (picomatch ≤
  4.0.7), with no fixed release.
* Recorded in [A1 section 3](m4c-c5-g5d-addendum-a1.md). U1 does not touch it,
  does not waive it, and does not change the audit gate.

## 8. Remaining blockers

1. **Engine execution is blocked:** G5D stop condition 1 (ALSA-2026:98475 under
   A1), and stop condition 7 for the new pins. No 1.186.0 behaviour has been
   observed at runtime.
2. **Engine-dependent verification is pending:**
   * the harness on the repository (controls as catalogued in `controls.json`,
     the target count, 0 findings);
   * the E03 suite (29 tests, real engine);
   * the F3 34-case matrix;
   * the G4 end-to-end harness test;
   * the parser-gap fixture expectations;
   * confirmation that the `secret_hash` field is absent for CE rules;
   * hosted Linux execution.
3. **Native identity:** resolved by [U1B](m4c-c5-u1b-pre-execution-assurance.md)
   for all 17 rebuilt libraries: 16 against signed RPMs, and `libtree-sitter` by
   reproducible build.
4. **Sequencing conflict with A1 / X1:** X1 requires trial inputs that are
   byte-identical to `268bc75`. U1 changes three of them:
   * `requirements-sast-linux.txt`;
   * `security/sast/toolchain.json`;
   * `scripts/sast/feasibility.py`.

   Committing U1 voids X1's dispatch conditions.
5. **G2 and V3–V6, V8** remain open under 1.186.0, and the G5D section 7
   pre-E04 remediation is unmet.
6. **Mandatory CI** is red (section 7).

## 9. GO/NO-GO criteria

| Decision | Status | Exact criteria to change |
| --- | --- | --- |
| **Commit the U1 preparation** | **Owner choice: sequencing.** Option A: dispatch X1 on 1.185.0 first, then commit U1. Option B (recommended): withdraw X1 and proceed with U1. Under 1.186.0 the ALSA-2026:98475 trigger disappears, so no exception is needed | The owner reviews this record and the changed files; local checks pass (section 10) |
| **Local real-engine verification of 1.186.0** | **NO-GO** | 1. An explicit owner authorisation scoped to local verification. 2. The pins, manifest and SBOM hashes equal section 2 and section 5. 3. A same-day OSV recheck shows no new HIGH or CRITICAL advisory and no exploit. 4. The G2 guard and the engine-free suite pass. 5. Runs use only the hardened harness (macOS sandbox, or the Linux `--network none` container) on owner-controlled content |
| **Adopt 1.186.0 and SBOM v3 as the baseline** | **NO-GO** | 1. The harness exits 0 with controls as catalogued. 2. E03 29/29, F3 34/34 and the G4 end-to-end test pass with the real engine. 3. The parser-gap fixtures are re-confirmed, and any changed engine behaviour is documented. 4. Native identities are resolved: all 17 rebuilt libraries are verified (U1B). 5. A recorded owner renewal of the G2, V3–V6 and V8 conditional acceptance for the 1.186.0 hashes (G5D D1–D3 are not edited; a new decision record) |
| **Hosted dispatch on 1.186.0** | **NO-GO** | Adoption above, plus per-run owner authorisation under the G5D trial conditions (same-day recheck, six-file allowlist, single run) |
| **E04, release, redistribution** | **NO-GO** | G5D section 7 met in full, mandatory CI green without waiver, and C5-A1/A2 and E05/E06 governance closed |

## 10. Verification run (static only)

| Check | Result |
| --- | --- |
| SAST test modules, `C5_SEMGREP` unset | 87 run: 57 pass, 30 skipped (engine). G2 guard 8/8, including the new 1.186.0 checks |
| `actionlint` 1.7.12, trial-workflow validator | Pass |
| `check_repository.py`, `git diff --check`, untracked whitespace, gitleaks, local links | Pass (section 11) |
| `ci.yml`, trial workflow, Dockerfile, `controls.json`, `hosted_trial.py`, app lockfile, G5D record, SBOM v1 and v2, `native-libraries.json` | Unchanged (hash-checked) |

## 11. Changed files (U1)

* **Modified:**
  * `requirements-sast-linux.txt` and `requirements-sast-macos.txt` (the
    `semgrep` line and header only);
  * `security/sast/toolchain.json`;
  * `scripts/sast/feasibility.py` (`ENGINE_VERSION` only);
  * `tests/security/sast/test_g2_mitigation_guard.py` (strengthened);
  * `THIRD_PARTY_NOTICES.md` (the Semgrep row);
  * status lines in `README.md`, `AGENTS.md`, `docs/capability-status.md` and
    `docs/milestones/m4c-c5-sast-plan.md`.
* **New:**
  * `security/sast/native-libraries-1.186.0.json`;
  * `security/sast/sbom/semgrep-toolchain-1.186.0.v3-candidate.cdx.json`;
  * this document and its JSON record.
* **Also uncommitted, from A1 and not part of U1:**
  `docs/evidence/m4c-c5-g5d-addendum-a1.md` and its status lines.
