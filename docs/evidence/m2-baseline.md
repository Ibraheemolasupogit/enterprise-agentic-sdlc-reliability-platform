# M2 verification — Reproducible application baseline

Date: 2026-10-30 (UTC). Status: **Locally tested; M2 exit PASS**, with the limits
below. Authority: [master brief](../project/master-brief.md), later owner decisions
and [ten M2 acceptance criteria](../milestones/m2-scope.md#acceptance-criteria).
Actor: scoped coding assistant implementing the owner's request, deterministic
test tools and local browser review. No application agents performed these tests
or repairs. Human review/commit/push remain with the owner.

## Delivered boundary and decisions

**Morrow Supply** is an independently authored React/TypeScript UI, TypeScript/
Express API and local SQLite commerce demo. [Setup and operations](../../apps/octocat-supply/README.md)
are executable instructions. Original code, fixtures, SQL, styles and inline SVG
illustrations use [MIT](../../LICENSE). OctoCAT Supply is a factual conceptual
reference, not a copied dependency or claimed fork. Claims Processing is absent.

The later owner request adds category filtering and deterministic discounts to
the original M1 contract. The selected small rule is automatic/non-stacking 10%
off a GBP subtotal >=30000p, rounded down to whole pence; no coupons, tax, shipping,
checkout or payment. Two feeders and three toys yield 31995p subtotal, 3199p
discount and **28796p total**. Requirements, architecture and handoff agree.

One application-level manifest/lockfile serves both runtime folders. No ORM,
workspace manager, agent runtime or shared framework was added. Node's bundled
`node:sqlite` avoids a separate native addon; its documented release-candidate
status is an accepted **local baseline** trade-off, not production stability.
One API writer, WAL/foreign keys, transactions and explicit checksummed migrations
provide local integrity. Migrate/seed/reset never run as a startup side effect.
Cloud SQL, backup/restore, authentication and multiple writers are not validated.

The API validates IDs, query allowlists/bounds, origins, JSON/media/body size and
quantities; uses parameterized SQL and canonical integer prices; returns safe
errors with generated request IDs. It does not trust browser prices or inbound
request IDs. Absolute quantity updates are idempotent; writes are not retried
automatically. Cart IDs are opaque demo references, **not authorization**.

The browser supports catalogue, trimmed search, category/price sorting, basket
add/update/remove, authoritative discount totals and reload recovery. Lost/reset
cart references need explicit recovery; an outage preserves the saved basket
rather than silently creating another. Original art/system fonts require no CDN.

## Version, source and environment record

| Item | Executed version / identity |
| --- | --- |
| Starting/current Git HEAD | `5d912b3955edf2b2fc8ba51468ebd8dd5221a3a7`; M2 is an uncommitted working-tree change |
| Source identity | [Per-file SHA-256 fingerprint](m2-source-fingerprint.json); excludes installed modules, dist, DBs and test output; not a release attestation |
| Host | macOS 15.6.1 (24G90), arm64; Python 3.12.8 for repository checks |
| Node / npm | Node 24.22.2 / npm 11.19.1, exact engines and `.node-version`; system Node 22 was not used for the baseline |
| SQLite | Node bundled SQLite 3.53.4 in Linux API container; release-candidate driver API |
| Direct production packages | Express 5.3.0, React/ReactDOM 19.3.1 |
| Build/test tools | TypeScript 6.0.3, Vite 8.3.5, Vitest 5.0.5, ESLint 10.14.0, Playwright 1.64.1, Prettier 3.9.10; exact transitive versions in lock/inventory |
| Browser | Playwright Chromium 156.0.8078.4, revision 1248; actual headless Chromium execution |
| Local containers | Docker 28.3.3 / Compose 2.39.2; Linux arm64; Nginx 1.30.6 |
| API local image ID after clean build | `sha256:be761db218acb8e73ba014b25e23bdffd5d750c310b1d0b99c17c2ea414b6337` |
| Frontend local image ID after final notices rebuild | `sha256:eb87e5cadac7c2a0ed407bee39903fb1c766b0b339e8173115ded8f0e6d58e50` |

Dockerfiles pin immutable multiarchitecture base digests; these local image IDs
identify this build, not a published registry artifact. The exact
[npm inventory](../../apps/octocat-supply/dependencies.json) has 347 locked records,
including optional platform variants. Host-specific optional installs differ.
The official Node tarball checksum was verified before using the toolchain.
Primary driver reference: [Node 24.22.2 SQLite documentation](https://nodejs.org/docs/v24.22.2/api/sqlite.html).

## Executed checks and outcomes

Commands below run in `apps/octocat-supply` with the pinned Node/npm unless noted.
Install/browser downloads and local sockets/Docker needed sandbox authorization;
no Azure, paid inference or application external service was called.

| Command / exercise | Actual result |
| --- | --- |
| `npm ci --ignore-scripts` | PASS, including a second clean copy without node_modules/dist/data; lifecycle scripts disabled; download cache reuse allowed |
| `npm run licenses` | PASS; 347 exact lock records and actual React/ReactDOM/scheduler license texts regenerated; identical inventory/notices across clean copy |
| `npm run typecheck` | PASS: API, frontend and test TypeScript contracts |
| `npm run lint` | PASS: ESLint, zero allowed warnings; rerun after final test-script change |
| `npm run format:check` | PASS: all selected application source/config/test files; documentation checker separately covers Markdown |
| `npm run build` | PASS: compiled API and production Vite frontend; matching browser asset hashes in original and clean copy |
| `npm test` | **39 passed in four files**: pricing, SQLite lifecycle, API integration and React components; passed again in clean copy |
| `npm exec -- playwright install chromium` | PASS; browser installed and exercised; no browser login/cloud dependency |
| `npm run test:e2e` | **3 passed** against isolated native API/Vite; same three passed in clean copy |
| `E2E_BASE_URL=http://127.0.0.1:8080 npm run test:e2e` | **3 passed** through actual production Nginx/API/SQLite; also passed in second clean Compose project |
| `docker compose build`, explicit migrate/seed, `up -d --wait` | PASS: both services healthy, only frontend 127.0.0.1:8080 published; API has no host-published ports |
| `npm run test:containers` | PASS: actual API replacement with retained cart; wrong-port 3001 fault; static 200 vs journey/readiness 503; restore 3000 and fresh correct cart total; own cart deleted |
| CLI migrate/repeat seed/reset and expected denials | PASS: deterministic reset of isolated `data/e2e.sqlite`; missing flag and four invalid paths exit 1, as required; [command results](m2-cli-checks.json) |
| `npm audit --omit=dev --audit-level=high --json` | PASS: zero reported production advisories at execution ([JSON](m2-production-audit.json)); advisory snapshot, not a security certification or dev/container scan |
| Repository docs/Git checks | See final validation below; includes new files, links/anchors and source whitespace |

The initial socket-based API attempt failed because sandbox networking returned
EPERM; the authorized rerun and clean-copy run passed. Initial type/UI issues
found during implementation were fixed before the final passes. No failing check
is waived to produce this exit status. Counts describe assertions actually run,
not a coverage percentage or proof against all possible defects.

The three browser cases cover the real catalogue/search/category/cart/discount/
reload/update/remove journey, an explicitly **simulated** browser-intercepted 503
with retry, and a 390px viewport with keyboard search/no horizontal overflow.
The container fault below is real local configuration failure, not interception.
Screenshots of our own UI were visually inspected:
[desktop](images/m2-desktop.png), [mobile](images/m2-mobile.png). Labelled controls,
focus and loading/empty/error/recovery states have component/browser checks;
this is not a complete accessibility audit or conformance claim.

## Clean reproduction, fault and persistence

The second copy contained application source/config/license/lock/inventory only;
it excluded node_modules, built assets, DBs and test output. Native installation,
license generation, type/lint/build, 39 tests and 3 browser cases passed there.
The lock, generated dependency inventory and browser notices were byte-identical.

A separate `morrow-supply-m2-clean` Compose project then built from that copy and
created a **previously absent** named volume. Explicit migration/seed/start and
three production browser cases passed. [Clean setup command/timing record](m2-clean-setup.json)
and [container fault/recovery record](m2-clean-container-smoke.json) retain actual
UTC times, port values, actor, statuses and request IDs. The clean volume/network/
containers were removed; the original project was restored healthy. Build/download
caches were reused normally; a fresh dependency/DB state does not require disabling
content-addressed caches. Verification was on arm64; x64/Windows are not claimed.

The fault test first verifies API port 3001 is refused. It creates only its own
synthetic cart, force-replaces the API container and confirms unchanged items/
totals on the named volume. It then changes frontend API_PORT 3000→3001. Static
`/` remains 200 while `/api/products` and frontend `/health/ready` return 503.
Finally it restores 3000, reads a fresh 200 response and correct 28796p total,
then deletes only its own cart and verifies 404. The actor is the deterministic
local script; no autonomous SRE diagnosis/remediation or cloud recovery is claimed.
Short local samples are not M6/M7's operational SLO/recovery measurement window.

## Acceptance mapping

| Criterion | Outcome / concrete evidence |
| --- | --- |
| M2-A1 source/license | PASS: owner-selected independent MIT; original data/art/code; [ADR 0002](../decisions/0002-source-reuse.md), [notices](../../THIRD_PARTY_NOTICES.md), exact dependency inventory and browser license text |
| M2-A2 toolchain/build | PASS: exact runtime/npm, lock and image pins; clean install/type/build on host and local containers |
| M2-A3 catalogue/contracts | PASS: 12 deterministic products, detail API, search/category/sort/page validation, actual same-origin UI/API journey |
| M2-A4 cart/pricing/errors | PASS: canonical integer arithmetic/discount thresholds, two-cart isolation, absolute updates, concurrent distinct-line requests, invalid/tampered values and cleanup |
| M2-A5 data lifecycle | PASS: replay/seed/reset determinism, altered/reordered/unknown migrations refused, foreign keys, new connection/container persistence, unsafe paths including dangling symlinks refused |
| M2-A6 meaningful checks | PASS: type/lint/build, 39 tests and three browser cases; malformed/error/threshold/migration/outage cases included, not merely component render snapshots |
| M2-A7 local/security boundary | PASS: non-root read-only containers, only loopback frontend published, bounded input/safe errors and source/config review; no cloud/agent/CI/Claims Processing implementation |
| M2-A8 clean setup | PASS: second clean copy and fresh independent Compose volume; explicit setup/reset/stop/teardown documented and exercised |
| M2-A9 UI states | PASS: keyboard/search/loading/empty/error/cart refresh/reset and outage restoration cases; focused desktop/mobile visual review |
| M2-A10 reversible fault | PASS: recorded actual port/config/time/request IDs; static-vs-dependency gap, replacement persistence and fresh recovery; actual repair actor recorded |

V01–V08 are exercised locally. V18 has local provenance/license/setup/ignore and
focused source checks; full secret/SAST/container/SBOM/protected-release checks
remain **M3 planned**. Cloud/agent cases V09–V17 remain planned. No 28-day
availability, production auth, Azure SQL, RPO/RTO or performance improvement result
is inferred from these tests.

## Final validation and remaining limits

Repository documentation links/anchors, M0–M12 titles and catalogue references,
UTF-8/LF/newlines, `git diff --check` and individual untracked-text no-index checks
passed: 28 documentation/text files, 25 Markdown files, 169 local file/anchor links,
all 13 milestone titles/order and M1 catalogue references. Individual no-index
checks cover all 52 untracked UTF-8 files, including source/config/licenses/JSON;
two binary screenshots are excluded from whitespace checks. External URL uptime
is not checked by the repository script. Generated DBs/modules/build/browser
output remain ignored; reviewed JSON records and original screenshots are retained.
The source fingerprint identifies the uncommitted app; HEAD remains unchanged,
with no staged changes, commit, push or repository visibility change.

Remaining limits are deliberate: SQLite driver release-candidate API, one local
writer and anonymous synthetic carts; no cloud authentication/durability, backup
restore, scale/performance/SLO validation, full accessibility/security audit or
cross-platform matrix. Package advisories and licensing need review when changing
dependencies/distribution. One manifest makes the small app maintainable but also
ships React packages in the API production dependency tree; separate packaging is
deferred until a concrete benefit justifies it. Direct OctoCAT reuse remains not
cleared and excluded, so it is not a blocker to this independent baseline.

M2 exits at this local baseline. M3 secure delivery is the next roadmap stage,
requiring a new scoped request; no M3 workflows, Azure infrastructure/deployment,
agents, credentials or paid services were implemented. The owner reviews and
manually commits/pushes the changes.
