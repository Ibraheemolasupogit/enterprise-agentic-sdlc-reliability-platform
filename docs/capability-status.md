# Capability and status matrix

Authority: [master brief](project/master-brief.md), sections 9, 16–17. Assessed on
2026-11-10. Use its states: **Planned, Implemented, Locally tested, Cloud verified,
Simulated, Design only, Blocked, Retired**. Historical validation is a separate
evidence classification, not current repository verification. M3 delivery definitions and local security checks are recorded in
[M3 evidence](evidence/m3-secure-delivery.md); the [M4C assessment](evidence/m4c-readiness-assessment.md)
confirms hosted M4B mandatory checks at `40a6353`; Azure
session/permissions/quotas, deployment and CodeQL execution remain unverified.
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
| Secure delivery, images and Azure IaC/identity | Implemented; Locally tested with hosted synthetic CI evidence | Run 42794873352 at `40a6353` passed policy/application/containers/required, including browser/proxy/image gates; CodeQL skipped. No registry publication or Azure identity/runtime proof. Main protection disabled; rulesets plan-restricted; environment state not re-read | M3/M4B |
| Personal Azure deployment/internal API/durability | Blocked for deployment; Design only | [M4A](milestones/m4a-preflight.md) NO-GO preserved: Azure subscription/region/permissions/quotas unverified; private SQL/network/diagnostics IaC, live auth/DB/protection/cost gates pending. Local preparation does not establish a deployment | M4A/M4B |
| Application identity and owner isolation | Locally tested API crypto/SQLite ownership; Implemented browser OIDC | [M4B evidence](evidence/m4b-local-preparation.md): fixed issuer/audience/JWKS/role/scope, every cart method, legacy anonymous migration and namespaces; browser code exchange/real tenant claims unverified | M4B local |
| SQL persistence adapter/migrations | Implemented; Simulated recording-driver contracts | Parameter binding intentions, owner locks/transactions, history/fixtures/readiness errors tested with doubles; no T-SQL engine, managed identity, concurrency/private DNS or Azure SQL integration proof | M4B local; live release gate |
| Shared repository acceptance contracts | Locally tested on real file-backed SQLite | [C1 evidence](evidence/m4c-c1-repository-contracts.md): 27 shared cases plus six SQLite transaction/constraint regressions; same contracts await an independent-connection SQL fixture in C2. Scheduled SQLite calls do not prove parallel SQL locking; no SQL engine runner/claim | M4C-C1; C2 Blocked |
| HTTPS frontend/API proxy | Locally tested | Published TLS test peer, hostname/CA/SNI, bearer/header boundary, readiness failure, CSP/config rejection; ACA DNS/TLS/internal ingress unverified | M4B local |
| Engineering-readiness assessment | Design only; assessment recorded; C1 locally tested separately | [M4C plan](milestones/m4c-scope.md): C1-only implementation authorized/completed; SQL/provider/IaC/identity/diagnostic/SAST/governance acceptance and later authority boundaries remain open | M4C planning/C1 |
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
