# Capability and status matrix

Authority: [master brief](project/master-brief.md), sections 9, 16–17. Assessed on
2026-10-30. Use its states: **Planned, Implemented, Locally tested, Cloud verified,
Simulated, Design only, Blocked, Retired**. Historical validation is a separate
evidence classification, not current repository verification. No application or
agent execution is verified here. M0 document checks do not complete M1.

| Capability | Current repository status | Evidence or gap | Target |
| --- | --- | --- | --- |
| Independent foundation/source assessment | Design only; document checks passed | [M0 assessment](evidence/m0-assessment.md); no runtime implementation | M0 |
| Product/architecture/threat model/ADRs | Planned; initial M0 drafts exist | [M1 proposal](milestones/m1-scope.md); architecture and threat model absent | M1 |
| OctoCAT Supply application/container baseline | Blocked for import; otherwise Planned | [Source rights](source-assessment.md); no code, runtime, tests or data here | M2 |
| Agent-assisted development/review | Planned | Requirement-to-change/tests/review evidence needed; no separate framework assumed | M2–M3; M8 |
| Secure delivery, images and Azure IaC/identity | Planned | No workflows, images, scans or infrastructure validation | M3 |
| Personal Azure deployment/internal API/durability | Planned | No cloud deployment; persistence and identity require M1 ADRs | M4 |
| Working agentic maintenance | Planned | C7 failure must be closed with real inference and useful output; not compilation alone | M5 |
| Telemetry and dependency-aware health | Planned | Logs/metrics/traces as justified, config/deployment annotations and API journey checks absent | M6 |
| SLIs/SLOs, error budgets, alerts, severity/escalation | Planned | Define formulas/windows/targets and release consequences; no operational baseline | M1 design; M6 |
| Incident diagnosis/management | Planned | Actual SRE Agent findings, impact/timeline, confidence, mitigation/permanent fix and postmortem needed | M7 |
| Bounded remediation and independent recovery | Planned | Approval/actor/audit and fresh recovery evidence absent | M7–M9 |
| Incident-to-PR handoff | Planned | Issue/dedup/assignment/repair/review/release/outcome integrations or fallback unverified | M8 |
| Backup/restore and recovery objectives | Planned | No durability, restore or rollback-integrity proof | M1 design; M4/M9 |
| Performance/capacity and measured improvements | Planned | No measurements or baseline; no percentage savings claim | M9 |
| Configuration drift/dependency/toil/runbook upkeep | Planned | Operational ownership, maintenance and measured toil evidence absent | M9 |
| Cost/resource hygiene | Planned | No estimate, authorized spend or teardown proof; budget alerts are not caps | M1 design; M3–M9 |
| Application/agent security and evaluation | Planned | Threat model, prompt injection/exfiltration, limits, safe failure and negative cases absent | M1 design; M2–M9 |
| Upstream integration/contribution register | Design only; source assessment started | No material adopted, contribution submitted or suitability validated | M0; M10 |
| Multi-cloud/alternative delivery modules | Planned; optional | No AWS/GCP core dependency; justify or defer after Azure core | M11 |
| Portfolio/video walkthrough | Planned | No end-to-end verified demonstration or video | M12 |
| Event challenge sequence as implementation roadmap | Retired | Replaced by master brief section 16; historical evidence preserved | M0 |

Claims Processing is outside this project's scope and remains a separate portfolio
repository. Shared patterns may be referenced without introducing its application,
data or runtime dependency here.

## Historical evidence classification

| Historical capability | Brief-reported result | Current verification and target |
| --- | --- | --- |
| Personal rehearsal assets | Cart/discounts, tests, Actions/scanning, containers, ACA/Bicep/OIDC, health/KQL reportedly existed | Assets unavailable; no current implementation or reuse proven |
| C1–C6 | Validated historically | [References preserved](historical-reuse.md); lab returned 404; do not claim current Cloud verified status |
| Wrong-port SRE experiment | Agent diagnosed API_PORT 443→444; watchdog rolled back; agent sampled recovery | Historical only; reproduce locally/container-first in M2 before authorized M7 live experiment |
| C7 maintenance | Implemented/compiled/pushed historically; inference authorization failed; no useful triage comment | Successful execution unverified; M5 must prove genuine inference and useful actual output |

Every future capability record must include version, environment, date, test/run,
result, limitation and linked evidence. A simulation or design must keep its label;
sampled recovery is not proof of full availability or autonomous remediation.
