# Upstream source assessment

Authority: [master brief](project/master-brief.md), sections 5–6 and 14.
Assessed: 2026-10-30 through read-only public GitHub metadata, file trees and source
reads. No clone, fork, source import, dependency install, workflow execution or
cloud access was performed. Revisions below are assessment snapshots, not adopted
dependencies or recommended package versions. Recheck rights and compatibility at
adoption time.

## Relevant upstream repositories

| ID | Repository and assessed revision | Role | Rights finding and disposition |
| --- | --- | --- | --- |
| S01 | [Azure-Samples/octocat-supply](https://github.com/Azure-Samples/octocat-supply/tree/65299c9df87fc466be28a6eec56d53ea1e4fa915) — `65299c9df87fc466be28a6eec56d53ea1e4fa915` | Preferred application assessment candidate: Azure-oriented demo, API/UI, tests, workflows and Bicep examples | No LICENSE/NOTICE/COPYING/COPYRIGHT-named file found in complete tree; API package declares MIT; repository license metadata is null. Full application/assets rights unresolved; reference only in M0 |
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
| S01 | First workload candidate for M1 design/M2 adoption; rights unresolved | File/asset permissions, runtime, native SQLite, local/container journey tests | No submission; investigate reproducible defect after rights/compatibility assessment | Explain reference selection and baseline |
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
   LICENSE is added in M0; it would not resolve third-party rights.
5. Update the [third-party register](../THIRD_PARTY_NOTICES.md) when anything is
   actually imported. Current entries acknowledge references only.

Recommendation: S01 is the first M1 design/M2 adoption candidate because its assessed tree covers the
reference application and Azure engineering examples. **Do not import it until
rights are resolved.** If permitted reuse cannot be established, record an ADR for
an independently authored sample informed by the high-level domain and reconcile
that scope with the owner before substituting it.

## Unresolved architecture and attribution decisions

M1 must decide or record bounded deferrals for workload revision/layout, complete
file/asset rights and notice retention, original project license, local versus
cloud persistence/durability, migration/concurrency/restore/rollback integrity,
Azure hosting/internal API and OIDC/runtime identities, narrower deployment roles,
Bicep reuse, agent responsibility/tool boundaries, supported gh-aw inference versus
repository-write access, dependency health/SLI/SLO/error budgets and costs/teardown.
No source adoption, agent framework, live SRE integration or federation design is
selected by this M0 register. See [M1 acceptance criteria](milestones/m1-scope.md).
