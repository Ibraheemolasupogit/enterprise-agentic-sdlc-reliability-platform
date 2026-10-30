# Project charter

Date: 2026-10-30. Owner: repository owner. Stage: M0.
Authority: [master brief](project/master-brief.md), particularly sections 1–4,
16–17. This M0 charter is an input to M1 refinement, not evidence M1 is complete.

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
in M0. Later milestones must define measurement windows and pass thresholds before
running demonstrations.

## Boundaries and delivery principles

- M0 produces documentation, source assessment, and lightweight repository checks.
- No application, agent, CI workflow, cloud infrastructure, credentials, deployment,
  paid cloud access, commit, or push is authorized in this task.
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

## Assumptions and decisions still open

The master brief is available and governs the roadmap. Historical source/run links
are now recorded, but the lab repository returned 404 through the current connection;
its artifacts have not been independently recovered. The unavailable personal
rehearsal assets remain unverified. Persistence/durability, hosting, service and
agent permission boundaries, supported inference authentication, Bicep reuse,
budget/region, numerical SLOs and license/asset rights need M1 decisions or explicit
deferrals. See the
[gap register](evidence/m0-assessment.md) and [M1 entry gates](milestones/m1-scope.md).
