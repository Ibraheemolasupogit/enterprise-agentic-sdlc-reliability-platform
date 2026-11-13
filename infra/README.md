# C4 Azure infrastructure contracts — local validation only

Status: **Implemented definitions; locally checked static contracts. Deployment NO-GO.**
The owner authorized C4 only at `e537eff`. Hosted run 43308294860 passed the four
mandatory jobs with CodeQL skipped, as supplied by the owner; it was not re-read
here. That baseline does not validate this uncommitted C4 diff or live Azure.
[C4 evidence](../docs/evidence/m4c-c4-infrastructure.md) records actual local checks.
All definitions are original; public Microsoft schemas/documentation were consulted,
with no upstream application/template code or credentials imported.

| File | Defined boundary |
| --- | --- |
| [network.bicep](network.bicep) | One required RFC1918 VNet; dedicated delegated ACA subnet and separate endpoint subnet, two NSGs, SQL private DNS zone/link; no VNet peering, NAT, firewall, resolver appliance or UDR |
| [foundation.bicep](foundation.bicep) | Existing network binding, authenticated public ACR Basic, five dedicated identities, Consumption-only environment/mTLS, initial workspace and two tables; no diagnostic export |
| [sql.bicep](sql.bicep) | Entra-group-admin/Entra-only SQL, public access disabled, TLS 1.2 minimum, explicit Proxy connection policy, Basic 5-DTU/2-GB database, TDE, seven-day local backups, private endpoint and DNS association |
| [registry-access.bicep](registry-access.bicep) | Separate privileged bootstrap: registry-scoped AcrPull for pull identity and AcrPush for publisher; no pipeline/RG/SQL authority |
| [apps.bicep](apps.bicep) | Internal HTTPS API, external HTTPS frontend with one required client CIDR, digest-only images, separate runtime/pull identities, dependency readiness, 0–1 replicas, release/config/schema revision labels |
| [migrator.bicep](migrator.bicep) | Definition of manual migrate OR seed job, one completion/replica, 600 seconds, zero retries; separate migrator identity, no ingress or schedule and no job execution |
| [diagnostics.bicep](diagnostics.bicep) | Workspace transform/link and conditional console/system export; export defaults OFF and C4 preflight rejects enabling it |
| [federation.bicep](federation.bicep) | Preserved separate administrator boundary: exact verified GitHub issuer/audience/subject on an existing publisher/release identity; no token requested |
| [identity-contract.json](identity-contract.json) / [release-role.example.json](release-role.example.json) | Unapplied app/environment/identity/operations grants and SQL permission manifest; no new SQL user, Graph permission or role provisioning |
| [secret-reference-contract.json](secret-reference-contract.json) | Current secret slots/references are empty. Future versioned Key Vault reference shape requires a new decision; inline credentials, connection strings, copied tokens and secret outputs are forbidden |

## Parameters and local checks

No real parameter file, address allocation, tenant/region selection, spend approval
or deployment entry point is supplied. Bicep required parameters/bounds are combined
with [offline parameter validation](../scripts/delivery/validate_parameters.py).
The validator accepts a flat JSON object containing the union of the eight compiled
templates' parameters plus `reservedNetworks` and `reservedNetworksReviewed`.
Only `diagnosticExportEnabled` defaults, to false. The unit fixture is synthetic;
it must never be used as an Azure parameter file or registered identity.

Preflight checks aligned/non-overlapping RFC1918 ranges and surrounding/platform
ranges; ACA subnet /27 or larger, endpoint subnet /28 or larger; bounded public
frontend client /24–/32; exact digest/SHA syntax; HTTPS/page/issuer/JWKS origin
bindings and explicit scopes; Azure-provided resolver; admin group UUID; federation
identity/subject; UTC expiry within 48 hours and no secret/unknown fields. These
checks do not inventory existing networks, reserve names or prove a region/SKU.
A future real handoff must also bind reviewed subscription/tenant/scope/IDs,
independent approvals, grants and cost; do not infer those from format checks.

Using the already pinned Bicep 0.48.1/tools and Node 24.22.2/npm 11.19.1:

```sh
python3 scripts/delivery/validate_infra.py
python3 scripts/delivery/policy.py
python3 -m unittest discover -s tests/delivery -v
python3 scripts/delivery/scan_config.py
python3 scripts/check_repository.py
git diff --check
```

Compilation checks formatting/lint/warnings for **all eight** templates. The loader
requires exact source/output inventories and hashes, rejecting stale, missing or
extra outputs before policy/scanning. Tests mutate network/SQL/DNS/identity/cost/
readiness/diagnostic contracts, invalid parameter sets and mandatory CI steps.
The existing read-only workflow discovers these checks without a new job or
permission change. Trivy's finite ARM coverage is supplemented by explicit policy;
neither compilation nor a clean scan is ARM validation/what-if or enforcement.

## Network and database design limits

The ACA subnet delegates only to `Microsoft.App/environments`. Endpoint NSG policies
are enabled; only ACA-to-endpoint TCP 1433 is allowed. SQL's explicit **Proxy** mode
is part of that port contract; Default/Redirect needs a new port/latency review.
Applications use the ordinary `<server>.database.windows.net` TLS hostname, not
the private IP or private-link alias. DNS registration is off; one zone links to
the dedicated VNet. Actual PE approval, DNS resolution, verified TLS, routes,
platform health and SQL/managed-identity access remain untested.
[SQL Private Link](https://learn.microsoft.com/en-us/azure/azure-sql/database/private-endpoint-overview?view=azuresql)
and [connection policy](https://learn.microsoft.com/en-us/azure/azure-sql/database/connectivity-architecture?view=azuresql)
explain these separate requirements.

The ACA NSG permits intra-subnet traffic, load-balancer probes 30000–32767, Azure
DNS TCP/UDP 53, private SQL 1433 and outbound Internet HTTPS 443. Remaining traffic
is denied. HTTPS is needed for the retained public ACR/IdP/platform dependencies:
MicrosoftContainerRegistry, AzureFrontDoor.FirstParty, AzureActiveDirectory,
AzureMonitor, AzureContainerRegistry and regional Storage. **This is a port bound,
not an FQDN egress firewall or a private registry.** System routes/Azure DNS are
selected; no paid network appliance is added. The public environment's incoming
frontend traffic bypasses subnet NSGs, so the template uses app-level client CIDR
restrictions as well as TLS. Internal API ingress still needs JWT authorization.
[ACA NSG guidance](https://learn.microsoft.com/en-us/azure/container-apps/firewall-integration)
also warns about ACR/NSG private-endpoint configurations. Compatibility of this
public Basic ACR model must be checked in C7; if policy/platform requires private
ACR, stop for Premium/PE/network repricing rather than widening rules or changing
SKU automatically. [Ingress IP rules](https://learn.microsoft.com/en-us/azure/container-apps/ip-restrictions)
are a separate app boundary and are not proven effective here.

Basic SQL is a synthetic-workload cost candidate, not performance/HA readiness.
Service-managed TDE and seven-day Local backup storage are defined. No LTR,
geo-recovery, CMK, export, restore exercise or RPO/RTO result is claimed. No SQL
firewall allow-Azure rule, password, server directory identity or Graph grant is
created. Database users/object grants are a separate reviewed bootstrap. Migrator
ALTER dbo is broad inside the dedicated application-only schema and must be
time-bound/revoked; runtime has no DDL/product-write/db_owner grant. The proposed
first-creation window also grants schema SELECT/INSERT so the unmodified migrator
can read newly created tables before object grants exist; those schema data grants
must then be replaced by the listed history/product object grants. This is a
bootstrap contract, not an executed or validated grant sequence.
[SQL permission scope](https://learn.microsoft.com/en-us/sql/relational-databases/security/authentication-access/getting-started-with-database-engine-permissions?view=sql-server-ver17)
distinguishes schema data access from CREATE/ALTER rights. Real engine,
permission denials, concurrency, recovery and MI renewal remain C2/C7 gates.

## Diagnostic safety and phased prerequisite contract

These are dependency contracts for a later separately authorized executor, **not
commands or approval to run them**: network precedes foundation; foundation creates
the workspace and tables with no export; SQL follows network; diagnostics creates
the DCR against those existing tables and then fully updates the workspace to
link it; apps/migrator follow approved SQL bootstrap/identity and image gates.
Registry/federation/grants stay separate privileged operations. Do not replay the
initial foundation workspace definition over a live linked workspace or enable
export while changing its DCR: incremental ARM is not a property-only patch.
The future executor must enforce order, stop export before changing transforms,
verify the complete workspace definition and detect unrelated diagnostic settings.
No orchestration/execution workflow is added in C4.

The workspace/tables use Analytics, 30-day retention, workspace-only RBAC query
access, disabled shared-key auth and a 0.1-GB/day safeguard. Its Azure Monitor
HTTPS ingestion/query endpoints remain public and identity controlled; no AMPLS
private-monitoring claim is made. No storage/event-hub/partner/HTTP/query/audit
export, dashboard, alert or collector is added. Diagnostic export defaults OFF
until live supported-table/schema/KQL/canary tests and explicit authorization.

Candidate [console](diagnostics-console.kql) and [system](diagnostics-system.kql)
queries project only timestamp, reviewed platform app/revision/image/resource
metadata and a fixed DNS/TLS/SQL/SCHEMA/REDACTED class. Raw Log, headers, bodies,
queries, owner/subject and extra fields are discarded. Names/images/revisions must
be produced from validated dedicated-deployment parameters. The local
[reference model](../scripts/delivery/diagnostics.py) binds that exact grammar and
tests payload canaries; it does **not** execute KQL or prove universal redaction.
Classification is a diagnostic hint, not a verified cause or execution authority.
[Workspace transformations](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/tutorial-workspace-transformations-api)
run after delivery to Azure Monitor, before table ingestion; raw data can still
exist in source stdout/live streams/provider transport. Existing application
no-sensitive-logging/capture controls and restricted stream permissions remain
necessary. Real ingestion/transformation/retention/role behavior is unverified.
The [daily cap](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/daily-cap)
can overshoot and stop visibility; it is not a hard budget or availability control.

Deployment remains **NO-GO** pending C2, C5, C6 and separately authorized C7 facts,
reviewed live parameters/permissions/quotas/cost/teardown and independent release
approval. No Azure authentication, ARM call, resource, credential, real provider,
paid service, GitHub settings change, commit or push occurs in C4.
