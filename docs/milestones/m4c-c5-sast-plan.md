# M4C-C5 — Proposed SAST and release-governance implementation plan

Date: 2026-11-13. Status: **Design only; not authorized for implementation**.
Authority is assessment/planning only at `e9b5704`; the
[readiness assessment](../evidence/m4c-c5-readiness.md) and
[GET/verification evidence](../evidence/m4c-c5-readiness.json) record actual work.
This proposal refines C5-A1/A2 in [M4C scope](m4c-scope.md), without lowering either.
No step below has been executed. Stop after planning.

**C5-F1 execution update (2026-11-13, separately owner-authorized):** local Semgrep CE
feasibility only. See the [C5-F1 evidence](../evidence/m4c-c5-f1-semgrep-feasibility.md).
It adds the locks, toolchain manifest, original rules, control fixtures and a local
harness (`scripts/sast/feasibility.py`, not the planned `scripts/delivery/*` CI runner).
It records a non-clean source scan, parser/inventory gaps and conditions G1–G5. No
CI, policy or governance step was executed, and the matrix below stays as planned.

**C5-F2 update (2026-11-13):** the F1 harness ran unchanged on emulated Linux x86_64.
See the [C5-F2 evidence](../evidence/m4c-c5-f2-linux-feasibility.md): results match F1;
it found fail-open gaps (G6) and an egress-namespace dependency; mandatory CI is NO-GO.

**C5-F3 update (2026-11-13):** see the [C5-F3 evidence](../evidence/m4c-c5-f3-harness-hardening.md).
It adds the local harness hardening (catalogue, classification, exit codes, pip check/RECORD,
isolation probe), a literal-SQL test fix for G1 and a native-library inventory for G5.
F3 is ready for a separately authorized hosted trial; mandatory CI is not wired.

**C5-F4 update (2026-11-13):** see the [C5-F4 evidence](../evidence/m4c-c5-f4-hosted-trial-preparation.md).
It prepares, but does not run, a separate workflow_dispatch-only, read-only, non-blocking
hosted trial. `ci.yml` and the `required` gate are unchanged. Dispatching it needs owner
authorization. Owner run 43432851816 failed closed with exit 5 on Ubuntu 24.04's AppArmor
restriction on unprivileged user namespaces. See the
[diagnosis](../evidence/m4c-c5-f4-hosted-run-diagnosis.md). The owner then selected Option B: see
[C5-F4R](../evidence/m4c-c5-f4r-docker-trial-preparation.md) (Docker `--network none`, prepared and
locally validated). Owner run 43478654843 at `2b050a1` passed. The
[execution evidence](../evidence/m4c-c5-f4r-hosted-trial-execution.md) accepts hosted feasibility
(E02 met, E03 partly met). [E03 robustness](../evidence/m4c-c5-e03-robustness.md) later met E03 locally
(M11/M12/M14 with the real engine on both platforms); E04–E06, C5-A1/A2 and G2/G5 remain open (G4 later closed
for TypeScript only, below).
Per the [G2 assessment](../evidence/m4c-c5-g2-dependency-assessment.md) (advisories not reached in scans;
no Semgrep-compatible fix), the owner conditionally accepted G2 with a mitigation regression guard; the scope
was later narrowed and extended by G5D (below). G2 stays OPEN for mandatory CI (E04).
The [G5 assessment](../evidence/m4c-c5-g5-native-library-assessment.md) recommends local/trial GO, mandatory CI
NO-GO (owner decisions since recorded in G5D), and redistribution NO-GO; G5 stays open. [G5B](../evidence/m4c-c5-g5b-sbom-static-inventory.md)
added the project toolchain SBOM and semgrep-core static inventory; mandatory CI remains NO-GO.
[G5C](../evidence/m4c-c5-g5c-vulnerability-assessment.md) assessed the SBOM online: G5 cannot close yet; mandatory CI
and release remain NO-GO; its findings and the v2 SBOM candidate were decided in G5D.
[G5D](../evidence/m4c-c5-g5d-security-risk-decision.md) records the owner decision (2026-11-17): G2 incl. GHSA-mf5v
and G5 V3–V8 conditionally accepted for local trusted-repository scans and separately authorised non-blocking
trials until 2026-12-17 under its early-stop conditions and controls; SBOM v2 adopted as assessment baseline
(v1 frozen) for the now-retired 1.185.0 toolchain; G2/G5 OPEN; E04, release and redistribution NO-GO until its minimum remediation is met.
The [G4 assessment](../evidence/m4c-c5-g4-typescript-syntax-gate-assessment.md) recommends a syntax-only gate using the
pinned typescript 6.0.3 plus CI ordering on lint/typecheck. The [G4 implementation](../evidence/m4c-c5-g4-typescript-syntax-gate-implementation.md)
adds that gate to the harness (host attestation for container trials) and is verified locally. **E04 requirement:** the SAST
job must hard-depend (`needs:`) on the mandatory lint/typecheck job and provide the lock-pinned compiler. Hosted verification
prepared in [G4H](../evidence/m4c-c5-g4h-hosted-gate-preparation.md) passed in Run 44393309563 at `2e0bd25`
([G4H execution](../evidence/m4c-c5-g4h-hosted-gate-execution.md)); G4 is CLOSED for TypeScript only (JavaScript out of scope); the workflow then gained an explicit
setup-node `package-manager-cache: false`, enforced by the validator (not yet hosted-verified). [G5D addendum A1](../evidence/m4c-c5-g5d-addendum-a1.md) is the historical 1.185.0 record (ALSA-2026:98475, picomatch HIGH, red mandatory CI not
waived); the owner chose path B and exception X1 is withdrawn. [C5-U1](../evidence/m4c-c5-u1-semgrep-1.186.0-upgrade-preparation.md) prepared Semgrep 1.186.0,
[U1B](../evidence/m4c-c5-u1b-pre-execution-assurance.md) verified all 17 rebuilt libraries, [U1C](../evidence/m4c-c5-u1c-lt-u1-execution.md) and
[U1D](../evidence/m4c-c5-u1d-lt-u1-verification.md) record LT-U1 (S0–S8 passed), and the owner-approved [U1E](../evidence/m4c-c5-u1e-adoption-decision.md)
(2026-11-18) adopts 1.186.0 with SBOM v3 as baseline and G2 V1/V2 + G5 V3–V6/V8 conditionally accepted for local scans and authorised
non-blocking trials until 2026-12-17 (G2/G5 OPEN; G4 closed for TypeScript only). E04–E06 and release remain NO-GO.

## Entry decision and bounded scope

Recommend a local **Semgrep CE 1.185.0** feasibility slice with original MIT rules,
then mandatory CI integration only after parser/coverage/control results justify
it. The owner must select the engine/license/coverage proposal and authorize that
implementation slice. No entitlement, billing, visibility or repository-setting
change follows. Current CodeQL opt-in remains absent and its private eligibility
unestablished; local CodeQL is not a licensing fallback.

Preserve C1/C3/C4, application dependencies/behavior, SQLite, P01–P15, all existing
workflow checks/tool pins and Azure NO-GO. Do not add deployment/publishing/OIDC,
real provider/SQL/Azure access, paid rules/engines/accounts or C2/C6/C7/C8 work.
If the source scan reveals a finding needing an application or infrastructure fix,
record exact rule/location/severity and stop for bounded direction. Do not suppress,
rename, downgrade, ignore or waive findings to obtain green CI.

Proposed implementation surface (future files, not created by this plan):

| Surface | Proposed change / boundary |
| --- | --- |
| `requirements-sast-linux.txt`, `requirements-sast-macos.txt`; `security/sast/toolchain.json` | Dedicated complete wheel-only hash locks and engine/platform/license manifest, isolated from application and delivery dependencies |
| `security/sast/rules/typescript.yml`, `python.yml`; `targets.json`, `controls.json` | Original local rules with CWE/rationale/positive-negative bindings; exhaustive source classification and mandatory catalog hashes |
| `scripts/delivery/install_sast.py`, `scan_source.py`, `verify_sast_controls.py` | Verified tool install, offline real-engine scan, report/target/provenance validation, real seeded controls and safe outputs |
| `tests/delivery/test_sast.py`; `tests/security/sast/fixtures/` | Positive/negative rules plus parser, report, coverage, suppression, workflow and capture adversaries; unsafe code stays in fixtures/disposable copies |
| `scripts/delivery/verify_release_review.py`, `tests/delivery/test_release_review.py` | Optional local manifest/approval-predicate checks after governance route selection; never a release executor or proof of an authentic human approval |
| Existing `.github/workflows/ci.yml`, `scripts/delivery/policy.py`, `tests/delivery/test_security.py` | Future mandatory `source-security` job, aggregate success requirement, anti-bypass policy/mutations; no publish/deploy/write permissions |
| `THIRD_PARTY_NOTICES.md`, delivery/capability docs and new C5 execution evidence | Engine and full dependency rights/notices before adoption, exact results and limits; preserve original C1/C3/C4 evidence snapshots |

If feasibility requires changing this surface, licensing model, package scope or
coverage promise, report the gap before broadening implementation.

## Pinned candidate and supply-chain entry gate

Primary metadata: [release](https://github.com/semgrep/semgrep/releases/tag/v1.185.0),
[PyPI](https://pypi.org/pypi/semgrep/1.185.0/json),
[pinned source](https://github.com/semgrep/semgrep/tree/9240f708f8d7e2fbd38b67aa6cd17704b1f81e14).
Release tag object `18866f410389ff28d02310adeb770e9b3c59da56` peels to commit
`9240f708f8d7e2fbd38b67aa6cd17704b1f81e14`. Tag is unsigned; immutable release
metadata and PyPI hashes do not establish a verified publisher signature.

| Candidate platform | Exact wheel filename | Published SHA-256 |
| --- | --- | --- |
| macOS arm64 | `semgrep-1.185.0-cp310.cp311.cp312.cp313.cp314.py310.py311.py312.py313.py314-none-macosx_11_0_arm64.whl` | `d54c7dc22f6f360e0f9f850b1ecdfe00ec755600f9cf2ec6be3928b42818f1b4` |
| Linux x86_64, glibc >=2.34 | `semgrep-1.185.0-cp310.cp311.cp312.cp313.cp314.py310.py311.py312.py313.py314-none-manylinux_2_34_x86_64.whl` | `0eb6aaadad5b957af96d1300487e10af1dc8016e8ef53072effb48cd4906c02b` |

These are metadata observations, **not verified installed binaries**. Full URLs,
retrieval times and metadata hashes are in evidence. Engine metadata requires
Python >=3.10 and declares LGPL-2.1-or-later; root source contains LGPL 2.1 text.
Review wheel contents, bundled/transitive rights, notices and known tool/dependency
vulnerabilities before adoption. Author rules independently under project MIT;
never silently import the separately licensed maintained Semgrep rule pack.

Resolve all tool dependencies once under a separately approved implementation
scope, lock exact versions/hashes for each platform and interpreter, require binary
wheels and install with hashes/no dependency resolution from the verified local
wheelhouse. Reject missing/unpinned/yanked/incompatible artifacts and source builds;
no arbitrary setup hooks or engine/Pro auto-install. Root-wheel hashes alone do
not close transitive supply-chain risk. Existing `install_tools.py` handles native
archives/binaries, so do not force pip tooling into it or alter app lockfiles.
Record actual interpreter/platform, version, dependency audit and installed hashes.
Failure stops the slice; do not substitute an unreviewed version or paid service.

## Explicit coverage and source inventory

At this baseline, 65 tracked code files comprise 33 TS, nine TSX, eight MJS,
14 Python and one shell. Classify every file in a reviewed manifest; verify the
inventory against the actual snapshot on every run. Include new/untracked local
source before local acceptance; never infer safety from a Git ignore entry.
Generated dependencies/build output are excluded only through explicit reviewed
classification, with no runtime/tool source hidden. Tests/fixtures/configs need
separate classifications and parser/positive-negative coverage, not silent skips.

| Boundary | Required feasibility evidence | Limits retained |
| --- | --- | --- |
| 12 API source files, including auth/app/SQL/SQLite | Parse all; real rules for SQL concatenation/unsafe query calls, TLS bypass, unverified JWT trust, risky process execution and sensitive logging; safe bound-query and verified-JOSE controls | Single-function rules do not prove owner locks, transaction isolation or whole request authorization; preserve C1/C3/SQL tests and independent semantic review |
| Six frontend source files, including ID-token/session/API modules | Parse TS/TSX; unsafe HTML/eval, raw token/claim logging and configured crypto/trust bypass controls with safe pairs | Cross-module state/nonce, callback races, verified-before-publish and bearer-target ownership require C3/P01–P15 tests and explicit review |
| Eight MJS files and remaining TS/TSX | Parser probe and classification of application scripts, config and tests; rules where applicable; fixtures execute through an isolated control scan | Do not let intentionally unsafe fixtures fail the production scan, or mislabel them as production scan coverage; scan each through its specified control profile |
| 14 Python files, including ten delivery modules | Process/shell injection, insecure TLS and unsafe execution/logging positive-negative rules; scan future SAST runner/installer too | Subprocess/network uses may be intentional; review findings rather than broad path suppression |
| Shell, workflow YAML, Bicep/ARM and KQL | Retain proxy tests, mandatory workflow policy, eight-template compilation/Trivy/resource-policy mutations, parameter/redaction controls and manual review | CE Bash/YAML are experimental; no CE Bicep/KQL or live-policy proof is claimed; separately classify these outside the finite TS/Python SAST claim |

[CE language documentation](https://docs.semgrep.dev/semgrep-ce-languages) describes
community single-function analysis, not proprietary cross-file dataflow. Real TS 6,
TSX/MJS and Python parser probes precede rule acceptance. Exercise aliases,
constructed options, wrappers and cross-module variants to measure blind spots.
A missed critical case is a documented unresolved gate, never a fabricated scan
success. Existing behavioral checks complement finite static coverage; they do not
turn a missing source scan into SAST or automatically justify every blind spot.
An independent coverage review must judge C5-A1's suitability before closure.

## Mandatory fail-closed execution contract

Use `semgrep scan` with only owned local configuration, no `auto`/registry/URL,
platform login, Pro/AI, GitHub SARIF upload or source upload. Pinned CLI source
supports this proposed core command; it has **not** been run here:

```text
semgrep scan --oss-only --config <owned-local-rules> --metrics=off \
  --disable-version-check --no-trace --disable-nosem --no-git-ignore \
  --no-rewrite-rule-ids --strict --error --json --timeout 30 \
  --timeout-threshold 1 --max-memory 1024 --jobs 2 \
  --max-target-bytes 1048576 -- <explicit-target-arguments>
```

The runner must validate actual flag/report behavior against the pinned installed
engine. Before invocation, reject missing/empty/changed rules/catalog, unexpected
version/platform/hash, symlink/path escapes, unclassified/new/missing/oversize
source and unsafe config. Proposed per-file ceiling is 1 MiB (largest current
source about 34 KB), process deadline 120 seconds and CI job deadline ten minutes;
measure suitability, do not silently increase thresholds or omit files on timeout.
Use bounded subprocess argv without shell interpolation. No retry that converts
partial/failure into clean success.

Run in an isolated environment allowlist with an owned temporary
`SEMGREP_SETTINGS_FILE` and log path, without reading user-global Semgrep settings
or operational token values. Exclude inherited platform/OTEL/tracing credentials
and endpoints; explicitly disable metrics/version checking/traces. Prefetch only
reviewed verified artifacts during authorized installation, then deny scan-time
network egress. Test those denials; flags alone are not proof of zero egress.
See [metrics](https://docs.semgrep.dev/metrics) and
[CLI reference](https://docs.semgrep.dev/cli-reference).

A clean result requires engine exit success **and** a valid complete report:
expected version/rule IDs/catalog hash, no errors/parse failures/skips/timeouts/
truncation, exact agreement between expected targets and reported scanned paths,
zero security findings and source/rule/tool/config hashes tied to the reviewed
snapshot. Reject unknown severities/fields that defeat validation, malformed or
empty JSON, missing targets and exit-zero/error-report contradictions. Preflight
and postflight inventory checks must catch target omissions that the report does
not describe. Inline `nosemgrep` and ignore files must not suppress mandatory
controls. No severity or diff/baseline filter can hide a finding. Proposal blocks
**every finding**, preserving the existing HIGH/CRITICAL minimum without exceptions.

A seeded unsafe control passes only when the actual engine detects the intended
rule at the intended location with a complete valid report and expected finding
exit code; a parser/setup crash is a failed control. Its safe pair must parse and
remain clean. Mocked engines can test wrapper error paths but cannot substitute
for any actual-engine coverage assertion. Evidence records expected and actual
rule/location/outcome separately for each case.

Raw engine stdout/JSON may contain snippets, metavariables and sensitive values.
Keep it private with restrictive permissions in ignored `artifacts/sast-private/`,
outside existing CI upload roots (`artifacts/m3`, `artifacts/m4b`), and remove it
at job completion. Console uses fixed safe diagnostics. Publish only a schema-
allowlisted `artifacts/sast/report.json`: rule ID, severity, bounded relative path/
location, counts/status and hashes; no source lines, dataflow, arbitrary messages,
claims, URLs, headers or tokens. Canary tests must prove both stdout and the exact
artifact upload selection are safe. SARIF is not an entitlement workaround.

## Proposed CI and governance boundaries

After local feasibility, add an unconditional read-only `source-security` job to
the existing workflow on every current event (PR, main push and dispatch), scanning
the full candidate snapshot. No enable variable, path filter, `continue-on-error`,
optional engine or diff-only baseline. Use the verified toolchain and bounded
resources; retain all existing jobs/actions/permissions. The `required` job must
need `source-security` and accept **only success**, rejecting failure, cancellation,
skipped, neutral or absent results. Keep the skipped CodeQL history explicit;
never relabel it as execution or make the CE gate conditional on its opt-in flag.
No `security-events: write`, `id-token: write`, repository write, privileged
`pull_request_target`, deployment or publishing is needed for this profile.

Repository-owned workflow/rule/runner checks can all be edited by the same change.
Passing CI alone cannot resist a malicious change to its own verifier, particularly
on this unprotected main branch. An independent review of the exact implementation
and later changes, plus one verified governance route, is required:

1. **Protected route, if owner separately chooses and authorizes it:** establish
   supported entitlements, require independently approved PRs (at least one),
   stale-review dismissal or approval of latest push by another person, no admin/
   actor bypass, no force-push/deletion, and trusted check `required` bound to
   github-actions App ID **15368**. Protect workflow/rules/runner changes through
   independent review. Verify a supported private deployment environment's required
   reviewer, no self-review/bypass and branch restriction. A CODEOWNERS file alone
   does not enforce these controls. Settings verification/denials require separate
   human scope; Pro branch protection does not supply private Code Security or
   private required deployment reviewers automatically.
2. **Recommended no-purchase private direction, only if explicitly selected:** use
   [ADR 0005](../decisions/0005-delivery-identity.md)'s owner-operated release gate,
   with automatic release/OIDC still absent. Establish an independent reviewer
   and authentic approval channel outside the candidate's control. Bind approval
   to repository, exact source SHA/tree, workflow/rules/tool hashes, all check
   reports, image digests, config/schema, scope, expiry and operator identity.
   Refuse missing, stale, changed, self-approved or unauthenticated approval. A
   JSON/predicate test verifies local matching only; it cannot prove a real human,
   independence, channel integrity or execution-time enforcement. Those need actual
   external review evidence. No reviewer is established by this assessment.

No route is selected or implemented here. No release executor is included. Even
an eventual C5 pass cannot authorize Azure execution or close C2/C6/C7.

## Adversarial acceptance matrix — all Planned, none run

Use disposable source/workflow/report copies; no mutation of the owner's working
application or CI. Every rejection needs a control-specific reason, not a generic
setup error. The real engine is mandatory for detection rows.

| ID | Mutation / positive-negative control | Required future result |
| --- | --- | --- |
| C5-M01 | Interpolated/untrusted SQL versus bound parameters | Unsafe query detected by named rule; safe query clean |
| C5-M02 | Disabled certificate/hostname verification versus verified TLS | Bypass detected; legitimate test-fixture context explicitly classified |
| C5-M03 | Decode-only/untrusted JWT key, issuer or algorithm versus verified JOSE | Actual detectable bypass variants fail; missed aliases/wrappers remain an open coverage gate |
| C5-M04 | Tainted process command / Python shell=True versus fixed argv | Unsafe execution detected; safe pair clean |
| C5-M05 | Unsafe HTML/eval versus escaped JSX | Real TSX parser and matching controls behave as specified |
| C5-M06 | Bearer/claims/callback-value logging versus fixed error codes | Unsafe logging detected; safe pair clean; finite dataflow limits documented |
| C5-M07 | Malformed TS/TSX/Python | Parser failure blocks, never counted as detected vulnerability or clean scan |
| C5-M08 | New/missing/oversize source, path escape, ignore entry or inline suppression | Inventory/config blocks omission or real unsafe detection persists; no silent skip |
| C5-M09 | Remove/empty/disable/downgrade a rule or change catalog/hash | Mandatory-rule/catalog policy rejects tampering |
| C5-M10 | Wrong engine/version/checksum/platform or missing tool dependency | Installation/run fails closed, without source build/alternate engine fallback |
| C5-M11 | Timeout, crash, killed process, partial/empty/truncated/malformed JSON or skipped target | Scan rejected, exact safe failure class recorded |
| C5-M12 | Forged exit 0 with report errors/findings/coverage mismatch | Report/inventory validator rejects independently of exit code |
| C5-M13 | Remote/auto rules, Pro, token/metrics/trace destination or network attempt | Configuration/environment/egress controls reject; no remote fallback |
| C5-M14 | Canary fragments in raw source/results/messages/dataflows/stdout/upload roots | Published console/artifacts contain no canaries; raw report never uploaded |
| C5-M15 | Conditional/omitted SAST job, path filters or continue-on-error | Workflow policy rejects every bypass variant |
| C5-M16 | Remove aggregate dependency or permit skipped/cancelled/neutral/failed result | Executable aggregate matrix blocks every non-success/absent state |
| C5-M17 | Add PR write/OIDC/security-events privileges or privileged PR execution | Existing and new policy reject privilege escalation |
| C5-M18 | Change approved SHA/tree/tool/rules/report/image/config/schema/scope/expiry | Review-manifest predicate rejects mismatch/staleness |
| C5-M19 | Missing reviewer, owner self-review or invented approval identity | Predicate rejects; authentic independent external evidence remains separately required |
| C5-M20 | Cross-file ownership/session/authorization variant beyond CE capability | Record actual miss/coverage limit; complementary tests and independent review required; never claim CE detection without output |

## Execution order and acceptance decision

| Gate | Future evidence required | Current status |
| --- | --- | --- |
| C5-E01 Entry | Owner selects finite engine/license/coverage and separately authorizes exact implementation; complete dependency/rights/advisory review | Planned; not selected/adopted |
| C5-E02 Feasibility | Real installed version/hashes, every target parser-compatible, reviewed exhaustive classification, initial actual scan and M01–M06 safe/unsafe results | Not executed |
| C5-E03 Robustness | M07–M14 report/inventory/supply-chain/egress/capture controls fail closed; safe controls pass | Not executed |
| C5-E04 Mandatory CI | `source-security`, strict aggregate, M15–M17 and existing policy tests pass without disabling any old gate | Not implemented |
| C5-E05 Coverage/review | Human reviews real source findings and finite limitations/M20; no unresolved blocking finding or critical unsupported boundary | No SAST result or coverage acceptance |
| C5-E06 Governance | Owner selects supported route, establishes independent reviewer/authentic channel; M18–M19 and actual route evidence satisfy C5-A2 | Blocked; main unprotected, no environments/reviewer established |
| C5-E07 Regression | Existing application 195-test baseline, SQLite/C1, C3 P01–P15/browser/capture, 22 delivery tests, proxy/container security and eight-template C4 checks stay green; no scanner waiver | Not rerun in planning |
| C5-E08 Reviewed source | Exact SHA/tree/tool/rules/target/report hashes, scan time/exit/findings, mutation results and independent acceptance; owner manually commits/pushes separately for hosted evidence | Not executed; no commit/push authorized here |

**C5-A1** requires E01–E05/E07–E08: an actual reviewed-source scan, justified
coverage and all real positive/negative/error/bypass controls, not merely a pinned
binary, parser success or mocked wrapper tests. **C5-A2** requires E06 and genuine
independent review bound to those exact results. A manual manifest alone is not
server enforcement; distinguish the chosen fallback's limits. Missing proof leaves
its gate Blocked. No waiver of HIGH/CRITICAL findings or invented exception.

Risks include CE false negatives/interprocedural limits, TS 6 parser uncertainty,
original-rule maintenance/false positives, unsigned upstream tag/transitive supply
chain, report leakage, and same-change verifier tampering. Actions compute/storage,
local tool downloads and human review can cost money/time; no free quota or paid
entitlement is assumed. No services were activated or runtime/cost benchmarked.
The assessment's read-only plan observations can become stale and must be refreshed
before future route acceptance without turning a refresh into settings mutation.

Recommendation: **planning complete; conditional GO for a separately authorized
feasibility/implementation slice; NO-GO for C5 acceptance, automatic release and
Azure deployment.** Stop here. C2/C6/C7/C8 and cloud actions remain outside scope.
