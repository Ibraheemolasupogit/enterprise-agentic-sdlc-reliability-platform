# Enterprise Agentic SDLC & Reliability Platform

An Azure-first engineering portfolio demonstrating agent-assisted SDLC, DevSecOps,
observability, SRE incident diagnosis, controlled remediation, recovery, and GitHub
engineering handoffs.

**Current milestone: M3 — Secure delivery.** CI and deployment-free Azure IaC
validation are implemented; hosted CI/Azure remain unverified. Morrow Supply is
an independently implemented React/TypeScript, TypeScript API and local SQLite
demo with original synthetic data and illustrations. OctoCAT Supply is the
conceptual reference; no upstream application source or assets were copied.
Agents, cloud deployment and release execution remain planned.

## Project documents

| Document | Purpose |
| --- | --- |
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
delivery dependency here. Current authorization stops at M3 secure delivery/local validation.
Agents, paid services, cloud authentication/provisioning/deployment, commits and pushes are outside
this task.
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
verification, hosted CI pass or production-readiness claim follows from local results.
