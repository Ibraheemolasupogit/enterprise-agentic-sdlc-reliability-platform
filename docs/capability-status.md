# Capability and status matrix

Authority: [master brief](project/master-brief.md), sections 9, 16–17. Assessed on
2026-11-13. Use its states: **Planned, Implemented, Locally tested, Cloud verified,
Simulated, Design only, Blocked, Retired**. Historical validation is a separate
evidence classification, not current repository verification. M3 delivery definitions and local security checks are recorded in
[M3 evidence](evidence/m3-secure-delivery.md); the [M4C assessment](evidence/m4c-readiness-assessment.md)
confirms hosted M4B mandatory checks at `40a6353`; Azure
session/permissions/quotas, deployment and CodeQL execution remain unverified.
The [C3 plan](milestones/m4c-c3-oidc-plan.md) confirms hosted mandatory jobs at
`b56d9bd` with 97 application tests, CodeQL skipped. Subsequent C3 implementation
has [local evidence](evidence/m4c-c3-oidc.md). The owner subsequently supplies
`e537eff` / hosted run 43308294860 with mandatory jobs passed, CodeQL skipped;
that run was not independently re-read here. [C4](evidence/m4c-c4-infrastructure.md)
adds local definitions/static checks only. Subsequent
[C5 read-only assessment](evidence/m4c-c5-readiness.md) independently confirms C4
`e9b5704` / run 43407086701 mandatory jobs passed, CodeQL skipped; hosted artifact
contents were not reverified. Main is unprotected, no environments exist, and
independent reviewer/eligible SAST governance remain unestablished.
M2 application execution is locally verified as recorded in
[M2 evidence](evidence/m2-baseline.md); agent/cloud execution remains unverified.
M1 establishes design evidence only; the
[design review](evidence/m1-design-review.md) records criteria and remaining gates.

| Capability | Current repository status | Evidence or gap | Target |
| --- | --- | --- | --- |
| Independent foundation/source assessment | Design only; document checks passed | [M0 assessment](evidence/m0-assessment.md); no runtime implementation | M0 |
| Product/architecture/threat model/ADRs | Design only | [Architecture](architecture.md), [STRIDE model](threat-model.md), ADRs 0002–0006 and [M1 review](evidence/m1-design-review.md); no enforcement claim | M1 |
| Independent Morrow Supply application/container baseline | Locally tested | [M2 evidence](evidence/m2-baseline.md): original React/API/SQLite, fixtures, pricing/discounts, unit/integration/component/browser and local container fault/persistence checks; upstream reuse remains not cleared | M2 |
| Agent-assisted development/review | Planned | Requirement-to-change/tests/review evidence needed; no separate framework assumed | M2–M3; M8 |
| Secure delivery, images and Azure IaC/identity | Implemented; Locally tested with hosted synthetic CI evidence | Run 42805606271 at `b56d9bd` passed policy/application/containers/required, including browser/proxy/image gates; CodeQL skipped. Artifact contents not reverified in C3 planning; no registry publication or Azure identity/runtime proof. Prior protection/ruleset/environment observations remain dated, settings not re-read | M3/M4B/C1 |
| Personal Azure deployment/internal API/durability | Blocked for deployment; Design only | [M4A](milestones/m4a-preflight.md) NO-GO preserved: Azure subscription/region/permissions/quotas unverified. C4 defines private SQL/network/diagnostics locally; live auth/DB/network/ingestion/protection/cost gates remain pending. Static preparation does not establish a deployment | M4A/M4B/C4 |
| Application identity and owner isolation | Locally tested API crypto/SQLite ownership; Implemented browser OIDC | [M4B evidence](evidence/m4b-local-preparation.md): fixed issuer/audience/JWKS/role/scope, every cart method, legacy anonymous migration and namespaces; browser code exchange/real tenant claims unverified | M4B local |
| OIDC client/PKCE/session completion | Locally tested actual client/crypto; provider responses Simulated; overall local acceptance met | [C3 evidence](evidence/m4c-c3-oidc.md): P01–P15, 195 tests including preserved original 97; seven OIDC browser journeys, gated ID verification, nonce/state/metadata, lifecycle/isolation, capture/mutation and security checks. Fresh 2026-11-12 verification passes P01–P15 after the owner-authorized libxslt 1.1.43-r4 pin; both rebuilt images have zero HIGH/CRITICAL findings, with no waiver. Real provider remains C6 Blocked | M4C-C3 local |
| SQL persistence adapter/migrations | Implemented; Simulated recording-driver contracts | Parameter binding intentions, owner locks/transactions, history/fixtures/readiness errors tested with doubles; no T-SQL engine, managed identity, concurrency/private DNS or Azure SQL integration proof | M4B local; live release gate |
| Shared repository acceptance contracts | Locally tested on real file-backed SQLite | [C1 evidence](evidence/m4c-c1-repository-contracts.md): 27 shared cases plus six SQLite transaction/constraint regressions; same contracts await an independent-connection SQL fixture in C2. Scheduled SQLite calls do not prove parallel SQL locking; no SQL engine runner/claim | M4C-C1; C2 Blocked |
| Private infrastructure and minimum diagnostics contracts | Implemented; Design only infrastructure with Locally tested static checks | [C4 evidence](evidence/m4c-c4-infrastructure.md): eight Bicep templates, network/SQL PE/DNS/TLS/Entra-only definitions, five identities and unapplied least-privilege manifests, manual migrator, export-off diagnostics, parameter/freshness/security mutations. No live DNS/SQL/MI/RBAC/ingestion proof; Python redaction model is not KQL execution | M4C-C4 local only |
| HTTPS frontend/API proxy | Locally tested | Published TLS test peer, hostname/CA/SNI, bearer/header boundary, readiness failure, CSP/config rejection; ACA DNS/TLS/internal ingress unverified | M4B local |
| SAST and independent release governance | Hosted SAST feasibility accepted (Docker `--network none` run 43478654843 at `2b050a1`: exit 0, 0 findings, controls as catalogued; [execution evidence](evidence/m4c-c5-f4r-hosted-trial-execution.md)); non-blocking; [E03 robustness](evidence/m4c-c5-e03-robustness.md) met locally (M11/M12/M14); mandatory CI NO-GO; acceptance Blocked | [C5 assessment](evidence/m4c-c5-readiness.md), [proposed plan](milestones/m4c-c5-sast-plan.md), [C5-F1](evidence/m4c-c5-f1-semgrep-feasibility.md) [C5-F2](evidence/m4c-c5-f2-linux-feasibility.md) and [C5-F3 evidence](evidence/m4c-c5-f3-harness-hardening.md): Linux parity; F3 closed harness fail-open gaps (catalogue, classification, exit codes, pip check/RECORD) and the test-file finding, so scans are clean on both platforms; hosted-runner egress unverified; native-library notices/SBOM absent; hash-locked Semgrep CE 1.185.0 with 15 original local rules; 40/40 positive and 19/19 negative controls, 5 recorded blind spots; real 65-file scan has 1 untriaged test-file finding; hosted CI not run; 5 MODERATE tool-dependency advisories open and loaded (not invoked) during scans; [G2 assessment](evidence/m4c-c5-g2-dependency-assessment.md) traced them as not reached and found no compatible fix; owner conditionally accepted them for local/trial use until 2026-12-17 (open for mandatory CI; not waived), guarded by a flag/environment regression test; [G5 assessment](evidence/m4c-c5-g5-native-library-assessment.md) traced 30/33 native libraries to signed packages or bottles, recorded licences/texts and Moderate advisories, and allows local/trial use only (redistribution NO-GO; G5 open); [G5B](evidence/m4c-c5-g5b-sbom-static-inventory.md) added a CycloneDX toolchain SBOM and static inventory of semgrep-core (incomplete parts marked); [G5C](evidence/m4c-c5-g5c-vulnerability-assessment.md) found affected OCaml-fork and embedded-OpenSSL versions present (not shown reachable) and a new opentelemetry-api advisory outside the G2 acceptance; G5 not closable (v2 SBOM candidate since adopted in G5D); [G5D](evidence/m4c-c5-g5d-security-risk-decision.md) records the owner decision (2026-11-17): G2 incl. GHSA-mf5v and V3–V8 conditionally accepted for local trusted-repository scans and separately authorised non-blocking trials until 2026-12-17, SBOM v2 is the schema-valid assessment baseline (v1 frozen), G2/G5 OPEN; E04/release/redistribution NO-GO; [G4 gate](evidence/m4c-c5-g4-typescript-syntax-gate-implementation.md) implemented and verified locally (pinned typescript 6.0.3 before Semgrep; trial workflow with pinned Node 24.22.2, `npm ci --ignore-scripts` and a pre-container preflight per [G4H](evidence/m4c-c5-g4h-hosted-gate-preparation.md); hosted Run 44393309563 at `2e0bd25` passed per [G4H execution](evidence/m4c-c5-g4h-hosted-gate-execution.md); G4 CLOSED for TypeScript only, JavaScript out of scope; [G5D addendum A1](evidence/m4c-c5-g5d-addendum-a1.md) is the historical 1.185.0 record (path B; exception X1 withdrawn); mandatory CI at `2e0bd25` passed after GitHub withdrew the picomatch advisory (9 moderate minimatch findings remain below the high threshold, not waived); Semgrep CE 1.186.0 ADOPTED per the owner-approved [U1E](evidence/m4c-c5-u1e-adoption-decision.md) (2026-11-18) after [C5-U1](evidence/m4c-c5-u1-semgrep-1.186.0-upgrade-preparation.md), [U1B](evidence/m4c-c5-u1b-pre-execution-assurance.md) (17/17 rebuilt libraries verified), [U1C](evidence/m4c-c5-u1c-lt-u1-execution.md) and [U1D](evidence/m4c-c5-u1d-lt-u1-verification.md) (LT-U1 S0–S8 passed); SBOM v3 baseline; G2 V1/V2 + G5 V3–V6/V8 conditionally accepted for local scans and authorised non-blocking trials until 2026-12-17; G4H Run 1 on 1.186.0 passed; setup-node `package-manager-cache: false` hardening applied afterwards, not yet hosted-verified; [G2/G5 R1](evidence/m4c-c5-g2g5-r1-remediation.md): no-redistribution recorded, macOS-only V8/PCRE2 noted (OPEN), guard strengthened and rebound by [U1E addendum 1](evidence/m4c-c5-u1e-addendum-1-guard-rebinding.md), R2(a) main-only proposal not approved). CodeQL opt-in absent; no governance route/independent reviewer; no CI/settings changes | M4C-C5-F1–F4 (F4 preparation only) |
| Engineering-readiness assessment | Design only; C1/C3 local execution and C4 static checks recorded separately | [M4C plan](milestones/m4c-scope.md): C1/C3 preserved; C4 definition/static-validation slice implemented. Real SQL/provider/network/identity/diagnostic/SAST/governance and later authority boundaries remain open | M4C planning/C1/C3/C4 |
| Working agentic maintenance | Planned | C7 failure must be closed with real inference and useful output; not compilation alone | M5 |
| Local dependency-aware health | Locally tested | Process liveness, DB/seed readiness, frontend API dependency path and wrong-port failure/recovery in M2 | M2 |
| Azure observability and telemetry correlation | Planned | Local request IDs/logs exist; no Azure logs/metrics/traces, dashboards, SLO monitoring or config/deployment annotations verified | M6 |
| SLIs/SLOs, error budgets, alerts, severity/escalation | Planned | NF04 and validation strategy define formulas/windows/targets and release consequences; no operational baseline | M1 design; M6 |
| Incident diagnosis/management | Planned | Actual SRE Agent findings, impact/timeline, confidence, mitigation/permanent fix and postmortem needed | M7 |
| Bounded remediation and independent recovery | Planned | Approval/actor/audit and fresh recovery evidence absent | M7–M9 |
| Incident-to-PR handoff | Planned | Issue/dedup/assignment/repair/review/release/outcome integrations or fallback unverified | M8 |
| Backup/restore and recovery objectives | Planned | Local restart/container replacement preserves rows and reset is tested; cloud restore/RPO/RTO remain design-only and unverified | M1 design; M4/M9 |
| Performance/capacity and measured improvements | Planned | No measurements or baseline; no percentage savings claim | M9 |
| Configuration drift/dependency/toil/runbook upkeep | Planned | Operational ownership, maintenance and measured toil evidence absent | M9 |
| Cost/resource hygiene | Planned | Cost/teardown gates designed; actual estimate, approved spend and teardown proof deferred; budget alerts are not caps | M1 design; M3–M9 |
| Application/agent security and evaluation | Locally tested application cases; Planned agent/cloud cases | M2 V01–V08 local input/error/data cases pass; M3 adds pipeline/IaC mutation tests and real scanner gates; STRIDE T01–T12 and V09–V18 broader agent/release/cloud evaluations remain planned | M1 design; M2–M9 |
| Upstream integration/contribution register | Design only; source assessment started | Owner selected independent/MIT, exact npm inventory and notices recorded; no upstream app copied or contribution submitted | M0; M10 |
| Multi-cloud/alternative delivery modules | Planned; optional | No AWS/GCP core dependency; justify or defer after Azure core | M11 |
| Portfolio/video walkthrough | Planned | No end-to-end verified demonstration or video | M12 |
| Event challenge sequence as implementation roadmap | Retired | Replaced by master brief section 16; historical evidence preserved | M0 |

Claims Processing is outside this project's scope and remains a separate portfolio
repository. Shared patterns may be referenced without introducing its application,
data or runtime dependency here.

## Historical evidence classification

| Historical capability | Brief-reported result | Current verification and target |
| --- | --- | --- |
| Personal rehearsal assets | Cart/discounts, tests, Actions/scanning, containers, ACA/Bicep/OIDC, health/KQL reportedly existed | Assets unavailable; no current implementation or reuse proven |
| C1–C6 | Validated historically | [References preserved](historical-reuse.md); lab returned 404; do not claim current Cloud verified status |
| Wrong-port SRE experiment | Agent diagnosed API_PORT 443→444; watchdog rolled back; agent sampled recovery | Historical only; reproduce locally/container-first in M2 before authorized M7 live experiment |
| C7 maintenance | Implemented/compiled/pushed historically; inference authorization failed; no useful triage comment | Successful execution unverified; M5 must prove genuine inference and useful actual output |

Every future capability record must include version, environment, date, test/run,
result, limitation and linked evidence. A simulation or design must keep its label;
sampled recovery is not proof of full availability or autonomous remediation.

## M1 design versus execution evidence

J01–J06 and NF01–NF10 are specified in [requirements](requirements.md), with six
architecture diagrams, five focused ADRs and a STRIDE/evaluation mapping. Those
artifacts are **Design only** even where a design choice is accepted. Per-journey
99.5% availability, latency and RPO/RTO targets are unmeasured. No capability moves
to Locally tested or Cloud verified until its actual stage checks pass. C7 still
requires genuine successful inference/useful output in M5. The owner selected independent implementation and MIT for M2; that gate is closed
without copying upstream material. Direct OctoCAT copying remains not cleared.
See the updated [M2 scope](milestones/m2-scope.md) and execution evidence.
