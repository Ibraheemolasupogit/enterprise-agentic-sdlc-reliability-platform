# M4C-C5 — G5D addendum A1: pre-dispatch blockers for the G4H hosted trial

Date: 2026-11-18 UTC. Base: commit `268bc75` (HEAD and `origin/main`).
It extends the [G5D decision](m4c-c5-g5d-security-risk-decision.md) and does
not edit it.

**Status: PROPOSED, NOT APPROVED, except decision A6, which the owner recorded
on 2026-11-18: path B. Exception X1 is WITHDRAWN and was never approved or used.**
Sections 1–3 remain the historical record for the retired 1.185.0 toolchain.
The 1.186.0 adoption is decided separately in
[U1E](m4c-c5-u1e-adoption-decision.md).

* Nothing here takes effect until the owner records approval in the
  [Owner decision](#owner-decision-pending) section.
* The decisions D1 to D6 in G5D are unchanged.
* G2, G4 and G5 remain **OPEN**.
* E04, E05, E06, release and redistribution remain **NO-GO**.
* No advisory is waived.

How this addendum was prepared:

* **Inputs:** the pre-dispatch recheck and the read-only blocker assessment
  done on 2026-11-18.
* **No changes made:** no dependency, lock, CI control, workflow, harness or
  SBOM change.
* **No actions taken:** no dispatch, commit or push.

## 1. ALSA-2026:98475 (gcc: libgcc, libstdc++)

### Finding

| Item | Value |
| --- | --- |
| Advisory | ALSA-2026:98475, "Moderate: gcc security update" (RHSA-2026:98475). Published 2026-11-11; indexed in OSV 2026-11-17, after the G5/G5C queries |
| CVEs | **CVE-2026-95619**: integer overflow in libstdc++ **aligned** `operator new`. **CVE-2026-102010**: use-after-free in `__gnu_pbds::priority_queue` (`binary_heap_tag`) `erase_if` |
| Severity | Vendor rating: **Moderate**. **CVSS 3.1 base 7.7** (`AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:H/A:H`) and **7.0** (`AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:L/A:H`), both in the CVSS **HIGH** band (Red Hat security data). **This addendum classifies the advisory as HIGH** |
| Affected component | `semgrep/bin/libs/libstdc++.so.6` and `libgcc_s.so.1` in the hash-pinned Linux wheel `semgrep-1.185.0-…-manylinux_2_34_x86_64.whl` (`sha256:0eb6aaadad5b957af96d1300487e10af1dc8016e8ef53072effb48cd4906c02b`). Package build 11.5.0-14.el9.alma.1. Fixed in 11.5.0-16.el9_9.alma.1 |
| Presence | **Confirmed**: the affected version is bundled, and it is the copy `semgrep-core` loads through `RUNPATH $ORIGIN/libs` |
| Scope | The Linux wheel only, which is the wheel the hosted trial installs in its container. The macOS wheel does not contain the AlmaLinux libraries |
| SBOM | Not listed in SBOM v2 (its 29 vulnerability entries include six ALSA advisories, not this one). SBOM v1 and v2 are unchanged. Adding the advisory needs a separately authorised v3 candidate |

### G5D consequence

On the CVSS basis, this is "a HIGH … advisory … for any SBOM component", so
**G5D section 6, stop condition 1, is tripped as of 2026-11-18**. Under G5D,
every scanning use is BLOCKED until the owner decides otherwise:

* the hosted trial;
* local scans;
* local tests that run the real engine.

Section 4 proposes an exception for **one hosted trial only**.

### Static reachability evidence (Linux wheel 1.185.0)

The ELF files were analysed from the re-downloaded, hash-verified wheel. No
binary from the wheel was executed.

1. **Only one binary loads libstdc++.** `semgrep-core` is the only bundled ELF
   file whose `DT_NEEDED` list includes `libstdc++.so.6`. Python extensions in
   the venv use the container's Ubuntu libraries, which are outside this
   advisory.
2. **`semgrep-core` never imports aligned `operator new`.** It imports 74
   libstdc++ symbols: `std::string`, iostream/ifstream, `getline`,
   `_Hash_bytes`, exception ABI and type-info symbols, and **plain**
   `operator new(size_t)` (`_Znwm`). None of these is
   `_ZnwmSt11align_val_t` or `_ZnamSt11align_val_t`, nor their nothrow forms.
3. **Inside libstdc++, aligned `new` has only two kinds of caller.**
   Disassembly finds its PLT stubs called only by:
   * the aligned nothrow and array wrappers;
   * one internal two-instruction thunk whose shape matches
     `std::pmr::new_delete_resource()`'s `do_allocate`.

   `semgrep-core` imports nothing from `std::pmr`.
4. **CVE-2026-102010 is header-only template code.** It affects only binaries
   that instantiate `__gnu_pbds::priority_queue`. `semgrep-core` keeps its
   symbol table, and it contains no `__gnu_pbds` symbol or string.
5. **The only C++ code in `semgrep-core` is crash-trace printing.** G5B records
   a single C++ unit, `backward.cpp` (`obackward`), which prints stack traces.
6. **The scan context is hardened.** The trial container:
   * runs with `--network none`, so the CVSS `AV:N` attack vector does not
     apply;
   * runs as uid 1001 with all capabilities dropped, `no-new-privileges`, a
     read-only root and `--ipc none`;
   * scans only the owner's repository with local, reviewed rules.

**Conclusion:** not reachable in our hardened offline execution, on static
evidence. This is the same kind of exposure as the six AlmaLinux advisories V7
already lists, and more clearly unreachable than the gcc advisory V7 already
covers (ALSA-2026:98524).

### Residual uncertainty

* **Static analysis only.** No dynamic trace of `semgrep-core` was run on Linux.
* **Indirect calls are not traced.** Calls through vtables and function pointers
  were not followed. Reaching the `pmr` allocator needs a `pmr` resource object,
  and `semgrep-core` imports nothing that creates one.
* **The `pmr` identification is inferred** from the code's shape: the library's
  local symbols are not exported.
* **`semgrep-core` imports `dlopen`/`dlsym`.** A library loaded at runtime that
  uses aligned `new` is not covered by this analysis. The bundled libraries
  that import `dlopen` are libcrypto, libdw, libkrb5support and libselinux.
* **The vendor's network attack vector reflects generic use,** not our offline
  setup. Exploitability under arbitrary inputs was not assessed. G5D section 7
  item 3 still requires dynamic tracing over adversarial inputs before E04.

## 2. Semgrep 1.186.0 early review (G5D section 6 trigger)

Semgrep 1.186.0 was published to PyPI on 2026-11-18. It was inspected only:
**no lock, venv or image was changed.** The Linux wheel inspected has
`sha256:54ebaf79adf4e5855c54d5e4457d8d03f27cc6bf73d79642281790b833d92e4f`.

| Area | Finding |
| --- | --- |
| G2 (V1, V2) | **Unchanged.** Same `requires_dist`: `mcp==1.29.0`, `opentelemetry-api~=1.37.0` |
| V3–V5 (OCaml runtime) | **Unchanged.** `semgrep-core` is built on the same `semgrep/ocaml` commit `4046c817` (OCaml 5.4.0) |
| V6 (OpenSSL in `cryptography`) | **Unchanged.** `cryptography` is a separate wheel; there is no release after 50.0.2 |
| V7 (bundled AlmaLinux libraries) | **Fully remediated in 1.186.0.** Rebuilt libraries include libstdc++/libgcc 11.5.0-17.el9_9.alma.1, OpenSSL 3.5.9-1.el9_9, glibc 2.34-290.el9_9, xz 5.2.5-8.el9_9.1, curl 7.76.1-43.el9 and elfutils 0.195. Versions come from debug-link names, the G5 method. OSV returns **0** AlmaLinux advisories for all 20 bundled packages at these versions, including ALSA-2026:98475 |
| Behaviour changes to re-verify | A new optional `secret_hash` output; `SEMGREP_METRICS_URL` is now respected; MCP telemetry redaction; a rebuilt `semgrep-core` |
| Security fixes stated in the release notes | None |

**Review result:**

* 1.186.0 is the remediation path for V7, including ALSA-2026:98475.
* It does not reduce G2 or V3–V6.
* It does not satisfy G5D section 7.

**Recommendation:** treat the 1.186.0 upgrade as a separate, owner-authorised
track, not part of this dispatch. That track would need:

* new hash-pinned Linux and macOS locks;
* SBOM v3 and a G5/G5B re-inventory;
* the G2 guard (including the metrics-URL behaviour), the E03 suite, the
  34-case matrix and the controls;
* a hosted re-run.

The G4H trial stays on the pinned 1.185.0.

## 3. Application dependencies: picomatch HIGH and mandatory CI

| Item | Value |
| --- | --- |
| CI status | Mandatory CI run **44216318120** at `268bc75`: the **`application` job failed** at `npm audit --audit-level=high`, so the `required` job failed closed. `policy` passed; `containers` and `codeql` were skipped |
| Advisory | **GHSA-fc5q-39xc-vjpf** (CVE-2026-112366): ReDoS in picomatch ≤ 4.0.7, triggered by crafted extglob patterns. GitHub severity **HIGH** (CVSS 3.1 `AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H`) |
| The 7 HIGH entries | One advisory, reported through `picomatch` 4.0.7, `tinyglobby`, `fdir`, `vite`, `vitest`, `@vitejs/plugin-react` and `@typescript-eslint/typescript-estree` |
| Moderate (8 entries, below the CI threshold) | GHSA-g3hv-75wg-m249, minimatch 10.2.6 through `eslint`, `@eslint/config-array` and `typescript-eslint` |
| Why the gate failed now | The lockfile is unchanged since `2b050a1`, whose CI passed. The advisory database changed |
| Presence | **Confirmed in the development dependency tree only.** The production-only audit (`--omit=dev`) reports 0 vulnerabilities. The API image installs with `--omit=dev`; the frontend image ships static files from nginx |
| Exposure | Theoretical. Glob patterns come from repository-controlled configuration, not from request input |
| Fix availability | **No fixed picomatch release** (4.0.7 is the latest and is vulnerable; upstream PR #194 is open and unmerged). The latest `vite` 8.3.8 and `vitest` 5.1.0 still require `picomatch ^4.0.7`. npm's suggested fixes are major-version downgrades and are rejected |

**Record:**

* This is **not waived** and no exception is proposed.
* `npm audit --audit-level=high` is unchanged.
* Mandatory CI stays **red** until one of the following:
  * (a) picomatch publishes a fixed release, followed by a **lockfile-only**
    update within the existing `^4` ranges, with no `package.json` change.
    This is the recommended path.
  * (b) a separate owner decision on the scope of the CI audit gate. That would
    be a change to a mandatory control, not a remediation.
* The moderate findings can be fixed with minor bumps, `eslint` 10.15.0 and
  `typescript-eslint` 8.73.0. Those are dependency changes and need separate
  authorisation.

**Relevance to the trial:**

* The G4H step `npm ci --ignore-scripts` installs this lockfile, including
  picomatch, on the runner.
* No picomatch code runs in the trial:
  * lifecycle scripts are disabled;
  * the TypeScript gate loads only the hash-verified `typescript/lib/typescript.js`;
  * Semgrep excludes `node_modules`.
* The trial is not a release gate, and its result cannot clear or offset the
  failed mandatory check.

## 4. Proposed exception X1: one G4H hosted trial only (WITHDRAWN 2026-11-18, path B)

Proposed, not approved. If approved, X1 suspends G5D section 6 stop condition 1
**for ALSA-2026:98475 only**, and **only** for the use defined here.

| Field | Proposal |
| --- | --- |
| Use | Exactly **one** dispatch of the existing workflow `.github/workflows/c5-sast-hosted-trial.yml` (G4H hosted TypeScript gate verification) on `main` |
| Advisory scope | ALSA-2026:98475 (CVE-2026-95619, CVE-2026-102010) in the Linux wheel's bundled libstdc++ and libgcc. No other advisory, and no other component |
| Time limit | From owner approval until the **earlier** of: (a) the end of that single run, whatever its result; (b) **2026-11-25 23:59 UTC**; (c) any stop condition in section 5. It never extends the G5D expiry (2026-12-17) |
| Not covered | Local scans, local engine-backed tests, any second or re-run dispatch, mandatory CI (E04), release and redistribution. Under G5D section 6, these stay BLOCKED or NO-GO unless the owner decides separately. This addendum does not propose resuming local scans |
| Basis | Static non-reachability (section 1); network-less hardened container; owner-controlled input; non-blocking, dispatch-only workflow with a six-file artifact allowlist |
| Not a waiver | The advisory stays OPEN and visible. Remediation is the separate 1.186.0 upgrade track (section 2) |

## 5. Conditions for one G4H hosted dispatch (WITHDRAWN with X1; not applicable)

### Before dispatch (all required)

1. **Approval.** The owner records approval of A1 to A3 below, with the date and
   an authorisation reference.
2. **Ref.** Dispatch runs on `main` at `268bc75` or a descendant whose changes
   relative to `268bc75` are documentation only (this addendum and status
   lines). These trial inputs must be **byte-identical** to `268bc75` (SHA-256):

   | File | SHA-256 |
   | --- | --- |
   | `scripts/sast/feasibility.py` | `78ae1f5d4d65eb0e63ea754b916b6cd331d3379873d9e780b779e60382416e6f` |
   | `scripts/sast/hosted_trial.py` | `6dde3e0d6fd665cc761379ba62aa8c68339b2641755178ba71c5cfd7d537d66a` |
   | `security/sast/toolchain.json` | `6f78e663eac723cd347c1bad0c426ce257f3aadb3e3615b579718bbc6bc6dc72` |
   | `security/sast/controls.json` | `ee61fedf3b6afce976189227cd7c41c48402082562cc368d291683b34d05dbe6` |
   | `security/sast/rules/typescript.yml` | `b03836178aa25b08201495f7cec0337cda14f55a42cfe964c8ef004b1709fc7c` |
   | `security/sast/rules/python.yml` | `526c3e7f56a9da409f491c088ea4e4104317bdae54bcbb017b1bc650799b1f73` |
   | `requirements-sast-linux.txt` | `8d7d13b691f4df781c9730b40344441fcf30ff59d3ac3d9ad495ee791a8b8b15` |
   | `security/sast/container/Dockerfile` | `58d355494b33afa832789114e90ee124ec423e67d9cb6219189ea0e0eec2b2ae` |
   | `.github/workflows/c5-sast-hosted-trial.yml` | `0fc6f22dafec175426ff4dff1d910077dbbe182a86dfc155c60300cdf7fabb4b` |
   | `scripts/sast/ts_syntax_gate.mjs` | `a91e8b91fbd7ee89317c6d0cb56723918c5c0bc1edb0bb885a0cd99695001e29` |
   | `security/sast/typescript-gate.json` | `3f46c454ed43917cd9dcab185acb3cc01c5c045bd9247441166f92a008d4db67` |
   | `scripts/sast/check_trial_workflow.py` | `587a54ed099f5f11ab3a97609070e5b93b87c40806b7ffeb3ef53ef50d0ea6d0` |
   | `apps/octocat-supply/package-lock.json` | `811c6683412ec606b159bc6e411f22594bd77a66997f264ceb1db41cd175a7fc` |
   | `apps/octocat-supply/.node-version` | `9185b9f67843cabfa8054f65ce47ce0b52036b0bfe07ae5a6b834d97cc127140` |

3. **Same-day advisory recheck.** An OSV and upstream recheck on the dispatch
   day shows:
   * no advisory for any SBOM component beyond those recorded in G5D and this
     addendum;
   * no known exploit for V1 to V8 or for ALSA-2026:98475;
   * no new Semgrep, `cryptography` or `semgrep/ocaml` release beyond those
     reviewed here.
4. **Local checks pass at the dispatch commit:**
   * `actionlint`;
   * `check_trial_workflow.py`;
   * `check_repository.py`;
   * the SAST test modules, including the G2 guard and the G4/G4H tests.
5. **No other trial run** is queued or in progress (the workflow has a
   concurrency group).
6. **Dispatch inputs:** `confirm = run-c5-f4-hosted-trial`, plus a **new**
   `authorization_reference` that names this addendum (for example
   `C5-G4H-1 G5D-A1 X1`).

### During and after the run

* **Exactly one run.** Rerunning or redispatching for any reason, including
  failure, needs a new owner decision.
* **Acceptance checks:** follow the G4H procedure in
  [m4c-c5-g4h-hosted-gate-preparation.md](m4c-c5-g4h-hosted-gate-preparation.md).
  In summary:
  * the artifact has exactly six files;
  * `container-run.json` `typescript_gate.exit` is 0;
  * `c5-summary.json` records `host-attestation`, TypeScript 6.0.3, Node
    v24.22.2, 49 parsed files and 5 rejected malformed controls;
  * the input hashes equal the table above;
  * no private report content is present.
* **A failure is a fail-closed result,** recorded as such and not waived.

### Immediate stop conditions

Any of the following **ends X1 at once**. No further dispatch, and the outcome
is recorded:

1. Any G5D section 6 stop condition other than the one X1 suspends, including:
   * a new HIGH or CRITICAL advisory;
   * an advisory shown reachable;
   * a guard, isolation or hash failure;
   * hardening or allowlist drift;
   * untrusted input;
   * the trial made blocking or automatic;
   * redistribution;
   * the lock, engine or SBOM no longer matching their recorded hashes.
2. Reachability of ALSA-2026:98475 shown by any means, or a public exploit.
3. Any trial input differing from the hashes in the table above.
4. The preflight reports a Node version other than v24.22.2, or a compiler
   mismatch.
5. Any isolation evidence fails, or any network egress is observed from the
   scan container.
6. The artifact contains anything other than the six allowlisted files, or any
   toolchain artifact is uploaded or cached.
7. The single run completes, or 2026-11-25 23:59 UTC passes.

## 6. Status preserved

* **G2:** OPEN.
* **G4:** OPEN, pending hosted verification.
* **G5:** OPEN. SBOM `analysis.state` values are unchanged.
* **E04, E05, E06, release and redistribution:** NO-GO.
* **Mandatory CI:** red (section 3), not waived.
* **G5D D1 to D6:** unchanged. Expiry stays 2026-12-17. This addendum
  authorises no dispatch by itself.

## 7. Reconciliation with the C5-U1 upgrade path (added 2026-11-18)

The owner-directed upgrade preparation
([C5-U1](m4c-c5-u1-semgrep-1.186.0-upgrade-preparation.md) and its
[pre-execution assurance](m4c-c5-u1b-pre-execution-assurance.md)) interacts
with X1 as follows.

| Point | Effect |
| --- | --- |
| Trigger | ALSA-2026:98475 affects the libstdc++/libgcc **11.5.0-14** bundled in the 1.185.0 Linux wheel. The 1.186.0 wheel bundles **11.5.0-17.el9_9.alma.1**, verified against the signed AlmaLinux RPM. The advisory, and the stop condition 1 trigger it causes, **does not apply to the 1.186.0 toolchain** |
| X1 dispatch conditions | Section 5 requires `requirements-sast-linux.txt`, `security/sast/toolchain.json` and `scripts/sast/feasibility.py` to equal `268bc75`. U1 changes all three. **X1 cannot be met once U1 is committed** |
| Toolchain coverage | X1 covers only the 1.185.0 toolchain. 1.186.0 is outside the G5D acceptance (stop condition 7) and needs its own owner decision |
| Paths | **Path A:** approve X1, dispatch once on `268bc75` (1.185.0) **before** committing U1, then commit U1. **Path B (recommended):** withdraw X1, retire the 1.185.0 toolchain, and verify G4H on the hosted runner only after U1 is executed locally and adopted. That needs no exception for ALSA-2026:98475 |
| Under path B | A1 sections 1 to 3 stay as the historical record for 1.185.0 (classification, reachability and the picomatch record). Sections 4 and 5 (X1) are withdrawn, not used. Local 1.185.0 scans stay BLOCKED (A5). G4H hosted verification moves to the 1.186.0 toolchain under a new per-run authorisation |
| Staging | Under path B, A1 and U1 can be committed together. Under path A, commit A1 alone, dispatch, then commit U1 |

## Owner decision (pending)

To be completed by the owner. Until then, every item is **NOT APPROVED**.

| # | Proposed decision | Owner response |
| --- | --- | --- |
| A1 | Record ALSA-2026:98475 as a confirmed-present, CVSS-HIGH advisory under V7, with the static non-reachability evidence and residual uncertainty in section 1 | _pending_ |
| A2 | Approve exception X1 (section 4) for exactly one G4H hosted dispatch under the conditions in section 5 | **WITHDRAWN** (owner, 2026-11-18, path B); not approved, never used |
| A3 | Record the Semgrep 1.186.0 early review (section 2), with the upgrade as a separate, unauthorised-until-approved track | _pending_ |
| A4 | Record the picomatch HIGH findings and the red mandatory CI without waiver; remediate through path (a) in section 3 | _pending_ |
| A5 | Confirm that local scans and local engine-backed tests stay BLOCKED under G5D section 6 (not covered by X1) unless separately decided | _pending_ |
| A6 | Choose path A (X1 on 1.185.0 before U1) or path B (withdraw X1; proceed with U1). Path B is recommended (section 7) | **PATH B** (owner, 2026-11-18). X1 is formally withdrawn; the 1.185.0 toolchain is retired from use; G4H hosted verification proceeds only on 1.186.0 after adoption ([U1E](m4c-c5-u1e-adoption-decision.md)) and a per-run authorisation |

## Changed files (A1)

* New: this document. Section 7 and decision A6 were added on 2026-11-18 (reconciliation with C5-U1).
* Modified (status lines only): `README.md`, `AGENTS.md`,
  `docs/capability-status.md`, `docs/milestones/m4c-c5-sast-plan.md`.
* Unchanged: the G5D decision record, both SBOMs, all locks and dependencies,
  `ci.yml`, the trial workflow, the harness, the driver, the tests and the
  application.
