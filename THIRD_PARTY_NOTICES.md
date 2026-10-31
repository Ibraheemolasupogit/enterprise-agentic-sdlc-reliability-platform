# Third-party references and import register

Current M3 status: independently authored **Morrow Supply**, original code under
[root MIT](LICENSE). No upstream OctoCAT application source/assets or agent/cloud
material was copied. Standard npm dependencies and container bases are adopted as
recorded below. This register does not replace their own licenses or grant rights.

| Source | Reference purpose | Imported material | Rights status |
| --- | --- | --- | --- |
| Azure-Samples/octocat-supply | Factual workload reference; independent implementation now recommended | None | API declares MIT; whole application/assets not cleared; frontend copyright/rights-reserved notice recorded in source assessment |
| octodemo/octocat_supply | Alternative OctoCAT Supply application reference | None | Rights unresolved |
| microsoft/agent-framework | Later agent architecture candidate | None | MIT license inspected |
| microsoft/mcp | Later Azure tool integration candidate | None | MIT license inspected |
| github/github-mcp-server | Later GitHub handoff integration candidate | None | MIT license inspected |
| open-telemetry/opentelemetry-js | Later JavaScript telemetry candidate | None | Apache-2.0 license inspected |
| markharrison/microhack-sdlc | Brief-designated event/starter reference | None | Repository license metadata null; no root license file; reuse rights unresolved |
| microsoft/sre-agent | Brief-designated operational labs/resources and federation discovery | None | MIT license inspected; service access is separate |
| Azure-Samples/github-copilot-hands-on | Brief-designated engineering/educational reference | None | MIT license inspected; contribution guidance includes CLA requirements |
| github/gh-aw | Brief-designated M5 maintenance execution model | None | MIT license inspected; contribution process must be checked before submission |
| MngEnvMCAP447224/microhack-sdlc-labuser-0039 | Historical evidence cited by the master brief | None | Current connection returned 404; file rights and artifacts unverified |

Exact revisions, source links and obligations are in the
[source assessment](docs/source-assessment.md). Historical source, commits and run
links are now identified by the [master brief](docs/project/master-brief.md) and
preserved in the [reuse assessment](docs/historical-reuse.md). Reference
acknowledgement does not establish source ancestry or transfer file/asset rights.

Before importing material, add an entry specifying source URL/commit, local paths,
copyright holder, governing license, retained license/NOTICE locations, permission
evidence where needed, and modifications. Preserve upstream notices as required;
do not replace them with this table. The owner selected MIT for original work;
third-party material retains its own terms.

M1 rechecked S01/S07 complete pinned trees and S08/S09/S10 license texts using
upstream GitHub sources. API-only MIT metadata does not settle whole-workload or
asset rights. [ADR 0002](docs/decisions/0002-source-reuse.md) records the no-import
gate and the later owner decision to implement independently under MIT. Direct
upstream source adoption stays blocked until permission evidence
covers the selected revision/paths; the independent implementation is not blocked. Documentation design and source links are not
an import of application code, assets or upstream license text.

## Historical bounded M2 reuse recommendation

Rechecked current upstream main at
`65299c9df87fc466be28a6eec56d53ea1e4fa915` on 2026-10-30. The API MIT declaration
is package-specific evidence, not a grant for frontend, artwork or designs. The
frontend footer identifies © 2025 OctoCAT Supply and reserves rights; the legal
rights holder has not been independently established. Do not substitute a guessed
Microsoft copyright statement or delete an existing notice to make content appear
original. This register records the notice; it is not an imported application asset.

[ADR 0002](docs/decisions/0002-source-reuse.md) now recommends independently authored
synthetic commerce code/UI/data/tests rather than application source or asset
reuse. OctoCAT Supply remains a factual reference, not a claimed fork or licensed
distribution. Use original visuals and no implied GitHub/Microsoft endorsement.
The [source assessment](docs/source-assessment.md#bounded-m2-source-reuse-and-licensing-assessment)
contains primary sources, private/public publication analysis and validation.

At the assessment stage MIT was recommended, pending owner selection. The owner
subsequently selected it and M2 added LICENSE. It cannot relicense third-party content.
Keep each adopted package/container/asset license, copyright and required notices;
record version/provenance/modifications and distribution obligations. Public
source, frontend bundles, images and walkthroughs must all respect those terms.
The historical assessment itself created no LICENSE file, imported code or
permission grant. The following adoption register records subsequent M2 work.

## M2 adopted dependencies and distribution

Morrow Supply's original source, SQL, data, styles, inline SVG art and tests are
MIT; copyright (c) 2026 Enterprise Agentic SDLC & Reliability Platform contributors.
The application LICENSE duplicates [root LICENSE](LICENSE) for standalone builds.
No upstream application attribution is substituted for a missing grant.

| Adopted material | Version/source | License and retained obligations / placement |
| --- | --- | --- |
| Express and its installed runtime dependencies | Express 5.3.0; exact transitive versions/integrity in our fresh npm lockfile | Package license/copyright files remain in installed runtime `node_modules`; preserve them when redistributing the API image/package. Express is MIT; transitive terms are individually inventoried |
| React, ReactDOM, scheduler browser runtime | React/ReactDOM 19.3.1; scheduler exact version in inventory | MIT texts and copyright notices copied verbatim from installed package LICENSE files to [browser notices](apps/octocat-supply/frontend/public/third-party-notices.txt), served as `/third-party-notices.txt` and shipped with built assets; application MIT served at `/LICENSE` |
| npm development/build/test dependencies | Exact [347 locked package records](apps/octocat-supply/dependencies.json), including optional platform variants | MIT, MIT-0, ISC, BSD-2-Clause, BSD-3-Clause, Apache-2.0, MPL-2.0, BlueOak-1.0.0 and CC0-1.0 metadata. Dependencies remain unmodified; installed license/NOTICE files are retained. This inventory is metadata, not replacement license text or proof of every obligation |
| Node official Debian slim image | `node:24.22.2-bookworm-slim@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c` | Node/bundled components and Debian packages keep their distinct terms and shipped notices. Node MIT does not relicense the OS/image. `/usr/local/LICENSE` and Debian `/usr/share/doc/*/copyright` are retained; application MIT applies only to original additions |
| Unprivileged Nginx Alpine image | `nginxinc/nginx-unprivileged:stable-alpine@sha256:f5116ed4606f3eb015dd4a8e28cb9b351476dc0ad4bc6e9f93b19cec130cdf03` | Nginx BSD-2-Clause and bundled/Alpine component terms remain separate; retain base image notices, including `/usr/share/licenses/nginx/COPYRIGHT`. The base Dockerfile metadata declares Apache-2.0 separately. Tested runtime Nginx 1.30.6; mutable tag is constrained by immutable digest |

The MPL-2.0 entries are development-only Lightning CSS/platform packages. They
are not copied into API runtime dependencies or browser bundles. Distributing
those tools or modified covered files separately would require their MPL notices/
source obligations; do not describe the whole dependency graph as MIT. Build-tool
license headers are not a substitute for actual runtime notices. Apache/BSD/other
package notices remain with installed packages; review additional NOTICE/source
offers if distributing new tools, source archives or modified third-party files.

The inventory is generated by `npm run licenses` from the locked npm metadata;
React notices use actual installed primary license text. `npm ci --ignore-scripts`
disables lifecycle execution. Optional platform variants are in the lock but not
all installed on each host. No dependencies or base components were modified.
No external artwork/fonts are adopted. [M2 evidence](docs/evidence/m2-baseline.md)
records reproducibility, scope of the audit and limitations. The root MIT does
not change repository visibility, supply upstream rights or license trademarks.

## M3 tooling and packaging provenance

No upstream application source/assets are adopted. Original pipeline/Bicep/security
test code is MIT. [Pinned tool manifest](security/tools.json) records official
release URLs, exact versions, SHA-256 asset digests and license identifiers for
Bicep/actionlint (MIT), Gitleaks (MIT) and Trivy (Apache-2.0); downloaded tools are
not committed or redistributed in application images. PyYAML 6.0.3 (MIT) is a
local/CI-only dependency. Retain their actual license/NOTICE files if distributing
these tools rather than just referencing/installing them. GitHub Actions are
commit-pinned; their upstream terms remain applicable to their execution.

The M2 Debian Node digest remains the build-stage base. M3 changes only the API
runtime to official `node:24.22.2-alpine` index digest
`sha256:8a32c8cf649a49915a66e81e7a609223c708d0adabf288ee3f4077d765542f85`,
removing unused global npm/yarn entry points/code after installing unchanged
locked production dependencies. Node/bundled-component and Alpine terms remain
separate; existing base license layers/notices are retained. The frontend retains
the pinned Nginx base and installs exact signed Alpine packages brotli-libs
1.2.1-r0, curl/libcurl 8.23.0-r0; package copyright/license terms are not replaced
by MIT. Generated CycloneDX SBOMs inventory installed components; image source,
OS package availability and distribution/source-offer obligations must be reviewed
again when publishing images. No third-party source file was modified. Existing
React notices and application license remain shipped with the frontend.

[M3 evidence](docs/evidence/m3-secure-delivery.md) records image hashes/scans and
limits. The earlier M2 runtime image/table is historical; it does not establish
the contents/security of the hardened M3 runtime. No container registry push or
public distribution occurred during this task.
