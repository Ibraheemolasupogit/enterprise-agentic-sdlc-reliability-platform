# M2 planning — Reproducible application baseline

Authority: [master brief](../project/master-brief.md), section 16.
Preserved from the initial local-baseline proposal, now assigned to M2.
Status: preliminary planning; refine during M1. No implementation authorized by M0.
Requirement coverage:
R02–R03, R14–R17, R23, R25. Outcome: a small, reproducible local OctoCAT Supply API/UI baseline
with synthetic data and evidence, ready for later agent-assisted engineering work.

## Entry gates

1. Complete the [M1 design review](m1-scope.md) and close its M2-critical
   architecture, threat-model, source and persistence decisions. Historical
   C1–C7 evidence remains context, not proof of a working personal baseline.
2. Establish file/asset reuse rights for a selected upstream at an exact commit.
   S01 is the first candidate; the current rights gap blocks source import.
3. Select a license for original project work and retain separate upstream notices.
4. Confirm a local runtime/package-manager combination from manifests/lockfiles;
   Node 24 is an initial candidate based on assessed upstream CI, not a verified
   environment result. Document native SQLite prerequisites.

## Included implementation

- Import only the permitted API, frontend and necessary seed/test/build material
  into the layout selected by M1 (`apps/octocat-supply/` is a candidate), with a
  file-level provenance and modification record.
  Keep the platform's documentation and future operations components separate.
- Establish the M1-selected product, search/filtering, cart and pricing journeys,
  including UI → API → persistence flow and one synthetic product mutation.
- Provide containerised local execution and dependency-aware smoke checks. Reproduce
  the known wrong-port/static-health gap locally or in containers before any live
  fault; preserve evidence for M6/M7 without claiming Azure SRE Agent execution.
- Provide deterministic data initialization/reset, explicit localhost ports, API
  base URL and CORS settings, and a documented start/stop procedure.
- Preserve useful existing tests; add only the smoke/integration coverage needed
  to prove this slice. Run noninteractive lint, build and relevant tests.
- Record setup commands, runtime versions, selected revision, actual results,
  limitations and minimal screenshots or equivalent response evidence.

No agent service/maintenance workflow, paid inference, CI/CD activation, cloud resources, IaC,
deployment, registry publication or Claims Processing integration is included.
Do not copy upstream `.github`, hooks, MCP configurations or deployment scripts
into active locations. Local setup must require no GitHub/Azure credentials or
paid services. Commits and pushes remain manual owner actions.

## Acceptance criteria

| ID | Pass condition | Evidence |
| --- | --- | --- |
| M2-A1 | Import rights resolved for every adopted file/asset; source pinned to full commit | License/permission evidence, notices and import manifest; unresolved files excluded |
| M2-A2 | From a clean local directory, documented locked installs and build complete using the pinned runtime | Exact versions/commands and successful output; no pre-existing database or cloud dependency |
| M2-A3 | API and UI start on documented localhost ports; UI displays seeded products | UI evidence, successful product-list and known-product responses; browser request has correct API URL/CORS |
| M2-A4 | Create a uniquely named synthetic product, read it, restart API, read it again, then delete it | Expected HTTP results and persistence evidence; invalid payload and unknown ID have documented error behavior |
| M2-A5 | Reset twice produces the same seed counts and stable IDs without duplicate records | Recorded counts/IDs, reset commands and safe local database path |
| M2-A6 | Noninteractive lint/build/relevant tests pass, including one UI/API smoke flow | Command results; failures must be fixed or scope explicitly revised, not counted as passes |
| M2-A7 | Setup contains no live secrets, cloud login, paid service call, active deployment workflow or Claims Processing dependency | File review, local configuration check, source manifest and repository diff |
| M2-A8 | A second clean setup using only the documented instructions succeeds | Reproduction record, start/stop/reset procedure, limitations and updated status matrix |
| M2-A9 | Product, search/filtering, cart and pricing behaviours match M1 acceptance criteria | Meaningful API/component/end-to-end tests, invalid/empty/error cases and synthetic data; discounts only if specified by M1 |
| M2-A10 | Local container setup and wrong-port dependency failure can be reproduced and reset safely | Container smoke evidence, user-facing failure versus static health, documented local persistence/migration constraints; no live cloud fault |

## Sequence and stop condition

Resolve rights and runtime → import the minimal permitted baseline → configure
local data and connectivity → verify the slice → reproduce from clean setup →
update evidence and capability status. If rights remain unresolved, finish the
source decision and report that gate; do not silently copy or substitute an app.

M2 ends at a locally tested application/container baseline. M3 secure delivery and
M5 working agentic maintenance have separate scopes. M1 is design only; M0 ends
before any implementation above. Keep cloud durability claims separate from local
SQLite persistence tests and record migration/rollback constraints.
