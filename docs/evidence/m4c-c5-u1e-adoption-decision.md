# M4C-C5 — U1E: Semgrep CE 1.186.0 adoption decision (APPROVED)

Date: 2026-11-18 UTC. Base: commit `268bc75`, plus the uncommitted C5-U1 work.
This extends the [G5D decision](m4c-c5-g5d-security-risk-decision.md) and does
**not** edit it. Machine-readable record:
[JSON](m4c-c5-u1e-adoption-decision.json).

**Status: APPROVED by the owner on 2026-11-18.** [Addendum 1](m4c-c5-u1e-addendum-1-guard-rebinding.md) (2026-11-19) rebinds the G2 guard hash only.
**Original decision:** (decisions E1–E8, subject to
the documented scope, expiry and stop conditions).

* The section 4 follow-up edits are **applied**; section 9 documents the
  status-only `toolchain.json` difference.
* The path B choice (A6) and the **withdrawal of X1** were recorded by the
  owner on 2026-11-18 in [addendum A1](m4c-c5-g5d-addendum-a1.md).
* Nothing has been committed, pushed or dispatched; all of that remains an
  owner action.

## 1. Evidence basis

| Record | What it establishes |
| --- | --- |
| [C5-U1](m4c-c5-u1-semgrep-1.186.0-upgrade-preparation.md) | Pins, manifest, behaviour and telemetry review; the strengthened G2 guard; SBOM v3 derivation; G2/G5 reassessment under 1.186.0 |
| [U1B](m4c-c5-u1b-pre-execution-assurance.md) | **17/17** rebuilt Linux libraries verified: 16 against signed AlmaLinux RPMs (signed `repomd.xml` through to byte-identical code sections), and `libtree-sitter` 0.26.3 by reproducible build. 237 consistency checks |
| [U1C](m4c-c5-u1c-lt-u1-execution.md) | First LT-U1 run stopped at S2 (a G2 guard test-design defect, not retried). Owner-approved guard fixes, validated without the engine |
| [U1D](m4c-c5-u1d-lt-u1-verification.md) | Fresh LT-U1 run: **S0–S8 all passed** (harness exit 0, G2 guard 9/9, E03 29/29, G4 14/14, F3 34/34, suite 88/88, hardened Linux container exit 0, repository unchanged) |

**Re-verification for this draft:**

* All **13** U1D output hashes were recomputed and match.
* Every stage exit is 0, and the test counts are as recorded.
* The S1/S7 `semgrep-core` hashes equal the manifest.
* **At draft time (before the section 4 edits)**, only documentation had
  changed since LT-U1 S0: the U1D record and status lines.
* **After approval,** `security/sast/toolchain.json` was changed status-only.
  It is **not** byte-identical to the LT-U1-tested file (section 9). The locks,
  harness, tests, rules, controls, inventory and SBOM v3 that LT-U1 verified
  remain byte-identical.
* Consistency: 237/237.

## 2. Decisions (approved 2026-11-18)

| # | Decision |
| --- | --- |
| E1 | **Adopt Semgrep CE 1.186.0** as the pinned C5 toolchain, exactly as hashed in section 3. Its uses are **only** local scans of the owner's trusted repository through the hardened harness, and separately authorised, non-blocking, dispatch-only hosted trials. It is **not** a CI gate. The 1.185.0 toolchain is retired from use |
| E2 | **SBOM v3** (`security/sast/sbom/semgrep-toolchain-1.186.0.v3-candidate.cdx.json`, SHA-256 `7d534e90ad6fe45e2cd664ee786f56cc780a0f235566aec4e7ae7696d63424ca`, CycloneDX 1.6.2, 0 schema errors) becomes the **current assessment baseline**. SBOM v1 (frozen) and v2 (the 1.185.0 record) stay unchanged. The file keeps its name and its internal "CANDIDATE v3" status; this record governs, as G5D did for v2 |
| E3 | **Conditional acceptance, scoped to the section 3 hashes:**<br>• **G2 V1:** `mcp` 1.29.0, with GHSA-5h93-6whr-6q8j, GHSA-84m7-p3x7-pcfv, GHSA-rwrf-2pqf-9j8j and GHSA-w4fh-qvv9-3v23<br>• **G2 V2:** `opentelemetry-api` 1.37.0, with GHSA-xcq7-p3pf-p88h and GHSA-mf5v-w3w3-f6cg<br>• **G5 V3–V5:** the OCaml 5.4.0 fork `4046c817`, with the OSEC advisories<br>• **G5 V6:** OpenSSL in `cryptography` 50.0.2<br>• **G5 V8:** libdwarf in the macOS wheel<br>Accepted for the **E1 uses only**, under the hardened controls (G5D sections 2 and 4) and the stop conditions in E5. **Not a waiver:** every advisory stays OPEN and visible |
| E4 | **Expiry is unchanged: 2026-12-17**, the same date as G5D D3. Without a recorded renewal the acceptance lapses, and every use other than local development is blocked |
| E5 | **Stop conditions:** G5D section 6 conditions 1–7 apply unchanged, with "recorded hashes" meaning the section 3 table. In addition, **stop immediately** if any of these occurs:<br>(a) any section 3 hash changes;<br>(b) any LT-U1-verified gate fails on re-run: the G2 guard, E03, the F3 matrix, G4, isolation verification, or the `pip check`/RECORD/hash preflight;<br>(c) any scan is attempted outside the E1 uses.<br>**Early review** is due on a Semgrep, `cryptography` or `semgrep/ocaml` release, or on any new advisory for an SBOM v3 component |
| E6 | **V7 under 1.186.0:** no open advisory. All 17 rebuilt Linux libraries have verified identity, and OSV returns 0 AlmaLinux advisories for them. ALSA-2026:98475 and the six earlier ALSA advisories apply only to the retired 1.185.0 toolchain. A1 sections 1–3 stay the historical record. **G5 remains OPEN** (V3–V6, V8, licensing and notices) |
| E7 | **Unchanged:**<br>• G5D D1–D6 (they govern the retired 1.185.0 toolchain);<br>• G2, G4 and G5 **OPEN**;<br>• E04, E05, E06, release and redistribution **NO-GO**;<br>• mandatory CI **red** (GHSA-fc5q-39xc-vjpf, picomatch), **not waived**;<br>• the `npm audit --audit-level=high` gate and all CI thresholds unchanged |
| E8 | **G4H:** a hosted dispatch on 1.186.0 still requires:<br>(1) the owner to commit and push this changeset;<br>(2) a same-day OSV, KEV and upstream recheck;<br>(3) per-run owner authorisation with a new `authorization_reference`;<br>(4) the G4H acceptance checks, where the trial's recorded `input_sha256sum` must equal the committed files |

## 3. Toolchain hashes covered by E1 and E3

| Item | SHA-256 |
| --- | --- |
| Linux wheel `semgrep-1.186.0-…-manylinux_2_34_x86_64.whl` | `54ebaf79adf4e5855c54d5e4457d8d03f27cc6bf73d79642281790b833d92e4f` |
| macOS wheel `semgrep-1.186.0-…-macosx_11_0_arm64.whl` | `94b473227b1abe89d104bf87a50e257b3c47f0e09483e4290babc99c01e3aea8` |
| `semgrep-core`, Linux | `dcaa53ef689d5e0145e6d418016ed40561a11ad6fa2c9472a760ed8131131e68` |
| `semgrep-core`, macOS | `8a41e91cef264cef399853606e0600c34bb11145afc10fc181e96cc92795cd46` |
| `requirements-sast-linux.txt` | `a6472b7823e8e1c6442a05516b99c198be2244340867c410723bc41c9d42fc25` |
| `requirements-sast-macos.txt` | `c7381523700084a16ffa3cc9f51de277d72c490e83046cb510ec2630e21e74f2` |
| `security/sast/native-libraries-1.186.0.json` | `2e7cb87088dca3d9c5068fd1b53a35fa91c4b02ba04ff8b601a22dd9cac2ceaa` |
| SBOM v3 | `7d534e90ad6fe45e2cd664ee786f56cc780a0f235566aec4e7ae7696d63424ca` |
| `scripts/sast/feasibility.py` | `f7690a9aceadbe8e8be00b55ba105f8922c21bca26a7f66719432737a67bc3d0` |
| `tests/security/sast/test_g2_mitigation_guard.py` | **`42672fd941fde28e387d4dd461e3b5d216e64597c0cc7bb20549f37ca6b04a79`** (rebound by [addendum 1](m4c-c5-u1e-addendum-1-guard-rebinding.md), 2026-11-19; was `0ac3de5d0016ff3fab094d5bf4463cf2994d39c4b719e0c7aa19ea9aa513f286`, the version LT-U1 executed) |
| `security/sast/controls.json` (unchanged) | `ee61fedf3b6afce976189227cd7c41c48402082562cc368d291683b34d05dbe6` |
| Rules (unchanged) | `python.yml` `526c3e7f…1f73`; `typescript.yml` `b0383617…fc7c` |
| `security/sast/toolchain.json` | **`91f9a3d0f31781c35911c7136b244b3c42f378f72ac19971f6676422d3d6603d`** (bound by this decision; the status-only edit is in section 9). The LT-U1-tested version was `32eaef70c5438a7ded01eff0e0d938be10f11bf846de87ef24095d93b3456357` |

## 4. Post-approval edits (APPLIED 2026-11-18)

All four were applied after the owner approved E1–E8 on 2026-11-18. Each is
documentation or status text. The only hash in section 3 that changed is
`toolchain.json`, which section 9 verifies.

1. **`security/sast/toolchain.json`:** change the two platform `status` strings.
   They said "NOT executed (engine execution blocked …)", which LT-U1
   made **stale**. Proposed text:
   * `Darwin-arm64`: "C5-U1: hash-locked; installed offline and executed in
     LT-U1 (U1D 2026-11-18: harness exit 0, E03 29/29, G4 14/14, F3 34/34,
     suite 88/88); adopted by U1E";
   * `Linux-x86_64`: "C5-U1: hash-locked; installed offline in the hardened
     container and executed in LT-U1 S7 (U1D 2026-11-18: --network none, exit
     0); adopted by U1E".

   These fields are not read by the harness (it reads only `lock`,
   `lock_sha256` and `semgrep_core_sha256`). The edit changes `toolchain.json`'s
   hash, which is a hosted-trial input. The new hash is recorded in this
   decision. The edit was verified as a status-only JSON diff with identical
   harness preflight results (section 9), and the engine-free suite and
   consistency checks were re-run.
2. **`THIRD_PARTY_NOTICES.md`:** change "C5-U1 candidate pin" to "adopted pin
   (U1E)".
3. **Status lines** in `AGENTS.md`, `README.md`, `docs/capability-status.md` and
   `docs/milestones/m4c-c5-sast-plan.md`:
   * replace the now-obsolete A1/X1 "scanning BLOCKED / never dispatch unless
     X1" and C5-U1 "never run the engine" rules with the E1/E3/E5 rules;
   * name SBOM v3 as the baseline;
   * keep G2/G4/G5 OPEN and E04/release/redistribution NO-GO.
4. **This record:** marked APPROVED, with the date and the owner's response in
   section 8, and the exact hashes in section 3.

## 5. Changeset audit (uncommitted against `268bc75`)

| Area | Finding |
| --- | --- |
| Locks | Only the `semgrep` line (version and hash) and the header comment changed in each lock. The other 66 entries are unchanged |
| Harness `feasibility.py` | Only `ENGINE_VERSION` changed (`1.185.0` → `1.186.0`). Flags, environment, isolation, gates and exit codes are unchanged |
| `toolchain.json` | Engine version, tag and commit, a `previous_pin` record, per-platform lock/wheel/core hashes, the `semgrep` dependency version, a 2026-11-18 OSV record, and the inventory pointer. Platform `status` text corrected after approval (section 4 item 1; status-only, section 9) |
| G2 guard | Strengthened only: forbids `--compute-secret-hash`; treats `SEMGREP_METRICS_URL` as hostile/secret-like; adds two harness mutations and two synthetic overrides for 1.186.0; uses a deterministic caller environment with non-vacuity assertions; adds one positive control. **No assertion removed or relaxed.** Against a harness with its `PATH` pin removed, 5 tests fail |
| New data | `native-libraries-1.186.0.json`; SBOM v3 (both regenerated from preserved baselines by hashed scratch tools) |
| Docs | Evidence A1, U1, U1B, U1C, U1D and this U1E; the `THIRD_PARTY_NOTICES.md` Semgrep row; status lines |
| Unchanged (verified) | `ci.yml` and the trial workflow; `hosted_trial.py`; `check_trial_workflow.py`; the G4 gate script and manifest; the Dockerfile; `controls.json`; the rules; the application and lockfile; SBOM v1 and v2; `native-libraries.json`; the G5D record |
| Security regressions | **None found.** No CI threshold, `npm audit` setting, isolation, hardening, artifact allowlist or harness control changed |
| Unrelated modifications | **None.** Every change belongs to the C5-U1/A1 track |
| Historical text | Fixture comments state the observed **1.185.0** parser-gap behaviour. They sit inside catalogue-hashed fixtures and LT-U1 showed the behaviour unchanged in 1.186.0, so they are left as they are. The 1.185.0 references in README section 2 and `docs/delivery.md` describe F1 history |

## 6. Files to commit (one commit; final 23-file inventory)

* **Modified (10):**
  * `AGENTS.md`
  * `README.md`
  * `THIRD_PARTY_NOTICES.md`
  * `docs/capability-status.md`
  * `docs/milestones/m4c-c5-sast-plan.md`
  * `requirements-sast-linux.txt`
  * `requirements-sast-macos.txt`
  * `scripts/sast/feasibility.py`
  * `security/sast/toolchain.json`
  * `tests/security/sast/test_g2_mitigation_guard.py`
* **New (13):**
  * `docs/evidence/m4c-c5-g5d-addendum-a1.md`
  * `docs/evidence/m4c-c5-u1-semgrep-1.186.0-upgrade-preparation.md` and `.json`
  * `docs/evidence/m4c-c5-u1b-pre-execution-assurance.md` and `.json`
  * `docs/evidence/m4c-c5-u1c-lt-u1-execution.md` and `.json`
  * `docs/evidence/m4c-c5-u1d-lt-u1-verification.md` and `.json`
  * `docs/evidence/m4c-c5-u1e-adoption-decision.md` and `.json`
  * `security/sast/native-libraries-1.186.0.json`
  * `security/sast/sbom/semgrep-toolchain-1.186.0.v3-candidate.cdx.json`
* **Do not commit:** anything under `artifacts/` (git-ignored) or the session
  scratch directory, including the wheels, venvs, RPMs, rebuilt library and
  LT-U1 outputs. Redistribution is prohibited.

## 7. Remaining risks

* **Hosted behaviour is unverified.** LT-U1 S7 used Docker Desktop
  (`linux/amd64`) locally, with Node v22.17.1 and `--repeat 1`. The G4H steps
  (`setup-node` 24.22.2 and `npm ci`) have never run.
* **Pushing will trigger mandatory CI,** which is expected to **fail again** on
  `npm audit` (picomatch, no fixed release). This is not waived and the
  threshold is unchanged.
* **Findings carried forward:** G2 V1/V2 and G5 V3–V6, V8 are present, open
  and accepted only conditionally until 2026-12-17. G5D section 7 (minimum
  before E04) is unmet.
* **Guard coverage gap:** `test_engine_invocation_platform_wrapper` still
  inherits the caller environment. The `PATH` pin is covered by 5 other tests.
* **macOS `libtree-sitter`** identity remains inferred, as in v2
  (byte-identical to 1.185.0).
* **The committed `toolchain.json` is not byte-identical to the LT-U1-tested
  file.** The difference is status text only (section 9). The first hosted
  trial will record the new hash `91f9a3d0…603d` in `input_sha256sum`.

## 8. Owner decision

| # | Owner response |
| --- | --- |
| E1–E8 | **APPROVED, 2026-11-18**, subject to the documented scope (E1 uses only), expiry (2026-12-17) and stop conditions (E5) |
| Section 4 edits | **Directed and applied, 2026-11-18** (section 9) |

## 9. Status-only `toolchain.json` difference after LT-U1

`security/sast/toolchain.json` is a hashed hosted-trial input (`INPUT_HASHES` in
`hosted_trial.py`). After approval, its two platform `status` strings were
corrected. **The committed file is therefore not byte-identical to the file
LT-U1 tested.**

| Item | Value |
| --- | --- |
| LT-U1-tested SHA-256 | `32eaef70c5438a7ded01eff0e0d938be10f11bf846de87ef24095d93b3456357` |
| Current SHA-256 (bound by this decision) | `91f9a3d0f31781c35911c7136b244b3c42f378f72ac19971f6676422d3d6603d` |
| Structural JSON difference | **Exactly two values:** `engine.platforms.Darwin-arm64.status` and `engine.platforms.Linux-x86_64.status`. Lines 19 and 26 of 502; no other key, value or line changed |
| What reads the file | The harness reads `toolchain.json` only in `preflight()`. It uses `engine.platforms[<platform>]` for `lock`, `lock_sha256` and `semgrep_core_sha256`, plus `rules`, `rule_ids` and `controls_catalogue_sha256`. **No code reads `status`.** The hosted driver only records the file's hash in `input_sha256sum` |
| Execution equivalence (no Semgrep) | The harness `preflight()` was run on two disposable copies, with the pre-edit and post-edit file, on the macOS venv. **The results are identical:** Darwin-arm64, 67 distributions, 3,224 RECORD files, same `semgrep-core` hash and lock. **The subprocess calls are identical:** only the venv Python, for `pip check`, the distribution listing and the RECORD check. Semgrep was never invoked (an engine-call guard was active). The Linux container preflight runs the same code path |
| Rebound | U1, U1B (JSON and table) and this record now carry the new hash. The consistency check passes against it |
