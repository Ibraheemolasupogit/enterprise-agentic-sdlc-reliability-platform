# Enterprise Agentic SDLC & Reliability Platform

An Azure-first engineering portfolio demonstrating agent-assisted SDLC, DevSecOps,
observability, SRE incident diagnosis, controlled remediation, recovery, and GitHub
engineering handoffs.

**Current milestone: M0 — Assess and preserve (closure).** This is a fresh
repository. Only foundation documents and a local repository checker exist.
OctoCAT Supply is the reference application; no upstream application, agents,
workflows, or cloud infrastructure have been imported or implemented.

## Project documents

| Document | Purpose |
| --- | --- |
| [Authoritative master brief](docs/project/master-brief.md) | Project specification; governs the documents below |
| [Charter](docs/project-charter.md) | Direction, success measures, boundaries, and assumptions |
| [Requirements](docs/requirements.md) | Initial functional and engineering requirements |
| [Capability/status matrix](docs/capability-status.md) | Current evidence versus planned capabilities |
| [Roadmap M0–M12](docs/roadmap.md) | Master-brief milestone sequence and exit evidence |
| [Fresh-start decision](docs/decisions/0001-start-fresh.md) | Why this repository starts independently |
| [Source assessment](docs/source-assessment.md) | Upstream candidates, pinned references, and integration constraints |
| [Historical reuse](docs/historical-reuse.md) | C1–C7 status and conditional reuse opportunities |
| [M1 scope](docs/milestones/m1-scope.md) | Product and architecture foundation; documentation and design only |
| [M2 baseline planning](docs/milestones/m2-scope.md) | Preserved application baseline criteria, deferred until after M1 |
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
delivery dependency here. M0 does not authorize M1 implementation. Credentials,
paid cloud access, deployments, commits, and pushes are outside this task.
The owner performs Git commits and pushes manually.

The [master brief](docs/project/master-brief.md) is the authoritative specification.
Its event challenge sequence is suspended as an implementation plan. The owner's
fresh-start instruction resolves its conditional repository-reuse guidance: the
original personal repository is unavailable, so this repository is the implementation
home. M1 defines the product and architecture; M2 establishes the working application.
No project-wide distribution license has been selected yet.
