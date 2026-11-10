# M4B frontend image vulnerability repair

Date: 2026-11-10 UTC. Base HEAD: `1e8d92d69a7947a2d7bbf301886580d5c95d8254`.
Status: **Locally tested; image gate PASS. Deployment remains NO-GO.**
Authority: owner's bounded frontend image remediation request and
[M4B scope](../milestones/m4b-scope.md). Exact findings, versions, image identities,
report/SBOM/provenance hashes and preservation checks are in
[machine-readable results](m4b-frontend-image-repair.json).

This closes the seven-HIGH local image blocker recorded in the 2026-11-09
[proxy-repair evidence](m4b-ci-repair.md#resumed-validation--2026-11-09).
That historical record and all five uncommitted proxy-repair files are preserved
byte-for-byte. The hosted proxy repair remains unverified; no GitHub run or
setting change was performed.

## Findings and dependency origin

The retained before scan is from 2026-11-09 18:06:21 UTC. Trivy classified all seven
entries as `os-pkgs/alpine`, sourced from Alpine Secdb: **six distinct CVEs across
four installed packages**, all HIGH, all with published fixes. API had zero
HIGH/CRITICAL. These are installed final-runtime OS packages inherited from the
pinned Nginx base, rather than Node build-stage or npm application findings.

| Package | Installed before | CVE | Severity | Reported minimum fix | Installed after |
| --- | --- | --- | --- | --- | --- |
| libexpat | 2.9.0-r0 | CVE-2026-113351 | HIGH | 2.10.0-r0 | 2.10.0-r0 |
| libexpat | 2.9.0-r0 | CVE-2026-115506 | HIGH | 2.10.0-r0 | 2.10.0-r0 |
| libexpat | 2.9.0-r0 | CVE-2026-117610 | HIGH | 2.10.0-r0 | 2.10.0-r0 |
| libexpat | 2.9.0-r0 | CVE-2026-118370 | HIGH | 2.10.0-r0 | 2.10.0-r0 |
| musl | 1.2.6-r2 | CVE-2026-107891 | HIGH | 1.2.6-r3 | 1.2.6-r3 |
| musl-utils | 1.2.6-r2 | CVE-2026-107891 | HIGH | 1.2.6-r3 | 1.2.6-r3 |
| zlib | 1.3.2-r0 | CVE-2026-85091 | HIGH | 1.3.2-r1 | 1.4-r0 |

The pinned base has nine filesystem layers, all an exact prefix of the original
frontend image. Each finding's reported layer belongs to that base: musl,
musl-utils and zlib are in its first Alpine layer; libexpat is in its ninth layer.
Installed-package reverse dependencies show libexpat via fontconfig → libgd →
nginx-module-image-filter. Musl is the runtime libc used by Nginx and other binaries;
musl-utils supplies base utilities. Zlib is required by Nginx, curl/libcurl and
several bundled libraries. No claim of CVE exploitability/reachability is inferred
from package presence or from unused optional modules.

## Smallest supported correction

The only implementation change is one continuation line in the existing
[frontend Dockerfile](../../apps/octocat-supply/frontend/Dockerfile), selecting
four exact signed package versions through its existing `apk add --no-cache`
operation. The package-manager simulation and final SBOM comparison both show
exactly those four version changes; no packages were added or removed.

The official Alpine v3.24 `main` indexes list these versions for both aarch64 and
x86_64. Alpine's [security database](https://secdb.alpinelinux.org/v3.24/main.json)
confirms the reported fixes. Its current repository index offers zlib 1.4-r0,
rather than 1.3.2-r1. Although the older APK URL remains reachable, 1.4-r0 is the
indexed version available through the existing exact-version installation pattern;
it also fixes the separately reported MEDIUM CVE-2026-4738. No archive repository,
direct-URL package installation, signature bypass or alternative distribution was
introduced. The retained SONAMEs include `libz.so.1`, `libexpat.so.1` and the musl
loader; actual runtime compatibility was tested below.

The Nginx base digest remains
`sha256:f5116ed4606f3eb015dd4a8e28cb9b351476dc0ad4bc6e9f93b19cec130cdf03`;
Nginx remains 1.30.6, the Alpine release marker remains 3.24.2, and runtime UID
remains 101. Existing brotli/curl/libcurl pins and the Node build stage are retained.
No blanket OS upgrade, npm change, application refactor, API recipe change or new
test framework was needed. The API was rebuilt/tested from its unchanged recipe.

Upstream URLs, exact Alpine source revisions and distinct package terms were
recorded in the [third-party register](../../THIRD_PARTY_NOTICES.md#m4b-frontend-os-security-patches--2026-11-10)
before building. No third-party source was modified. The base Nginx COPYRIGHT file
remains byte-identical; existing application/browser notices are retained.

## Executed verification

| Check | Actual result |
| --- | --- |
| `verify_containers.py` | PASS: rebuilt production pair, 12 fixtures/authoritative discount, non-root/read-only/cap-drop/loopback exposure, API replacement persistence and all 3 browser cases |
| `verify_proxy.py` | PASS: verified CA/name/SNI, bearer/header isolation/CSP, wrong certificate name yields API/readiness 503 with static 200, all 7 unsafe-config cases rejected |
| `scan_images.py` | PASS unchanged HIGH/CRITICAL policy; both final images 0 HIGH/CRITICAL; both CycloneDX SBOMs regenerated |
| Supplemental all-severity image inventory | Frontend: 0 findings. API: 1 MEDIUM; details below. This inventory does not replace the release gate |
| Application formatting/lint/types/test/build | PASS; 64 tests in 7 files, original M2 behavior/tests retained |
| Native browser journeys | 3 passed; only existing NO_COLOR/FORCE_COLOR warnings |
| License generation/drift | PASS; 417 exact locked records and browser notices unchanged |
| npm high/critical audit gate | PASS threshold; 0 HIGH/CRITICAL, 10 moderate development-graph findings |
| Bicep lint/build/policy | PASS all four templates; no Azure/ARM validate/what-if |
| Delivery/security tests and actionlint | 12 passed, including proxy regressions, boundary mutations, fail-closed gate and secret canary; actionlint passed without shellcheck |
| Trivy configuration | PASS two Dockerfiles and finite registry-access ARM coverage; compiled policy covers all four templates |
| Unsigned provenance | Regenerated; source/report/SBOM hashes and final image IDs verified; `releaseEligible=false` |
| Secrets/repository/whitespace | Final results in JSON; includes all tracked and untracked text changes |

Trivy 0.72.0 used vulnerability DB updated 2026-11-09 13:58:27 UTC, still within its
next-update window at the 2026-11-10 05:05 UTC gate. No skipped DB update, severity
downgrade, ignore-unfixed, CVE exclusion, exception or policy modification was used.

## Residual risks and stop boundary

The full API inventory reports **CVE-2026-4738, MEDIUM, zlib 1.3.2-r1**, with reported
fix 1.4-r0. Its HIGH/CRITICAL gate still passes; this is an open lower-severity
finding, not an accepted exception. API package remediation is outside this
frontend-only request. The unchanged npm graph still has 10 moderate findings;
no clean full-dependency-audit claim is made.

Execution is macOS arm64 with Docker Desktop 28.3.3/Linux arm64, pinned Node
24.22.2/npm 11.19.1, Bicep 0.48.1, actionlint 1.7.12, Gitleaks 8.30.1 and Trivy
0.72.0. x86_64 package availability was inspected, but no x86_64 build or hosted
execution was run. Signed repository availability and future advisories can change;
rescan the exact reviewed images before release. Local image IDs are not approved
published registry manifest digests. Reports are unsigned local evidence.

Raw before/after reports, package indexes, dependency/layer evidence, test logs
and retained notices are in ignored `artifacts/m4b-image-repair/`; selected values
and hashes are retained in the JSON evidence. Test-owned resources were removed;
pre-existing stopped M2 containers, volume and network were untouched. No cloud
authentication, credential creation, GitHub settings change, Azure resource,
deployment, paid inference, commit or push occurred. CodeQL and hosted confirmation
remain unverified. This bounded frontend image repair stops here; broader M4B
integration, governance and deployment gates remain open.
