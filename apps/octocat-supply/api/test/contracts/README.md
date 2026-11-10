# Repository acceptance contracts

M4C-C1 implements `repositoryContract(name, createFixture)` in
[repository.contract.ts](repository.contract.ts). The real SQLite runner is
[repository-sqlite.contract.test.ts](../repository-sqlite.contract.test.ts).
Vitest's existing API project discovers the runner; no workflow, package, runtime
or production repository changes are needed.

From `apps/octocat-supply`, using the pinned Node 24.22.2:

```sh
npm run test:api -- api/test/repository-sqlite.contract.test.ts
npm test
```

## Fixture contract for C2

The factory may be asynchronous and must return a `RepositoryFixture`:

```ts
interface RepositoryFixture {
  open(): Repository | Promise<Repository>;
  dispose(): void | Promise<void>;
}
```

- Create one isolated disposable database per test; migrate and seed the unchanged
  twelve products before returning. If setup fails, clean up before rejecting.
- Every `open()` returns an independent connection/pool to that same database.
  Opening a new empty database or returning a cached repository invalidates the
  persistence and multi-connection tests. The factory must not retain a bootstrap
  connection. Runtime `open()` must not migrate, seed or reset.
- The suite awaits every repository operation, including close. It closes all
  connections before disposal and explicitly closes/reopens all connections in
  R16. `dispose()` deletes only the fixture it owns, even on failure. It must not
  reset an owner's database or depend on an existing cloud demo.
- Register the same function in a future real-engine `*.test.ts` runner. Supply
  actual `SqlStore(new DriverExecutor(approvedTestConfiguration))` instances;
  adapter-specific work is restricted to provisioning/bootstrap/open/dispose.
  Do not copy/relax expectations, wrap errors into success, fake query results,
  silently retry writes or skip missing mandatory configuration.
- Both owners are synthetic `oidc:` keys containing 64 hex characters. This is a
  repository ownership contract, not JWT/provider verification. Anonymous-demo
  behavior remains in existing SQLite/API tests; SQL deliberately rejects it.

C1 contains no SQL engine runner, skipped placeholder, credential, SQL configuration
fallback or engine success claim. The existing eight `sql.test.ts` cases remain
**Simulated recording-driver checks**. C2 needs a new bounded authorization,
supported x64 host/pinned engine/license, dedicated fixture/principals, trusted
TLS CA/host and disposal rights; see [C2 acceptance](../../../../../docs/milestones/m4c-scope.md#c2--real-sql-server--driver-integration).

## Case matrix and proof boundary

| IDs                      | Invariant                                                                                                                                                                                      | Validation / threat mapping                      | Real SQLite C1                    | Real SQL C2                                           |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | --------------------------------- | ----------------------------------------------------- |
| R01–R05                  | Exact fixtures/detail/readiness, case/category search, literal wildcards/injection-like input, count-before-page, stable price ties, safe unknown product                                      | V01/V02/V08; T02                                 | Pass                              | Blocked                                               |
| R06–R08                  | Unique empty carts, every cross-owner read/set/remove/delete denial in both directions matches missing-resource error, same-owner cart and other-owner line isolation                          | V04/V08/V09; T01/T02/T06 ownership boundary only | Pass                              | Blocked                                               |
| R09–R11                  | Absolute quantity 1/99, duplicate idempotence, product-ID line order, authoritative GBP integer totals, discount flooring/threshold/recalculation                                              | V03/V04; T02                                     | Pass                              | Blocked                                               |
| R12–R15                  | Invalid quantities and missing products leave committed state unchanged, subsequent transactions work, repeated line removal succeeds, repeated cart deletion returns 404, other carts survive | V03/V04/V08; T02                                 | Pass                              | Blocked                                               |
| R16                      | Ownership, cart edits and deletion survive closing every connection and reopening the file/database                                                                                            | V05; T01/T02                                     | Pass                              | Blocked                                               |
| R17–R18                  | Twenty rounds of distinct-product updates on two connections retain both lines; same-product outcome is one serialized absolute quantity; duplicate concurrent submissions remain idempotent   | V04; T02                                         | Pass, scheduled synchronous calls | Blocked; actual driver overlap/locking must be proved |
| S01 INSERT/UPDATE/DELETE | SQLite post-write `RAISE(FAIL)` leaves no partial changes; transaction ends and second connection can write                                                                                    | V04/V05; T02                                     | Pass, real triggers/rollback      | Dialect-specific C2 extension required                |
| S02                      | Raw SQLite FK/quantity/unique constraints, physical cascade deletion, other-cart preservation and `foreign_key_check`                                                                          | V04/V05; T02                                     | Pass                              | Dialect-specific C2 extension required                |
| S03                      | Real competing connection cannot see uncommitted data or write through an existing write lock; rollback releases it without data loss                                                          | V04/V05; T02                                     | Pass, existing 1s busy timeout    | Actual lock/deadlock/timeout extension required       |
| S04                      | Failed cart deletion rolls back both the cart and its cascaded line deletions                                                                                                                  | V04/V05; T02                                     | Pass, real post-delete trigger    | Dialect-specific C2 extension required                |

There are **27 shared cases** (18 IDs, with four R07 methods and seven R12 values)
and **six SQLite-specific cases** (four IDs, with three S01 operations). No pricing
helper or production fixture import computes shared expected results. Prices,
totals, errors and order have independent explicit expectations.

R17/R18 schedule both calls through promises on two real connections. Node's
synchronous SQLite calls execute serially on one event loop. This demonstrates
observable interleaved-operation invariants, **not simultaneous writer execution,
thread/process safety, SQL isolation or deadlock behavior**. S03 holds a real write
lock across a second connection's attempted write, but does not assert a throughput
or wall-clock latency SLA. SQLite supports one writer; C2 must exercise actual
asynchronous TDS overlap and record both connection identities/timing.

S01/S04 use `RAISE(FAIL)` intentionally: unlike statement ABORT, FAIL can retain
earlier statement effects, so these regressions require the repository's explicit
rollback. Fault triggers and raw constraint probes exist only in owned test files.

The common fixture has twelve products: reaching the 100-distinct-line cart limit
would require noncanonical data, so that limit is not claimed here. Existing
pricing unit tests cover its helper guard. API request shape/content type/ID and
query bounds, JWT authentication, anonymous compatibility, migration drift/reset
paths and HTTP error serialization remain in the unchanged original suite.
SQL-specific migration/application-lock/DDL rollback, grants, type conversions,
TLS/outage/deadline and managed-identity/private-network acceptance remain C2/later
gates, not SQLite assertions. [C1 evidence](../../../../../docs/evidence/m4c-c1-repository-contracts.md)
records commands, hashes and limitations.
