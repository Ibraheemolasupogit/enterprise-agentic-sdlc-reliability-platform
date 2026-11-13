# Secure delivery — M3

Authority: [master brief](project/master-brief.md), [ADR 0005](decisions/0005-delivery-identity.md).
[M3 evidence](evidence/m3-secure-delivery.md) distinguishes actual local execution
from unexecuted GitHub/Azure settings. The M2 application and tests are preserved;
only container packaging changes address scanner findings. No release is enabled.
Subsequent [M4A preflight](milestones/m4a-preflight.md) confirms hosted run
41149829560 passed application/policy/containers/required, with CodeQL skipped.
It found no GitHub environments and plan-restricted branch/ruleset protection
reads; Azure live checks remain blocked. M3 evidence remains a historical snapshot.

The [M4C assessment](evidence/m4c-readiness-assessment.md) confirms hosted run
42794873352 at `40a6353` passed policy/application/containers/required, including
the M4B repairs; CodeQL skipped. Current main reports protection disabled and
ruleset/protection observations are dated, not re-read here. C3 local implementation
adds mandatory simulated OIDC browser/capture/mutation checks; no GitHub settings,
publishing, Azure authentication or release is authorized. See [C3 evidence](evidence/m4c-c3-oidc.md).

## One validation pipeline

[Secure delivery](../.github/workflows/ci.yml) runs for PRs/main pushes and manual
validation. Jobs check the locked application, policy/IaC/secrets and real local
containers; `required` fails on failed/cancelled/skipped mandatory dependencies.
There are no path filters that silently omit a required check, caches shared from
untrusted PRs, publishing steps, cloud login, deploy jobs or OIDC permission.
Actions are pinned to reviewed commit SHAs with credentials not persisted.
PRs receive repository read access only. The isolated hosted runner executes
untrusted PR code; never move these jobs to a privileged self-hosted runner.

The workflow installs with `npm ci --ignore-scripts`, checks generated licensing
drift, formatting/lint/types, 195 application tests, production builds, full dependency
audit and three original anonymous browser cases. The separate container job reuses those browser
cases through built Nginx/API images. No business functionality was changed.

C3 adds `npm run test:auth-mutations`, `npm run test:e2e:oidc` and capture checks
before/after the seven OIDC journeys. No npm package/version upgrade, job permission,
timeout, Playwright image, required-gate or container/proxy security setting changes.
The OIDC profile blocks service workers, rejects debug/capture overrides, turns
trace/video/screenshots off, preserves no per-test output and uses a sanitized
case/status/counter reporter. Its automatic fixture intercepts every test context
before navigation; only the two fixed virtual HTTPS origins route to the owned
loopback bridge. Additional contexts explicitly join that fence. Unknown targets
are aborted. Real providers never run in this pipeline.

Run locally after `npm run build`: `npm run test:auth-capture`,
`npm run test:e2e:oidc`, then `npm run test:auth-capture`. The original anonymous
profile keeps its traces/screenshots. Its test-only Vite server now prebundles and
warms the module graph before readiness (forced cold optimization), preventing a
first-use JOSE import from reloading an in-progress journey. Production Vite/proxy
configuration and the original browser assertions are unchanged. Isolated mutation
copies must fail intended assertions, not merely fail compilation or test discovery.
The 2026-11-12 owner-authorized P15 follow-up pins only frontend libxslt 1.1.43-r4
from the existing Alpine v3.24 main repository. Both rebuilt images pass the
unchanged HIGH/CRITICAL gate, and P01–P15 acceptance is met locally. The earlier
three-HIGH scan is retained as history; no scanner exception or base-image update.
See the current C3 evidence for exact results and remaining release limits.
No fixture/private-vector code enters the built frontend; JOSE's full MIT text is
included in generated browser notices, and lock/dependency inventory remain unchanged.

The application job runs as UID 1001 in the official Playwright 1.64.1 Noble
image, pinned by immutable multiarchitecture digest in the workflow and matched
to the existing lockfile. Its browser libraries/fonts and Chromium are supplied
by that image. `npm exec -- playwright install chromium` uses the bundled matching
revision without a runtime apt refresh; setup-node still selects exact Node
24.22.2. The job retains its 20-minute bound and browser setup has a five-minute
step bound. Missing/mismatched browsers or dependencies still fail real E2E.
See the [bounded timeout repair evidence](evidence/m4b-playwright-ci-repair.md).
The containers job, including its separate host-side `--with-deps` installation,
is unchanged and succeeded in that run, along with the new application environment.
This closes the repair's hosted gap, not its continuing external mirror/network
dependency or any SQL/provider/cloud/SAST/governance gate.

CodeQL is the trusted-main-only `codeql` job, disabled unless the owner explicitly
sets repository variable `CODEQL_ENABLED=true` **after** confirming support and
cost. GitHub documents that private/internal code scanning requires appropriate
[Code Security entitlement](https://docs.github.com/en/code-security/reference/code-scanning/troubleshoot-analysis-errors/private-repository-enablement).
Do not purchase/enable it under M3 authority. Disabled means **not executed**, not
a clean code scan. Enabling it makes its successful result mandatory on trusted
main; PR checks never get its `security-events: write`. No `id-token: write` is
used by any M3 job. Enable Actions-code scanning later only if supported and useful.

The owner must configure branch rules to require `required`, prohibit direct/
force pushes, require independent PR approval and dismiss stale approvals. This
repository has one human owner: obtain another eligible reviewer for independence
or record an owner-operated review limitation; do not claim self-review is
independent. Workflow code cannot create or prove server-side protections. Protect
workflow/IaC/security-policy changes with qualified review. No bypass should be
granted to agents. Confirm the actual check name from the first run before rules.

## Local equivalent and tool provenance

Use Node/npm from [M2 setup](../apps/octocat-supply/README.md). From repo root:

```sh
python3 -m pip install -r requirements-delivery.txt
python3 scripts/delivery/install_tools.py /tmp/morrow-delivery-tools
export PATH="/tmp/morrow-delivery-tools:$PATH"
export DOTNET_BUNDLE_EXTRACT_BASE_DIR=/tmp/morrow-bicep-cache
actionlint -shellcheck=""
python3 scripts/delivery/validate_infra.py
python3 -m unittest discover -s tests/delivery -v
python3 scripts/delivery/scan_config.py
gitleaks git --redact --exit-code 1 --log-opts="--all" .
gitleaks dir --redact --exit-code 1 .
python3 scripts/delivery/verify_containers.py
python3 scripts/delivery/scan_images.py
python3 scripts/delivery/provenance.py
python3 scripts/check_repository.py
git diff --check
```

Run application checks/audit in `apps/octocat-supply`, not repo root; commands are
in its README and workflow. Tool downloads/scanner DB/rules need public network
access; Bicep lint/build itself never calls Azure. The installer accepts only
Darwin arm64/Linux x86_64 platform entries from [tools.json](../security/tools.json)
and verifies SHA-256 before extracting exactly one binary. Official release
URLs, versions and license identifiers are retained there. PyYAML is pinned in
the delivery-only requirements file. Update pins through reviewed changes; never
pipe a remote installer to a shell. No tool installs inside the application.

`verify_containers.py` uses the existing Compose definition plus a small port/image
overlay. It refuses existing test project/volume state, builds locally, explicitly
migrates/seeds, checks same-origin journeys, non-root/read-only/cap-drop/port
settings, API replacement persistence and the unchanged browser cases. It uses
only 127.0.0.1:18080 and removes its own project/volume in `finally`. It never
stops or resets the original M2 demo on 8080. Existing wrong-port tests remain
available under the M2 instructions. Port conflicts fail rather than kill services.

Reports, CycloneDX SBOMs and unsigned provenance go to ignored `artifacts/m3/`.
CI retains container artifacts seven days, including scan reports on failure.
PR artifacts are untrusted and are never consumed by a release job. Provenance
binds Git SHA/dirty flag, lock/tool/Dockerfile/report/SBOM hashes to local image
IDs/platform (with descriptor type). These IDs are **not registry manifest digests**. No signed
attestation or bit-for-bit image reproducibility is claimed: immutable bases,
exact npm packages, exact patched APK versions and fresh builds/smoke are verified;
package index availability, transitive OS updates and build timestamps can vary.
M4 must build once from a clean reviewed main SHA, rescan, publish immutable
manifest digests and bind provenance/signature before approval; never promote a
mutable local tag or PR artifact by name.

## Security gates and exceptions

`npm audit --audit-level=high` covers development and runtime dependencies; errors
and reported HIGH/CRITICAL advisories fail. Gitleaks scans full fetched history
and the working tree with redacted output. Its only path exclusions are generated
dependencies/builds/demo DBs/scanner outputs; source/config/docs/history remain
covered. Mutation tests remove critical checks/escalate permissions and require
rejection. A generated non-live token canary must actually fail Gitleaks.

Trivy scans ARM/Dockerfile configuration and both final images with a fresh
vulnerability DB/rule bundle where available. Image scanning fails on **all**
reported HIGH/CRITICAL findings, including unfixed issues; there is no global
ignore-unfixed, continue-on-error or severity downgrade. SBOMs are generated even
when vulnerability findings block the gate. Scanner/network failure also blocks.
Rules have finite coverage: custom compiled-template tests enforce the internal
API, TLS, managed registry access, pull identity isolation, exact digest use,
capacity and exact OIDC trust. Compile success and scanner findings are not live
Azure policy/identity/network proof. See evidence for actual scanner coverage.

[exceptions.json](../security/exceptions.json) is empty: **no accepted exceptions**.
The scripts do not suppress findings based on that register. To request one,
record CVE/rule, exact package/image/path, reachability evidence, compensating
control, owner, independent approver, review/expiry date and fix plan. An owner
decision plus reviewed narrowly scoped gate change is required; do not enter an
exception automatically or suppress a whole package/severity. Expired/unreviewed
findings block release. Raw scanner reports stay available for independent review.

## OIDC and identities — configuration only

Use separate future `azure-publish` and `azure-release` protected environments,
each restricted to reviewed main, with required independent reviewers, self-review
disabled and administrator bypass disabled where supported. Do not add a release
workflow until entitlement/protections are verified. If this private repository's
plan cannot enforce them, retain an owner-operated release with equivalent review
evidence and **no automatic deployment**.

Use two dedicated Entra workload identities: publisher and release. The future
approved job alone receives `id-token: write`, requests audience
`api://AzureADTokenExchange`, and exchanges through Azure OIDC without a client
secret. The [federation template](../infra/federation.bicep) binds one existing
identity to one exact verified subject per apply, issuer
`https://token.actions.githubusercontent.com`, and that audience. An identity
administrator handles federation/bootstrap separately. CI/release must never be
able to alter its own trust or RBAC.

The actual subject must be inspected in an independently authorized protected
claim-discovery run, retaining only sanitized claim values, never the token or
request URL/authorization headers. For new/transferred/renamed repositories,
[GitHub's immutable-ID subject rules](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure)
apply; do not invent a name-only subject. Review repository/owner IDs, environment,
ref, audience and issuer against actual settings. No such token was requested in
M3. The template's mandatory `verifiedSubject` has no wildcard/default and is not
proof that the operator supplied the correct subject. Wrong repo/environment/
issuer/audience and rename/transfer tests must fail at Azure before M4 release.

| Principal | Candidate grant and assignment scope | Exclusions / validation needed |
| --- | --- | --- |
| Validation CI | GitHub contents read only; CodeQL trusted-main security-events write if opted in | No OIDC, cloud, publication or repository writes |
| Image publisher | AcrPush on this single non-ABAC ACR; a dedicated registry contains only this project's images | No app/RG/RBAC administration; verify role model before using an ABAC registry |
| Bootstrap human | Time-bound Contributor at dedicated RG upper bound; separate identity/RBAC admin performs registry-access/federation | Never pipeline Owner; Contributor cannot create the role assignment by itself |
| Release identity | [Candidate updater role](../infra/release-role.example.json) assigned individually to the two existing app resources; read/join on this environment and Managed Identity Operator only on identities it attaches if required | No delete/listSecrets/RBAC/federation/SQL DDL; verify actual action requirements and denial cases in M4 |
| Image pull identity | AcrPull at registry only; `identitySettings.lifecycle=None` keeps it unavailable to application code | No push; no grants at RG/subscription; propagation/first pull must be tested |
| API runtime | Dedicated identity, no RBAC grant in these templates | M4 grants necessary SQL data operations, never DDL/owner; separate migration identity |

The updater JSON enumerates allowed Container Apps operations without wildcard
actions. It is a **candidate**, not a deployed/tested role. RBAC `containerApps/write`
can change more than image fields; constrain targets and reviewed diffs, add Azure
Policy denying external API/insecure ingress as needed, and validate that a changed
identity/ingress/capacity cannot escape the approved release. No script assumes
that a resource-scoped role can enforce field-level policy. M4 must determine
whether direct approved app updates or narrowly scoped ARM deployment operations
are needed; do not grant RG deployment/Contributor permissions as a shortcut.

## Release and rollback design

M3 has no executable publishing/deploy path. M4 entry requires source SHA, clean
required CI, reviewed CodeQL support/fallback, unresolved-findings decision,
SBOMs/provenance, immutable frontend/API registry digests, config hash, schema
version/compatibility, scope/cost/teardown approval and human approval bound to
those exact artifacts. Stale SHA/config/approval means stop and review again.
Never build unreviewed code in the credentialed release job.

Record the previous known-good **pair** of image digests, config and schema before
change. Run read-only compatibility/preflight first, apply only approved targets,
then verify dependency readiness and synthetic catalogue/search/cart/price through
the frontend. Failed smoke prevents promotion. A separately approved deterministic
executor may restore that compatible pair/config and independently rerun probes;
do not silently retry a partial release, self-certify recovery or let an agent
choose arbitrary images/actions. Destructive/down database migrations are not
rollback; use additive compatibility or separately approved restore/cutover with
data-loss assessment. No live release/rollback/restore was executed in M3.

## M4B local configuration

M4A remains **NO-GO**. M4B changes are local preparation; no cloud account, provider
sign-in, SQL connection or registry publication was performed. Historical hosted
run 41149829560 validates its earlier SHA, not these changes. See
[M4B evidence](evidence/m4b-local-preparation.md),
[identity ADR](decisions/0007-application-identity.md) and
[SQL ADR](decisions/0003-persistence.md). The app's commented
[configuration example](../apps/octocat-supply/.env.example) has no credentials.
Compose retains its loopback anonymous/SQLite configuration; new variables are not
automatically forwarded by Compose or loaded into native Node. Supply explicit
reviewed settings to each service.

| Component | Required settings and behavior |
| --- | --- |
| API local default | `APP_ENV=local`, `AUTH_MODE=anonymous`, `DATABASE_BACKEND=sqlite`; existing explicit SQLite migrate/seed/reset remain available |
| API OIDC | `AUTH_MODE=oidc`; fixed HTTPS `OIDC_ISSUER`, `OIDC_JWKS_URI`; bounded `OIDC_AUDIENCE`, `OIDC_REQUIRED_ROLE`, `OIDC_REQUIRED_SCOPE`; comma-separated exact HTTPS `ALLOWED_ORIGINS`. Configure API access-token audience, never SPA ID-token audience |
| API cloud candidate | `APP_ENV=cloud`, `AUTH_MODE=oidc`, `DATABASE_BACKEND=sql`; explicit `SQL_SERVER`, `SQL_DATABASE`, `SQL_CLIENT_ID`. This selects only the assigned runtime managed identity; no password/default-chain fallback |
| Frontend local | `PROXY_MODE=local`, `AUTH_MODE=anonymous`; fixed Docker host `api`, validated `API_PORT` default 3000, resolver default Docker 127.0.0.11; strips Authorization |
| Frontend HTTPS candidate | `PROXY_MODE=https`, `AUTH_MODE=oidc`; fixed `API_ORIGIN=https://<host>` (no custom port/path/userinfo/query), identical `TRUSTED_API_HOST`, reviewed IPv4 `DNS_RESOLVER`; system CA, SNI and certificate verification, port 443 only |
| Browser config | Server renders non-secret `/auth-config.json`: `OIDC_ISSUER`, public `OIDC_CLIENT_ID`, `OIDC_SCOPES` including `openid` plus API scope, `PUBLIC_ORIGIN` exact HTTPS origin. Callback: `<PUBLIC_ORIGIN>/auth/callback`; provider must register a public SPA with PKCE/CORS and assign the required role |
| CSP | `OIDC_CONNECT_ORIGIN`: one exact reviewed HTTPS origin, default issuer origin; discovery/token endpoints must fit it. No wildcard/inline script permission or automatic expansion. Native Vite remains anonymous demo only |

Only public identifiers/configuration belong in settings. Do not add client secrets,
passwords, tokens or private keys. For Entra, use a tenant-specific v2 issuer and
verify actual access-token issuer/audience/roles/scp/sub before release. No real
tenant/client/host/resolver values have been chosen. Read-only, unauthenticated health
exposes generic status/request ID; readiness checks schema/data, not IdP reachability.
Sign-in/journey probes must separately prove identity availability. Invalid config
prevents startup, DB failure prevents readiness/application access, invalid token
never receives anonymous ownership.

### SQL migration and rights handoff — not executed

The driver is deliberately managed-identity-only. Do not sign in locally to make
tests pass or create an SA password/test account. When separately authorized on a
supported SQL/managed-identity environment, explicitly run `npm run db:sql:migrate`
then `npm run db:sql:seed` (built equivalents: `node api/dist/sql-cli.js migrate
--confirm-sql-change`, and `seed` with the same flag). The migrator requires
`SQL_MIGRATOR_CLIENT_ID`, different from `SQL_CLIENT_ID`. Startup/readiness never
migrate/seed; no SQL reset/down command exists.

Provision users/grants only in separately reviewed bootstrap work:

| Identity | Candidate SQL permissions | Forbidden |
| --- | --- | --- |
| API runtime | SELECT products/schema_migrations; SELECT/INSERT/UPDATE/DELETE carts/cart_items; transactional access | DDL, user/role administration, product updates, db_owner, control over migrator |
| Explicit migrator | Bounded create/alter/index/reference and migration-history writes for these objects; fixture SELECT/INSERT; application-lock permission verified on actual engine | Server/database owner shortcut, broad Azure/Graph grants, persistent attachment to API runtime |

Review exact object/schema ownership, grants and application-lock/driver behavior
on a real engine. Test runtime DDL denial, cross-owner denial, fresh/replay/edited
migrations, fixture drift, failed-transaction rollback, concurrency, collation,
reconnect/cold start and compatibility. Recording doubles do not execute T-SQL.
Start with fresh synthetic SQL data; no SQLite export or user-cart adoption exists.

At the M4B snapshot, private SQL/network/Entra admin/users and a dedicated migrator job were absent.
`infra/apps.bicep` now binds fail-closed OIDC/SQL/HTTPS modes and required non-secret
inputs. C4 subsequently adds SQL/private DNS/network/diagnostic and migrator
definitions; actual permissions, capacity and runtime interoperability remain unverified.

### Workflow changes and warning review

CodeQL's trusted-main opt-in remains unchanged and **has not executed**. M4A recorded
private-repository protection restrictions, separate from Code Security entitlement.
No variable, plan, visibility or protection setting was changed. Release needs
supported CodeQL results or a reviewed alternative/coverage decision and human gates.

The previous artifact-action pin declared Node 20 and produced runtime warnings.
Both uploads now pin v7.0.2 at `cf430e030ddbb5b0abf93d22962f4752f3646cd9`, whose
[primary action metadata](https://github.com/actions/upload-artifact/blob/cf430e030ddbb5b0abf93d22962f4752f3646cd9/action.yml)
declares Node 24. Both upload steps succeeded in run 42794873352; this assessment
does not claim every historical warning is absent. No Node-force flag or
warning suppression was added. Playwright's local NO_COLOR/FORCE_COLOR conflict is
separate from those hosted warnings.

The existing containers job now runs `python3 scripts/delivery/verify_proxy.py`
and retains its evidence. It uses hash-pinned published Node test certificates,
local Docker and a fake bearer string, without provider authentication. It checks
TLS name/CA/SNI, CSP, forwarding, dependency failure and seven rejected configs; see
[fixture notice](../scripts/delivery/TLS_FIXTURE_NOTICE.txt). The required job emits
a coverage notice when CodeQL is skipped. No publish/deploy/OIDC job or new
permission is introduced. Hosted execution passed at `40a6353`; the original
dated M4B repair records remain historical snapshots.

## C4 static infrastructure validation

The owner authorized local C4 definitions/static checks at `e537eff`; supplied
hosted run 43308294860 passed policy/application/containers/required with CodeQL
skipped. It was not independently re-read here and is not a hosted result for C4.
[C4 evidence](evidence/m4c-c4-infrastructure.md) records the new local results.

The same `validate_infra.py` command now requires all **eight** Bicep sources,
checks formatter output, lints/builds without warnings and binds exact source/KQL/
config/output hashes. `policy.py` rejects stale/missing/extra outputs and enforces
all original app/registry/federation/workflow invariants plus C4 network/SQL/PE/DNS/
identity/migration/retention/redaction bounds. Explicit resource counts reject
uncovered resource additions. Existing unittest discovery automatically runs the
nine new C4 tests with compiled, parameter, grant, diagnostic and CI mutations;
mandatory compilation/tests/scanning cannot be conditional or omitted. No CI
permission, job, timeout, image, action pin or release gate was changed.

`python3 scripts/delivery/validate_parameters.py <review-manifest.json>` is an
offline contract check for a later owner-supplied flat parameter handoff; it never
discovers an account or loads credentials. No real manifest is supplied. Its input
is the union of compiled parameters and reviewed surrounding-network context;
invalid/missing input exits nonzero without printing values. Tests exercise
synthetic values, not a live SQL/provider/network profile. The complete parameter
surface and required order are in [infra/README](../infra/README.md).

Runtime/migrator/pull/publisher/release identities are separate. Registry grants
remain privileged bootstrap; release/operations and contained-SQL user/grant
manifests are unapplied. No workload receives Owner/Contributor/Graph rights.
Secret slots/references are currently empty; adding any needs a separate review.
The manual migration definition has no scheduler, retry, API/operations/release
start grant or execution step. No migration is started by deployment/startup.

The candidate uses Azure Monitor workspace transformations, no workspace shared
key or HTTP/query/audit export. Diagnostic export defaults OFF until separately
authorized live table/KQL/payload-canary verification. C4 tests bind the KQL grammar
to a small Python projection model; they cannot establish Kusto syntax/runtime or
collection-time protection. Transformations occur after transport to Azure Monitor,
so source no-sensitive-logging and restricted live-stream access remain mandatory.
Complete workspace updates/diagnostic settings and external sources need live
review; do not replay the initial workspace bootstrap over a linked live workspace.

Trivy's HIGH/CRITICAL/no-exception gate is unchanged. Its finite ARM coverage does
not prove all new resources safe, so explicit compiled-resource policies remain
mandatory. No live parameter/ARM/what-if, DNS, SQL, MI/RBAC, region/SKU/quota, grant,
restore or ingestion proof follows. Existing application/crypto/SQLite/proxy tests
remain local; real SQL/provider, SAST/governance and cloud gates remain open.
Deployment stays NO-GO; C4 execution stopped at its static boundary.

## C5 read-only SAST and governance planning

The owner authorized assessment/planning only at C4 `e9b5704`. The
[C5 assessment](evidence/m4c-c5-readiness.md) and
[GET/verification evidence](evidence/m4c-c5-readiness.json) independently confirm
run 43407086701 passed policy/application/containers/required while codeql was
skipped. Its opt-in variable is absent; the aggregate intentionally accepts that
disabled state with a coverage notice. No CodeQL analysis was attempted in this run.
The current condition also excludes PRs. No workflow was changed in this task.

Private Code Security eligibility is not established. Main reports unprotected
with status-check enforcement off; protection/ruleset reads return plan-restriction
403s. No environments exist, and only the owner appears as a collaborator. Exact
billing plan, independent reviewer and enforceable approval route remain unverified.
Private branch protection, private Code Security and private deployment reviewers
have different eligibility; an admin token or a green run proves none of them.

The [proposed bounded C5 plan](milestones/m4c-c5-sast-plan.md) recommends a separately
authorized Semgrep CE 1.185.0/original-local-rule feasibility slice, complete isolated
hash locks, actual TS/TSX/Python parser/coverage probes, full target inventory,
strict error/report/capture handling and mandatory future `source-security` plus
aggregate enforcement. Twenty seeded/error/bypass/review cases are **Planned**,
not executed. No tool or rule pack was installed/adopted and no source scan ran.
CE's single-function limits need independent coverage review alongside existing
C1/C3/C4 tests; it is not asserted equivalent to CodeQL.

Owner must separately select the supported protected route or ADR 0005's proposed
owner-operated fallback, establish an independent reviewer and obtain authentic
exact-artifact approval evidence. A local approval manifest cannot prove human
identity/independence or enforce repository settings. No route is enabled here.
C5-A1/A2 remain unmet; implementation, automatic release and Azure deployment are
NO-GO under this task. No settings/visibility/subscription/permission, paid service,
credential, application or CI change, commit or push is authorized. Stop at planning.
