# ADR 0005 — GitHub Actions, Azure OIDC and protected releases

Date: 2026-10-30. Status: M3 workflow/IaC implemented; hosted validation confirmed in M4A.
No Azure identities, protected environments or release created by this project work.
Requirements: R04–R06, R10, R17. Owner: repository owner.

## Decision

Primary delivery is GitHub Actions, immutable container images in Azure Container
Registry, Azure Container Apps and Bicep. Preserve suitable Bicep patterns only
after rights review; do not copy the lab's environment identifiers or disabled
deployment workflow. One trusted pipeline; no duplicate Jenkins/Azure DevOps path.

Build/test untrusted PRs with read-only contents and no Azure/inference/write
identity; do not use a privileged `pull_request_target` job to run PR code. Pin
actions/base images, check lockfiles, scan secrets/dependencies/code/images, produce
SBOM and artifact provenance, then review the exact trusted SHA/digests. A protected
release environment and separate approved deploy job gates OIDC issuance.

Use short-lived GitHub-to-Entra OIDC rather than a client secret. Trust issuer
`https://token.actions.githubusercontent.com` and Azure public-cloud audience
`api://AzureADTokenExchange`; exact subject must be discovered from the actual
repository/environment and matched narrowly. **Do not hardcode the older
name-only `repo:OWNER/REPO:environment:...` format**. Current [GitHub OIDC guidance](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure)
describes immutable owner/repository-ID subjects for newly created/renamed repos.
Verify emitted claims without recording the bearer token. Wrong repository,
environment, audience or issuer must be rejected. No wildcard repository trust.
Grant `id-token: write` only to the approved deploy job; it permits requesting a
token, not Azure authorization by itself.

## Identity boundaries

| Identity | Intended scope | Explicit exclusions |
| --- | --- | --- |
| PR validation | Read repository, execute sandboxed tests | No OIDC, publish, repository write or inference secret |
| Trusted image publisher | Push selected repository images to ACR | No Azure app/config/role administration |
| Bicep bootstrap executor | Separate human-authorized dedicated-RG provisioning; Contributor at that RG only as initial upper bound | No subscription Owner or role-assignment writes; privileged assignments performed separately by owner |
| Release executor | Scoped update/read for the two named apps and required deployment operations | No RBAC/federation creation, database DDL, arbitrary resource deletion or general subscription access |
| API runtime managed identity | Required SQL data operations only | No DDL, deployment or repository access |
| Schema migrator | Scoped versioned DDL during approved release | No permanent runtime identity sharing |
| Image pull / telemetry / investigator | Separate minimal pull, emit or read scopes | No inferred cross-role authority |

Enumerate actual Azure actions in M3 and derive/test the release role; a table is
not proof of enforcement. RG Contributor bootstrap remains powerful within that
dedicated group; time-bound it and do not give it to agents. Roles and SQL users
are provisioned separately by an authorized human, not by granting the pipeline
Owner. Runtime tokens are not logged or placed in images/config files.

## Gates and consequences

Require explicit deployment scope, subscription/region, SKU/network/storage cost
estimate, owner-set spending/usage ceiling, resource tags and teardown/verification
plan before M4. Budget alerts do not enforce a hard cap. Validate Bicep/what-if,
diff and destructive changes before apply. Confirm branch/environment protection
is available on the chosen GitHub plan; if not, keep automatic deploy disabled
and use the owner-operated gate, not an unprotected approximation.

Deploy exact approved image digests and schema version, then run dependency-aware
smoke journeys. Rollback only to recorded compatible digests/config; see
[persistence ADR](0003-persistence.md). Rejected release/federation, unavailable
credentials, malicious artifact, failed smoke or exceeded cost/scope stops the
pipeline and records escalation. No hidden long-lived secret fallback.

Private SQL connectivity/Entra API authorization are in the
[architecture](../architecture.md). Exact custom role actions, region/SKUs,
protection entitlement, actual OIDC subject and network cost are deferred to M3
with owner and are M4 entry blockers, not assumptions that the lab proves.

## M3 implementation and remaining authorization proof

[Delivery guidance](../delivery.md) and [M3 evidence](../evidence/m3-secure-delivery.md)
record the read-only validation workflow, pinned tools/actions, fail-closed gates,
source/image/SBOM evidence and separate Bicep boundaries. No publish/deploy/OIDC job
exists. CodeQL is explicit opt-in on trusted main after entitlement review. The
candidate updater role enumerates app operations at the two app scopes; environment
read/join and identity assignment scopes need separate narrow grants and live tests.
RBAC write cannot constrain ingress/image fields: reviewed diffs and appropriate
Azure Policy are M4 prerequisites. Actual emitted subject, protected reviewers,
federation/RBAC denial tests, SQL/private networking, cloud-ready images, cost and
rollback/teardown remain unverified M4 entry gates. No token or credential was
requested or created during M3. Current Bicep/compiler checks do not satisfy ARM
what-if/authorization/policy validation, which would need cloud authentication.

## M4A preflight addendum

[Preflight](../milestones/m4a-preflight.md) independently confirms hosted run
41149829560 at the current committed SHA; CodeQL was skipped, not executed.
Existing environments are empty and branch/ruleset APIs return a private-plan
restriction. Automatic release remains blocked pending enforceable protections;
ADR's owner-operated fallback remains a proposal requiring reviewed scope/approval,
not an enabled deploy path. Azure session/subscription/region/RBAC/quotas and actual
OIDC subject are unverified; no sign-in or refresh was attempted. The
[M4B handoff](../milestones/m4b-scope.md) and
[cost/control proposal](../project/azure-cost-estimate.md) authorize no mutation.

## M4B local-only update

The owner subsequently authorized application/auth/SQL/HTTPS preparation and bounded
workflow fixes. [Local evidence](../evidence/m4b-local-preparation.md) and
[configuration](../delivery.md#m4b-local-configuration) record the Node 24 artifact
action pin and TLS check added to the existing containers job. M4A's hosted success
does not validate those edits. CodeQL remains conditional, skipped historically
and unexecuted. No GitHub settings/entitlements/protections or Azure credentials,
federation, resource or release were created. The deployment NO-GO remains.

## C4 identity definition boundary

C4 defines exactly five distinct user-assigned identities: pull, API runtime,
migrator, publisher and release. Pull endpoints are hidden from application code;
runtime/migrator endpoints are Main-only in their respective workloads. Registry
bootstrap defines AcrPull/AcrPush at the one registry. The
[grant manifest](../../infra/identity-contract.json) retains the unapplied custom
app updater, separate environment join/identity attach scopes and an existing
operations group's table-specific read rights. No SQL data/admin grant, broad
Contributor/Owner, Graph grant, live stream/exec/listSecrets or migration start
permission is inferred for release/operations. No identity is created in Azure.

These manifests are static design evidence. Azure action support/effective denials,
SQL contained users, actual federation subject/issuer/audience, governance and a
scoped human migration-start route still need separately authorized verification.
The app write action is coarse: actual field constraints require reviewed diffs/
Azure Policy and live tests. C4 adds no release workflow or Azure token issuance.
See [C4 evidence](../evidence/m4c-c4-infrastructure.md). Deployment remains NO-GO.
