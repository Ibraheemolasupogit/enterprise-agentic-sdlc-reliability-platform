# Upstream source assessment

Authority: [master brief](project/master-brief.md), sections 5–6 and 14.
Current M2 status: the owner selected independent original code and MIT.
[M2 provenance and execution](#m2-independent-implementation-and-adoption) closes
those gates; the bounded licensing assessment below is retained as historical.
Historical assessment: 2026-10-30 through read-only public GitHub metadata, file trees and source
reads. No clone, fork, application source import, application dependency install, workflow
execution or cloud access was performed. M1 rechecked the pinned rights evidence
read-only; documentation tooling, if used, stays outside the repository. Revisions below are assessment snapshots, not adopted
dependencies or recommended package versions. Recheck rights and compatibility at
adoption time.

Latest bounded M2 assessment: **direct OctoCAT application reuse is not cleared;
independent implementation of the synthetic commerce requirements is recommended**.
See [current licensing decision](#bounded-m2-source-reuse-and-licensing-assessment)
and [ADR 0002](decisions/0002-source-reuse.md). M0/M1 findings below remain historical
snapshots; this recommendation does not authorize implementation or change any
repository visibility.

## Relevant upstream repositories

| ID | Repository and assessed revision | Role | Rights finding and disposition |
| --- | --- | --- | --- |
| S01 | [Azure-Samples/octocat-supply](https://github.com/Azure-Samples/octocat-supply/tree/65299c9df87fc466be28a6eec56d53ea1e4fa915) — `65299c9df87fc466be28a6eec56d53ea1e4fa915` | Preferred application assessment candidate: Azure-oriented demo, API/UI, tests, workflows and Bicep examples | No LICENSE/NOTICE/COPYING/COPYRIGHT-named file found in complete tree; API package declares MIT; repository license metadata is null. Full application/assets rights unresolved; Reference only; see current M2 assessment below |
| S02 | [octodemo/octocat_supply](https://github.com/octodemo/octocat_supply/tree/616536c69052141d5cd32e5c422099e0fa73d83c) — `616536c69052141d5cd32e5c422099e0fa73d83c` | Alternative application reference with API/UI, docs and lockfiles | No LICENSE/NOTICE/COPYING/COPYRIGHT-named file found in complete tree; repository license metadata is null. Assess separately; do not assume shared rights or exact equivalence with S01 |
| S03 | [microsoft/agent-framework](https://github.com/microsoft/agent-framework/tree/4d4e2168fe57ee20903e152928a61cf276372d29) — `4d4e2168fe57ee20903e152928a61cf276372d29` | Candidate for later agent architecture evaluation | [MIT license](https://github.com/microsoft/agent-framework/blob/4d4e2168fe57ee20903e152928a61cf276372d29/LICENSE) inspected; preserve copyright and permission notice for copies/substantial reuse; no framework selected |
| S04 | [microsoft/mcp](https://github.com/microsoft/mcp/tree/286a2b8b6ec0e2fe1d388ad45963a3fe8bf5a3b5) — `286a2b8b6ec0e2fe1d388ad45963a3fe8bf5a3b5` | Candidate Azure tool integration reference | [MIT license](https://github.com/microsoft/mcp/blob/286a2b8b6ec0e2fe1d388ad45963a3fe8bf5a3b5/LICENSE) inspected; retain notices; Azure identity, tool scope and service costs require separate design |
| S05 | [github/github-mcp-server](https://github.com/github/github-mcp-server/tree/f2a07cd13243ea9773a0ef42692e5b0e156f0951) — `f2a07cd13243ea9773a0ef42692e5b0e156f0951` | Candidate GitHub handoff/tool integration reference | [MIT license](https://github.com/github/github-mcp-server/blob/f2a07cd13243ea9773a0ef42692e5b0e156f0951/LICENSE) inspected; retain notices; later authentication and repository permissions required |
| S06 | [open-telemetry/opentelemetry-js](https://github.com/open-telemetry/opentelemetry-js/tree/cc2a315edefa532f84812c568aeeb1eabb01c924) — `cc2a315edefa532f84812c568aeeb1eabb01c924` | Candidate JavaScript telemetry foundation | [Apache-2.0 license](https://github.com/open-telemetry/opentelemetry-js/blob/cc2a315edefa532f84812c568aeeb1eabb01c924/LICENSE) inspected; preserve license/relevant notices, mark modified files, and retain applicable NOTICE content if supplied |
| S07 | [markharrison/microhack-sdlc](https://github.com/markharrison/microhack-sdlc/tree/ab5380ef37a5761413721f94334bff3127e75aa3) — `ab5380ef37a5761413721f94334bff3127e75aa3` | Brief-designated event guidance and starter context | Metadata license null; no root license file. README/root inspected; file-level rights unresolved; do not import starter material |
| S08 | [microsoft/sre-agent](https://github.com/microsoft/sre-agent/tree/f3dccc6bae8c932ff4f21e6d4117e14285da4db3) — `f3dccc6bae8c932ff4f21e6d4117e14285da4db3` | Brief-designated operational resources, labs and contribution leads | [MIT license](https://github.com/microsoft/sre-agent/blob/f3dccc6bae8c932ff4f21e6d4117e14285da4db3/LICENSE) inspected; preserve notices. README identifies a community/resources hub, not complete commercial product source or service entitlement |
| S09 | [Azure-Samples/github-copilot-hands-on](https://github.com/Azure-Samples/github-copilot-hands-on/tree/6a9682ed3e06364bbe0c8e5dc1ed88c6235e7466) — `6a9682ed3e06364bbe0c8e5dc1ed88c6235e7466` | Brief-designated agent-assisted engineering and educational patterns | [MIT license](https://github.com/Azure-Samples/github-copilot-hands-on/blob/6a9682ed3e06364bbe0c8e5dc1ed88c6235e7466/LICENSE.md) inspected; preserve notices; contribution guidance includes CLA requirements |
| S10 | [github/gh-aw](https://github.com/github/gh-aw/tree/c8152951950bbaf0d6205e02c51efd9ac5ab0b1a) — `c8152951950bbaf0d6205e02c51efd9ac5ab0b1a` | Brief-designated supported agentic maintenance model for M5 | [MIT license](https://github.com/github/gh-aw/blob/c8152951950bbaf0d6205e02c51efd9ac5ab0b1a/LICENSE) inspected; preserve notices; compilation is distinct from supported inference and useful safe outputs |
| S11 | [Historical lab repository](https://github.com/MngEnvMCAP447224/microhack-sdlc-labuser-0039); short commit/run references in [historical reuse](historical-reuse.md) | Brief-supplied historical implementation/evidence | Repository fetch returned 404 through current connection; full revisions, files and rights unverified. Historical evidence only; no temporary-org dependency |

S01 and S07–S10 are the five section-6 references required by the master brief.
S02–S06 remain optional assessment leads; no custom framework adoption is implied.
The historical event source is now identified by the brief, but its artifacts and
ancestry with this fresh repository have not been established independently.

### Upstream adoption and contribution register

Assessment date for every row: **2026-10-30**. The repository/revision or historical
commit/run links above identify the change being assessed. **Nothing is adopted,
implemented or runtime-tested here**; remote inspection is the only current test
evidence. Rights/attribution are recorded above and in the
[third-party register](../THIRD_PARTY_NOTICES.md). Revisit this version-controlled
register in M10 and whenever an adoption decision changes.

| Source | Relevance and adoption decision/rationale | Dependencies and verification still required | Contribution opportunity/status | Walkthrough relevance |
| --- | --- | --- | --- | --- |
| S01 | Reference only; direct reuse not cleared; independent synthetic implementation now recommended | File/asset permissions, runtime, native SQLite, local/container journey tests | No submission; investigate reproducible defect after rights/compatibility assessment | Explain reference selection and baseline |
| S02 | Alternative reference only; avoid parallel baseline | Independent rights and ancestry/compatibility check | No submission; none selected | Explain alternatives if relevant |
| S03 | Defer SDK choice; custom orchestration needs a requirement | Role/tool contracts, complexity, authentication and evaluation | No submission; none selected | Only if actually adopted |
| S04 | Optional Azure tool reference; no integration selected | Scoped identity, supported operations, tool bounds and service cost | No submission; none selected | Identity boundaries if demonstrated |
| S05 | Optional GitHub connector reference; no integration selected | Permissions, dedup/assignment support, safe output/human fallback | No submission; none selected | M8 handoff if verified |
| S06 | Telemetry option; assess purpose before adoption | Runtime/exporter compatibility, redaction, retention/cost and signal tests | No submission; none selected | M6 diagnostic evidence |
| S07 | Preserve event lessons; retire challenge sequence as delivery plan | File-level licensing, historical revision differences and no lab-account dependency | No submission; contribution rules not yet assessed | Explain historical context honestly |
| S08 | M7 operational reference; federation leads reserved for optional M11 | Service access/cost, actual SRE Agent execution, topology and scoped identities | No personal contribution; PR leads below are upstream work only | Diagnosis/repair actor and optional federation |
| S09 | Selective educational reference; no copied material | Asset-specific rights, suitability, current contribution rules/CLA | No submission; inspect/reproduce a focused issue before contributing | Agent-assisted engineering narrative |
| S10 | M5 maintenance reference; design separate inference and write access in M1 | Supported engine/version/auth, security advisories, useful output and negative-case tests | No submission; current guide directs non-core contributors to issue-based plans | Show genuine maintenance result, including C7 gap |
| S11 | Preserve supplied historical references; do not use as live dependency | Recover access/full hashes/rights before any code reuse; personal revalidation | No submission; historical lab is not a personal contribution target | Separate historical claims from fresh evidence |

### Verified discovery leads and integration constraints

[SRE Agent PR #385](https://github.com/microsoft/sre-agent/pull/385) (AWS-side
federation) and [PR #386](https://github.com/microsoft/sre-agent/pull/386) (GCP
federation) both returned **closed, merged** during the read-only 2026-10-30
assessment. These are upstream status findings, not personal contributions,
compatibility tests or adoption decisions. Consider them only for justified M11
modules after the Azure core; inspect actual files and current trust/permissions,
negative cases, costs and teardown before use.

The [SRE Agent README](https://github.com/microsoft/sre-agent/blob/f3dccc6bae8c932ff4f21e6d4117e14285da4db3/README.md)
is a resources/labs hub. Do not equate its MIT license with access to the commercial
service or assume direct issue creation/coding-agent assignment is supported.
[gh-aw documentation](https://github.com/github/gh-aw/blob/c8152951950bbaf0d6205e02c51efd9ac5ab0b1a/README.md)
separates compiled workflows from agent execution and scoped safe outputs. Assess
current engine/authentication/version/security guidance before M5; no installation
or inference was attempted here. Its
[contribution guide](https://github.com/github/gh-aw/blob/c8152951950bbaf0d6205e02c51efd9ac5ab0b1a/CONTRIBUTING.md)
currently directs non-core contributors to issue-based agentic plans rather than
direct PRs. The [Copilot labs guide](https://github.com/Azure-Samples/github-copilot-hands-on/blob/6a9682ed3e06364bbe0c8e5dc1ed88c6235e7466/CONTRIBUTING.md)
includes CLA requirements. Recheck repository rules before any M10 submission;
no external issue, PR or message is authorized by M0 closure.

## Application findings and integration constraints

Findings below concern S01 at the assessed revision, not a running local system.

| Finding | Evidence | Consequence for integration |
| --- | --- | --- |
| React/TypeScript/Vite frontend; Express/TypeScript/SQLite API; synthetic supply-chain entities | [README](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/README.md), [architecture](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/docs/architecture.md) | Suitable reference for local request/data flows; retain domain context without expanding business functionality |
| API manifest declares MIT; frontend manifest has no license declaration | [API package](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/api/package.json), [frontend package](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/frontend/package.json) | API metadata alone does not establish a license for UI, images, documentation or all repository content |
| README says Node 18+, while CI selects Node 24; native SQLite dependency present | [README](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/README.md), [CI](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/.github/workflows/ci.yml), [API package](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/api/package.json) | Pin and verify one compatible runtime/package-manager pair in M2 after M1 selection; check native module support on the target machine |
| README frontend port is 5173; API default CORS origins include 5137 and 3001 | [README](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/README.md), [API entrypoint](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/api/src/index.ts) | Resolve the effective local port, API URL and explicit localhost CORS configuration; broad cloud-domain defaults are not a security baseline |
| File-based SQLite and startup migration/seeding behavior | [API entrypoint](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/api/src/index.ts), [initialization](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/api/src/init-db.ts) | Verify repeatable seeds, local persistence and reset behavior; cloud replicas/storage and migration safety require a later ADR |
| Deployment workflow is disabled and includes upstream environment identifiers; Bicep expects an existing environment and registry credentials | [Deploy workflow](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/.github/workflows/deploy.yml), [Bicep](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/infra/container-apps.bicep) | Not a ready independent Azure foundation; design identity/configuration/cost in M1, implement/validate in M3 and deploy in M4; do not copy environment identifiers |
| Upstream contains agent prompts and workflows | [Source tree](https://github.com/Azure-Samples/octocat-supply/tree/65299c9df87fc466be28a6eec56d53ea1e4fa915/.github) | Import only reviewed, needed material later; prevent inherited automation, tool permissions or deployment behavior from activating |

Agent frameworks, MCP authentication, service availability, models, GitHub feature
entitlements and telemetry exporters have not been integration-tested. SDK/server
licenses do not grant cloud usage or account access. Later design must verify
version compatibility, read/write tool separation, data redaction, action bounds,
approval semantics, API limits and costs. No C7 inference test is part of M1; genuine execution belongs to M5.

## Reuse and attribution rules

1. Resolve rights for the exact intended files, images and documentation before
   copying. Public visibility is insufficient evidence of a general reuse license;
   see [GitHub's licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).
2. Record upstream URL, commit, imported paths, purpose, license evidence, retained
   notices and local modifications in an import manifest. Retain required license
   text and copyright notices with future distributions.
3. Assess assets, branding, packages, container bases and transitive dependencies
   separately. Do not imply GitHub/Microsoft endorsement or assume image/trademark
   rights follow an API package declaration.
4. Choose the owner's license for original work separately. No repository-wide
   LICENSE is added in M0/M1; it would not resolve third-party rights.
5. Update the [third-party register](../THIRD_PARTY_NOTICES.md) when anything is
   actually imported. Current entries acknowledge references only.

M1 decision: S01 is the conditional M2 workload source (ADR 0002) because its assessed tree covers the
reference application and Azure engineering examples. **Do not import it until
rights are resolved.** If permitted reuse cannot be established, record an ADR for
an independently authored sample informed by the high-level domain and reconcile
that scope with the owner before substituting it.

## M1 authoritative rights recheck and adoption decision

On 2026-10-30 M1 re-read the complete pinned S01 and S07 trees (`truncated=false`),
S01 API/frontend manifests, current repository license metadata, and pinned S08,
S09 and S10 license texts. Findings:

| Source | Authoritative evidence inspected | M1 conclusion / owner and gate |
| --- | --- | --- |
| S01 OctoCAT Supply | [Pinned tree](https://api.github.com/repos/Azure-Samples/octocat-supply/git/trees/65299c9df87fc466be28a6eec56d53ea1e4fa915?recursive=1), linked manifests above; repository metadata license null | No license/notice/copying/copyright-named file anywhere in inspected tree; API says MIT, frontend does not declare license. Whole workload/asset rights unresolved. Owner must resolve before M2 import |
| S07 microhack | [Pinned tree](https://api.github.com/repos/markharrison/microhack-sdlc/git/trees/ab5380ef37a5761413721f94334bff3127e75aa3?recursive=1), repository metadata license null | Same full-tree license-file gap; not an alternative rights shortcut. Reference/lessons only |
| S08 SRE resources | [MIT LICENSE](https://github.com/microsoft/sre-agent/blob/f3dccc6bae8c932ff4f21e6d4117e14285da4db3/LICENSE), Microsoft copyright | Retain notice/license for future copied material; not commercial product source/access permission |
| S09 Copilot labs | [MIT LICENSE.md](https://github.com/Azure-Samples/github-copilot-hands-on/blob/6a9682ed3e06364bbe0c8e5dc1ed88c6235e7466/LICENSE.md), Microsoft copyright | Retain notice/license and check asset-specific terms/contribution CLA before actual use |
| S10 gh-aw | [MIT LICENSE](https://github.com/github/gh-aw/blob/c8152951950bbaf0d6205e02c51efd9ac5ab0b1a/LICENSE), GitHub copyright | Retain notice/license; supported execution/auth and output controls still need M5 verification |

S02–S06 remain M0-inspected optional references, not newly adopted dependencies.
No inference can establish missing permission. The
[GitHub licensing guide](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
explains default copyright versus public viewing/forking. An API package declaration
is evidence about that package, not a blanket rights finding for unrelated assets.
Record actual file-level license/permission coverage before copying/distributing.
No upstream author was contacted, issue/PR opened or permission fabricated.

[ADR 0002](decisions/0002-source-reuse.md) selects S01 conditionally and the minimal
`apps/octocat-supply/` layout. Ownership of a public personal repo does not grant
ownership of source. Recommend MIT for original work, but the repository owner must
select it explicitly; no new LICENSE or blanket grant is issued in M1. This and
source/asset permission remain M2 entry blockers. Images/brands, npm dependencies,
container bases and transitive licenses need their own records before adoption.

## M1 architecture decisions and remaining gates

| Topic | Selected design / ADR | Deferred verification and owner |
| --- | --- | --- |
| Source/reuse | S01 pinned conditional candidate and minimal import, [0002](decisions/0002-source-reuse.md) | Owner before M2: rights, assets, original license; blocked until evidence exists |
| Persistence | Local SQLite, cloud Azure SQL, [0003](decisions/0003-persistence.md) | Owner/M2 pins native-compatible runtime; owner/M3–M4 costs SKU/private connectivity/migrations; owner/M9 measures restore |
| Agent execution | Existing assistant + gh-aw + actual SRE Agent, separate role/tool authority, [0004](decisions/0004-agent-execution-permissions.md) | Owner before M5 engine/auth/usage cap; M7/M8 service/read/connector support; no custom framework selected |
| Azure delivery | ACA external frontend/internal API, ACR/Bicep/Actions/OIDC, [0005](decisions/0005-delivery-identity.md) | Owner before M3/M4 verifies actual immutable subject, exact roles, protection entitlement, Entra API auth and costs/teardown |
| Observability | Journey-driven logs/metrics and justified traces with Azure Monitor target, [0006](decisions/0006-observability.md) | Owner before M6 validates SDK versions, retention/cost/alerts; SLOs are unmeasured targets |

See the [M1 review](evidence/m1-design-review.md) and
[M2 implementation handoff](milestones/m2-scope.md). Upstream read/inspection status
is not current capability execution evidence.

## Bounded M2 source-reuse and licensing assessment

Assessed: **2026-10-30**, read-only. Working repository was clean at owner-created
commit `5289623202c73e4e3699d3ba7e8b5a2fc3eb3999`. Only this assessment,
ADR 0002, notices and the M2 handoff are updated. No source/asset/package import,
installation, application execution, author contact, deployment, commit or push was
performed. This is a decision from documented grants, not a legal clearance of
unknown ownership, jurisdiction-specific exceptions, patents or trademarks.

### Current upstream and primary evidence

| Evidence | Verified finding and scope |
| --- | --- |
| [Repository metadata](https://api.github.com/repos/Azure-Samples/octocat-supply), [current main commit](https://api.github.com/repos/Azure-Samples/octocat-supply/commits/main) | Public `Azure-Samples/octocat-supply`, default branch `main`, repository license metadata `null`; main resolves to `65299c9df87fc466be28a6eec56d53ea1e4fa915`, the same revision assessed in M1 |
| [Complete pinned tree](https://api.github.com/repos/Azure-Samples/octocat-supply/git/trees/65299c9df87fc466be28a6eec56d53ea1e4fa915?recursive=1) | `truncated=false`, 324 tree entries/270 blobs; no path named for LICENSE, NOTICE, COPYING or COPYRIGHT. A filename search alone cannot rule out a grant embedded in other files |
| [API package.json](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/api/package.json) | Declares `license: MIT`. Treat this as meaningful package-specific licensing evidence, not as no license merely because a LICENSE file is absent. It does not establish repository-wide or artwork coverage |
| [Frontend package.json](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/frontend/package.json), [frontend README](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/frontend/README.md) | No frontend license grant identified. `private: true` prevents npm publishing; it is not itself a copyright license or a prohibition on all reuse, per [npm documentation](https://docs.npmjs.com/cli/v11/configuring-npm/package-json/#license) |
| [Frontend Footer.tsx](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/frontend/src/components/Footer.tsx) | Displays “Copyright © 2025 OctoCAT Supply. All Rights Reserved”. This is an actual notice to record, not a verified legal identity of the rights holder and not a grant of reuse permission |
| [Root README](https://github.com/Azure-Samples/octocat-supply/blob/65299c9df87fc466be28a6eec56d53ea1e4fa915/README.md), [public artwork](https://github.com/Azure-Samples/octocat-supply/tree/65299c9df87fc466be28a6eec56d53ea1e4fa915/frontend/public), [design images](https://github.com/Azure-Samples/octocat-supply/tree/65299c9df87fc466be28a6eec56d53ea1e4fa915/docs/design) | README describes AI/Copilot creation including the hero image. No blanket grant for product/hero art, UI copies, designs or branding identified; AI provenance is not a public-domain dedication or proof of ownership |

Targeted upstream code searches for copyright/license and the linked files were
read. Dependency lockfiles contain package license metadata, which does not license
the surrounding application. No exhaustive per-file ownership or dependency audit
was performed. The connector rejected the `/license` API endpoint as unsupported;
that was **not** a GitHub 404 or proof of an absent license. Conclusions use the
accessible metadata, complete tree and actual file declarations instead.

### Copy, modify and distribute: component decisions

| Material | Assessment / project decision |
| --- | --- |
| API package | MIT is declared. For material actually covered by that declaration, [MIT terms](https://opensource.org/license/mit) permit copying/modification/distribution with retained copyright and permission notices. Confirm package boundaries, provenance and applicable existing notices before any selective reuse; do not invent a Microsoft copyright notice. API reuse is not selected for this project |
| Frontend, shared application docs, tests, migrations and seed content outside a confirmed grant | No adequate grant located for the proposed complete workload. **Not cleared for copy/modify/redistribute with attribution alone**. This is a lack-of-established-permission finding, not a claim that no right could exist under any agreement/exception |
| Hero/product/design images, logos and copied demo screenshots | No adequate asset-specific grant established. Exclude from implementation and published portfolio unless separately cleared. GitHub [brand rules](https://brand.github.com/foundations/logo) are separate from software licensing; do not imply endorsement |
| Independently licensed packages, frameworks and container bases | Reusable under each applicable license once selected/versioned and reviewed. Obtain from their own authoritative distribution, not by assuming the OctoCAT license covers them |
| Our independently authored code, original synthetic data, text and simple original visuals | Recommended implementation route, subject to normal ownership/dependency checks. High-level catalogue/search/cart/pricing behaviour is the target, not copied source, schema, tests, prose, visual layout or data |

[GitHub's licensing guide](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
and [Terms section D.5](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service#5-license-grant-to-other-users)
distinguish public viewing/service forking from additional license rights. Neither
attribution nor private visibility supplies a missing general permission. The
[UK IPO overview](https://www.gov.uk/copyright) covers automatic protection and
restricted copying/adaptation/publication. The [US Copyright Office's computer-program guidance](https://www.copyright.gov/circs/circ61.pdf)
distinguishes protected expression from functionality; it supports the functional
reimplementation approach, not copying expressive code or a jurisdiction-wide
non-infringement guarantee. No formal clean-room process is claimed: upstream
material has already been inspected during source assessment.

### Private development and eventual publication

| Context | Compatibility decision |
| --- | --- |
| Current private working repository | Our own original implementation can remain private. Legitimately MIT-covered components can be used privately with required notices; MIT does not force publication, but recipients receive redistribution rights. Repository access control does not revoke those rights or cure missing rights for other copied content |
| Eventual public source release | Publish original code under the selected project license, retaining third-party terms/notices. Unresolved upstream content must be absent from files **and any history made public**; review before changing visibility, not after |
| Images, frontend bundles, container images, screenshots and video walkthroughs | Review embedded/copied content and shipped dependency notices, not just source folders. Prefer recording our own independently implemented UI with original visuals; reference upstream with a factual link rather than copying its artwork or demo screenshots |
| Adding MIT to our repository | Does not change repository visibility or require a public release. It grants rights only in material we have authority to license, and cannot clear unlicensed third-party content |

### Recommended compliant strategy and original license

**Recommend an independently authored synthetic commerce workload** using the
existing J01–J06/NF requirements, neutral original UI, original 12-product fixture
and independently written tests/migrations/configuration. Retain OctoCAT Supply as
an acknowledged reference; do not describe the implementation as an upstream fork,
formal clean-room product, or licensed OctoCAT distribution. Do not feed upstream
source/images to a coding agent for translation/paraphrasing. Existing framework
APIs and separately licensed dependencies may be used under their own terms.

This route avoids needing permission for application content we do not copy;
permission remains necessary if we later elect to copy it. The owner still must
select this strategy before M2 functionality begins. The current task authorizes
recommendation and document updates only; no independent substitute is implemented.

Recommend **MIT for original project code**: simple permissive private/public
reuse, copyright/permission notice retention, no requirement to publish our own
source. Apache-2.0 is an alternative when an explicit patent grant is a requirement,
with additional [notice/modification obligations](https://www.apache.org/licenses/LICENSE-2.0).
MIT is the simpler fit here; use the actual rights holder/year, preserve third-party
licenses and avoid claiming exclusive ownership of third-party or uncertain material.
No LICENSE file or blanket grant is created in this bounded assessment.

Remaining gates: owner confirms independent implementation and original-license
choice; M2 records actual dependency/container/asset versions and terms before
adoption, plus provenance/originality review before public release. If direct
OctoCAT reuse is chosen instead, obtain rights-holder permission or a clearly
licensed revision covering the intended paths/assets and redistribution, then
update this decision. Attribution alone does not clear that route. M1 review and
other project-wide status documents are left as historical/design records under
the four-document edit boundary; reconcile their conditional-source language when
the implementation strategy is accepted.

### Assessment validation

| Check | Result / scope |
| --- | --- |
| `python3 scripts/check_repository.py` | PASS: 26 text files, 23 Markdown files, 125 local file/anchor links; all 13 roadmap titles and M1 catalogue references resolve |
| `git diff --check` | PASS: no whitespace diagnostics in the four modified tracked documents |
| Edit boundary and Git review | PASS: exactly source assessment, ADR 0002, notices and M2 handoff changed; no untracked/staged files, implementation, new LICENSE, commit/push or visibility change; HEAD unchanged |
| Decision/handoff consistency | PASS: all four documents retain the same source pin and independent/MIT recommendations; all ten M2 acceptance criteria retained |

Current upstream evidence was read directly; the local checker does not verify all
external URL availability. No dependency/asset ownership audit or application/
integration test was run. This bounded task stops after the recommendation.

## M2 independent implementation and adoption

The later owner request explicitly selects original independent commerce code,
MIT, React/TypeScript, a TypeScript API and local SQLite. Morrow Supply implements
J01–J06 with original UI, inline SVG art, twelve synthetic products, tests and SQL.
No OctoCAT application code, schema, fixtures, tests, prose, logos or images were
copied. The internal directory label preserves project continuity; the displayed
identity is original. No formal clean-room or comprehensive ownership assurance
is claimed. The historical upstream license findings above remain unchanged.

Original source is covered by [root MIT](../LICENSE) and the application copy.
[ADR 0002](decisions/0002-source-reuse.md) records the selected strategy. Exact npm
versions, license identifiers, resolved sources and integrity hashes are in the
[dependency register](../apps/octocat-supply/dependencies.json), generated from our
fresh lockfile, not an upstream lockfile. Adopted packages are unmodified; original
migrations, seed data and tests were written against this project's requirements.

[Third-party notices](../THIRD_PARTY_NOTICES.md#m2-adopted-dependencies-and-distribution)
records runtime notice placement, development-only licenses, immutable base images
and distribution obligations. No external font, photo, CDN, analytics, inference
or cloud dependency is used by the application. Browser screenshots in the M2
record show our own UI and synthetic data. Event/lab and agent references remain
reference-only, not dependencies. The prior assessment's four-file/no-install/no-
implementation statements describe that historical task, not this implementation.

See [M2 evidence](evidence/m2-baseline.md) for actual versions, source fingerprint,
clean reproduction, tests and remaining limits. Private development and eventual
public MIT publication of original work remain compatible with retained package/
image obligations. Publication is not performed here; review source/history and
bundled license coverage again when distribution changes. Direct OctoCAT copying
remains not cleared; it is not an M2 blocker because that material is excluded.
