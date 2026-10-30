# ADR 0003 — Local SQLite and cloud relational durability

Date: 2026-10-30. Status: local SQLite implementation Locally tested in M2; cloud design unverified.
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
