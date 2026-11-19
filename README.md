# Enterprise Agentic SDLC & Reliability Platform

An Azure-first engineering portfolio demonstrating agent-assisted SDLC, DevSecOps,
observability, SRE incident diagnosis, controlled remediation, recovery, and GitHub
engineering handoffs.

**Current stage: M4C-C5-F4R closed out — hosted Docker SAST trial run 43478654843 at
`2b050a1` passed (exit 0, 69 targets, 0 findings, controls as catalogued); hosted SAST
feasibility accepted; [E03 robustness](docs/evidence/m4c-c5-e03-robustness.md) met locally;
the [G5D owner decision](docs/evidence/m4c-c5-g5d-security-risk-decision.md) (2026-11-17) covered the now-retired 1.185.0 toolchain
([G2](docs/evidence/m4c-c5-g2-dependency-assessment.md), [G5](docs/evidence/m4c-c5-g5-native-library-assessment.md)/[G5C](docs/evidence/m4c-c5-g5c-vulnerability-assessment.md); SBOM v2, [G5B](docs/evidence/m4c-c5-g5b-sbom-static-inventory.md) v1 frozen);
[G4 TypeScript syntax gate](docs/evidence/m4c-c5-g4-typescript-syntax-gate-implementation.md) implemented and verified locally
([G4H](docs/evidence/m4c-c5-g4h-hosted-gate-preparation.md) workflow; hosted Run 1 44393309563 at `2e0bd25` passed per [G4H execution](docs/evidence/m4c-c5-g4h-hosted-gate-execution.md);
G4 CLOSED for TypeScript only; JavaScript out of scope).
[G5D addendum A1](docs/evidence/m4c-c5-g5d-addendum-a1.md) is the historical 1.185.0 record (ALSA-2026:98475); path B chosen, exception X1 WITHDRAWN (never used).
**Semgrep CE 1.186.0 is ADOPTED** per the owner-approved [U1E decision](docs/evidence/m4c-c5-u1e-adoption-decision.md) (2026-11-18), based on
[C5-U1](docs/evidence/m4c-c5-u1-semgrep-1.186.0-upgrade-preparation.md), [U1B](docs/evidence/m4c-c5-u1b-pre-execution-assurance.md) (17/17 rebuilt libraries verified),
[U1C](docs/evidence/m4c-c5-u1c-lt-u1-execution.md) and [U1D](docs/evidence/m4c-c5-u1d-lt-u1-verification.md) (LT-U1 S0–S8 passed): G2 V1/V2 and G5 V3–V6/V8 are
conditionally accepted only for local trusted-repository scans and separately authorised non-blocking trials, scoped to the U1E hashes,
until 2026-12-17 under the G5D/U1E stop conditions; schema-valid SBOM v3 is the baseline (G2/G5 OPEN, not waived).
Mandatory CI at `2e0bd25` passed (run 44380044262) after GitHub withdrew picomatch GHSA-fc5q-39xc-vjpf; 9 moderate minimatch findings remain below the
unchanged high threshold, not waived. G4H Run 1 on 1.186.0 passed (clean, 0 findings); owner-approved setup-node `package-manager-cache: false` hardening applied afterwards (not yet hosted-verified).
[G2/G5 R1](docs/evidence/m4c-c5-g2g5-r1-remediation.md): no-redistribution record, macOS-only V8/PCRE2 scope note, guard strengthening rebound by [U1E addendum 1](docs/evidence/m4c-c5-u1e-addendum-1-guard-rebinding.md) (2026-11-19), R2(a) main-only proposal (not approved); [R2(a) P1](docs/evidence/m4c-c5-r2a-p1-trusted-input.md) adds the driver's offline fail-closed trusted-input check (P2–P6 pending).
Mandatory SAST CI (E04), release, redistribution, C5 acceptance and deployment remain NO-GO.**
C1/C3 local acceptance and C4 static validation are preserved. Read-only checks
confirm C4 commit `e9b5704`, hosted run 43407086701: policy/application/containers/
required passed, CodeQL skipped. CodeQL's opt-in flag is absent; private eligibility
and independent release governance remain unestablished. Main is unprotected and
no environments exist. [C5-F1](docs/evidence/m4c-c5-f1-semgrep-feasibility.md)
locally installed hash-locked Semgrep CE 1.185.0 with original rules. All controls
behave as expected, but the real scan has one untriaged test-file finding.
[C5-F2](docs/evidence/m4c-c5-f2-linux-feasibility.md) reproduced identical results on
Linux x86_64, but found harness fail-open gaps and an unverified hosted-runner egress
restriction. [C5-F3](docs/evidence/m4c-c5-f3-harness-hardening.md) closed those
harness gaps and the test-file finding (clean scans on both platforms); hosted-runner
isolation, tool advisories and native-library notices remain open, so mandatory SAST
CI remains NO-GO. [C5-F4](docs/evidence/m4c-c5-f4-hosted-trial-preparation.md) adds a
dispatch-only, read-only, non-blocking trial workflow; its first hosted run failed closed on
AppArmor user-namespace restriction ([diagnosis](docs/evidence/m4c-c5-f4-hosted-run-diagnosis.md)).
[C5-F4R](docs/evidence/m4c-c5-f4r-docker-trial-preparation.md) moves install and scan into a
digest-pinned `--network none` hardened container; its hosted run succeeded and is reviewed in the
[execution evidence](docs/evidence/m4c-c5-f4r-hosted-trial-execution.md). G2/G5 and governance remain open (G4 closed for TypeScript only). C5 acceptance and C2/C6/C7/C8 remain open; no live
network/SQL/provider/identity enforcement or Azure readiness follows from CI.
Azure session/permission/quota checks remain blocked. Morrow Supply is
an independently implemented React/TypeScript, TypeScript API and local SQLite
demo with original synthetic data and illustrations. OctoCAT Supply is the
conceptual reference; no upstream application source or assets were copied.
Agents, cloud deployment and release execution remain planned.

## Project documents

| Document | Purpose |
| --- | --- |
| [M4C readiness assessment](docs/evidence/m4c-readiness-assessment.md) | Dated M4B baseline, real SQL/provider gaps, governance reads and verification limits |
| [M4C work packages](docs/milestones/m4c-scope.md) | Completed C1; C3 accepted locally with Simulated providers; remaining dependency order, acceptance tests, boundaries and costs |
| [C1 repository evidence](docs/evidence/m4c-c1-repository-contracts.md) | 27 shared contracts and six SQLite regressions; real SQL C2 handoff remains Blocked |
| [C3 OIDC/PKCE plan](docs/milestones/m4c-c3-oidc-plan.md) | Approved design, original gap assessment, test matrix and separately authorized execution update |
| [C3 implementation evidence](docs/evidence/m4c-c3-oidc.md) | Actual-library PKCE/nonce/ID-token/session tests, seven local browser journeys, capture controls, scans and C6 limits |
| [C5 readiness assessment](docs/evidence/m4c-c5-readiness.md) | Read-only CodeQL/entitlement, branch/reviewer/environment facts, limits and NO-GO recommendation |
| [C5-F1 Semgrep feasibility](docs/evidence/m4c-c5-f1-semgrep-feasibility.md) | Toolchain provenance/licences/advisories, original rules, control and real-scan results, timing, fail-closed checks, G1–G5 conditions |
| [C5-F2 Linux verification](docs/evidence/m4c-c5-f2-linux-feasibility.md) | Linux toolchain/harness parity, fail-closed matrix, namespace isolation, time/memory, G1/G2 reconciliation and mandatory-CI NO-GO |
| [C5-F3 harness hardening](docs/evidence/m4c-c5-f3-harness-hardening.md) | Control catalogue, exhaustive classification, exit codes, toolchain/RECORD integrity, isolation diagnostics, G1 fix, native-library inventory, 34-case mutation matrix |
| [C5-F4 hosted trial preparation](docs/evidence/m4c-c5-f4-hosted-trial-preparation.md) | Dispatch-only trial workflow, validator/mutations, local Ubuntu simulation, G2/G5 risk register and owner run steps (not executed) |
| [C5-F4 hosted run diagnosis](docs/evidence/m4c-c5-f4-hosted-run-diagnosis.md) | Run 43432851816 exit 5 cause (AppArmor userns restriction), runner facts vs expectations, alternatives and proposed C5-F4R plan |
| [C5-F4R Docker trial preparation](docs/evidence/m4c-c5-f4r-docker-trial-preparation.md) | Pinned Ubuntu 24.04 runtime image, hardened network-less containers, in-container isolation proof, exit codes 0–7, provenance/licences, local results and owner steps (not dispatched) |
| [C5-F4R hosted trial execution](docs/evidence/m4c-c5-f4r-hosted-trial-execution.md) | Run 43478654843 identity/integrity, isolation controls, results vs local expectations, feasibility GO and remaining G2/G4/G5/governance blockers |
| [C5 E03 robustness](docs/evidence/m4c-c5-e03-robustness.md) | M11 failure handling, M12 forged reports, M14 canary capture with real engine on both platforms; four harness/driver gaps fixed; 34-case matrix preserved |
| [C5 G2 dependency assessment](docs/evidence/m4c-c5-g2-dependency-assessment.md) | Five MODERATE `mcp`/`opentelemetry-api` advisories verified; traced as not reached during scans; no compatible fix; owner conditional acceptance (local/trial only, expires 2026-12-17; open for mandatory CI; not waived); regression guard for flags/environment |
| [C5 R2(a) P1 trusted-input enforcement](docs/evidence/m4c-c5-r2a-p1-trusted-input.md) | Pinned repository/owner IDs; driver trust-check and fail-closed gates in typescript-preflight/container-build/install/run (exit 2, no subprocess on rejection); 16 tests incl. mutations; no U1E impact; next-run input list updated; P2–P6 not implemented |
| [C5 U1E addendum 1](docs/evidence/m4c-c5-u1e-addendum-1-guard-rebinding.md) | Owner-approved 2026-11-19: G2 guard hash `0ac3de5d…` → `42672fd9…` (strengthening only); all other adopted inputs verified unchanged; consistency 237/237 |
| [C5 G2/G5 remediation R1](docs/evidence/m4c-c5-g2g5-r1-remediation.md) | G5D s7 item 4 no-redistribution record; V8 and PCRE2 macOS-only (OPEN); platform-wrapper guard test strengthened (rebound by U1E addendum 1); R2(a) owner-controlled-`main`-only proposal with enforcement without branch protection (not approved); upstream blockers and 2026-12-17 expiry |
| [C5 G4H hosted gate execution](docs/evidence/m4c-c5-g4h-hosted-gate-execution.md) | Run 44393309563 at `2e0bd25`: artifact digest verified, 6 files, 11 input hashes, Node 24.22.2, host-attestation 49/5, Semgrep 1.186.0, isolation, 59/64 controls, 0 findings; G4 closed for TypeScript only; Run 1 vs hardened configuration (setup-node `package-manager-cache: false` applied after Run 1, new hashes, binding review) |
| [C5 G4H hosted gate preparation](docs/evidence/m4c-c5-g4h-hosted-gate-preparation.md) | Trial workflow: pinned setup-node 24.22.2, `npm ci --ignore-scripts`, TypeScript preflight before any container, exact six-file allowlist; validator + 22 workflow and 14 driver tests; hosted verification procedure (not dispatched) |
| [C5 G4 TypeScript syntax-gate implementation](docs/evidence/m4c-c5-g4-typescript-syntax-gate-implementation.md) | Pinned typescript 6.0.3 gate before Semgrep (lockfile-verified compiler, self-test, post-scan re-hash; host attestation for container trials); 77/77 SAST tests, 34/34 matrix (T03 now exit 3), 5 real-Docker scenarios; E04 lint/typecheck dependency recorded |
| [C5 G4 TypeScript syntax-gate assessment](docs/evidence/m4c-c5-g4-typescript-syntax-gate-assessment.md) | Semgrep silently accepted 188/755 malformed TS mutants and all 4 G4 cases; TypeScript syntax-only and ESLint parser caught all with 0 false positives; esbuild missed 2; recommends pinned typescript 6.0.3 gate plus CI ordering (not implemented) |
| [C5 U1 Semgrep 1.186.0 upgrade preparation](docs/evidence/m4c-c5-u1-semgrep-1.186.0-upgrade-preparation.md) | Pins and verified hashes, offline install/RECORD checks (macOS + hardened Linux container), behaviour/telemetry review, strengthened G2 guard, SBOM v3 candidate (0 schema errors; 6 ALSA cleared), G2/G5 reassessment, blockers and GO/NO-GO; engine NOT executed, not adopted |
| [C5 U1E adoption decision](docs/evidence/m4c-c5-u1e-adoption-decision.md) | APPROVED 2026-11-18: adopt Semgrep 1.186.0 (exact hashes), SBOM v3 baseline, G2 V1/V2 + G5 V3–V6/V8 conditional acceptance for local scans and authorised non-blocking trials until 2026-12-17 with G5D stop conditions; path B recorded, X1 withdrawn; status-only toolchain.json edit verified; changeset audit, 23-file commit inventory, risks |
| [C5 U1D LT-U1 verification](docs/evidence/m4c-c5-u1d-lt-u1-verification.md) | Fresh owner-authorised LT-U1 of Semgrep 1.186.0: S0 clean (OSV/KEV/upstream, 237 checks), S1 harness exit 0, S2 9/9, S3 E03 29/29, S4 G4 14/14, S5 F3 34/34, S6 88/88, S7 hardened Linux container exit 0, S8 repository unchanged; residual risks; adopted via U1E |
| [C5 U1C LT-U1 execution](docs/evidence/m4c-c5-u1c-lt-u1-execution.md) | Owner-authorised local run of Semgrep 1.186.0: S0 clean (OSV/KEV/upstream), S1 harness exit 0 (isolation EPERM, 59/64 controls as baseline, parser-gap drift 0, 73 targets, 0 findings); S2 G2 guard 7/8 FAIL (test-design defect, analysis and proposed fix); S3-S7 not run; repository unchanged |
| [C5 U1B pre-execution assurance](docs/evidence/m4c-c5-u1b-pre-execution-assurance.md) | Signed-RPM verification (repomd signature, metadata and package hashes, header signatures, file digests, build-id and code sections): 16/16 AlmaLinux libraries VERIFIED, libtree-sitter VERIFIED by reproducible build; 217 consistency checks; SBOM v3 regenerated (0 schema errors); LT-U1 plan, preconditions, stop conditions; X1 reconciliation; not executed |
| [C5 G5D addendum A1](docs/evidence/m4c-c5-g5d-addendum-a1.md) | 2026-11-18, historical 1.185.0 record: ALSA-2026:98475 CVSS HIGH with static reachability evidence; path B chosen, exception X1 WITHDRAWN (never used); Semgrep 1.186.0 early review; picomatch HIGH and red mandatory CI recorded without waiver; dispatch and stop conditions |
| [C5 G5D security-risk decision](docs/evidence/m4c-c5-g5d-security-risk-decision.md) | Owner decision recorded 2026-11-17 (G2 incl. GHSA-mf5v and V3–V8 conditionally accepted for local trusted-repository scans and authorised non-blocking trials until 2026-12-17; SBOM v2 baseline); confirmed vulnerabilities, reachability, controls, gaps, early-stop conditions, minimum pre-E04 remediation; SBOM schema validation |
| [C5 G5C vulnerability assessment](docs/evidence/m4c-c5-g5c-vulnerability-assessment.md) | Online OSV/upstream research on the SBOM: OCaml 5.4.0 fork (public; lacks OSEC fixes), OpenSSL 4.0.3 in cryptography (6 CVEs), new opentelemetry-api GHSA; libyaml corrected to 0.2.5; 229 locked opam and 147 Rust crates clean; none shown reachable; v2 SBOM candidate; G5 not closable |
| [C5 G5B SBOM and static inventory](docs/evidence/m4c-c5-g5b-sbom-static-inventory.md) | CycloneDX 1.6 toolchain SBOM (418 components, classed confirmed/build-metadata/inferred/claim/unknown); semgrep-core static inventory from DWARF and symbols (OCaml 5.4.0 Semgrep fork, 84 opam packages, libyaml 0.1.7 claim, 34 grammars; SQLite/Mbed TLS not linked); tree-sitter runtime reassessed |
| [C5 G5 native library assessment](docs/evidence/m4c-c5-g5-native-library-assessment.md) | 33 bundled native libraries: 30 traced to signed AlmaLinux/EPEL RPMs or Homebrew bottles, licences and texts recorded, tree-sitter/static code unresolved, Moderate advisories, obligations by use; local/trial GO, mandatory CI and redistribution NO-GO |
| [C5 proposed implementation plan](docs/milestones/m4c-c5-sast-plan.md) | Unexecuted local SAST pilot, fail-closed controls, adversarial cases and independent-governance acceptance gates |
| [C4 infrastructure evidence](docs/evidence/m4c-c4-infrastructure.md) | Eight local Bicep contracts, parameter/redaction/security mutations, regression results, costs and open integration gates |
| [M4B local evidence](docs/evidence/m4b-local-preparation.md) | Executed local checks, SQL simulation limits and remaining NO-GO gates |
| [M4A preflight](docs/milestones/m4a-preflight.md) | Verified CI, blocked Azure facts and deployment readiness gaps |
| [Azure cost/control plan](docs/project/azure-cost-estimate.md) | Itemised provisional costs, approval/budget-alert proposal and teardown |
| [M4B scope](docs/milestones/m4b-scope.md) | Authorized local preparation and separately approved deployment scope |
| [Secure delivery](docs/delivery.md) | CI, scanners, provenance, OIDC/protection configuration and rollback design |
| [M3 evidence](docs/evidence/m3-secure-delivery.md) | Local results, scanner coverage, limitations, costs and M4 prerequisites |
| [Azure definitions](infra/README.md) | Bicep candidate definitions; validation only, no deployment |
| [Run the local app](apps/octocat-supply/README.md) | Exact setup, localhost:8080 containers, tests, data/reset and teardown |
| [M2 verification](docs/evidence/m2-baseline.md) | Executed checks, versions, provenance, outcomes, limits and exit status |
| [Authoritative master brief](docs/project/master-brief.md) | Project specification; governs the documents below |
| [Charter](docs/project-charter.md) | Direction, success measures, boundaries, and assumptions |
| [Requirements](docs/requirements.md) | Lifecycle requirements, critical journeys and measurable functional/non-functional contracts |
| [Capability/status matrix](docs/capability-status.md) | Current evidence versus planned capabilities |
| [Roadmap M0–M12](docs/roadmap.md) | Master-brief milestone sequence and exit evidence |
| [Fresh-start decision](docs/decisions/0001-start-fresh.md) | Why this repository starts independently |
| [Source assessment](docs/source-assessment.md) | Upstream candidates, pinned references, and integration constraints |
| [Historical reuse](docs/historical-reuse.md) | C1–C7 status and conditional reuse opportunities |
| [M1 scope](docs/milestones/m1-scope.md) | Product and architecture foundation; documentation and design only |
| [M2 scope](docs/milestones/m2-scope.md) | Independent local implementation and acceptance criteria |
| [Architecture](docs/architecture.md) | Application, agent SDLC, delivery, Azure, observability and incident-to-PR diagrams |
| [STRIDE threat model](docs/threat-model.md) | Application/agent threats, trust boundaries, permissions and approvals |
| [Validation strategy](docs/validation-strategy.md) | Application/agent evaluations, SLIs/SLOs, release gates and evidence |
| [M1 review](docs/evidence/m1-design-review.md) | Eight acceptance criteria, ADR index, checks, open decisions and M2 readiness |
| [M0 assessment and checks](docs/evidence/m0-assessment.md) | Findings, gaps, and verification results |
| [Third-party register](THIRD_PARTY_NOTICES.md) | Reference attribution and future import obligations |

## Local checks

Run from the repository root with Python 3.10 or newer; no packages are required:

```sh
python3 scripts/check_repository.py
git diff --check
git status --short --branch
```

The checker includes untracked project files, validates relative Markdown file
links, and checks text hygiene. It does not contact cloud services.

## Working boundaries

Claims Processing is a separate project and has no code, data, credentials, or
delivery dependency here. Current authorization stopped after the owner-approved C5-U1E adoption of Semgrep CE 1.186.0 (locally verified; not committed, pushed or hosted-dispatched by the agent); CI wiring and other C5 work need new direction.
Azure sign-in, credential refresh, GitHub setting changes, credentials, agents, provisioning/deployment, paid inference,
commits and pushes are outside this task.
The owner performs Git commits and pushes manually.

The [master brief](docs/project/master-brief.md) is the authoritative specification.
Its event challenge sequence is suspended as an implementation plan. The owner's
fresh-start instruction resolves its conditional repository-reuse guidance: the
original personal repository is unavailable, so this repository is the implementation
home. M1 defines the product and architecture; M2 establishes the working application.
Original code uses [MIT](LICENSE). Third-party packages/base images retain their
[own terms and notices](THIRD_PARTY_NOTICES.md). The owner selected independent
implementation; the upstream copying restriction in
[ADR 0002](docs/decisions/0002-source-reuse.md) remains in force. No cloud/agent
verification or production-readiness claim follows from local/hosted CI results.
