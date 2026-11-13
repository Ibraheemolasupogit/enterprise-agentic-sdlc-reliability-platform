# ADR 0003 — Local SQLite and cloud relational durability

Updated: 2026-11-10. Status: SQLite/shared contracts Locally tested; SQL adapter Implemented,
recording-driver contracts Simulated; real SQL/Azure integration unverified.
Requirements: R02, R06, R11, R20. Owner: repository owner.

## Decision and reasons

Use SQLite for M2 on a **local named volume**, one API writer process, foreign
keys enabled, ordered tracked migrations and deterministic synthetic seed data.
Test databases are isolated; never run tests/reset against the normal demo file.
Seed explicitly/idempotently, not destructively on every server start. Schema and
repository contracts isolate storage choices without introducing a generic ORM
framework solely for portability.

Choose **Azure SQL Database** as the durable cloud target, not ephemeral container
SQLite. The commerce entities and transactional cart updates justify relational
constraints; managed backups/recovery and Entra access avoid building an operations
stack for a file database. M4 adds a SQL repository adapter and dialect-specific
migrations behind the same domain contract. M2 does not install a cloud driver or
pretend SQLite tests validate Azure SQL. Shared adapter contract tests must pass on
both before cloud release.

Cloud recovery design: automated backups with a chosen retention policy, restore
to an isolated database, verify schema/seed/control-record integrity, authorize
cutover, then test journeys. Target **RPO <= 1 hour, RTO <= 60 minutes** for the
small synthetic workload, measured in M9, not asserted from service marketing.
RPO measures lost committed control writes; RTO starts at observed loss of service
or data requiring restore and ends at independently verified usable service.
Detection, approval, execution and verification durations are recorded separately
and included in that elapsed objective. An exercise uses its known fault timestamp;
unknown real incident onset is reported as a measurement limitation.
[Azure SQL backup documentation](https://learn.microsoft.com/en-us/azure/azure-sql/database/automated-backups-overview?view=azuresql)
supports point-in-time restore, but does not prove these project objectives.

Select Azure SQL SKU/compute mode, retention, region and private networking only
after a costed M3/M4 plan. Serverless auto-pause is a candidate, not a promise of
low latency or zero idle charges. No deployment is authorized by this ADR.

## Integrity and rollback rules

- Money is integer minor units; validate quantity and use transactions. Browser
  prices are untrusted. Concurrent cart writes must not lose updates.
- Migrations are versioned and checksummed; reject changed applied migrations.
  Run once with a separate DDL identity before releasing code that needs them.
  Application runtime gets necessary data access, not DDL or database owner.
- Prefer additive, backward-compatible changes; rollback application/configuration
  only when compatible with current schema. Destructive/down migrations are not
  routine rollback. Restore requires separate approval and a data-loss assessment.
- A local reset names only the designated demo path, requires an explicit flag,
  refuses absolute/out-of-root or symlink targets and cannot address cloud storage.
- A file copy of a live WAL database is not the backup procedure. Use SQLite's
  backup API or a stopped/quiesced consistent snapshot; verify restored integrity.
- API restart and container replacement must retain data when the local volume is
  retained. Explicit volume deletion is destructive reset, not a persistence test.

## Alternatives and consequences

Ephemeral SQLite is useful for disposable tests, rejected for cloud durability.
SQLite over shared network storage is rejected: [SQLite WAL guidance](https://www.sqlite.org/wal.html)
requires same-host coordination and does not support network filesystems.
PostgreSQL is viable but adds another dialect with no current differentiating
requirement; Azure SQL is selected for the Azure/Entra demonstration. A managed
database costs more than ephemeral storage and introduces adapter/private-network
work in M4. If the authorized budget cannot support it, keep cloud deployment
blocked or revise this ADR; do not quietly claim ephemeral storage is durable.

## M2 driver and local evidence

Use the SQLite driver bundled with Node 24.22.2 rather than a separate native
addon. This avoids a package-specific compilation toolchain while keeping one
writer and the same parameterized repository contracts. The Node documentation
labels this driver release-candidate API; pinning/testing this runtime is required
and no production/cloud driver stability is claimed. M2 proves checksummed
migrations, explicit seed/reset, foreign keys, cart transactions, safe local paths,
fresh-connection persistence and API-container replacement with retained volume.
Cloud SQL adapter, backups/PITR, RPO/RTO and concurrency at scale remain untested.
See [M2 evidence](../evidence/m2-baseline.md).

## M4B bounded adapter decision

Use `mssql` 12.7.13 (MIT), default pure-JavaScript Tedious driver, pinned with
transitives in the application lock. The minimal asynchronous `Repository` boundary
preserves existing SQLite calls/tests and domain totals. SQL selects an explicit
user-assigned managed identity through Tedious `azure-active-directory-msi-app-service`
with required client ID; no password, DefaultAzureCredential chain or SQLite fallback.
TLS encryption/certificate verification are required. Pool max 4/min 0, idle 10s,
acquire/connect/request timeouts 1s. Readiness has an aggregate one-second deadline,
shares outstanding read work, and checks exact schema checksums and fixture rows.
Timed-out reads can finish in the driver under its own bounds; readiness never DDLs.

SQL queries bind bounded strings/numbers; sort column names use a fixed allowlist.
SQL schema uses int minor units/quantity constraints, foreign keys and an owner
column. Transactions are SERIALIZABLE, locking the owner/cart row before mutations;
this simple low-throughput design trades concurrency for correctness. T-SQL has an
independent checksummed migration history and transaction-scoped application lock.
Explicit migration/seed use a different required managed identity. Seed inserts
missing synthetic products and refuses drift; no SQL reset/down migration exists.
Runtime rights are table-specific, as detailed in [delivery](../delivery.md#m4b-local-configuration).

SQLite rows are not copied to SQL automatically. Start a new synthetic SQL database,
explicitly migrate and seed, then verify identical journeys/contract behavior on a
real engine before authorizing writes. Existing anonymous carts stay local; importing
them as authenticated carts is forbidden. SQLite migration 3 is additive but the
old M2 schema/readiness contract recognizes only migrations 1–2:
do not roll back to M2 images against schema 3. SQL schema 1 has no previously
cloud-verified image pair; record the first compatible pair before a future release.
No generic down migration, reset or file-to-SQL portability claim is made.

Recording-driver tests validate intended SQL/parameters, ownership, totals, history,
drift/error paths and transaction callbacks. They **do not parse/execute T-SQL**,
verify real driver binds/rollback/locking/collation, or establish managed identity,
private DNS, Azure SQL durability/backup behavior. No compatible authenticated SQL
test database was available under this no-credentials/no-cloud scope. Real-engine
contract, migration replay/drift/rollback and concurrency tests remain release gates.
Host is macOS arm64; do not assume a supported Linux SQL Server engine from emulation.
M4C-C1 adds 27 reusable domain cases executed against real file-backed SQLite and
six SQLite-specific transaction/constraint regressions, without production changes.
The [fixture contract and C2 matrix](../../apps/octocat-supply/api/test/contracts/README.md)
require independent connections and asynchronous operations; real SQL execution
remains Blocked. Scheduled synchronous SQLite operations do not establish parallel
SQL transaction behavior. See [C1 evidence](../evidence/m4c-c1-repository-contracts.md).
See [driver docs](https://tediousjs.github.io/node-mssql/),
[Tedious configuration](https://tediousjs.github.io/tedious/api-connection.html)
and [local evidence](../evidence/m4b-local-preparation.md).

## C4 static database contract

The separately authorized C4 slice defines a candidate Basic 5-DTU/2-GB database,
Entra group administrator/Entra-only access, public network disabled, TLS 1.2
minimum, explicit Proxy connection policy/TCP 1433, private endpoint/DNS, TDE and
seven-day Local backup retention. These are compiled/static-checked **definitions**,
not a SQL engine, backup/restore, grant, private network or managed-identity result.
Local backup redundancy does not establish geographic recovery or the unmeasured
RPO/RTO objectives. Costs/region/SKU and actual permissions remain release gates.

The [unapplied grant manifest](../../infra/identity-contract.json) separates runtime
table data access from time-bound migration CREATE TABLE/ALTER/REFERENCES and
history/seed rights. ALTER dbo remains broad inside that dedicated application-only
schema; bootstrap must verify no unrelated objects, actual engine permissions and
revoke DDL after the approved window. First creation also proposes temporary
schema SELECT/INSERT before new object grants can exist, then requires replacement
with the listed history/product object grants; no permanent schema data grant.
This sequence still needs real-engine proof. No db_owner, server directory identity,
Graph grant, SQL principal, credential or connection is created. The
[manual migrator definition](../../infra/migrator.bicep) is bounded but never started.
See [C4 evidence](../evidence/m4c-c4-infrastructure.md); C2/C7 real proofs remain Blocked.
