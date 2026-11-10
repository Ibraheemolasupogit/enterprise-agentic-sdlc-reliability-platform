# M4C-C1 — Repository acceptance contracts

Date: 2026-11-10 UTC. Authority: owner's **C1-only implementation** request.
Base HEAD: `0645f09b8a8bad0cdbbafe694c3a60e27be601f8`; test changes are uncommitted.
Status: **Locally tested on real SQLite; C1-A1–A4 met**. Real SQL engine execution
remains **Blocked for C2**; existing eight SQL adapter recording tests remain
**Simulated**. M4A deployment **NO-GO** and C2–C8 authorization boundaries remain.
The earlier [assessment](m4c-readiness-assessment.md) is a dated planning snapshot,
not proof of these new tests. [Machine-readable evidence](m4c-c1-repository-contracts.json)
records source/tool/schema hashes, individual cases, commands and outcomes.

## Implemented boundary

Added a reusable asynchronous repository contract and real file-backed SQLite
fixture/runner. Every test gets a new owned temporary database, explicitly migrated
and seeded before opening independent runtime connections. Cleanup closes all
connections then removes only its owned directory, including WAL files. No demo
database, normal volume, SQL engine, operational credential or cloud resource is
used. R16 closes every connection before reopening the same database twice.

The shared contract uses the existing production `Repository` interface, awaits
synchronous/asynchronous methods and captures both synchronous throws and rejected
promises. Independent expected values specify prices, errors, fixtures and order;
the shared assertions do not import production pricing helpers or fixture values.
No production source, API, authentication boundary, migration, dependency/lock,
workflow, IaC, proxy, scanner or security threshold changed.

The initial working tree already contained changes to AGENTS/README, architecture,
capability status, delivery, roadmap and threat model, plus untracked
`m4c-readiness-assessment.json`. They were preserved. Architecture, delivery, threat
model and that JSON are byte-identical to the initial snapshot. This task updates
only C1 authority/status in the other four existing documents, persistence ADR,
M4C scope and new contracts/evidence. Original application/test/configuration files
are byte-identical to the initial snapshot; the JSON records the aggregate digest.

## Coverage and regression evidence

The [contract matrix and fixture handoff](../../apps/octocat-supply/api/test/contracts/README.md)
maps IDs to V01–V05/V08/V09 and T01/T02/T06, with the limits of those mappings.
There are **27 shared cases and six SQLite-specific regressions**, all passing:

| Cases | Actual assertions |
| --- | --- |
| R01–R05 | Twelve exact products/details, ready schema/fixtures, case-insensitive search/category combination, literal wildcard/injection-like text, filtered count before pagination, empty pages, deterministic price ties, safe missing-product error |
| R06–R08 | Unique empty carts, same-owner cart isolation, symmetric other-owner denials for read/set/remove/delete matching missing-cart 404/code/message, unchanged state observed through another connection |
| R09–R11 | Absolute quantities 1/99 and duplicate idempotence, product-ID line order, GBP minor units, 31995p subtotal / 3199p discount / 28796p total, discount floor/exact threshold/recalculation after edits/removal |
| R12–R15 | Seven invalid numeric quantities, missing product, committed state unchanged on failure, subsequent usable transaction, idempotent removal including missing product, repeated cart delete gives 404, other carts preserved |
| R16 | Ownership, exact committed contents, edits and deletion persist after all connections close/reopen |
| R17–R18 | Two connections, 20 scheduled distinct-product rounds retaining both lines/exact totals, same-product serialized absolute outcome and duplicate concurrent submissions without duplicate lines |
| S01 (three operations) / S04 | Real post-INSERT/UPDATE/DELETE and cart/cascade-delete `RAISE(FAIL)` triggers require transaction rollback; state unchanged from another connection, transaction released, subsequent writer succeeds |
| S02 / S03 | Actual SQLite FK/quantity/unique constraints, physical cascading cleanup and integrity check; uncommitted data hidden and competing write rejected while a real lock is held, followed by rollback/recovery |

The post-write triggers use SQLite `FAIL`, which can preserve earlier statement
effects if no explicit transaction rollback occurs. This makes rollback regressions
observable instead of merely counting transaction callbacks. Faults are injected
only into disposable test schema; no production hook was introduced.

## Commands and results

Execution window, per-command UTC times, exit codes and case names are in the JSON.
Local raw logs/reports are retained under ignored `artifacts/m4c-c1/`, with existing
delivery outputs under `artifacts/m3/` and `artifacts/m4b/`. These are local evidence,
not uploaded hosted results. Tools: Node **24.22.2**, npm **11.19.1**, SQLite **3.53.4**,
Vitest **5.0.5**, Playwright **1.64.1**, Python **3.12.8**, Docker Engine **28.3.3**
Linux/arm64, Bicep **0.48.1**, actionlint **1.7.12**, Gitleaks **8.30.1**, Trivy
**0.72.0**. Native application/contracts run on macOS arm64. The pinned Node/tools
under `/private/tmp/morrow-repair-node/` and `/private/tmp/morrow-repair-tools/`
were placed on PATH; no installation or package upgrade was needed.

| Check | Result |
| --- | --- |
| `npm run test:api -- api/test/repository-sqlite.contract.test.ts` (equivalent direct Vitest command with JSON reporter) | 33 passed, zero failed/skipped |
| `npm run format:check`; `npm run lint`; `npm run typecheck`; `npm run build` | Pass |
| `npm test -- --reporter=default --reporter=json --outputFile=../../artifacts/m4c-c1/application-tests.json` | 97 passed across eight files: original 64 plus 33 new; zero failed/skipped |
| `npm run licenses`; diff check of dependency inventory/notices | Pass; generated tracked files unchanged |
| `npm audit --audit-level=high --json` | Pass: zero HIGH/CRITICAL; ten pre-existing MODERATE findings remain, no waiver or dependency change |
| `npm run test:e2e` | Three original Chromium journeys passed, no retries/skips |
| `actionlint -shellcheck=` | Pass |
| `python3 scripts/delivery/validate_infra.py` | Four existing Bicep templates lint/build passed, no warnings; no ARM/cloud validation |
| `python3 -m unittest discover -s tests/delivery -v` | 12 passed, including fail-closed gate, negative workflow/IaC mutations, proxy diagnostics and generated secret canary |
| `python3 scripts/delivery/scan_config.py` | Pass, zero HIGH/CRITICAL reported for compiled ARM/API/frontend Dockerfile inputs; finite Trivy coverage supplemented by explicit compiled policy tests |
| `python3 scripts/delivery/verify_containers.py` | Pass: isolated image build, 12 fixtures/pricing, hardening, API replacement persistence, three original Chromium journeys, cart cleanup; owned project/volume removed |
| `python3 scripts/delivery/verify_proxy.py` | Pass: verified CA/SNI/host and bearer forwarding/header stripping/readiness 200; wrong host static 200/API+readiness 503; seven unsafe configurations rejected |
| `python3 scripts/delivery/scan_images.py` | Pass for rebuilt API and frontend: zero HIGH/CRITICAL reported in each, SBOMs generated, no suppressions/threshold changes |
| `python3 scripts/check_repository.py`; tracked and each untracked text whitespace checks | Pass |
| `gitleaks git --redact --exit-code 1 --log-opts=--all .`; `gitleaks dir --redact --exit-code 1 .` | Pass, zero reported secrets |

The first sandboxed Bicep invocation exited 159 because .NET could not extract its
bundle into the user cache. It did not report an IaC defect. Its failure log is
retained as `artifacts/m4c-c1/sandbox-bicep.log`; the complete policy group passed
when rerun with authorized local tool-cache access. Application tests/browser and
container/proxy checks also used authorized local port/Docker access. No cloud
authentication or alternate credential mechanism was invoked.

The initial directory secret scan flagged the evidence JSON's source-file SHA-256
beside an `auth.ts` filename key as `generic-api-key`. The value was confirmed as
the public source checksum, not a credential. Evidence now uses separate `path`
and `sha256` fields; the scanner passes without rule/allowlist changes or suppression.
The initial redacted finding and failed-check log are retained locally.

Fixture JSON SHA-256 (UTF-8 `JSON.stringify(fixtures)`, no trailing newline):
`674bb9e29fbd1eef921680cfb4ce99a1293f5ea313c55e05bcc491a68fdcad89`.
SQLite applied migration SQL hashes, unchanged:

| Version | SHA-256 |
| --- | --- |
| 1 | `5ad18314480f4df1511889491541bc16b44a482e0af90251eb71b2f84bdf695f` |
| 2 | `a5f8561c6965ee6c95b0612ffffa5acc804738dcac0a03d64bf66997cecd4fac` |
| 3 | `3efb5845fc30a76b325e03a08e6e2d32677ab09618119218b69b79745efee75d` |

## C2 handoff, exclusions and acceptance

**C1-A1:** met by reusable awaited contracts and isolated real SQLite, with two
synthetic OIDC owner keys and original anonymous tests preserved.
**C1-A2:** met by the mapped assertions, exact pricing, per-fixture disposal and
real connection reopen/transaction probes.
**C1-A3:** met by the same R01–R18 C2 matrix, explicitly Blocked; no SQL placeholder
or fake engine result. The eight existing recording-driver tests remain Simulated.
**C1-A4:** met by the complete passing local checks above and hash/case evidence.
This earns C1 local acceptance only; it is not a release or cloud readiness claim.

R17/R18 invoke promises over two real SQLite connections, but synchronous calls
serialize on Node's event loop. They do not prove parallel writers, thread/process
safety, SQL SERIALIZABLE behavior, deadlock handling or throughput. S03 proves
actual lock contention/committed visibility/recovery with the existing one-second
SQLite busy timeout, without claiming a timing SLA. SQLite triggers/constraints
are not T-SQL proofs. Reopening a file is persistence evidence, not backup/PITR,
crash/power-loss durability or RPO/RTO validation.

The 100-distinct-product repository limit cannot be reached using the canonical
twelve-row fixture; the existing pricing helper oversized-cart guard remains
tested. Raw HTTP validation and auth/JWT/provider behavior are outside the common
repository contract and remain in the original suite. Browser checks retain the
anonymous synthetic journey; no new real provider flow was executed. No new hosted
run, SQL Server engine/driver connection, Azure SQL/managed identity/private DNS,
cloud validation, CodeQL execution, governance enforcement or deployment occurred.
Image scans use the existing HIGH/CRITICAL filter, so they do not assert an absence
of lower-severity findings. SAST/governance and all M4A/M4C cloud gates remain open.

C2 must first obtain a separate owner decision for a supported x64 host (the
current ARM Mac is not the supported SQL Server container target), pinned engine/
edition/license, owned disposable fixture, explicitly authorized bootstrap/runtime/
migrator principals and disposal, and trusted TLS CA/host. Do not accept an EULA,
create credentials, emulate an unsupported engine or add a production auth/TLS
fallback under C1. Compute/storage/hosted-minute costs require a bounded decision.

Once separately authorized, C2 supplies only the backend fixture to run the same
27 shared cases with actual `SqlStore`/`DriverExecutor`, and adds dialect-specific
constraint/cascade/fault/rollback tests. It must additionally meet C2-A1–A4: record
engine/version/collation and true TDS types, migration replay/drift/parallel locks/
DDL and seed rollback, actual overlapping two-connection rounds, least-privilege
denials, bad CA/hostname/outage/reconnect and configured timeout bounds. No silent
retries or skipped mandatory engine configuration. Azure SQL + managed identity/
private network proof remains a separate later boundary even after local C2 passes.

Stop after C1. No SQL deployment, credentials, cloud authentication, Azure resources,
GitHub settings, production behavior changes, commit or push was performed.
