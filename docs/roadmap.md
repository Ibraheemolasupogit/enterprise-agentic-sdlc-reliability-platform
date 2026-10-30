# Milestone roadmap M0–M12

Authority: [master brief](project/master-brief.md), section 16. This roadmap
replaces the initial M0 proposal and the event challenge sequence. Only M0 closure
is authorized now; all later milestones remain planned. Security and evidence
apply throughout. Earlier M0 charter/requirements drafts are inputs to M1, not
proof that M1 has been completed.

| Milestone | Scope | Exit evidence |
| --- | --- | --- |
| M0 — Assess and preserve | Inventory this fresh repository, preserve historical references, assess sources and gaps, select the source of truth | Master brief linked, reusable/retired material identified, capability matrix, corrected roadmap, precise M1 proposal and closure checks |
| M1 — Product and architecture foundation | Refine charter, requirements and capability matrix; define architecture, threat model and ADRs | Traceable journeys/requirements, trust and service boundaries, persistence/identity/source decisions, evaluation plan and bounded M2 handoff; design only |
| M2 — Reproducible application baseline | Establish the permitted OctoCAT Supply reference workload with synthetic data and containerised local execution | Fresh setup, functioning product/search/cart/pricing journeys, meaningful tests, documented persistence/migrations and local/container fault reproduction |
| M3 — Secure delivery | GitHub Actions CI, security checks, container image build, Azure IaC validation, scoped identities and release controls | Passing/failing gates, image provenance, threat-model checks, validated IaC and authorized identity/release design; no implicit deployment approval |
| M4 — Personal Azure deployment | Deploy the personal workload when separately authorized, with an internal API boundary and an explicit durability decision | Deployment evidence, smoke checks, migration/data integrity checks, recovery procedure, cost and teardown record |
| M5 — Working agentic maintenance | Use a supported workflow execution/authentication model with separate inference and repository-write permissions | Genuine successful inference, useful actual repository output, least-privilege and failure-path evidence; closes C7 only after these pass |
| M6 — Observability and reliability | Useful telemetry, deployment/config annotations, dependency-aware checks, SLIs/SLOs, error budgets, dashboards and alerts | User-facing journey signals, declared windows/targets, actionable alerts and release implications; static homepage alone is insufficient |
| M7 — Incident diagnosis and recovery | Reproduce the known fault locally/container-first, then run a separately authorized controlled experiment with Azure SRE Agent | Detection/acknowledgement, impact/timeline, actual agent findings, bounded rollback, independent fresh recovery verification and postmortem; identify the repair actor |
| M8 — Incident-to-PR lifecycle | Issue creation/deduplication, authorized assignment, repair branch/PR, review, release and verification | Verified integrations or documented connector/human fallback; incident → issue → tested repair → reviewed release → fresh recovery → prevention record |
| M9 — Operational assurance | Backup/restore, resilience and security evaluations, performance/capacity exercise, drift/dependency/toil/runbook upkeep and cost hygiene | Restore against recovery objectives, malicious-input/permission/repair-failure evaluations, measured improvement and retained operational evidence |
| M10 — Upstream collaboration | Maintain the integration register and select a focused contribution where appropriate | Verified source/change/adoption/test status; contribution submitted through the upstream's accepted process, with review outcome recorded honestly |
| M11 — Optional extensions | Justified isolated multi-cloud federation, alternative delivery or deployment modules after the Azure core is validated | Independent identity/negative-case tests, cost/teardown evidence and no core dependency; record a reasoned deferral if no extension is justified |
| M12 — Portfolio and walkthrough | Assemble the evidence index, professional README, architecture narrative and reproducible video demonstration | Reviewable end-to-end lifecycle, evidence classifications, limitations, attribution, costs and reproducible main/decision-focused walkthroughs |

## Milestone boundaries

M1 creates or refines design documents only: no source import, app setup, package
installation, container execution, agents, workflows, IaC or cloud changes. M2
creates the working application baseline after source rights and the M1 design
permit it. The original local-baseline proposal is preserved as
[M2 planning](milestones/m2-scope.md).

M3 prepares secure delivery; M4 is the personal Azure deployment; M5 proves real
agentic maintenance. M7 establishes diagnosis/recovery; M8 closes the engineering
handoff loop; M9 broadens assurance. M10 is upstream collaboration and M11 is
optional extensions. All cloud resources and paid inference need explicit scope,
identity, cost estimate and teardown planning before execution. Budget alerts are
not spending caps. The owner performs commits and pushes manually.

Detailed next step: [M1 scope and acceptance criteria](milestones/m1-scope.md).
