# M4A — Azure deployment preflight

Date: 2026-10-31. Authority: [master brief](../project/master-brief.md) and the
owner's M4A request. **Assessment recorded; Azure live verification BLOCKED;
deployment NO-GO.** M4A permits read-only checks through an already authenticated
session and documentation only. No sign-in/credential refresh, GitHub setting
change, provisioning, deployment, paid inference, commit or push is authorized.

[Evidence and selected retail meters](../evidence/m4a-preflight.json),
[itemised cost model](../project/azure-cost-estimate.md) and
[M4B handoff](m4b-scope.md) separate observations, assumptions and future gates.
M2 application/tests, M3 workflow and all infrastructure definitions are unchanged.
Claims Processing remains separate. Historical M3 evidence is preserved as captured.

## Verified observations

| Check | Observation and limit |
| --- | --- |
| Repository | Private `Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform`, main at `735989950304959dfda203d2b37558bcd30a3f71`; initially clean working tree |
| Hosted CI | [Run 41149829560](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/41149829560): policy, application, containers and required completed successfully; job/step APIs and logs inspected |
| Test outcomes | Hosted logs show 39 application tests, three native browser cases, three container browser cases and seven delivery-security tests passing; audit and history/tree secret gates passed |
| CodeQL | Job skipped. Required-job log shows `CODEQL_ENABLED` empty. **CodeQL has not executed**; a green aggregate job does not close the SAST gap |
| CI artifacts | Artifact metadata binds main/current SHA; downloaded image/security ZIP SHA-256 matches GitHub digest `ef6540a539174d962e48aec68e167ae558d5530b727c9837d19e7c6ec5e59c97`; artifact expires 2026-11-07 |
| Provenance/scans | Clean hosted working tree, run ID and SHA match; all 65 recorded source/build inputs match checkout; both Linux amd64 image reports show zero HIGH/CRITICAL findings and match SBOM image identities/hashes |
| Release identity | Hosted provenance is unsigned and `releaseEligible=false`; local image IDs are not published/approved ACR manifest references. No publishing/deploy/OIDC job exists |
| GitHub environments | Existing CLI GET returned HTTP 200 and `total_count=0`; no protected publisher/release environments exist |
| Branch governance | Classic branch-protection and ruleset GETs both returned HTTP 403 with a private-repository plan restriction. Effective protected review/required-check enforcement is not established; do not infer protections from the successful job named `required` |
| Local Azure surface | `az` unavailable in PATH; no custom `AZURE_CONFIG_DIR`; standard account profile/token-cache files absent. No usable existing authenticated Azure surface was identified. Credential-cache contents were not read; sessions elsewhere are not ruled out |
| Public pricing | GBP retail meters retrieved without Azure credentials for provisional UK South; some other price queries returned 429 or no applicable rows and are explicit allowances, not verified rates |

GitHub metadata/log/artifact tools and GET-only existing CLI authorization were
used. No workflow was triggered or rerun. Download links/tokens/raw credentials
are not retained. Hosted success verifies that committed validation baseline,
not the subsequently edited preflight documents or any Azure runtime capability.

## Azure subscription, region, permissions and quota checks

The following checks could **not** execute without an accessible valid Azure
session. No subscription/tenant ID, principal, offer, permissions, existing resource
inventory, regional capacity, policy or quota is asserted. UK South (`uksouth`) is
only a pricing/design candidate; it is not an approved or subscription-verified
target. An existing session's absence must not trigger `az login`, device code,
`get-access-token`, refresh or fallback credential searches under M4A.

| Required read-only evidence | Current status / acceptance before deployment |
| --- | --- |
| Subscription/tenant/principal | BLOCKED: confirm exact active subscription/tenant and Enabled state, existing principal identity and offer restrictions; retain sanitized references, not tokens |
| Effective authority | BLOCKED: inspect scoped assignments, effective permissions, inherited/deny assignments, locks, allowed locations/SKUs, policy and applicable PIM activation state. Reader does not prove deployment or RBAC authority |
| Provider readiness | BLOCKED: inspect Microsoft.App, ContainerRegistry, ManagedIdentity, Network, Sql, OperationalInsights/Insights and Authorization/Consumption where used; missing registration is a future approved mutation, not a read-only fix |
| Region/SKU capacity | BLOCKED: confirm Container Apps Consumption workload profiles, registry, SQL Basic and Private Link support for the selected subscription/region; catalogue listings do not reserve capacity |
| Quota/headroom | BLOCKED: confirm one environment, two apps, Consumption regional/core and environment limits, SQL logical-server/DB limits, registry and networking quotas. Allow overlap of old/new revisions and a bounded migrator; recommend at least 2 vCPU/4 GiB transient planning headroom, not a claimed quota |
| Resource/network inventory | BLOCKED: identify a new dedicated RG, no conflicting names/CIDRs, any shared DNS/network dependency, policy requirements, existing cost scope and platform-managed RG behavior |
| Entra authority | BLOCKED: confirm who may create the two app registrations/roles, configure SQL Entra administrator/users and create exact federation bindings; Azure RBAC is not Entra directory permission |

Follow-up reads may inspect the selected subscription/provider/location/usage,
RBAC/policy/lock, network/DNS and SQL capability resources through an existing
valid session. If it is expired, stop. Ordinary CLI REST calls can refresh tokens:
do not use them as an implicit workaround for the no-refresh instruction. Current
[quota guidance](https://learn.microsoft.com/en-us/azure/container-apps/quotas)
distinguishes subscription/region and per-environment limits; environment-specific
usage cannot be proven for an environment that does not yet exist. Check it after
separately approved foundation creation and before app release, not by creating
resources merely to complete M4A.

## Service and architecture assessment

| Area | Existing definition / gap / required M4B result |
| --- | --- |
| Container Apps | M3 defines one Consumption workload-profiles environment and two apps, 0.25 vCPU/0.5 GiB each, min 0/max 1; probes and resource limits compile. Region/capacity/provisioning and effective policies remain untested |
| Internal API | `infra/apps.bicep` has API `external=false`, frontend `external=true`, insecure ingress disabled. This is an app boundary inside an externally reachable environment, not an internal-only environment or end-user authorization |
| VNet/SQL network | Foundation requires an existing infrastructure subnet but creates none. Plan a dedicated delegated ACA subnet at least /27 and separate private-endpoint subnet; actual CIDRs/non-overlap are unresolved. SQL PE, DNS link and public access disabled are missing |
| Registry | ACR Basic, admin/anonymous access disabled; authenticated public endpoint explicitly selected. Managed pull and registry-scoped AcrPull exist in definitions; verify non-ABAC role model, ARM-token authentication and propagation. A private registry would change SKU/network/cost scope |
| Managed identities | Only pull/API runtime identities are defined. Publisher, release, bounded schema migrator and any necessary SQL directory-lookup identity/user provisioning are unresolved. Pull lifecycle None is defined; effective access not tested |
| OIDC | Exact issuer/audience/mandatory subject parameter defined; no federation created, no actual emitted subject verified. Repository/owner IDs are known from GitHub but do not substitute for the actual protected-environment subject. Current missing protections block automatic release |
| SQL persistence | SQLite-only `Store` is constructed at startup; no SQL adapter/driver, T-SQL migrations, SQL resource, Entra users, backup/restore procedure or fail-closed cloud DB mode exists. A local SQLite file is not the selected cloud durability implementation |
| Cloud auth/cart ownership | API routes are anonymous; carts table stores ID only. Missing signature/issuer/audience/expiry/role validation and per-owner cart read/update/delete protection. Local origin checks/opaque IDs do not supply identity |
| HTTPS proxy/browser | Nginx uses Docker DNS at 127.0.0.11 and HTTP `api:API_PORT`, strips Authorization and ignores the Bicep-proposed API_ORIGIN. Missing SPA sign-in, exact cloud origin/CSP, token forwarding, ACA HTTPS/FQDN/TLS/SNI and DNS handling |
| Readiness/migrations | Preserve dependency health and safe errors; add SQL/schema checks, bounded cold-start behavior and separate explicit DDL/seed execution. No startup migration or anonymous/cloud reset |
| Diagnostics/release | Current skeleton exports no cloud logs. Add minimal bounded deployment diagnostics, reviewed digest/config/schema manifest, effective denial tests and compatible rollback before release; M6 dashboards/traces/SLO collection remain later work |

Primary networking references: [ACA network design](https://learn.microsoft.com/en-us/azure/container-apps/custom-virtual-networks?tabs=workload-profiles-env),
[managed pulls](https://learn.microsoft.com/azure/container-apps/managed-identity-image-pull)
and [SQL Private Link](https://learn.microsoft.com/en-us/azure/azure-sql/database/private-endpoint-overview?view=azuresql).
SQL Private Link needs correct public server FQDN plus private DNS resolution;
creating a private endpoint alone does not disable public access. Do not add an
allow-all Azure-services firewall fallback.

## Security coverage and release decision

The run proves existing lint/type/tests/audit/Gitleaks/image/config gates on
Ubuntu amd64. Trivy's finite ARM coverage still covers only the role-assignment
template in this set; targeted compiled-template tests supplement it. CodeQL is
not present in those passing results. Private-repository
[Code Security entitlement](https://docs.github.com/en/code-security/reference/code-scanning/troubleshoot-analysis-errors/private-repository-enablement)
is separate from the branch-protection plan restriction. No entitlement, billing
plan or setting is changed here.

Before cloud exposure, the owner must select either supported CodeQL with an
actual successful run or a reviewed supported SAST alternative plus an explicit
coverage/risk decision. ESLint, dependency audit and image scans are not equivalent
to CodeQL. No exception has been accepted by this assessment. Resolve required
review/check enforcement or explicitly select ADR 0005's owner-operated release
fallback; do not add a nominal unprotected environment and claim approval gates.
Manual fallback must still bind independent review/owner authorization to exact
artifacts and record any unavailable independent reviewer as an unresolved gate.

M4B is proposed, **not authorized by M4A**. Local preparation can be scoped next
without cloud access. Deployment remains NO-GO until actual Azure facts, application/
data/proxy work, security/governance, priced cost approval and teardown gates close.

## M4A validation and stop boundary

Run repository documentation/link/catalogue checks, JSON/evidence and Decimal cost
arithmetic consistency, tracked and untracked whitespace checks, secret scan and
Git/edit-boundary review. CI source/SBOM/report/ZIP hashes were independently
checked. No application/IaC/workflow edit or repeat deployment validation is needed
for this documentation-only assessment. Results are recorded with the evidence.
Do not promote M4 as Cloud verified or report blocked Azure checks as passed.
