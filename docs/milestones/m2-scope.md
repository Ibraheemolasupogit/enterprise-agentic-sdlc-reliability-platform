# M2 handoff — Reproducible application baseline

Status: **Planned; independent implementation recommended; upstream copying not
cleared**. Bounded source assessment updated 2026-10-30; functionality remains
unimplemented and unauthorized by this assessment.
Authority: [master brief](../project/master-brief.md), section 16. M1 design is in
[architecture](../architecture.md), [requirements](../requirements.md),
[threat model](../threat-model.md) and [validation strategy](../validation-strategy.md).
No source was imported or app setup executed while writing this handoff.
Coverage: R02–R03, R14–R17, R23/R25; J01–J06, NF01–NF03/NF05/NF06.

## Entry gates and source decision

1. Owner selects the recommended **independently authored synthetic implementation**
   and original-code license (MIT recommended), as
   [ADR 0002](../decisions/0002-source-reuse.md) records. Use our own J01–J06/NF
   contracts, original UI/data/tests/migrations and separately licensed dependencies.
   No OctoCAT source/assets are needed on this route. This assessment is a
   recommendation, not permission to start implementation.
2. Direct upstream reuse remains an alternative **not cleared for the full app**.
   Current reference only: `Azure-Samples/octocat-supply` commit
   `65299c9df87fc466be28a6eec56d53ea1e4fa915`, unchanged from M1. API declares MIT,
   while frontend/asset coverage is unresolved and a rights-reserved notice exists.
   If owner chooses reuse instead, record the actual grant, scope, holder/notices
   and redistribution conditions before import. Attribution or private visibility
   is not a substitute. Review M1 decisions and start M2 only when requested.
3. Select Node.js **24** major. Before installing app dependencies, record one exact
   supported patched Node version, its bundled npm version, OS/architecture and
   container base digest. Existing M1 host Node 22.17.1 is not baseline evidence.
   Verify native `better-sqlite3` support; do not bypass install failures silently.
4. Review independently chosen dependency licenses/scripts; generate fresh
   project manifests/lockfiles, isolate local data and
   confirm loopback-only ports. No Azure/GitHub login or paid service is needed.

## Expected implementation paths (create in M2 only)

| Path | Purpose |
| --- | --- |
| `apps/octocat-supply/api/` | Original TypeScript/Express routes, domain/repositories, SQLite migrations/seeds, unit/integration tests and API Dockerfile |
| `apps/octocat-supply/frontend/` | Original React/Vite UI, component/Playwright tests, static build, Nginx config and frontend Dockerfile |
| `apps/octocat-supply/compose.yaml` | One API container and one frontend, isolated local volume, health/config contracts; publish only loopback frontend 8080 |
| `apps/octocat-supply/.node-version` and freshly generated per-package lockfiles | Exact runtime and repeatable package installs; avoid adding a second package manager or unnecessary root workspace |
| `apps/octocat-supply/README.md` | Real setup/start/stop/migrate/seed/reset/test commands; runtime versions, known limitations and local fault exercise |
| `docs/evidence/m2-baseline.md` | Actual command results, clean setup reproduction, journey/data/fault evidence, limitations and compatibility findings |
| `docs/source-assessment.md`, `THIRD_PARTY_NOTICES.md`, provenance/dependency register and retained license/NOTICE files | Record original authorship and exact adopted dependency/asset terms; add file-level import manifest only if later selecting permitted source reuse |

Do not copy active upstream `.github`, hooks, agents, MCP configs, cloud identities,
resource IDs, deployment scripts or unneeded images. On the recommended independent
route, copy no upstream application files at all. Source exclusion alone would not
establish rights for any remaining imported files. Use original text placeholders
for art; no remote image/CDN/telemetry dependency in local journeys. Extend the existing
repo ignore rules for local DB/WAL/SHM/generated evidence without hiding migrations.

## Behaviour and fixture contract

Implement J01–J06 and the proposed API in architecture independently, using our
requirements rather than translated upstream source, schemas or tests. Use a
neutral original display identity; retain OctoCAT only as factual reference. Do
not create duplicate product/cart APIs. Use same-origin `/api`, frontend 8080, API
target 3000, SQLite local named volume, one writer process. Optional dev UI 5173
proxies to localhost:3000. API
port publication is loopback-only and optional for direct testing. No public
anonymous mutation or credential-based cloud fallback.

Synthetic fixture: exactly 12 products, IDs 1–12. Product 1 is `Demo Feeder`,
`unitPriceMinor=12999`; product 2 is `Demo Toy`, `unitPriceMinor=1999`. Products
3–12 are `Synthetic Product 03` through `Synthetic Product 12`, each priced 1500.
All use GBP. `feeder` matches ID 1 only; price ties order by ID. These are original
synthetic data specifications, not claims about the historical 12 products.
Independently design only the product/cart/line schema needed by these contracts;
create deterministic related rows as needed, without copying upstream schema/seed
SQL or product descriptions; no PII.
Tests create isolated carts/databases and clean up only their own fixtures.
Use the specified cart-delete contract for probe/fixture cleanup; verify it cannot
delete another cloud principal's cart when cloud auth is introduced in M4.

Cart totals are server-authoritative integer minor units; quantity 1–99, maximum
100 distinct lines/cart. Setting the same quantity twice is idempotent. Two feeder
units and three toy units cost 31995 minor units. Refresh recovers cart reference;
API/container replacement preserves data with retained volume. A stale reference
after explicit reset displays a clear recovery choice. Discounts, tax, shipping,
checkout, payments and real customer authentication are excluded from M2.

Migrations run explicitly in tracked order with checksums; seed/reset are explicit
and repeatable, not destructive startup side effects. Tests use temporary DBs;
reset requires an explicit demo target and rejects symlink/out-of-root/cloud
paths. Do not claim cloud durability from a local retained-volume test.

## Build, tests and local fault exercise

Write tests from our requirements, not copies of upstream tests: unit
price/validation, SQLite API integration tests, UI component states and a focused Playwright suite using the
actual UI/API. Required cases are V01–V08/V18, including unknown/invalid inputs,
concurrent cart updates, deterministic seeds, migration replays/checksum rejection,
restart/persistence, visible dependency failure and request-ID/error redaction.

M2 must provide documented noninteractive `lint`, type/build, unit/integration,
component and E2E commands in the appropriate packages, plus migration/seed/reset
and Compose commands. Use locked installs after script review. Any command shown
in the final README must actually run; no placeholder pass results. Build/run
containers and smoke through `http://localhost:8080`, not only direct API tests.
Repeat setup from a second clean copy with no existing node_modules, built assets
or DB volume, using only the documentation.

For the reversible fault, snapshot local configuration/data, set the frontend
proxy API port from the correct local value 3000 to a closed test port 3001,
confirm static `/` is still 200 while product journey/frontend readiness fails,
then restore 3000 and independently verify recovery. Use a verified unused port;
stop if it reaches another service. The historical cloud 443→444 incident is the
analogue, not a command to change live resources. No SRE Agent execution or
cloud monitoring change is part of this exercise.

## Acceptance criteria

| ID | Pass condition | Required evidence |
| --- | --- | --- |
| M2-A1 | Owner-selected strategy/original license recorded; original code/fixtures independently authored and adopted dependencies/assets licensed with notices; any upstream import separately cleared | Authorship/provenance and exact dependency/asset license register; if reuse is chosen, full source revision/path/rights/import manifest required; unknown-rights content excluded from public files/history |
| M2-A2 | Exact Node/npm/base versions and lockfiles produce clean install/type/build | Successful commands, OS/native module notes and reviewed dependency scripts |
| M2-A3 | Local UI/API catalogue/detail/search and same-origin connection work | V01/V02/V06, 12 products and deterministic IDs/sorting; no cloud/remote image dependencies |
| M2-A4 | Cart create/set/remove/isolation and authoritative pricing/error contracts pass | V03/V04 including 31995 arithmetic, invalid quantities, unknown references and concurrency |
| M2-A5 | Repeat migration/seed/reset and retained-volume persistence behave safely | V05, exact fixture comparison, changed migration rejection, restart/replacement and reset-path denials |
| M2-A6 | Lint/type/build/unit/integration/component/E2E commands pass noninteractively with meaningful assertions | V01–V08/V18 actual output and failing-defect sensitivity; no count-based coverage claim |
| M2-A7 | Containers bind only intended loopback exposure and setup contains no secrets/active cloud/agent/workflow/Claims Processing integration | File/config/provenance review, V08/V18; no credential creation or paid calls |
| M2-A8 | Second clean setup succeeds solely from documented instructions | Clean-copy commands, start/stop/reset/recovery procedure and limitations |
| M2-A9 | Product/search/cart/pricing UI handles keyboard/loading/empty/error/refresh states | V06 component/Playwright evidence and focused manual accessibility review |
| M2-A10 | Wrong-port/static-health gap is reproduced and reversed locally with safe bounds | V07, actual actor/config/time/request IDs and fresh recovery evidence; no claim of live SRE diagnosis |

## Stop condition and readiness

M2 ends at a **Locally tested** application/container baseline with honest evidence.
Do not implement CI/IaC (M3), cloud auth/SQL/deployment (M4), maintenance inference
(M5), Azure telemetry/alerts (M6) or live SRE/PR integrations (M7/M8). Existing coding
assistance may prepare scoped local changes/tests, but the owner commits/pushes.

The implementation design and test handoff are specified. **Recommended next path:
independently author the equivalent synthetic commerce baseline**, retaining the
existing architecture/journeys/tests and original visuals. The owner must select
that strategy and original-code license before implementation; separately licensed
packages/container bases still need adoption review. Direct OctoCAT copying stays
not cleared unless an adequate grant is recorded. Private development and eventual
public publication are compatible with the independent/MIT recommendation, but
privacy does not cure copied-content rights. Review files and all history intended
for publication, plus distributed bundles/images/screenshots/video.

No application code is imported or implemented in this assessment. This handoff
does not change visibility, authorize M2 functionality, deploy, commit or push.
M1 review/source-gate statements remain historical design records; reconcile wider
status documents in the next authorized implementation task after strategy selection.
