# M4C-C4 — Infrastructure definitions and static validation

Date: 2026-11-13 UTC. Base HEAD: `e537efff74c6026e75cdf02a633d1e5e5c46e278`;
initial working tree clean. Authority: owner's **C4 local definitions/static
validation-only** request. Status: **C4-A1–A4 met within that static boundary**:
implemented definitions with locally tested static checks, not a deployed or
integrated infrastructure capability. C1/C3 application behavior/evidence are
preserved. M4A deployment remains **NO-GO**. C2/C5/C6/C7/C8 remain outside authority.

The owner supplies hosted run **43308294860** at `e537eff`: policy, application,
containers and required passed; CodeQL skipped. This task did not re-read hosted
artifacts/settings or execute a hosted run for C4. No Azure authentication, ARM
validate/what-if/request, principal/credential creation, provisioning/deployment,
real-provider authentication, paid service, GitHub setting, commit or push occurred.
No other repository was accessed. [Machine-readable evidence](m4c-c4-infrastructure.json)
binds source/output/report hashes, actual commands/times/exits, cases and limits.

## Gaps inspected before modification

The four baseline templates defined ACR Basic, two identities, an externally
accessible Consumption environment consuming an external subnet ID, two apps,
AcrPull and exact-subject federation. They lacked owned private network/SQL PE/DNS,
SQL server/database/data-protection contracts, remaining identities, migrator and
minimal diagnostics. The policy loader expected exactly four templates; compilation
could discover new files without adding resource-specific assertions. Existing
application OIDC/SQL-mode, digest/TLS, internal API, max-one, pull lifecycle and
workflow controls were retained and strengthened, not removed to accommodate C4.

The master brief, AGENTS, active scope, architecture/threat model, persistence/
delivery/identity ADRs, all Bicep, delivery policies/tests and cost plan were read.
Public Microsoft schemas/primary documentation were consulted, referenced in the
[infrastructure contract](../../infra/README.md); definitions are original, with
no upstream application/template assets imported or package/tool upgrades.

## Defined security invariants and acceptance

| Criterion | Implemented/static-checked evidence | Live proof still open |
| --- | --- | --- |
| C4-A1 network/private SQL | Required aligned RFC1918 VNet; dedicated ACA /27-or-larger delegated subnet, separate /28-or-larger endpoint subnet, two NSGs; DNS zone/link + SQL PE/zone group; SQL public access disabled, Entra-only, TLS 1.2 minimum, explicit Proxy policy/1433; Basic 5-DTU/2-GB, TDE, seven-day Local backups | Address/region/quota approval, PE approval, DNS/system routes/NSG effectiveness, verified SQL TLS/driver/MI, restore and actual performance; no geographic recovery/RPO/RTO claim |
| C4-A2 identity/application boundaries | Exactly five identities; distinct pull/runtime/migrator/publisher/release; pull token endpoint None, runtime/migrator Main-only; registry-only pull/push grants; unapplied app/environment/identity/operations and contained-SQL permission manifests; no runtime DDL/product write/db_owner/Graph role; frontend required client CIDR/TLS, internal API/JWT/SQL, dependency probes; manual migrator one replica/completion/600s/no retry | Effective Azure/SQL grants and denials, real principal/SID/bootstrap, schema ownership, managed-identity renewal, actual federation/ingress/pull behavior; release write remains coarse and needs field/diff controls |
| C4-A3 minimal diagnostics | Initial workspace/tables without export; separate DCR/workspace-link definition; Analytics/30-day retention, shared-key auth off, workspace-only query model, 0.1-GB/day safeguard; export OFF by default and rejected by C4 parameter preflight; candidate console/system-only projection to fixed DNS/TLS/SQL/SCHEMA/REDACTED classes plus reviewed platform metadata | Python model is not Kusto. Actual table/schema/KQL/transform/order/ingestion/retention/RBAC and unrelated diagnostic settings need C7 proof before export; source stdout/live streams/Monitor transport can still contain raw data |
| C4-A4 static/negative validation | All eight Bicep format/lint/build; exact resource and source/output hash inventories; invalid CIDR/trust/digest/expiry/secret inputs rejected; compiled/manifest/CI harmful mutations; all previous policy/application/capture/proxy/security regressions preserved | Not ARM/Azure Policy authorization, private connectivity, real SQL, provider integration, SAST, protected review or release evidence |

Secret slots and environment secret references are currently empty. A future
versioned Key Vault reference shape is documented but requires a new bounded
review; no vault, password, secret value, copied bearer or default credential chain
is created. SQL users/grants are a separate unapplied manifest. The migrator's
CREATE TABLE/ALTER/REFERENCES rights are time-bound within a dedicated application-
only dbo schema; ALTER dbo remains broad there. No unrelated database/schema,
permanent DDL, db_owner or SQL server directory/Graph identity is assumed.
For first creation, proposed temporary schema SELECT/INSERT covers tables before
named object grants can exist. The manifest explicitly requires replacing those
schema data grants with the listed object grants after creation. A mutation that
makes bootstrap data privileges permanent is rejected. Actual sequence/rights
remain a C2/C7 integration gate; no SQL command or grant was executed.

The NSG permits intra-subnet communication, load-balancer probes, Azure DNS,
private Proxy SQL and Internet HTTPS for retained public ACR/IdP/platform services.
It is **not an FQDN egress firewall/private registry**. External ACA public traffic
bypasses subnet NSGs; frontend app-level client restriction is separately defined.
Actual public Basic ACR/NSG compatibility must be checked later; if private ACR is
required, stop for Premium/PE/network repricing. No paid resolver/NAT/Firewall,
environment PE, ACR Premium, Key Vault, AMPLS, dashboard, alert or collector was added.

Diagnostics are phased prerequisites only, with no deploy executor: network,
foundation workspace/tables with no export, DCR/link, then separately verified
export. Never replay initial workspace bootstrap over a linked live workspace or
enable export while changing its DCR. Complete ARM updates are not property-only
patches. Live collection must inventory other settings/streams and test canaries.
The fixed classes are hints, not verified root causes or execution authority.

## Executed local checks

Host: macOS arm64, Node **24.22.2**, npm **11.19.1**, Python **3.12.8**;
Bicep **0.48.1**, actionlint **1.7.12**, Trivy **0.72.0**, Gitleaks **8.30.1**.
Containers: local Docker Engine **28.3.3**, Linux arm64. Existing tools/packages
were reused; no dependency/base-image/security threshold upgrade or exception.
Ignored raw logs/reports are under `artifacts/m4c-c4/`, with the existing delivery
outputs in `artifacts/m3/` and `artifacts/m4b/`. The JSON records exact UTC windows.

| Check | Result |
| --- | --- |
| `python3 scripts/delivery/validate_infra.py` | **8/8** format/lint/build, no warnings; exact source/KQL/config/output freshness bindings; no Azure call |
| `python3 scripts/delivery/policy.py` | Pass: retained workflow/app/registry/federation plus all C4 compiled resources and identity/secret manifests |
| `python3 -m unittest discover -s tests/delivery -v` | **22 passed**, zero skipped: original 13 plus nine C4 tests with adversarial subcases; failures must come from the intended contract |
| Application format/lint/typecheck/licences/build | Pass; application/lock/inventory/notices source unchanged |
| `npm test` | **195 passed in 13 files**, zero failed/skipped; C1's 33 real SQLite cases and eight Simulated SQL recording cases preserved |
| `npm run test:auth-mutations` | All **4** harmful mutations rejected by intended behavioral assertions |
| Native / OIDC / container Chromium | **3 + 7 + 3 passed**; no retries/skips; providers/virtual HTTPS routing remain Simulated |
| Capture guard before/after OIDC | Pass; unchanged capture-off profile/canaries, no real-provider traces |
| Container hardening/persistence and HTTPS proxy | Pass; owned local fixture/project/volume cleanup, no cloud resources |
| `npm audit --audit-level=high --json` | Exit 0; **0 HIGH, 0 CRITICAL; 10 existing MODERATE** findings remain |
| actionlint / configuration scan | Pass; **0 HIGH/CRITICAL**; Trivy evaluated network, registry-access and SQL ARM outputs plus API/frontend Dockerfiles. This is finite rule coverage, not every resource/property |
| Image scans / SBOMs / provenance | Both rebuilt images exit 0 with **0 HIGH/CRITICAL**; both SBOMs generated and image IDs match unsigned, dirty-tree, release-ineligible provenance |
| Repository/JSON/whitespace/secrets | Repository/link/hygiene, tracked and every untracked text whitespace, redacted Git history/tree checks pass; final bindings in JSON |

Published non-live keys/certificates remain solely the existing local fixtures;
none was generated, registered or used for a real account. The unchanged frontend
libxslt 1.1.43-r4 repair is retained; no new image finding was waived. Image/config
severity filters do not establish absence of lower findings or substitute for SAST.

Development checks exposed a local .NET cache restriction, a Bicep symbol/function
collision, formatting after an edit and Bicep's generated literal KQL variables.
Authorized local cache access, explicit `az.environment()`, formatting and narrow
literal-trim expansion corrected these. Final compilation/policy gates pass without
warning/rule suppression. Early rerun logs reused filenames; JSON identifies
superseded attempts instead of claiming overwritten raw failure logs are retained.
After a server restart, saved completed application results were checked and reused.

## Costs, remaining gates and stop boundary

No Azure/provider service consumption was initiated. The updated
[cost assumptions](../project/azure-cost-estimate.md#c4-definition-assumptions--2026-11-13-no-spend-or-quote)
retain the historical unapproved model and explicitly do not reprice it. SQL/PE/
DNS/registry, ACA/managed IP/LB, data/backup, manual migration and diagnostic
volume/transform/retention costs need a current approved quote. The log safeguard
can overshoot or stop visibility. Max replicas/expiry tags are not a hard budget
or automatic teardown. No price, SKU/region availability or spend approval is inferred.

Remaining gates include C2 real engine/TDS/grants, C5 actual SAST/independent
governance, C6 real provider/claim semantics, and separately authorized C7 session/
permissions/quota/region/ARM/private-network/SQL/MI/ingestion/cost/teardown proof.
No ARM validate/what-if was invoked. No clean hosted/x86_64 C4 run or signed
release candidate is claimed. Static tests do not establish live private
connectivity, Azure SQL access, managed-identity enforcement or universal redaction.
C4 stops here; deployment remains **NO-GO**.

## Exact files changed

Only the following C4 definition, static-check and documentation/evidence files
changed. All 86 protected application/workflow/security/C1/C3 evidence files in the
initial snapshot are byte-identical. The owner supplied a clean baseline, so no
pre-existing uncommitted work was overwritten. No commit or push was performed.

- `AGENTS.md`
- `README.md`
- `docs/architecture.md`
- `docs/capability-status.md`
- `docs/decisions/0003-persistence.md`
- `docs/decisions/0005-delivery-identity.md`
- `docs/delivery.md`
- `docs/evidence/m4c-c4-infrastructure.json`
- `docs/evidence/m4c-c4-infrastructure.md`
- `docs/milestones/m4c-scope.md`
- `docs/project/azure-cost-estimate.md`
- `docs/roadmap.md`
- `docs/threat-model.md`
- `infra/README.md`
- `infra/apps.bicep`
- `infra/diagnostics-console.kql`
- `infra/diagnostics-system.kql`
- `infra/diagnostics.bicep`
- `infra/foundation.bicep`
- `infra/identity-contract.json`
- `infra/migrator.bicep`
- `infra/network.bicep`
- `infra/registry-access.bicep`
- `infra/secret-reference-contract.json`
- `infra/sql.bicep`
- `scripts/delivery/diagnostics.py`
- `scripts/delivery/policy.py`
- `scripts/delivery/scan_config.py`
- `scripts/delivery/validate_infra.py`
- `scripts/delivery/validate_parameters.py`
- `tests/delivery/test_infra_c4.py`
