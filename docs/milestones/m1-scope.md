# M1 scope — Product and architecture foundation

Authority: [master brief](../project/master-brief.md), sections 7–17, especially
section 16. Status: M1 design work authorized by the owner; execution evidence and
remaining source gates are recorded in the [M1 review](../evidence/m1-design-review.md).
Requirement coverage: R18, R24 and the design portions of R02–R17, R19–R25.

Outcome: a reviewable product, architecture and security design for a small
OctoCAT Supply workload and its engineering/operations lifecycle, with a precise
M2 implementation handoff. Existing M0 drafts are preserved and refined.

## Included work and expected files

| Work | M1 files (design artifacts) |
| --- | --- |
| Refine fictional team problem, scope, critical product/search/cart/pricing journeys and measurable acceptance criteria | Update `docs/project-charter.md`, `docs/requirements.md`, `docs/capability-status.md` |
| Define React frontend, TypeScript API, repository/data layer, local/container and Azure target boundaries, internal API access and configuration/dependency paths | Create `docs/architecture.md` with context/component/data-flow diagrams and trust boundaries |
| Define application and agent threats, separate read/propose/execute/inference/write permissions, safe failures and malicious-input evaluations | Create `docs/threat-model.md`; include mitigation owner, verification milestone and residual risk |
| Decide or explicitly defer workload source/import layout and rights, persistence/durability/recovery, Azure hosting/identity/release controls, workflow authentication and minimal agent integration | Create focused ADRs under `docs/decisions/`; retain ADR 0001; assess Bicep reuse and narrower deployment roles |
| Plan application, container, infrastructure, agent and operational evaluations, including all eight required demonstration scenarios | Create `docs/validation-strategy.md` with evidence classification and milestone traceability |
| Complete source/adoption/attribution decisions and create a bounded implementation handoff | Update `docs/source-assessment.md`, `THIRD_PARTY_NOTICES.md`, `docs/milestones/m2-scope.md`; create `docs/evidence/m1-design-review.md` when M1 is actually reviewed |

## Architecture decisions to resolve or explicitly defer

- **Source and rights:** select a permitted workload revision; establish code,
  images, docs and branding rights separately; choose the owner's license and
  notice/import-manifest approach. Unresolved rights block source copying in M2,
  but do not block writing the M1 design.
- **Persistence:** decide local SQLite suitability and cloud durability requirements;
  cover concurrency, migrations, replacement, backups, restore objectives and
  rollback data integrity. Do not inherit ephemeral lab storage as durable design.
- **Azure and identity:** select hosting and internal API topology, scope OIDC and
  runtime identities, separate deployment from permission administration, assess
  Bicep reuse, and define cost/region/teardown gates. Reassess the lab Owner role.
- **Agents and workflows:** separate triage/development/review/maintenance/SRE/
  remediation coordination/recovery verification responsibilities without requiring
  separate services. Assess supported gh-aw inference authentication independently
  of repository writes; M5 will prove execution. No custom multi-agent framework
  without a concrete requirement.
- **Operations:** define dependency-aware health, critical journey SLI formulas,
  proposed SLO windows/targets and error-budget release implications; identify the
  actor authorized to repair and the independent recovery verifier. Runtime proof
  belongs to later milestones.
- **Handoffs and extensions:** specify duplicate handling and unsupported-tool or
  human fallbacks; keep Claims Processing separate and multi-cloud/alternative
  pipelines optional after the Azure core. Federation PRs are discovery inputs,
  not an adoption decision.

Each deferral needs a rationale, owner/decision milestone and affected acceptance
criteria. Close decisions required by M2 before starting its implementation.

## Acceptance criteria

| ID | Pass condition | Evidence |
| --- | --- | --- |
| M1-A1 | Charter, requirements and capability matrix agree with the master brief and corrected M0–M12 sequence | Design review with section/R-ID/milestone traceability; no runtime capability promoted by documentation alone |
| M1-A2 | Critical product, search, cart, pricing and API-dependency journeys have measurable acceptance/error criteria | Requirements and architecture traceability; no invented historical functionality or savings claims |
| M1-A3 | Architecture shows components, data flow, trust boundaries, local/container and Azure contexts, and internal API boundary | Architecture diagrams and configuration/identity contracts, labelled design only |
| M1-A4 | Threat model covers application and agent misuse, prompt injection, exfiltration, tool validation, read/propose/execute separation, bounded execution and safe permission failures | Threat → mitigation → planned validation mapping, including distinct inference/write access and protected releases |
| M1-A5 | Source/asset rights, attribution and original-license choices are decided or explicitly blocked with a resolution owner; ADRs address persistence, hosting, identity, workflow authentication and minimal orchestration | Decision records with alternatives, trade-offs, consequences and dated source evidence; M2-critical decisions closed before import |
| M1-A6 | Validation strategy maps all eight brief scenarios and wider operational responsibilities to milestones | Application/agent tests, evidence quality, independent review/recovery, negative cases, SLO/error-budget and recovery-objective plans |
| M1-A7 | M2 handoff specifies permitted revision/layout, runtime selection, synthetic data, working journeys, meaningful tests, local/container setup and persistence/reset criteria | Reviewed `m2-scope.md`; remaining blockers stated; no M2 implementation counted as M1 |
| M1-A8 | Design review and local documentation/link/consistency/whitespace checks pass without source import or runtime changes | M1 review record and check output; no credentials, paid inference, cloud provisioning, deployment, commits or pushes by the agent |

## Stop condition

M1 ends with reviewed design, decisions and an implementable M2 scope. Source import,
application setup/build/tests, container execution and fault reproduction belong to
M2. CI/image/IaC implementation belongs to M3; Azure deployment to M4; successful
agentic maintenance/inference to M5. This authorization stops after M1; M2 source import/implementation is not authorized.
