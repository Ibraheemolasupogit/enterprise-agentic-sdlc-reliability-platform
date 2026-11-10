# M4C engineering-readiness assessment

Date: 2026-11-10 UTC. Base: `40a6353c90bf614604f7de517639d0dd4f832867`,
initial working tree clean. Authority: owner's **assessment/planning-only** request.
Status: assessment recorded; implementation packages **Planned**, real SQL/provider/
Azure gates **Blocked** pending prerequisites and scoped authorization. Deployment
remains **NO-GO**. The [proposed work packages](../milestones/m4c-scope.md) authorize
no execution. [JSON evidence](m4c-readiness-assessment.json) records inspected facts,
sources, verification limits and documentation checks.

## Confirmed baseline and scope of proof

Read-only GitHub run/job metadata and application, containers and required logs
were inspected for [run 42794873352](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/42794873352).
Its SHA matches local HEAD and remote main: `40a6353`. Policy, application,
containers and required passed; CodeQL skipped. Logs show 64 application tests,
three application browser cases, three production-container browser cases and the
TLS proxy positive/negative cases passing. Image scan and unsigned provenance
steps succeeded. Their downloadable artifact contents/hashes were not independently
reverified in this assessment; a successful step is not a signed release approval.

This supplies the previously missing hosted evidence for the
[proxy repair](m4b-ci-repair.md), [frontend package repair](m4b-frontend-image-repair.md)
and [Playwright environment repair](m4b-playwright-ci-repair.md). Those dated records
are preserved as historical snapshots. The separate containers job's host apt
installation succeeded in this run; one success does not remove its mirror risk.
These remain synthetic SQLite/local-TLS tests on hosted infrastructure, not Azure
SQL, Entra sign-in, protected release or deployed-application verification.

## SQL: implemented adapter, simulated engine evidence

Inspected [SQL adapter](../../apps/octocat-supply/api/src/sql.ts),
[explicit CLI](../../apps/octocat-supply/api/src/sql-cli.ts),
[runtime selection](../../apps/octocat-supply/api/src/runtime.ts),
[repository interface](../../apps/octocat-supply/api/src/repository.ts) and
[eight SQL tests](../../apps/octocat-supply/api/test/sql.test.ts).
[ADR 0003](../decisions/0003-persistence.md) remains the persistence decision.

| Existing implementation/evidence | Missing integration proof |
| --- | --- |
| `SqlStore` uses a minimal async executor; eight tests use `RecordingExecutor`/fake clocks | No SQL parser/engine or production `DriverExecutor` connection executes in these tests. Recorded query text and commit counters do not establish real commit/rollback |
| `mssql` 12.7.13/Tedious, explicit user-assigned MI, encrypted TLS/certificate verification; pool max 4/min 0 and 1s bounds | Real TDS binds/results, trusted certificate/host matching, connect/reconnect/pool behavior, cancellation, MI token acquisition/renewal and actual latency remain unverified |
| Numbers bind as `BigInt`, strings as `NVarChar(256)`; UUID/string and int columns are used | Exercise real conversions/result types, overflow/rounding boundaries, UUID matching, collation/case/order, escaped LIKE wildcards and pagination. These are test targets, not confirmed defects |
| Checksummed T-SQL migration, transaction-owned `sp_getapplock`, explicit seed and drift rejection | Execute fresh/replay/edited/unknown history, parallel migrators, failed DDL/seed rollback and permission denials against an engine |
| SERIALIZABLE owner/cart locking, authoritative integer totals, owner-bound mutations | Two real connections must prove no lost updates, owner isolation, FK/cascade behavior and clean state after lock timeout/deadlock/rollback |
| Runtime/migrator IDs must differ; startup/readiness do not DDL | No actual SQL users/grants exist in these definitions. Azure RBAC/MI attachment is distinct from contained-database data/DDL rights |

Three proof layers are required: shared repository/domain contracts; actual SQL
Server driver/engine integration; then Azure SQL + ACA managed identity + private
network integration. Passing one must not be relabelled as another. SQL Server
tests also do not prove Azure SQL backup, service-tier or Private Link behavior.

The current macOS arm64 host is not a supported SQL Server Linux container host.
Microsoft documents [Intel/AMD x86-64 Linux support and excludes emulation](https://learn.microsoft.com/sql/linux/install-upgrade/setup).
Use an owner-approved supported x64 test host/image, or an explicitly approved
existing dedicated engine. No ARM/Rosetta/QEMU result should satisfy the supported
engine gate. No SQL instance, EULA acceptance, credential, login or connection
was created here. Current production configuration is MI-only; a local engine
cannot exercise that Azure identity endpoint. A future test-only principal/setup
exception would need explicit owner scope and must never add a runtime fallback.

## Identity: crypto boundaries verified, provider flow unverified

Inspected [API authentication](../../apps/octocat-supply/api/src/auth.ts),
[JWT/ownership tests](../../apps/octocat-supply/api/test/auth.test.ts),
[browser implementation](../../apps/octocat-supply/frontend/src/AuthApp.tsx) and
[three browser identity tests](../../apps/octocat-supply/frontend/test/AuthApp.test.tsx).
[ADR 0007](../decisions/0007-application-identity.md) remains authoritative.

JWT signature/claim denials execute real `jose` crypto with published test keys;
JWKS rotation/outage uses local/custom-fetch fixtures. SQLite ownership runs real
HTTP/repository code. The three browser identity tests cover config failure,
storage-key separation and bearer attachment; they do not exercise a provider
redirect, code exchange or full `UserManager` callback. Hosted E2E remains the
anonymous commerce journey. No tenant registration, consent, role assignment,
real user token or provider session has been validated.

Required real-flow evidence includes tenant-specific discovery/issuer/JWKS, actual
API audience and delegated scope plus top-level role, two owners, exact registered
SPA HTTPS callback/CORS, state/nonce/PKCE/code replay denials, expiry/reauthentication,
provider/JWKS errors, and proxy/CSP compatibility. Microsoft documents the
[SPA PKCE/CORS requirements](https://learn.microsoft.com/en-us/azure/active-directory/develop/v1-protocols-oauth-code).
Keep the current pinned libraries; no provider/library migration is justified by
this assessment alone.

Two concrete validation targets deserve early fixtures:

- The API enforces `maxTokenAge: "1 hour"`, while the UI checks the provider expiry.
  [Entra default token lifetimes can vary from 60–90 minutes](https://learn.microsoft.com/en-us/entra/identity-platform/access-tokens).
  Prove that an API 401 before browser `exp` leads to a usable sign-in path; do not
  silently widen token-age validation. Verify token-version/issuer/audience choices
  from the actual API registration rather than assuming a v2 endpoint fixes them.
- [Playwright config](../../apps/octocat-supply/playwright.config.ts) retains failure
  traces. Real-provider traces/HAR/network captures may contain codes, PKCE values,
  tokens and personal data. A separately configured provider rehearsal must prevent
  their retention and prove artifact redaction before real credentials are used.
  Preserve existing anonymous E2E diagnostics/coverage. Never upload tokens to a
  third-party decoder or commit browser auth storage.

Local sign-out is application-only; it does not revoke a token or end Entra SSO.
JWKS outage does not necessarily invalidate a still-valid token with a cached key;
unknown/unresolvable keys must fail closed. Readiness checks DB/schema, not IdP
availability. Observe live provider rotation when available; deterministic fixture
rotation is still **Simulated**, not a forced change to provider signing keys.

## Azure definitions, networking, identities and diagnostics

The [four existing templates](../../infra/README.md) compile candidate boundaries
and app settings. Their missing resources are not supplied by successful CI.

| Current source | Remaining requirement / proof |
| --- | --- |
| `foundation.bicep` consumes a subnet ID; external workload-profiles environment with internal API app; `peerAuthentication.mtls` | Dedicated VNet, non-overlapping reviewed CIDRs, ACA delegated subnet and separate SQL PE subnet, NSGs/routes/platform egress and DNS. Internal API ingress and environment mTLS do not replace JWT ownership |
| `apps.bicep` binds SQL server/database and OIDC settings | Actual SQL logical server/DB, Entra-only admin/bootstrap, public network disabled, private endpoint/connection and private DNS zone/link are absent |
| Pull and API runtime UAIs; registry-scoped AcrPull candidate | Dedicated migrator/publisher/release identities, exact bootstrap grants, SQL users/object rights and effective denials. Any SQL directory-lookup identity/Graph grant needs separate justification; do not default to Directory Readers/Owner |
| Authenticated public ACR Basic; exact federation subject input | Verify non-ABAC role model/pull propagation, approved registry manifest digests, actual emitted GitHub OIDC subject if that release route is selected; no discovery run or new OIDC permission now |
| API/frontend HTTPS configuration with resolver input | Resolve ACA API FQDN and SQL through approved DNS; preserve CA/name/SNI/host verification. Use the normal SQL server FQDN while private DNS resolves it privately; verify actual routing/connection-policy ports |
| Log destination `none`; API route/status/duration/request-ID console logs, Nginx access log off | Bounded console/system diagnostics, revision/image/config/schema correlation, log access/retention/ingestion settings and safe failure classification. No minimal deployment-diagnostic sink is defined |
| No migrator job, private test executor or release manifest | Explicit bounded migration execution, connectivity from the private network, compatible schema/image pair, teardown inventory and independently reviewed approval record |

Primary [ACA networking guidance](https://learn.microsoft.com/en-us/azure/container-apps/custom-virtual-networks)
requires a dedicated delegated workload-profiles subnet of at least /27; actual
CIDRs, capacity and Azure permissions remain unresolved. A SQL private endpoint
does not itself disable public access. [SQL Private Link guidance](https://learn.microsoft.com/en-us/azure/azure-sql/database/private-endpoint-overview?view=azuresql)
also requires the normal `<server>.database.windows.net` hostname for verified
client login. No public-SQL/firewall or TLS fallback is acceptable.

Keep diagnostics narrower than M6 observability. [ACA log documentation](https://learn.microsoft.com/en-us/azure/container-apps/log-monitoring)
identifies console/system logs and optional HTTP logs whose paths include query
strings and whose forwarding fields can contain personal data. Do not enable
raw HTTP/auth callback logging without proven collection-time controls. Proposed
minimal evidence is redacted startup/dependency/error classes and release/revision
correlation, not dashboards, full tracing, SLO measurement or an agent fleet.
Threat T05 also retains unproven request-rate/per-user cart-creation controls;
approve constrained synthetic exposure/traffic before any externally reachable
rehearsal rather than treating max replicas as an abuse or cost limit.

## CodeQL and governance observations

The repository is private and user-owned. Current GETs returned:

| Read-only source | Actual result / limit |
| --- | --- |
| Run/jobs/required log | Mandatory jobs passed; CodeQL skipped with coverage notice. No SAST result |
| Repository metadata | Private, owner type User; `security_and_analysis` not returned. No current entitlement/feature-enabled conclusion follows from omission |
| `branches/main` | `protected=false`, protection `enabled=false`, required status enforcement `off`; green `required` is not server-side enforcement |
| Detailed branch protection | 403 `Resource not accessible by integration`; current detailed settings are unreadable through this connection, not a newly observed plan error |
| Rulesets | 403 `Upgrade to GitHub Pro or make this repository public to enable this feature.`; explicit current private-plan restriction |
| Environments | Connector rejected this endpoint as unsupported (400); state not re-read. M4A's zero environments is historical, not a current observation |

These are three separate entitlement decisions. [Branch protections](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
can be available for private repositories on Pro/Team/Enterprise. That does not
enable private CodeQL: [GitHub's CodeQL guidance](https://docs.github.com/en/code-security/reference/code-scanning/troubleshoot-analysis-errors/private-repository-enablement)
requires an eligible Team/Enterprise arrangement with Code Security; Free/Pro
code scanning is public-only. This personal private repository has no established
eligible configuration. [Local CodeQL CLI use](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-cli)
is not a licensing workaround. Separately, [required deployment reviewers](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
on Free/Pro/Team are public-only under current documentation. Private environment
reviewer protection therefore needs a separately verified supported route.

Owner options remain an eligible protected/private Code Security arrangement;
an approved supported SAST alternative plus explicit coverage review and ADR
0005's owner-operated release route; or separately reviewed public publication.
None is selected, purchased, enabled or waived here. A SAST alternative needs
actual scan/negative-control evidence; ESLint/audit/Trivy are not substitutes.
An independent human reviewer is still required where policy calls for one;
owner self-review or assistant review does not establish independence. Automatic
publishing/deployment and inference stay disabled.

## Assessment limits and result

Azure account/session, subscription, region, quota, permissions, providers, policy,
locks, names and effective networking were not queried. M4A's blocked live checks
remain **Blocked**; no CLI sign-in, token refresh, credential fallback or cloud
authentication occurred. No engines/providers/containers, application suites,
image scans or infrastructure validation were run for this documentation-only
task. Local verification was limited to repository/JSON/whitespace checks,
implementation preservation and a working-tree secret scan. Existing hosted job
results and source inspection are evidence; future test matrices are proposals.

The assessment is delivered with the [dependency-ordered M4C plan](../milestones/m4c-scope.md).
M4B hosted repair verification is established at this SHA. SQL/provider/identity/
network/diagnostics/SAST/governance readiness is not established, and no M4C
implementation or release is authorized. Preserve Claims Processing separation,
the historical C1–C6/C7/watchdog distinctions and the M4A deployment NO-GO.
