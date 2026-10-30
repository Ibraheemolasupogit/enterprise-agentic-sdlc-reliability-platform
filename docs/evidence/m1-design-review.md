# M1 design review and implementation handoff

Date: 2026-10-30. Status: **Design only**; implementing assistant's document review,
not an independent human approval or execution result. Authority:
[master brief](../project/master-brief.md) and [M1 scope](../milestones/m1-scope.md).
The owner authorized M1 design only. Claims Processing remains separate.

## Starting state and preserved work

M1 began on clean `main`, tracking `origin/main`, at owner-created commit
`e7149a8068595a8975db6b1f7e52fff2daa9f43e` (`docs: establish agentic SDLC platform foundation`).
The owner had committed the M0 work between tasks. This differs from the historical
untracked/no-remote state in the M0 report; that report is preserved, not rewritten
as current Git state. No application, infrastructure or workflow existed at entry.

The full master brief, AGENTS and M1 scope were read first. M0 charter, requirements,
capability matrix, source register, roadmap and M2 plan were extended. The master
brief, historical reuse, ADR 0001 and M0 evidence remain substantive source history.
No application source, assets, migration SQL, Docker/Compose/workflow/IaC files,
agent runtime or credentials were created/imported.

## Completed files and decisions

| File/group | Result |
| --- | --- |
| [Charter](../project-charter.md), [requirements](../requirements.md), [capability matrix](../capability-status.md) | Defined scope, retained R01–R25, added J01–J06/FR01–FR06 and NF01–NF10; design evidence separated from unverified runtime |
| [Architecture](../architecture.md) | Six Mermaid diagrams: local application, agent SDLC, secure delivery, Azure target, observability and incident-to-PR; explicit API/config/auth/data contracts |
| [Threat model](../threat-model.md) | Application/agent STRIDE T01–T12, untrusted inputs, trust/identity boundaries, mitigation/validation/owner/residual risks and approvals |
| [ADR 0002](../decisions/0002-source-reuse.md) | Conditional pinned OctoCAT source/layout, file/asset permission and notice gate; original license remains owner decision |
| [ADR 0003](../decisions/0003-persistence.md) | Local SQLite/one writer/retained volume; cloud Azure SQL, separate migration identity, measured restore targets and compatible rollback |
| [ADR 0004](../decisions/0004-agent-execution-permissions.md) | Existing assistant/gh-aw/SRE surfaces, no custom framework, read/propose/execute/inference/write separation, bounded tools and single-use approval |
| [ADR 0005](../decisions/0005-delivery-identity.md) | Actions/ACR/ACA/Bicep/OIDC, protected trusted releases, exact subject discovery, narrow role design and no inherited Owner role |
| [ADR 0006](../decisions/0006-observability.md) | Journey/dependency signals, redaction/cardinality/retention, Azure Monitor target and purposeful tracing |
| [Validation strategy](../validation-strategy.md) | V01–V18 application/agent/security evaluations, SLIs/SLOs/error budgets, release gates, severity/recovery and all eight demonstration scenarios |
| [Source register](../source-assessment.md), [notices](../../THIRD_PARTY_NOTICES.md) | Authoritative pinned rights recheck, explicit adoption/attribution decisions and outstanding owner gates; no copied code/license text |
| [M2 handoff](../milestones/m2-scope.md) | Exact conditional source/layout, Node 24 selection/pinning gate, local ports/data/contracts, automated tests, safe local fault exercise and ten acceptance criteria |
| [README](../../README.md), [guidance](../../AGENTS.md), [roadmap](../roadmap.md), [M1 scope](../milestones/m1-scope.md), [checker](../../scripts/check_repository.py) | Current stage/links updated, milestone boundaries preserved, local anchor/catalogue consistency checks added |

## Eight M1 acceptance criteria review

| Criterion | Design review result | Evidence / limitation |
| --- | --- | --- |
| M1-A1 | PASS — design alignment | Charter/requirements/matrix and exact brief roadmap; no runtime promotion |
| M1-A2 | PASS — specified, unexecuted | J01–J06, price example 31995, invalid/empty/dependency cases, FR/NF targets and validation IDs |
| M1-A3 | PASS — design only | Six diagrams plus local/container/Azure/internal API, data/trust/config/identity contracts |
| M1-A4 | PASS — planned controls | Twelve STRIDE threats mapped to validations, separate permissions, bounded actions and safe failures; no enforcement claim |
| M1-A5 | PASS with explicit allowed blocker | Five focused ADRs; rights/original-license choices explicitly blocked with owner and M2 deadline; other deferrals have owner/stage |
| M1-A6 | PASS — evaluation design | V01–V18, all eight demonstration scenarios, wider SRE responsibilities, SLO/error-budget/restore targets and negative cases |
| M1-A7 | CONDITIONAL — handoff complete, permitted-source gate open | M2 source/layout/runtime/data/journey/test/persistence contracts are precise; no legally cleared revision has been established, so source import is not ready |
| M1-A8 | PASS — documentation checks | Local links/anchors, catalogue/roadmap consistency, Mermaid syntax and Git whitespace/boundary review passed; results below |

The design package is delivered. **Do not read M1-A7 as an unconditional pass or
M2 import authorization.** Its requirement for a permitted source cannot be proven
from current evidence. M1-A5 explicitly allows a documented licensing blocker;
M1-A7's implementation-readiness gate stays conditional until that blocker is
resolved. No permission or owner approval has been invented to close it.

## Outstanding decisions and risks

| ID | Decision / risk | Owner and due stage | Effect / default |
| --- | --- | --- | --- |
| D01 | S01 whole-workload/file/asset license or authoritative permission | Repository owner before M2-A1 | **Blocks import/install/execution**; API MIT metadata alone insufficient; alternative source needs updated ADR |
| D02 | License for original project material | Repository owner before M2 distribution/import integration | MIT recommended, no LICENSE issued; do not relicense upstream |
| D03 | Exact patched Node 24/npm and container base digests, native SQLite | M2 implementer before install/build | Major selected; host Node 22.17.1 is not compatibility evidence; record exact toolchain before execution |
| D04 | Azure SKU/region/private connectivity cost, exact OIDC subject/roles, protection entitlement and Entra API auth | Repository owner before M3/M4 execution | No cloud scope or cost approval assumed; fail closed, no public SQL/anonymous writes/Owner pipeline fallback |
| D05 | Supported gh-aw engine/auth/entitlement and paid-use ceiling | Repository owner before M5 | No inference or repository output integration until independently verified |
| D06 | SRE Agent read scopes/service availability, actual connector/assignment and executor semantics | Repository owner before M7/M8 | Read-only investigation and human handoff are default; no autonomy claim |
| D07 | Telemetry SDK/exporter, actual retention/cardinality/ingestion costs | Repository owner before M6 | Keep purpose/limits; selected targets not proven configuration |
| D08 | Measured SLO/latency/RPO/RTO and improvement baselines | Owner/implementer in M6/M9 | Numerical design goals only; no 28-day, restore or savings achievement claim |

Historical lab artifacts remain inaccessible per M0 and have not been revalidated.
Cloud SQL adapter, auth/private networking and operational costs add M4 work; if
cost/compatibility fails, revise the ADR before deployment rather than weaken claims.

## Validation actually performed

| Check | Result | Scope |
| --- | --- | --- |
| `python3 scripts/check_repository.py` | PASS | 26 text files, 23 Markdown files, 120 local file/anchor links; exact 13 roadmap titles and M1 catalogue references resolve |
| Mermaid parser | PASS | Seven diagrams parsed: six new architecture diagrams plus master-brief diagram; syntax check, not pixel rendering |
| Catalogue/acceptance/threat/scenario consistency | PASS | R01–R25, J01–J06/FR01–FR06, NF01–NF10, V01–V18, T01–T12, eight M1/ten M2 criteria and ADRs 0001–0006; both STRIDE surfaces/all eight scenarios covered; price/error-budget arithmetic correct |
| Checker negative probes | PASS | Isolated temporary copies reject an undefined validation ID and a broken local heading anchor; working tree not mutated by probes |
| `git diff --check` and per-untracked-file no-index checks | PASS | Tracked changes and all nine new Markdown files checked without staging; no whitespace diagnostics |
| Source/control boundary and Git review | PASS | HEAD/master brief unchanged; no tracked deletion/staging, application/cloud/agent/workflow assets or narrow credential patterns; no source import, paid inference, deployment, commits or pushes |

Mermaid parsing used temporary documentation-only tools outside the repository:
Mermaid 12.2.0, jsdom 29.1.1, host Node 22.17.1. The initial sandbox registry lookup
failed with ENOTFOUND; an approved retry installed the parser in `/private/tmp`.
No app dependencies or repository package/lockfiles were installed. Each fenced
Mermaid block was passed to `mermaid.parse` under a temporary jsdom document.
External documentation and pinned upstream evidence were read only; local checker
does not exhaustively validate all external URLs. No app, container, workflow,
inference, SQL or Azure integration tests were run; those remain future work.
The narrow credential-pattern review is not a full secret/security audit. Git's
no-index check compared each untracked file against `/dev/null`; a clean difference
may return 1, so absence of diagnostics plus the expected status was checked.

## M2 readiness and stop boundary

Architecture, security and local implementation contracts are specified. **M2 is
design-ready but source-import blocked by D01/D02**; close these before copying or
running upstream material. The exact Node/npm/base selection in D03 is an explicit
M2 setup step, not an unverified pin. All later execution needs its own scope.

Stop after M1. This review creates no application code, infrastructure, credentials,
paid inference, commits or pushes. Independent human acceptance of the design and
manual Git operations remain with the owner.
