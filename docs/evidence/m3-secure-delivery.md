# M3 verification — Secure delivery

Dates: 2026-10-30–31 (UTC).
Status: **Implemented and Locally tested; M3 local exit PASS**. GitHub-hosted CI,
CodeQL, protected settings, registry publication and Azure remain **unverified**.
Scope: [eight M3 criteria](../milestones/m3-scope.md), R04–R06/R14–R17/R25,
NF02/NF03/NF08/NF10, V09/V14 local controls and V18 supply-chain checks.
Authority: [master brief](../project/master-brief.md) and owner M3 request.
Actor: scoped coding assistant plus deterministic local tools; no application/
maintenance/SRE agent or cloud executor ran.

## Source, environment and delivered files

M3 began from clean committed M2 at HEAD
`8dca6c09278eedea20f8f6372007b8b44a8539a5`. M3 remains an uncommitted working-tree
change, not a published release. M2 source/tests/lockfile/fixtures are preserved;
application changes are Docker packaging and an explanatory README addition only.
Original code remains MIT and third-party notices are retained.

| Area | Files / result |
| --- | --- |
| CI | [One workflow](../../.github/workflows/ci.yml): application, policy, containers, conditional CodeQL and fail-closed aggregate required check; pinned actions, no publish/deploy/OIDC job |
| Security/config | [tools.json](../../security/tools.json), empty [exceptions](../../security/exceptions.json), root Gitleaks config and delivery-only PyYAML requirement; generated reports ignored |
| Local tools/checks | `scripts/delivery/`: checksum-verified binary installer, Bicep lint/build, workflow/compiled policy, isolated container smoke, config/image scanning, SBOMs and unsigned provenance |
| Azure definitions | [IaC index](../../infra/README.md): foundation, apps, registry pull binding, exact OIDC binding; candidate app-scoped updater role; no Azure deployment/resource instance |
| Regression/security tests | `tests/delivery/test_security.py`; all existing M2 test files unchanged |
| Guidance/status | [Delivery design](../delivery.md), [M3 scope/M4 handoff](../milestones/m3-scope.md), AGENTS/README/roadmap/architecture/charter/capability/validation/ADR 0005 and notices |

Environment: macOS 15.6.1 arm64; Python 3.12.8/PyYAML 6.0.3; pinned Node 24.22.2 /
npm 11.19.1; Docker 28.3.3/Compose 2.39.2, Linux arm64 images. Bicep
0.48.1.52935 and actionlint 1.7.12 were downloaded from official releases and
SHA-256 verified. Gitleaks 8.30.1 and Trivy 0.72.0 match the tool manifest.
Vulnerability DB/rule bundles were refreshed through public registries, not cloud
account authentication. CI targets Ubuntu 24.04 x64; that hosted environment is
not claimed as executed locally. Browser: installed Playwright Chromium, unchanged
Playwright 1.64.1 test suite from M2.

## Executed commands and actual outcomes

| Command / check | Outcome |
| --- | --- |
| `npm ci --ignore-scripts` (app directory) | PASS: 298 host-installed packages, original 347-record cross-platform lock; no lifecycle scripts |
| `npm run licenses` and generated-file drift | PASS: dependency inventory/browser notices unchanged |
| `npm run format:check`, `npm run lint`, `npm run typecheck` | PASS; original application checks preserved |
| `npm test` | **39 passed in four files**: pricing, API, database lifecycle and frontend |
| `npm run build` | PASS: API/production UI; unchanged CSS/JS asset identities `index-DBuhDI_X.css`, `index-C9_y59wX.js` |
| `npm run test:e2e` | **3 passed** against native isolated UI/API |
| `npm audit --audit-level=high --json` | PASS: zero advisories across runtime **and dev** dependencies at execution; not a guarantee against unknown vulnerabilities |
| `actionlint -shellcheck=""` | PASS: workflow syntax/context; shellcheck is not installed/invoked by this command |
| `python3 scripts/delivery/validate_infra.py` | PASS: four Bicep files lint/compile without unresolved warnings; no Azure connection, ARM validation or what-if |
| `python3 -m unittest discover -s tests/delivery -v` | **7 passed**, including 17 workflow/IaC mutation subcases, 15 actual shell gate outcome cases, candidate-role restrictions and actual non-live secret-canary rejection |
| `gitleaks git --redact --exit-code 1 --log-opts="--all" .` | PASS: four existing commits scanned, no detected leaks; not remote/private-scanning entitlement proof |
| `gitleaks dir --redact --exit-code 1 .` | PASS: working files scanned with documented generated-path exclusions; redacted output |
| `python3 scripts/delivery/verify_containers.py` | PASS after test-origin configuration fix: original browser cases **3 passed** through real built proxy/API, seeded data/pricing, replacement persistence and runtime/exposure checks |
| `python3 scripts/delivery/scan_images.py` | PASS: zero reported HIGH/CRITICAL findings in **both final images**, two CycloneDX SBOMs generated; no ignore-unfixed or accepted exception |
| `python3 scripts/delivery/scan_config.py` | PASS for evaluated Dockerfiles/ARM role assignment; finite ARM coverage explicitly below |
| `python3 scripts/delivery/provenance.py` | PASS: source/build-input/report/SBOM hashes and image identity recorded; rejects stale image scan identity; unsigned and `releaseEligible=false` |
| Repository docs/whitespace/Git | PASS: 40 text files, 29 Markdown files, 217 local links/anchors, all roadmap titles/catalogue references; tracked and 25 untracked text files pass whitespace checks; no staged files, commit/push or HEAD change |

Commands requiring local sockets/Docker/public downloads were run with sandbox
authorization. No Azure CLI, cloud login, OIDC token request, paid API/inference,
registry push, deployment or Git write was performed. A first root-directory npm
audit attempt correctly failed for no root lockfile; it was rerun successfully in
the app directory. Bicep needed a temporary .NET extraction cache in this sandbox.
An unsupported ACR property warning was removed rather than waived. Existing M2
evidence is historical; it is not rewritten to claim current M3 source identity.

## Findings fixed and retained scan limits

The initial M2 API image scan reported **63 HIGH/CRITICAL package occurrences**:
57 Debian OS entries without fixes in that snapshot and six fixed issues in
global npm-bundled brace-expansion/undici. These are scanner occurrences, not 63
independently demonstrated exploitable paths. The API runtime now uses pinned
official Node 24.22.2 Alpine and excludes unused global npm/yarn. Node/API version,
production dependency lock and business logic are unchanged. Build stages retain
the pinned Debian toolchain. This reduces runtime scope without suppressing CVEs;
the final merged runtime scan has zero reported HIGH/CRITICAL findings. Scanning
the final image does not prove every deleted lower-layer byte/build tool harmless.

The initial frontend scan found **three occurrences**: CRITICAL brotli-libs plus
HIGH curl/libcurl. The same immutable Nginx base is retained and exact signed
Alpine security versions installed: brotli-libs 1.2.1-r0, curl/libcurl 8.23.0-r0.
Explicit UID 101 also closes the inherited-user Dockerfile rule finding. Final
frontend/runtime scan reports zero HIGH/CRITICAL. All lower-severity results,
future advisories, build-stage/tool vulnerabilities and changing rule coverage
remain review concerns; no full security certification is claimed.

The first isolated browser run exposed the expected restrictive origin check:
test port 18080 was absent from M2's default 8080/5173 allowlist. The M3 overlay
now sets only `ALLOWED_ORIGINS=http://127.0.0.1:18080`; application defaults/tests
remain unchanged. Smoke requests include the real origin so this cannot be
masked by a non-browser probe. The fresh project rerun passed all browser cases.

Trivy 0.72.0 reports only `registry-access.json` in this compiled ARM set; it does
**not** establish scanner coverage of foundation/apps/federation resource types.
Both Dockerfiles are evaluated. Four-file Bicep lint/build and direct compiled
policy tests independently cover internal API vs external frontend, TLS, immutable
image references, probes, managed registry credentials, pull identity code
isolation, bounded replicas, registry admin/anonymous disabled, scoped AcrPull and
exact issuer/audience/subject configuration. The tests deliberately mutate those
controls and require failure. This is meaningful local IaC validation, not a
complete Azure security scan or live network/RBAC enforcement test.

After the smoke rebuild, the provenance guard rejected stale scan image IDs
because BuildKit's local index/attestation identities changed. Final image rescans
and SBOM generation then bound successfully. Local Docker image IDs may identify
a config or an index depending on the image store; descriptor types are retained,
and no local ID is presented as a published/approved registry reference.

Public fingerprints initially triggered generic-secret heuristics when API paths
were JSON keys beside hashes. Fingerprints now use separate `path`/`sha256` fields;
no secret-scanner exception or suppression was introduced.

No exceptions are accepted; the register is empty and no scanner ignores are
added. Network/scanner errors, audit findings and image HIGH/CRITICAL findings
fail the actual workflow gate. The aggregate shell gate was run with success,
failure/cancelled/skipped mandatory jobs and supported CodeQL skip cases; its
observed exit status matches fail-closed policy, not merely YAML string matching.

## Artifacts and capability boundary

[Retained local verification summary](m3-local-results.json) links source/image/
scan identities and actual smoke timing. Raw scan JSON, SBOMs, compiled templates
and unsigned provenance live in ignored `artifacts/m3/`; hosted jobs retain their
artifacts seven days when run. Local image IDs are not pushed manifest
digests, signed attestations or authorization to release. Exact source/build input
hashes distinguish this dirty working tree from the starting M2 commit.

Hosted Actions was **not triggered**. Repository/branch rules, reviewer protection,
environment plan entitlement and actual required check names are **not verified**.
CodeQL is implemented but explicitly disabled unless owner-enabled after support/
cost review; it did not run and is not counted as a clean scan. Private repository
support follows [GitHub's entitlement guidance](https://docs.github.com/en/code-security/reference/code-scanning/troubleshoot-analysis-errors/private-repository-enablement).
No GitHub/Azure setting, federation binding, role, identity, registry or resource
was created. Bicep/negative tests validate definitions, not real issuer/audience/
subject denials, policy/quota/region availability or SQL/cart authorization.

Application unit/integration/component/native/container browser checks remain
Locally tested. CI/Bicep/gates are Implemented and locally checked. Cloud delivery,
runtime identity/auth, durable SQL, restore, availability/SLOs and agents remain
Planned/Design only. Local input/secret cases do not establish agent prompt-
injection resistance. No Claims Processing integration exists.

## Costs and precise M4 handoff

No paid services executed and no Azure resources provisioned: no Azure service
usage was incurred by this task. Local Docker/CPU/disk/public package and scanner
downloads were used. No GitHub runner/artifact usage occurred because nothing was
pushed/run remotely. Future private-repository Actions/artifact/Code Security
charges depend on the owner's plan; check entitlement/minutes/storage before
enabling/running them. Job timeouts/retention bound runs but are not spending caps.

The Bicep Consumption/ACR Basic settings are candidates, not an approved cost
estimate or hard ceiling. Registry, SQL, private endpoints/DNS/VNet, diagnostics,
compute and storage can incur recurring costs even at low activity. There is no
approved region/subscription/SKU/paid ceiling, and no cloud deployment is ready.

Before M4, close the [six explicit entry prerequisites](../milestones/m3-scope.md#m4-prerequisites--not-implemented-here):
priced owner-approved cloud scope/teardown; genuine hosted CI and protected review
support; verified exact OIDC/split least-privilege grants and denial tests; private
Azure SQL adapter/migrations/runtime-vs-DDL identities; API token/role/cart ownership
and frontend sign-in/Authorization/HTTPS/DNS changes; clean cloud-ready digest-bound
builds, rescans/provenance, pull propagation and approved release/rollback smoke.
Current M2 images deliberately remain local and must not be deployed through the
candidate templates. Stop after M3; owner reviews and manually commits/pushes.
