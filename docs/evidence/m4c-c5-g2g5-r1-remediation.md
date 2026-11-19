# M4C-C5 — G2/G5 remediation step R1 (owner-approved), with a draft R2(a) decision

Date: 2026-11-18 UTC. Baseline: commit `9e4bedb` (`origin/main`). CI for
`9e4bedb` (run 44418461737) passed; `npm audit` reports 9 moderate minimatch
findings, below the unchanged high threshold and not waived.
Machine-readable record: [JSON](m4c-c5-g2g5-r1-remediation.json).

**Scope:** only R1 from the read-only G2/G5 remediation assessment. Nothing in
this record waives, dismisses or re-rates a finding.

* **Unchanged:** G2 and G5 remain **OPEN**. G4 remains **closed for
  TypeScript only**. E04, E05, E06, release and redistribution remain
  **NO-GO**.
* **Not done:** no Semgrep execution, dependency change, dispatch, external
  message, commit or push.

## 1. G5D section 7 item 4: no redistribution in hosted use (recorded)

G5D section 7 item 4 requires confirming that CI use involves no
redistribution, and that the artifact allowlist is kept. For the
owner-dispatched, non-blocking hosted trial at `9e4bedb`, the following
holds.

| Control | Evidence |
| --- | --- |
| Toolchain obtained per run, never stored | The hash-locked wheels are downloaded into `$RUNNER_TEMP/c5-wheels` (`pip download --require-hashes --no-deps --only-binary=:all:`). The venv is created in `$RUNNER_TEMP/c5-sast` by an offline install inside a `--network none` container. Both disappear with the ephemeral runner |
| Container image never published | The driver uses only `docker build` (local, `--iidfile`), `docker run` (with `--pull never`) and `docker image inspect`. There is **no** `push`, `login`, `tag`, `save` or registry reference. The validator rejects raw docker or namespace tools in the workflow |
| Caching disabled | `setup-node` sets **`package-manager-cache: false`** explicitly (`9e4bedb`), and the validator requires exactly that value. No `actions/cache` or any other unreviewed action is allowed: the validator rejects unpinned or unreviewed actions. Read-only check: the repository has **0 Actions caches** |
| Artifact allowlist | The upload step allows **exactly** the six reviewed JSON evidence files (validator: "Upload allowlist must be exactly the six reviewed evidence files"), with retention ≤ 7 days. Run 1's artifact held 6 JSON files (40,812 bytes uncompressed) and no wheels, venv, image, raw engine reports or private reports |
| Permissions | `contents: read`. Default workflow permissions are `read`. Checkout uses `persist-credentials: false` |

**Conclusion:** hosted use as designed involves **no redistribution** of the
toolchain (wheels, venv, wheelhouse or image). G5D section 7 item 4 is
satisfied for the hosted trial.

This does not authorise E04. Any future CI job must meet the same controls,
and redistribution itself remains **NO-GO** (G5 licensing and notice
obligations are unmet).

## 2. macOS-specific findings, recorded as out of the proposed Linux CI scope (not dismissed)

| Finding | Component | Platform | Status |
| --- | --- | --- | --- |
| **G5 V8**: CVE-2026-116732 (libdwarf out-of-bounds read on crafted object files) | `libdwarf.2.dylib` 2.3.3 (Homebrew bottle) in the **macOS** wheel | macOS arm64 only. The Linux wheel uses AlmaLinux `elfutils` `libdw`/`libelf`, not libdwarf | **OPEN, `in_triage`.** Upstream fix `71f04013` is not in any libdwarf release (ahead of v2.3.3) |
| OSV-2026-343 (heap overflow in `pcre2_compile_32`) | `libpcre2-8.0.dylib` 10.47 (Homebrew bottle) in the **macOS** wheel | macOS arm64 only. The Linux wheel's PCRE2 is a signed AlmaLinux build with no open advisory | **OPEN, `in_triage`.** The affected function is in the 32-bit code-unit library while the bundle ships the 8-bit library, so applicability is unconfirmed. Fix `e19e76ad` is not an ancestor of any release tag (10.49 diverged) |

**Meaning of "outside the proposed Linux CI scope":**

* A Linux CI job (E04, not authorised) would install only the
  `manylinux_2_34_x86_64` wheel. These two components would not be present in
  that job.
* They **remain open** for the conditionally accepted local macOS use (U1E
  E1/E3; expiry 2026-12-17) and stay listed in SBOM v3.
* This record does not change their analysis state, rating or acceptance.

## 3. Guard strengthening: `test_engine_invocation_platform_wrapper`

`tests/security/sast/test_g2_mitigation_guard.py` (SHA-256
`0ac3de5d…f286` → **`42672fd941fde28e387d4dd461e3b5d216e64597c0cc7bb20549f37ca6b04a79`**).

The test now:

* runs with the deterministic hostile caller environment
  (`MUTATION_CALLER_ENV`, caller `PATH` `/c5g2/bin:/usr/bin:/bin`);
* asserts that this caller `PATH` differs from the pin;
* asserts that the tool and engine `PATH` equal the pinned `/usr/bin:/bin`;
* then applies the unchanged `check_engine`, plus `check_tool_env`.

The fail-closed branch for unsupported operating systems is preserved. No
assertion was removed or relaxed.

| Check | Result |
| --- | --- |
| Unchanged harness, normal shell and `env -i PATH=/usr/bin:/bin` | Pass |
| Disposable copy with the harness `PATH` pin removed, both environments | **Fails** (`'/c5g2/bin:/usr/bin:/bin' != '/usr/bin:/bin'`). Before this change it passed in the `env -i` environment |
| Whole guard against the pin-removed copy, `env -i` | **6 tests fail** (previously 5): the mutation anchor, the source check, container mode, platform wrapper, the hostile environment and the positive control |

### Binding implication (resolved 2026-11-19 by U1E addendum 1)

This file's hash is one of the **U1E section 3 adoption hashes**. U1E E5(a)
says to stop immediately if any section 3 hash changes. Therefore:

* **Until the owner rebinds the hash,** U1E E5(a) applies: no Semgrep scan,
  local or hosted, may run under the U1E acceptance. None is planned or
  authorised.
* **This record deliberately does not edit U1E, U1B or U1C.** Those records
  stay accurate for their dates, and the U1 consistency check reports exactly
  this one expected mismatch: `236/237`, with the failure `evidence hash
  tests/security/sast/test_g2_mitigation_guard.py`. It was not suppressed.
* **Proposed rebinding (pending):** an owner decision recorded as a U1E
  addendum that:
  1. replaces the guard hash `0ac3de5d…f286` with `42672fd9…4a79` in U1E
     section 3 (strengthening only; the harness, toolchain, locks, controls,
     rules, inventory and SBOM v3 are unchanged);
  2. updates the U1B binding that the consistency check reads.

  Afterwards the consistency check should return to 237/237 and the E5(a)
  stop clears.

**Resolution (2026-11-19):** the owner approved the narrow rebinding, recorded
in [U1E addendum 1](m4c-c5-u1e-addendum-1-guard-rebinding.md).

* Only the active U1E section 3 binding and the U1B consistency reference
  were updated; U1, U1C, U1D and the LT-U1 outputs are preserved.
* No other adopted input changed.
* Consistency is **237/237**, and the E5(a) stop for this file is cleared.

The bullets above record the state at R1 time (2026-11-18).

## 4. Draft R2(a) decision: owner-controlled `main` only (REFINED 2026-11-19; PROPOSED, NOT APPROVED)

This satisfies the alternative in G5D section 7 item 3: "an owner decision that
CI only scans trusted branches". It is a **proposal**. It authorises nothing,
changes no workflow, driver, CI file or GitHub setting, and does not open E04.

**Observed repository state (read-only, 2026-11-18):**

* the repository is **private**, the owner is the **only** collaborator, and
  the default branch is `main`;
* default workflow permissions are **read**;
* **fork pull-request workflows are disabled**, with no write tokens or secrets;
* `allowed_actions: all`;
* **branch protection and rulesets are unavailable on the current plan**
  (HTTP 403);
* there is no `CODEOWNERS` file;
* `ci.yml` runs `actionlint` on all workflows, but not the trial validator or
  the SAST tests.

### Proposed scope

| # | Rule |
| --- | --- |
| S1 Trusted content | Only commits on **`refs/heads/main` of this repository, pushed or dispatched by the repository owner** |
| S2 Allowed triggers | Exactly `push` with `branches: [main]`, and `workflow_dispatch` on `main` |
| S3 Excluded | **No pull-request or fork scanning of any kind.** Never `pull_request`, `pull_request_target`, `merge_group`, `workflow_run`, `schedule` or `repository_dispatch`. Pull-request content gets no SAST before merge; findings surface after merge on `main` (accepted consequence) |
| S4 Job posture | `contents: read`; no secrets; non-blocking until E04 is separately authorised; the existing G5D/U1E controls apply (hardened network-less container, six-file allowlist, caching disabled) |

### Enforcement without branch protection

Branch protection and rulesets cannot be used on this plan, so the platform
cannot *prevent* a push to `main`. The proposal therefore layers
**preventive checks the repository can run itself**, a **fail-closed runtime
check**, and **detective controls**. Each item needs separate approval to
implement.

| # | Control | Type | What it does |
| --- | --- | --- | --- |
| C1 | Workflow shape, enforced by the validator | Static, preventive | Extend `check_trial_workflow.py` (or a sibling validator for any SAST CI workflow). The `on:` keys must be exactly `{push: {branches: [main]}, workflow_dispatch}`. A job-level `if:` must require `github.ref == 'refs/heads/main'`, `github.actor == github.repository_owner` and `github.triggering_actor == github.repository_owner`. Reject every excluded trigger, `contents: write` and any `secrets.` reference |
| C2 | Runtime fail-closed check in the driver | Runtime, preventive | Before any download or container, the driver refuses to proceed (exit 2) unless `GITHUB_EVENT_NAME` is `push` or `workflow_dispatch`, `GITHUB_REF` is `refs/heads/main`, `GITHUB_REPOSITORY` is the expected repository, and `GITHUB_ACTOR` and `GITHUB_TRIGGERING_ACTOR` are the repository owner (`GITHUB_REPOSITORY_OWNER`). The decision is recorded in the evidence. This holds even if the workflow's `if:` is edited, provided the driver itself is unchanged (C4 detects driver changes) |
| C3 | Governance precondition | Read-only, detective | Before every authorised run, and at least weekly: the collaborator list is exactly the owner; the repository is private; fork-PR workflows are disabled with no tokens or secrets; default workflow permissions are read. Any drift stops scanning until reviewed |
| C4 | Change control and hash binding for SAST-relevant paths | Procedural and detective | `.github/workflows/**`, `scripts/sast/**`, `security/sast/**`, `requirements-sast-*.txt` and `tests/security/sast/**` change only by owner commits. The validator and engine-free SAST tests must pass locally before commit. Approved hashes are recorded (as in U1E section 3). After each run, the run's `input_sha256sum` is compared with the approved list; any mismatch invalidates the result and triggers G5D stop condition 4. A `CODEOWNERS` file for these paths is advisory only |
| C5 | Post-run verification | Detective | The artifact digest matches; there are exactly six files; the run's `headSha` is on `main`; the event and actor match S1/S2. The C2 decision is present in the evidence |
| C6 | Optional CI enforcement | Preventive (CI) | Run `check_trial_workflow.py` and the engine-free SAST tests in the mandatory policy job. This is a `ci.yml` change and needs E04-level direction |

### What this cannot enforce (residual risk if approved)

* GitHub will not stop the owner, or anyone holding a compromised owner
  credential, from editing the workflow, driver or validator and pushing to
  `main`. Because C1/C2 live in the same repository, a malicious change could
  remove them. That is caught only by C4 (hash comparison and owner review)
  and C5, **after** the push.
* Without required status checks, a failing validator does not block a merge
  or push. It is visible only through the local pre-commit procedure, or
  through CI under C6.
* Pull-request code is not scanned before merge (S3).
* Plan upgrades (branch protection or rulesets) and `allowed_actions: selected`
  would close some of these gaps. They are GitHub setting or plan changes and
  are not authorised.

### Effect if approved

* Satisfies G5D section 7 item 3 **by scope**.
* Does **not** satisfy item 1 (the upstream-blocked vulnerabilities).
* E04 stays **NO-GO**.
* C1–C6 each need separate implementation approval.

## 5. Remaining upstream blockers and expiry

| Finding | Blocked on | Our action when unblocked |
| --- | --- | --- |
| G2 V1: `mcp` 1.29.0 (4 moderate GHSAs; fix ≥ 1.30.0) | Semgrep pins `mcp==1.29.0` (also on `develop`). Upstream PR #12057 is open, `mergeable_state: blocked`, 0 reviews | Semgrep upgrade track (as U1) |
| G2 V2: `opentelemetry-api` 1.37.0 (GHSA-xcq7 fixed in 1.45.1; GHSA-mf5v fixed in **1.45.2**) | Semgrep pins `~=1.37.0`. PR #12057 bumps only to **1.45.1**, which would leave GHSA-mf5v open | Semgrep upgrade track. Verify ≥ 1.45.2 |
| G5 V3–V5: OCaml 5.4.0 fork `4046c817` (7 OSEC advisories in triage) | A Semgrep rebuild on OCaml ≥ 5.4.1/5.5.2 or backports. The `develop` lockfile is still 5.4.0; the fork has no newer branch | Semgrep upgrade track |
| G5 V6: OpenSSL 4.0.3 in `cryptography` 50.0.2 (6 CVEs) | The OpenSSL fix commits are in **no release** (ahead of 4.0.3/4.1.0); `cryptography` 51.0.0 is unreleased | **Lock-only `cryptography` bump** (compatible: `pyjwt[crypto]` needs ≥ 3.4) with full U1-style re-verification |
| G5 V8 (libdwarf) and OSV-2026-343 (PCRE2): macOS only | No release with the fixes; a Semgrep macOS rebuild is needed | Semgrep upgrade track |
| G5 licensing and notices | Notices and source correspondence (redistribution only) | Not needed while redistribution is NO-GO |

**Expiry:** the U1E conditional acceptance of G2 V1/V2 and G5 V3–V6/V8 expires
**2026-12-17** (29 days from this record). It needs a renewal decision before
then; otherwise every use other than local development becomes BLOCKED. The
guard-hash E5(a) stop (section 3) was cleared on 2026-11-19 by U1E addendum 1.

## 6. Verification (no engine)

See the JSON record. Summary:

* G2 guard 9/9 in both environments;
* engine-free SAST modules 88 run, 58 pass, 30 skipped (engine), in both
  environments;
* `actionlint` and the trial-workflow validator pass;
* repository, whitespace, JSON, link, personal-data and gitleaks checks pass;
* consistency **236/237** at R1 time (the single expected guard-binding
  mismatch), restored to **237/237** after U1E addendum 1 (2026-11-19).

## Changed files (R1)

* **Modified:** `tests/security/sast/test_g2_mitigation_guard.py` (one test
  strengthened); status lines in `AGENTS.md`, `README.md`,
  `docs/capability-status.md` and `docs/milestones/m4c-c5-sast-plan.md`.
* **New:** this document and its JSON record.
* **Follow-up (2026-11-19):**
  * new: `docs/evidence/m4c-c5-u1e-addendum-1-guard-rebinding.md` and `.json`;
  * active-binding updates in the U1E Markdown/JSON and the U1B Markdown/JSON
    (guard entry only, annotated).
* **Not changed:** the workflow, validator, harness, driver, toolchain, locks,
  SBOMs, `ci.yml`, GitHub settings, the U1C/U1D/G5D records, and the U1E/U1B
  content other than the annotated guard binding.
