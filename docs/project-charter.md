# Project charter

Date: 2026-10-30. Owner: repository owner. Stage: M3 — Secure delivery; local validation only.
Authority: [master brief](project/master-brief.md), particularly sections 1–4,
16–17. M0 history remains in its assessment; M1 completion is assessed against
[the eight acceptance criteria](milestones/m1-scope.md).

## Purpose and intended outcome

Build an inspectable Azure-first portfolio that connects an engineering change to
secure delivery, operational signals, incident diagnosis, controlled remediation,
verified recovery, and a GitHub engineering handoff. Evidence should let a reviewer
distinguish what an agent suggested, what a human approved, what executed, and what
was verified.

OctoCAT Supply provides the reference supply-chain application and business context.
The unavailable personal OctoCAT repository is not a prerequisite. This repository
has its own history, requirements, and validation record.

## Scope and success measures

| Area | Intended evidence at portfolio completion |
| --- | --- |
| Agent-assisted SDLC | One traceable requirement → plan → change → tests → reviewed handoff |
| DevSecOps | Repeatable build, dependency/security checks, artifact provenance, and release gates |
| Azure operations | Documented identity, cost, deployment, teardown, and environment boundaries |
| Observability and SRE | Correlated logs, metrics, traces, declared SLIs/SLOs, and a repeatable incident |
| Diagnosis and remediation | Evidence-linked diagnosis, bounded action proposal, approval, execution audit, and denial path |
| Recovery and learning | Measured restoration, rollback exercise, post-incident record, and follow-up issue/PR packet |
| Operational assurance | Backup/restore, performance/capacity, configuration drift, dependency maintenance, runbooks and cost/toil evidence |
| Collaboration and presentation | Verified upstream register, focused contribution where appropriate, and reproducible walkthrough/video |

No availability, recovery-time, security-compliance, or AI-accuracy result is claimed
by design documents. The validation strategy defines measurement windows and pass
thresholds for later demonstrations; those targets still need execution evidence.

## Boundaries and delivery principles

- M1 refines the product and architecture, threat model, ADRs, validation strategy
  and M2 handoff. No runtime or platform capability is promoted by design alone.
- M2 established the independent local application/tests/containers under MIT. M3
  authorizes one CI pipeline, local security/image checks and static Azure IaC. No
  agent, cloud login/provisioning/deployment, credential creation, paid-service
  execution, commit or push is authorized.
- Claims Processing remains a separate project, including its data and backlog.
- Use synthetic supply-chain data; require explicit evidence for capability claims.
- Prefer small local slices before cloud integrations. Introduce dependencies only
  when a milestone needs them, with provenance and licensing recorded.
- Future state-changing tools need bounded permissions, explicit approval semantics,
  audit records, timeout/retry limits, rollback, and escalation behavior.
- Git commits and pushes remain manual owner actions.
- M1 is product and architecture design; implementation and local execution begin
  in M2. Use GitHub Actions, container images and Azure IaC as the primary delivery
  path; assess Bicep reuse. Avoid a custom multi-agent framework without a concrete
  requirement. AWS/GCP, Jenkins, Azure DevOps and Kubernetes are optional extensions.
- Measure improvements against recorded baselines; static homepage health does not
  prove dependency health, and sampled recovery does not prove full availability.

## Product scope and decision baseline

The fictional engineering team supports product catalogue/search, synthetic carts
and authoritative GBP pricing. These critical journeys, error criteria and
functional/non-functional requirements are defined once in
[requirements](requirements.md); tests/SLOs and proof live in the
[validation strategy](validation-strategy.md). The later M2 request adds deterministic automatic basket discounts. Real checkout,
payments, customer PII and inventory reservation remain outside the M2 slice.

Select a two-container React/Nginx → TypeScript API → repository design, local
SQLite for M2, Azure Container Apps with internal API and Azure SQL for the cloud
target. Use GitHub Actions/images/Bicep and scoped OIDC, existing assistant/gh-aw/
SRE surfaces with separate permissions, and journey-driven Azure Monitor telemetry.
These decisions are in [ADRs 0002–0006](decisions/0002-source-reuse.md). The local
application is tested in M2; cloud/agent integrations remain Design only. The architecture avoids an extra agent service, custom
multi-agent framework, duplicate CI pipeline or mandatory multi-cloud component.

Delivery success means reproducible tests/review/release and a verified incident
handoff/recovery loop, not a collection of tools. Record baseline investigation
minutes, manual steps, failures and recovery times before assessing improvement.
Do not invent percentage gains. M1 exits with reviewed design and a gated M2
handoff; a runnable baseline remains M2 work.

## Remaining blockers and decision owners

The master brief governs the roadmap. The personal rehearsal remains unavailable;
lab references are historical, not current reuse evidence. The repository owner
selected independent implementation and MIT, closing the original-code/source
strategy gates without copying upstream material. Direct OctoCAT reuse remains
not cleared. M2 uses Node 24.22.2/npm 11.19.1 with exact locks and pinned local
container bases; local evidence is separate from Azure design. Cloud SKU/region,
private network cost, actual OIDC subject/roles and protection entitlement are verified before M3/M4
execution. gh-aw supported engine/auth/spend ceiling is decided before M5 and
SRE/issue/assignment integration support before M7/M8. No secret, paid inference,
resource or scheduled monitoring change is authorized here. See the
[M1 review and decision register](evidence/m1-design-review.md).

M3 execution and outstanding M4 entry gates are recorded in
[secure-delivery evidence](evidence/m3-secure-delivery.md). The planned Azure
architecture is not runnable cloud functionality until M4 authentication, SQL,
proxy/network, identity/cost and release prerequisites are closed.
