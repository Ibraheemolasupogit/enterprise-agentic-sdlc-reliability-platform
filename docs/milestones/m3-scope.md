# M3 — Secure delivery

Authority: [master brief](../project/master-brief.md), roadmap M3 and the owner's
M3 implementation request. Status/results: [M3 evidence](../evidence/m3-secure-delivery.md).
The working independent MIT Morrow Supply/M2 tests remain the baseline. No agents,
Azure authentication/provisioning/deployment, credentials, paid-service execution,
commits or pushes are authorized. Claims Processing stays separate.

| Criterion | Delivered boundary and evidence |
| --- | --- |
| M3-A1 CI | One pinned, read-only GitHub Actions workflow installs locked dependencies, checks license drift/format/lint/types/tests/builds/audit/browser journeys; final required gate fails on non-success |
| M3-A2 DevSecOps | Full dependency audit, redacted history/tree secret scanning, conditional trusted-main CodeQL, final-image/config scans; finite coverage and unsupported CodeQL stated explicitly |
| M3-A3 images/smoke | Pinned frontend/API builds, isolated local Compose smoke using unchanged M2 browser tests, persistence and exposure restrictions; own temporary volume cleaned |
| M3-A4 IaC | Four minimal Bicep templates for candidate foundation/apps/pull grant/exact federation; lint/build locally, explicit internal API, TLS and managed registry pull; no deployment |
| M3-A5 identities/gates | Configuration guidance for exact OIDC subjects, split publisher/release/bootstrap/runtime/migrator identities, protected environments/independent approvals and candidate scoped role; no cloud identities/settings created |
| M3-A6 supply chain/recovery | SBOMs, source/tool/lock/image/report provenance, empty exception register, fail-closed gates, compatible image/config/schema rollback design and actual limits |
| M3-A7 negative tests | Workflow/IaC privilege/trust mutations, executed required-gate failure matrix, restrictive candidate role and actual synthetic-secret canary rejection |
| M3-A8 closure | Preserve application source/tests, execute available local checks, fix actionable findings, record hosted/cloud gaps, costs and precise M4 prerequisites |

Implementation/commands are defined once in [delivery guidance](../delivery.md),
with [IaC boundary](../../infra/README.md). Local passing checks do not establish
GitHub-hosted success or effective Azure protections. M3 ends with reviewed local
definitions/checks; no publication or release is silently enabled.

## M4 prerequisites — not implemented here

1. Owner approves an explicit cloud scope, region/subnet/SKUs/quotas, priced cost
   estimate, ceiling, tags/ownership and verified teardown. No budget is approved
   by compiling the Consumption/Basic candidate settings.
2. Obtain a genuine hosted CI run from the reviewed committed SHA; verify required
   checks, private-repository Actions/security entitlement and branch/protected
   environment features. Resolve CodeQL support/fallback and reviewer availability.
3. Verify actual immutable-ID OIDC subject/issuer/audience/environment; establish
   separate publisher/release identities/scoped grants through human bootstrap;
   run actual positive/negative federation and permission tests. No client secret.
4. Implement Azure SQL adapter/migrations, private endpoint/DNS/VNet and public
   access disabled; separate runtime data and DDL identities. Prove persistence,
   migration/rollback compatibility and restore procedure; local SQLite is not
   the cloud durability plan.
5. Implement/test cloud token issuer/audience/expiry/role and cart ownership;
   frontend sign-in/token forwarding and ACA HTTPS upstream/DNS. The current
   local Docker proxy strips Authorization and is not an Azure-ready image.
6. Build clean reviewed cloud-ready code once; scan, bind/sign provenance and
   publish immutable registry digests only with separate authorization. Verify
   image-pull grant propagation, deployment diagnostics, health, release/rollback
   approval and fresh user-journey checks. Do not deploy the M2 images via skeletons.

M4 requires new owner direction; these prerequisites are a handoff, not permission
to create accounts/resources, pay for services or begin implementation.
