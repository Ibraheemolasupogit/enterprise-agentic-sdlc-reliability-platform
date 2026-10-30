# ADR 0002 — Source selection and reuse gate

Date: 2026-10-30. Status: accepted design; **source import blocked**.
Owner for rights resolution: repository owner. Due: before M2 import (M2-A1).
Requirements: R02, R14–R17, R21. [Source evidence](../source-assessment.md).

## Context and decision

Select `Azure-Samples/octocat-supply` commit
`65299c9df87fc466be28a6eec56d53ea1e4fa915` as the **conditional** reference source.
It matches the required React/TypeScript/API/SQLite workload. Do not copy it yet.
Reinspection of its complete tree found no LICENSE/NOTICE/COPYING/COPYRIGHT-named
file. Its [API manifest](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/api/package.json)
declares MIT; the frontend manifest does not. This does not resolve all code,
images, branding, prompts or documentation rights. The event starter has the same
whole-tree license-file gap. GitHub documents the difference between public access
and licensed reuse in its [licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

The owner must record applicable permission/license evidence identifying intended
files, revision and redistribution scope. An upstream license addition must be
checked for coverage of the intended revision; do not assume retroactive coverage.
If a different licensed revision is selected, reassess compatibility and update
the register and M2 scope. Do not silently substitute another application or infer
rights from forks. An independently authored workload is an alternative scope
decision, not an approved workaround.

For permitted material, import only API/frontend and necessary tests/seeds/build
files under `apps/octocat-supply/`. Record upstream paths, full revision, local
paths, notices, permitted use and modifications in an import manifest. Exclude
active upstream `.github`, agents/hooks/MCP settings, credentials, deployment
configuration and unnecessary visual assets. Use plain text/original placeholders
for excluded art. Removing art alone does not resolve code rights.

## Attribution and original license

Retain applicable copyright/license text and relevant NOTICE content at import.
MIT reuse requires retained copyright and permission notices; Apache-2.0 reuse
requires its license, relevant notices/NOTICE content and marked modifications.
Neither grants all branding rights. Record package/container transitive licenses
at M2/M3; top-level notices alone are insufficient.

**Original project license is unresolved**: MIT is the recommendation for the
owner's original material, but no blanket license or rights grant is issued in
M1. Owner decides before M2 distribution/import integration. Do not relicense
upstream material. Rights evidence and original-license selection are distinct.
These are explicit M2 blockers; they do not prevent completing a design review.

## Alternatives and consequences

- Wholesale copy: rejected while rights are unresolved and inherited automation
  could activate unwanted workflows.
- Another fork/starter: not selected; public visibility does not fix rights.
- Independent implementation: requires a new scoped ADR and owner direction.

M1 can be complete while M2 remains blocked at import. Nothing in this ADR claims
permission, legal ownership, runtime compatibility or a working baseline.
