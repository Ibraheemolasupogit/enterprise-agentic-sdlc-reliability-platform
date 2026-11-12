# Enterprise Agentic SDLC & Reliability Platform

An Azure-first engineering portfolio demonstrating agent-assisted SDLC, DevSecOps,
observability, SRE incident diagnosis, controlled remediation, recovery, and GitHub
engineering handoffs.

**Current stage: M4C-C3 — locally tested client/crypto with simulated providers;
P01–P15 local acceptance met after the authorized libxslt security patch.**
C1 repository contracts remain locally tested on real SQLite; C2/C4/C5/C6/C7/C8
implementation needs new bounded owner direction. OIDC/cart ownership, SQL adapter
and HTTPS proxy retain the evidence limits below. Hosted run 42805606271 at
`b56d9bd` passed policy/application/containers/required; CodeQL skipped and has not
executed. Azure session/permission/quota checks
remain blocked and deployment is NO-GO pending the documented gates. Morrow Supply is
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
delivery dependency here. Current authorization stops at C3 local implementation/evidence.
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
