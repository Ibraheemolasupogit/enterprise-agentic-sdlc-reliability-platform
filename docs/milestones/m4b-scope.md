# M4B handoff — Cloud-ready preparation, then separately approved deployment

Status: **Local application/authentication/data/proxy preparation authorized by the
owner's subsequent request and implemented; deployment remains NO-GO.** See
[preflight findings](m4a-preflight.md), [cost/control plan](../project/azure-cost-estimate.md),
[persistence ADR](../decisions/0003-persistence.md) and
[delivery ADR](../decisions/0005-delivery-identity.md).
[Local evidence](../evidence/m4b-local-preparation.md) records actual outcomes and
limits. Keep cloud mutations disabled until all approval fields and live gates close.
The broader private-SQL/network/diagnostics IaC completion row below remains pending;
this bounded implementation adds app configuration bindings, not those resources.

## Slice 1 — Local preparation only

| Work | Precise acceptance before any cloud exposure |
| --- | --- |
| Preserve the baseline | All M2 assertions/journeys, synthetic fixtures, GBP integer pricing/discounts and safe local SQLite/Compose path continue to pass; Claims Processing remains independent |
| Application identity | Add explicit cloud-mode configuration, single-tenant JWT signature/JWKS rotation, issuer/audience/time/scope/allowed-role validation; reject missing/expired/wrong-tenant/audience/role/unsigned tokens and spoofed identity headers. Use validated tenant + stable principal ID consistently |
| Cart ownership | Persist owner identity on cloud carts; create/read/set/remove/delete and probe cleanup enforce that owner. Separate users cannot enumerate or mutate each other's carts; opaque IDs alone never authorize access. Define a safe policy for existing anonymous demo rows |
| SQL adapter | Introduce the smallest asynchronous data-access boundary needed for SQLite and Azure SQL, keeping domain validation unchanged. Select/version/license the driver and managed-identity integration deliberately; use explicit cloud identity, encrypted verified TLS and bounded pools/timeouts; no credential-chain or SQLite fallback in cloud mode |
| SQL migrations/data | Add independent T-SQL schema/checksummed migrations and exact fixture contracts, separate DDL/migrator from runtime data rights. Migration/seed/reset remain explicit; cloud reset is unavailable by default. Test rollback compatibility, isolation, integer totals and readiness failure; local doubles do not establish real Azure SQL compatibility |
| Browser/proxy | Add single-tenant SPA sign-in/PKCE, explicit cloud CSP/origins and bearer forwarding; validated fixed ACA HTTPS API origin, appropriate DNS, certificate verification and SNI. Keep Docker's local proxy mode unchanged; prove wrong host/port/TLS failure is visible and fails readiness |
| IaC completion | Add dedicated non-overlapping network/subnets/NSGs, SQL public access disabled, SQL PE/private DNS, Entra-only server/admin/runtime/migrator plan, missing dedicated identities and bounded diagnostics. Keep role/federation bootstrap separate; enforce API internal ingress/no credentials/digest-only images/capacity and cost tags |
| Supply chain/governance | Preserve one CI pipeline; close the SAST gap through supported CodeQL with real results or an approved supported alternative/coverage decision. Do not treat a skipped scan as success. Prepare digest/config/schema provenance and rollback manifest; no publishing/login/OIDC invocation during local work |

Use offline identity/SQL doubles for unit/error cases and an explicitly approved
compatible local/CI SQL engine for database integration where available; verify
engine/platform/license compatibility first. These results are labelled local or
simulated. Actual managed-identity/private SQL/token denials remain live gates.
Pin new dependencies and retain notices. No agents, paid inference, general
orchestrator, payment/order features or M6 telemetry platform is needed.

Local exit requires formatting/lint/types/build, the full M2 tests/browser smoke,
new positive/negative auth/ownership/data/proxy tests, IaC/security mutation checks,
license/secret/dependency/final-image scans and refreshed SBOM/provenance. Keep
the final application pair immutable after scanning; changed source/image/config
invalidates approval. Do not weaken passing tests or cloud security to fit a tier.

## Slice 2 — Candidate deployment scope, approval required

This is the proposed maximum scope for a first **48-hour synthetic rehearsal**,
not permission to run it. No real subscription, tenant, region, IDs, CIDRs, budget,
reviewer or executor has been approved. Do not populate those from another project.

| Boundary | Proposed resource/actions ceiling |
| --- | --- |
| Ownership | One new dedicated project RG in one verified subscription/region, plus only ACA's associated managed infrastructure; exact names/IDs/tags/UTC expiry recorded before apply |
| Networking | One dedicated VNet, separate ACA delegated >=/27 and SQL PE subnets with reviewed NSGs/DNS; no shared-network mutation, broad SQL firewall, NAT/Firewall/App Gateway/DNS Resolver or optional ACA environment Private Endpoint without a revised scope/cost approval |
| Runtime | One Consumption-only ACA environment, two apps each 0.25 vCPU/0.5 GiB, min 0/max 1; external HTTPS frontend and internal HTTPS API; no public API ingress |
| Registry | One Basic non-ABAC registry, admin/anonymous pull disabled, two approved image repositories/digests; scoped managed pull. No ACR Tasks/replication or automatic Premium upgrade |
| Data | One Azure SQL logical server and one Basic B DB, <=2 GB, one SQL private endpoint/zone/link, Entra-only authentication/public network disabled; runtime data rights and separate bounded DDL rights. Verify tier/retention/performance before creation; no production/Claims data |
| Identities | Dedicated pull, API runtime, migrator, publisher and release identities (five maximum initially), two SPA/API app registrations and at most two exact federation bindings if the protected OIDC path is approved. Any SQL directory-lookup identity/Graph grant is separately justified/approved; never grant blanket directory/subscription authority by default |
| Migration/diagnostics | One manually triggered migrator job, single execution/parallelism, ten-minute bound and no unapproved retry; one bounded diagnostics workspace, roughly 1 GB/month ingestion model, minimum supported retention/low daily cap. No dashboard/probe/agent fleet |
| Financial controls | Owner-approved repriced 48-hour ceiling (proposed £10 pre-tax, not approved), expiry and teardown inventory; budgets cover project and managed RG charges. Retaining the environment or increasing tiers/duration needs a new decision |

Before first apply, verify the exact subscription state, effective RBAC/denies/
policy/locks, providers, quotas/capacity, names/CIDRs and private-SQL prerequisites
through an authorized valid session. A missing session must not trigger a sign-in
or refresh without new explicit owner direction. Validate actual parameterized
ARM/what-if after separately authorizing the necessary Azure access; reject
unexpected/destructive/shared-resource changes. Provider registration, app
registrations, Graph permissions, roles/federation and budgets are mutations and
must be explicitly included in the approved bootstrap scope.

## Release route and approvals

Choose one route before adding an active publisher/release executor:

1. **Protected OIDC route:** verify the chosen GitHub plan can enforce main checks,
   independent review and required-reviewer environments; an authorized human
   configures them. Inspect actual emitted immutable-ID subject only in an
   independently authorized protected claim-discovery run, then bind exact
   issuer/audience/subject with separate publisher/release grants. Test wrong
   repo/environment/issuer/audience and unauthorized mutation denial. No token is
   retained; release cannot alter its own federation/RBAC.
2. **Owner-operated fallback:** automatic publishing/deployment remains disabled.
   An authorized human performs the same reviewed, manifest-bound bounded release
   with existing authorized Azure access and records independent review/approval
   and actor. Do not claim protected OIDC execution or independent review if those
   capabilities are absent. An unresolved independent-review requirement remains
   a gate, not permission for the coding assistant to self-approve.

An upgrade/public-visibility change, paid Code Security purchase or GitHub setting
change is never implied by this handoff. Current environments are empty and
protection/ruleset APIs return a plan restriction. CodeQL remains unexecuted.

The approval record must bind: reviewed committed SHA/CI run, source/SBOM/scan
hashes, two **registry manifest** digests, config/schema/migration compatibility,
exact Azure/Entra/RBAC mutations and scopes, operator/reviewer, expiry/max attempts,
region/SKUs/cost ceiling, diagnostics, rollback and data/teardown decisions. Scope,
digest or precondition changes stop execution and require a new review.

Create foundation/identity/network/data resources only after that approval. Verify
effective permissions, registry propagation, internal API/private SQL routing and
runtime-vs-DDL separation before serving user writes. Do not temporarily expose
anonymous carts or public SQL to get a green deployment.

## Cloud exit and failure handling

Require HTTPS frontend journeys with sign-in/search/cart/pricing, negative identity
and cross-owner tests, outside-environment API denial, private-only SQL and failed
public access, successful managed pulls and evidence that runtime cannot DDL/RBAC.
Prove data survives app revision replacement, explicit migrations remain compatible,
and dependency readiness fails under a bounded approved fault then recovers with
fresh independent checks. Restore a compatible known-good image/config pair only
through the approved actor; stop/escalate incompatible schema or failed smoke.
No down migration, data reset, broad role grant or credential fallback is a repair.

Record actual region/IDs/digests/schema, timestamps, results, actor, costs and
teardown outcome. A successful first deployment does not prove 28-day SLOs,
RPO/RTO, M5 maintenance inference or M7 autonomous SRE behavior. Stop after the
separately authorized M4B scope; these activities are not executed in M4A.
