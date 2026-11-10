# M4B verification — local preparation only

Subsequent hosted result: run 41198119793 at `1e8d92d` passed application/policy
but failed the TLS harness; the required gate correctly failed and CodeQL skipped.
See the [bounded CI repair](m4b-ci-repair.md) for the reproduced Linux fixture
permission defect, fix, diagnostics and fresh local validation. The evidence below
is the original local snapshot, not a claim of hosted M4B completion.

Date: 2026-10-31 UTC. Authority: [master brief](../project/master-brief.md),
[scope](../milestones/m4b-scope.md) and the owner’s subsequent local-only request.
**Bounded local implementation delivered; deployment NO-GO preserved.** The broader
Slice 1 private SQL/network/diagnostics IaC and real integration gates are not closed.
No Azure sign-in/refresh, provisioning, GitHub settings, credentials, paid inference,
deployment, commit or push was performed. Claims Processing remains separate.

## Source and changes

Base HEAD: `0321efcdb5c189b9a39b45e6616b4784bf1d9a55`; changes are an uncommitted
working tree. Historical hosted run 41149829560 belongs to an earlier committed
baseline and does not validate M4B. CodeQL was skipped and has not executed.
Environment: macOS 15.6.1 arm64, Node 24.22.2/npm 11.19.1, Python 3.12.8,
Docker 28.3.3/Compose 2.39.2; local Linux arm64 images and installed Playwright
Chromium. Delivery tools remain pinned Bicep 0.48.1.52935, actionlint 1.7.12,
Gitleaks 8.30.1 and Trivy 0.72.0. No cloud target/capacity is inferred from them.

| Area | Main files / resulting boundary |
| --- | --- |
| Identity / ownership | `api/src/auth.ts`, `runtime.ts`, `app.ts`, `database.ts`, `server.ts`; issuer/JWKS/audience/time/role/scope validation, owner-bound cart operations, SQLite migration 3, cloud fail-closed configuration |
| Persistence | `api/src/repository.ts`, `sql.ts`, `sql-cli.ts`, `database-cli.ts`; minimal async boundary, parameterized SQL, managed-identity-only driver, separate explicit migrations/seed, no cloud reset/fallback |
| Browser / proxy | `frontend/src/AuthApp.tsx`, `App.tsx`, `api.ts`, `main.tsx`, `public/auth-config.json`, `start.sh`, `default.conf.template`; code/PKCE, memory tokens, per-principal cart reference, explicit HTTPS/CA/SNI/forwarding/CSP configuration |
| Validation | `api/test/auth.test.ts`, `sql.test.ts`, `frontend/test/AuthApp.test.tsx`, RFC fixture/notice, `scripts/delivery/verify_proxy.py`, TLS notice, `tests/delivery/test_security.py`, compiled-template policy |
| Delivery / dependencies | Existing CI only: pinned Node 24 artifact action, TLS test, visible CodeQL skip. Exact jose/mssql/oidc-client-ts/types dependencies, lock/inventory/browser notices and license generator |
| IaC | `infra/apps.bicep`: required public configuration and explicit cloud/OIDC/SQL/HTTPS bindings. No SQL/network/Entra/diagnostics provisioning definitions added |
| Guidance | README/AGENTS, app README/example, architecture, threat model, capability matrix, validation/delivery guidance, roadmap/charter/M4B scope, ADR 0003/0005 plus new 0007, third-party register and this evidence |

Original M2 test files/fixtures/business calculations remain unchanged. SQLite
migrations 1–2 remain byte-identical. A real SQLite upgrade test preserves their
checksums, assigns old rows only to anonymous:v1 and denies authenticated adoption.
All cart read/set/remove/delete paths enforce owner. Unknown/other-owner returns
404. Shared anonymous local carts are a demonstration boundary, not user isolation.
See [identity ADR](../decisions/0007-application-identity.md) and
[persistence ADR](../decisions/0003-persistence.md) for trade-offs and rollback rules.

## Executed checks and proof limits

| Command / check | Actual outcome and limit |
| --- | --- |
| Exact dependency installation with `--ignore-scripts` | New pinned libraries installed; lifecycle scripts disabled; 417 locked records including optional variants. Full tarball integrity remains in lock |
| `npm run licenses` | PASS: exact metadata and retained browser runtime texts (including Apache-2.0 OIDC and MIT jwt-decode); regenerates deterministically. Trailing blank-line whitespace normalized without changing license wording |
| `npm run format:check`, `npm run lint`, `npm run typecheck` | PASS; initial actionable formatting findings corrected |
| `npm test` | **64 passed, seven files**, including all original 39 tests unchanged; JWT crypto/claims/rotation/down-service/unsigned/tampered cases, all cart-owner denials, legacy migration, SQL recording/fake-clock contracts and frontend configuration/token/storage tests |
| `npm run build` | PASS API and production UI; JS index-NqKkJnbn.js, CSS index-DBuhDI_X.css |
| `npm run test:e2e` | **3 passed** with native isolated real API/UI; original browser journeys unchanged |
| `npm audit --audit-level=high --json` | PASS threshold: 0 high/critical; 11 moderate development findings from one minimatch advisory, not zero total findings |
| `npm audit --omit=dev --json` | PASS: 0 production advisories at execution |
| `actionlint -shellcheck=""` | PASS syntax/context, no shellcheck execution or hosted result implied |
| `sh -n frontend/start.sh` | PASS shell syntax; actual runtime behavior also checked in containers |
| `python3 scripts/delivery/validate_infra.py` | PASS all four Bicep lint/build plus policy checks; no Azure/ARM validate/what-if |
| `python3 -m unittest discover -s tests/delivery -v` | **8 passed**, including cloud anonymous/SQLite mutations, required TLS test, action pin, fail-closed shell gates and real non-live secret canary rejection |
| `python3 scripts/delivery/scan_config.py` | PASS finite Trivy checks: both Dockerfiles and registry-access compiled ARM. Trivy evaluates only that one ARM file; custom policy/mutations cover all four templates |
| `python3 scripts/delivery/verify_containers.py` | PASS isolated production pair: 12 fixtures/authoritative discount, non-root/read-only/cap-drop, loopback-only frontend, internal API, persistence across API replacement, **3 original browser cases** |
| `python3 scripts/delivery/verify_proxy.py` | PASS real local TLS: trusted CA/name/SNI, bearer/header boundary, explicit CSP, wrong peer-name yields API/readiness 503 with static 200, seven unsafe host/protocol/port/scope/DNS/CSP/multiline settings rejected |
| Final image scans / SBOM / provenance | Final binding recorded in [machine-readable results](m4b-local-results.json); reports are unsigned local evidence, releaseEligible=false; no registry push or approved manifest digest |
| Documentation / whitespace / secret scans | Final results and coverage recorded in the machine-readable summary; includes untracked text files, local Markdown links/anchors and git diff --check. No secret waiver or accepted exception added |

Test isolation projects own ports 18080/18081 and remove only their temporary
containers/volumes/network in finally. The existing M2 demo/volume on 8080 was
untouched. TLS test vectors are already public Node fixtures, checksum pinned and
used transiently; RSA JWT fixture is a published RFC vector with retained terms.
No live credential/key was generated or registered. Tests use fake issuers/users
and a deliberately non-live bearer string. A scanner initially misclassified a
fixture checksum adjacent to its filename as a generic key; separating the fields
removed that false match without scanner exclusions or suppressions.

**Executed versus simulated:** JWT signature verification, mock JWKS rotation/error,
SQLite HTTP/cart ownership, native browser journeys and local TLS proxy networking
execute real code. SQL tests record intended SQL/parameters and transaction callbacks,
with fake-clock timeout cases; they do not execute T-SQL or the real connection path.
No supported existing SQL test database/managed identity was available within this
no-credentials/no-cloud scope. No real provider authorization-code exchange, Entra
role assignment, SQL engine/collation/locking/rollback, managed identity, private
DNS, ACA ingress or Azure SQL integration is claimed. Readiness checks data/schema,
not IdP availability; authenticated synthetic journeys remain a live release gate.

## Security coverage and remaining work

The [minimatch advisory GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249)
affects installed 10.2.6; patched version is 11.0.1, outside ESLint’s ^10.2.6 range.
All 11 full-audit entries trace to this development graph; no runtime finding was
reported. No forced incompatible major override/downgrade, ignore file, accepted
exception or threshold weakening was used. Track a compatible lint-tool update and
rerun checks; untrusted PR lint remains bounded on a read-only ephemeral runner.
Reassess this open moderate risk before release; a passing high threshold does not
mean a clean full audit.

The artifact action now declares Node 24 in its pinned primary metadata. This is a
locally validated fix for the Node 20 action warning; hosted execution and removal
of punycode/url.parse warnings are unverified. Local Playwright emitted only its
NO_COLOR/FORCE_COLOR conflict. CodeQL remains unexecuted and the SAST coverage gap
is open; existing private-plan/protection restrictions were not changed or rechecked.

Before any deployment:

1. Authorize a compatible real SQL/identity rehearsal separately. Execute shared
   API/domain contracts, fresh/replay/drift/rollback/concurrency tests and runtime
   DDL denial. Verify driver/T-SQL behavior, managed identity, latency/cold-start
   bounds, private connectivity and fixture/schema compatibility.
2. Rehearse real single-tenant PKCE, redirect/CORS/CSP, actual API claims, role/scope
   assignment, expiration/rotation/provider outage and cross-owner denials. Local
   sign-out is not global SSO logout/revocation. Memory tokens require sign-in after
   refresh; users retain only their separate cart reference.
3. Complete/review private SQL/VNet/subnet/NSG/DNS/Entra/migrator and minimal diagnostic
   IaC. Current app bindings cannot supply those resources or prove cloud isolation.
4. Resolve supported SAST execution and independent review/protected-release route;
   manually commit/push and obtain new hosted results for the reviewed M4B SHA.
5. Close M4A subscription/region/permission/quota, exact scope/cost/identity/expiry/
   teardown approvals and compatible digest/config/schema rollback manifest. No
   pre-existing image pair is cloud verified; never reset/down-migrate to bypass it.

No cloud or inference charges were incurred by this local work; local compute,
public npm/tool downloads and Docker storage were used. The existing
[cost proposal](../project/azure-cost-estimate.md) remains provisional/unapproved:
48-hour estimate £5.03 with contingency, proposed ceiling £10, retained low-duty
£51.20/month and continuously-active £102.32/month. These are historical M4A model
outputs, not refreshed quotes/spend approval. Code Security/GitHub licensing remains
separate. No extra paid service or resource was created.

Stop at the local boundary. **The bounded requested local work is delivered with
explicit simulation limits; the broader M4B Slice 1 and cloud-release exit criteria
are not met. Deployment remains NO-GO.** Next work needs a separately bounded
real-engine/provider integration and remaining IaC/governance scope, not an apply.
