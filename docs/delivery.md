# Secure delivery — M3

Authority: [master brief](project/master-brief.md), [ADR 0005](decisions/0005-delivery-identity.md).
[M3 evidence](evidence/m3-secure-delivery.md) distinguishes actual local execution
from unexecuted GitHub/Azure settings. The M2 application and tests are preserved;
only container packaging changes address scanner findings. No release is enabled.
Subsequent [M4A preflight](milestones/m4a-preflight.md) confirms hosted run
41149829560 passed application/policy/containers/required, with CodeQL skipped.
It found no GitHub environments and plan-restricted branch/ruleset protection
reads; Azure live checks remain blocked. M3 evidence remains a historical snapshot.

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
drift, formatting/lint/types, 39 existing tests, production builds, full dependency
audit and three browser cases. The separate container job reuses those browser
cases through built Nginx/API images. No business functionality was changed.

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
