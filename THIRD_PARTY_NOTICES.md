# Third-party references and import register

Current M4B local-preparation status: independently authored **Morrow Supply**, original code under
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
| npm development/build/test dependencies | Exact [current locked package records](apps/octocat-supply/dependencies.json), including optional platform variants | MIT, MIT-0, ISC, BSD-2-Clause, BSD-3-Clause, Apache-2.0, MPL-2.0, BlueOak-1.0.0 and CC0-1.0 metadata. Dependencies remain unmodified; installed license/NOTICE files are retained. This inventory is metadata, not replacement license text or proof of every obligation |
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

## M4B identity, SQL and test-vector adoption

No OctoCAT application code/assets were imported. Original adapter/auth/proxy/tests
remain MIT. Fresh exact lock metadata now records 417 package entries. The following
unmodified packages are adopted; package tarball URLs/integrity and transitive terms
are preserved in the lock/inventory, with installed license/NOTICE files retained.

| Material | Provenance / terms | Distribution obligations |
| --- | --- | --- |
| jose 6.2.14 | [Official project](https://github.com/panva/jose); installed `LICENSE.md`, MIT | Retain copyright/permission text in API runtime node_modules; original project MIT cannot replace it |
| mssql 12.7.13 and Tedious/managed-identity dependencies | [Official driver](https://github.com/tediousjs/node-mssql); installed `LICENSE.md`, MIT; transitive packages separately inventoried | Retain each installed runtime license/NOTICE, including Apache-2.0 Azure components; no driver source modified |
| oidc-client-ts 3.5.0 | [Versioned license](https://github.com/authts/oidc-client-ts/blob/v3.5.0/LICENSE), Apache-2.0 | Full installed LICENSE copied into browser notices, retaining its copyright/attribution. No package NOTICE file was present; generator copies one if supplied. No source modifications |
| jwt-decode 4.0.0 | Browser dependency of oidc-client-ts, MIT | Actual installed license/copyright copied into browser notices |
| @types/mssql 12.3.0 | Development-only type definitions, MIT | Preserve installed license if redistributing tools/source dependencies |
| RFC 7515 Appendix A.2.1 RSA JWK | [Primary RFC](https://www.rfc-editor.org/rfc/rfc7515#appendix-A.2.1); public non-live test vector | Imported only into [API test fixtures](apps/octocat-supply/api/fixtures/README.md); retained 2015 IETF Trust attribution/Simplified BSD terms there. Not copied into runtime images; never use as operational key |
| Node v24.22.2 TLS fixtures | [Official files](https://github.com/nodejs/node/tree/v24.22.2/test/fixtures/keys); three checksum-pinned downloads | Temporary tests only; downloaded files are unmodified, not committed/shipped in application images. [Retained Node MIT notice](scripts/delivery/TLS_FIXTURE_NOTICE.txt) accompanies test tooling; do not redistribute vectors without that notice |

`npm run licenses` copies actual browser runtime texts, including new OIDC/jwt-decode
notices, and fails on missing license metadata/text. Apache-2.0 is preserved rather
than relabelled MIT. Before any public package/image publication, retain these
texts and all transitive/base obligations; scans/SBOMs are inventory evidence, not
a legal clearance or a license for external identity/cloud services. The no-copy
decision for upstream OctoCAT remains unchanged.

## M4B frontend OS security patches — 2026-11-10

The existing pinned Nginx/Alpine base and its notices are retained. The frontend
recipe additionally selects these unmodified signed packages from Alpine v3.24
`main`, using exact versions. Package metadata/source revisions were recorded
before building. No upstream application source/assets are imported.

| Package/version | Upstream source and exact Alpine packaging revision | Terms and retained obligations |
| --- | --- | --- |
| libexpat 2.10.0-r0 | [Expat](https://libexpat.github.io/); [aports af0fa42036cd6e626768c0d65fddaa1d1b30cf21](https://gitlab.alpinelinux.org/alpine/aports/-/tree/af0fa42036cd6e626768c0d65fddaa1d1b30cf21/main/expat) | MIT package metadata; retain upstream copyright/permission texts when distributing |
| musl and musl-utils 1.2.6-r3 | [musl](https://musl.libc.org/); [aports 8f79d39391b46d6dbf1800fb68b8212a21d5ee2e](https://gitlab.alpinelinux.org/alpine/aports/-/tree/8f79d39391b46d6dbf1800fb68b8212a21d5ee2e/main/musl) | musl: MIT; musl-utils: MIT AND BSD-2-Clause AND GPL-2.0-or-later. Preserve package/base notices and applicable source obligations before public image distribution |
| zlib 1.4-r0 | [zlib](https://zlib.net/); [aports bdf501c870a92a05c097857401f69c48c4810384](https://gitlab.alpinelinux.org/alpine/aports/-/tree/bdf501c870a92a05c097857401f69c48c4810384/main/zlib) | Zlib package metadata; preserve upstream notice and restrictions when distributing |

Package source code is not modified. The modification is limited to replacing
four installed OS package versions through the existing `apk add` layer; image
notices, including `/usr/share/licenses/nginx/COPYRIGHT`, remain retained. Official
Alpine indexes list the selected versions for both aarch64 and x86_64; execution
platforms, package checksums and scan results are recorded in the bounded image
repair [evidence](docs/evidence/m4b-frontend-image-repair.md). No image publication
or public distribution is authorized here.
