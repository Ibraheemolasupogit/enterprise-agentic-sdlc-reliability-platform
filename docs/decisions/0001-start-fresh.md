# ADR 0001 — Start an independent repository

Date: 2026-10-30. Status: accepted for M0, as directed by the owner.
Authority: [master brief](../project/master-brief.md), section 2, together with the
owner's explicit fresh-start instruction.

## Context

The original personal OctoCAT repository is unavailable. Initial inspection found
an empty working tree with only Git metadata, no commits on `main`, and no remote.
There is no local application, agent, infrastructure, workflow or historical
validation evidence to continue from.

The brief names `octocat-supply-Agentic-AI` as a candidate to verify and prefers
reuse where practical. The owner has established that it is unavailable and has
authorized this fresh repository. This is the recorded exception to conditional
reuse guidance; it does not authorize another overlapping SDLC repository.

## Decision

Create an independent repository for the Enterprise Agentic SDLC & Reliability
Platform. Use OctoCAT Supply as the reference application, assessed through public
upstream sources. Do not assume it is installed, licensed for wholesale reuse, or
already integrated. Do not fabricate or recover the missing personal repository's
history. Preserve historical C1–C6 validation as owner-reported context and C7
inference execution as unverified.

Keep Claims Processing outside this repository. Begin with M0 documentation and
source assessment. The owner performs all commits and pushes manually.

## Consequences

The project has clear provenance and a small foundation, but implementation and
validation must be established anew. Any later source import needs a permitted,
pinned source, retained notices and an import manifest. Historical cloud resources,
credentials and workflow assumptions cannot supply current acceptance evidence.
The master brief is now the source of truth. Historical references in its section 5
are preserved in the [reuse assessment](../historical-reuse.md); their underlying
artifacts remain unavailable for independent inspection. The event roadmap is
suspended. M1 is product/architecture design and M2 is application implementation.
