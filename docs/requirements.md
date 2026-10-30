# Initial requirements

Authority: [master brief](project/master-brief.md). Status: M0 requirements baseline,
aligned during closure; M1 will refine product/architecture acceptance criteria.
Existing R-IDs are retained. Targets identify where evidence belongs, not completed
implementation. Agent-assisted work and security apply across milestones.

| ID | Requirement | Target | Acceptance evidence |
| --- | --- | --- | --- |
| R01 | Establish independent foundation and source assessment | M0 | Charter, ADR, source register, roadmap, checks |
| R02 | Reconstruct a reproducible local supply-chain reference baseline | M2 | Permitted source, exact revision, clean container/local setup, journeys, meaningful tests and documented persistence |
| R03 | Track agent-assisted engineering work from requirement to human review | M2–M3; M8 | Scoped task with plan, diff, tests and review; M8 completes the incident-to-PR lifecycle |
| R04 | Automate build, test, dependency and security checks with least privilege | M3 | Passing and deliberately failing gate evidence; documented exceptions |
| R05 | Define Azure deployment and identity boundaries, budget and teardown before cloud execution | M1 design; M3 validation | Architecture/threat model, validated IaC, scoped federation and release permissions; assess Bicep reuse and narrower roles than lab Owner |
| R06 | Produce versioned artifacts and controlled Azure delivery | M3 artifacts; M4 deployment | Authorized deployment with internal API boundary, release identity, smoke result, durability decision, recovery and teardown record |
| R07 | Correlate purposeful logs, metrics and traces where justified without leaking sensitive data | M6 | Synthetic user journey correlated end to end; redaction, retention and diagnostic value checks |
| R08 | Define operational objectives, error budgets and repeatable bounded fault scenarios | M1 design; M6–M7 | Critical journey SLIs/SLO windows/targets, error-budget release implications, severity/escalation and detected incident; local wrong-port reproduction in M2 |
| R09 | Diagnose incidents with cited signals and explicit uncertainty | M7 | Actual Azure SRE Agent findings, change/config correlation, timeline, impact, hypotheses and escalation; no autonomy claim for watchdog repair |
| R10 | Require policy and human approval for bounded remediation | M1 design; M7–M9 execution | Allowed/denied/expired approval paths, bounded rollback, audit trail, incorrect-repair and unavailable-tool handling |
| R11 | Verify recovery and rollback against declared objectives | M4 procedure; M7 recovery; M9 restore | Fresh independent signals, restoration time, data integrity, backup/restore and failed-remediation rollback evidence |
| R12 | Produce actionable GitHub engineering handoffs | M8 | Structured deduplicated issue, authorized assignment or connector/human fallback, repair PR/tests/review/release and independently verified outcome |
| R13 | Package repeatable portfolio demonstrations and honest capability claims | M12 | Independent walkthrough, evidence index, limitations and teardown proof |
| R14 | Preserve provenance, notices and third-party obligations | M0–M12 | Source assessment now; file-level import/change register and retained licenses before reuse |
| R15 | Separate historical validation from current verification | M0–M12 | C1–C6 historical status retained; C7 inference unverified until execution evidence exists |
| R16 | Keep Claims Processing independent | All | No Claims Processing application, data, shared deployment or required runtime integration |
| R17 | Protect credentials, scope and owner-controlled Git operations | All | No embedded secrets; M0 has no cloud execution; commits/pushes performed by owner |
| R18 | Establish product and architecture foundation | M1 | Refined charter/requirements/capability matrix, architecture, threat model, ADRs, validation strategy and bounded M2 handoff; design only |
| R19 | Close the historical C7 gap with working agentic maintenance | M5 | Supported genuine inference and useful repository output, distinct inference/write permissions, least privilege and safe authorization failure |
| R20 | Demonstrate wider operational assurance | M9 | Backup/restore against objectives, performance/capacity measurements, drift/dependency maintenance, runbook/toil and cost hygiene evidence |
| R21 | Maintain an upstream integration/contribution register | M0 assessment; M10 collaboration | Source/change/date/rights/relevance, adoption rationale, dependencies, tests, contribution and walkthrough status; focused submission where appropriate |
| R22 | Keep multi-cloud and alternative delivery modules optional | M11 | Justified distinct extension after Azure core validation, independent identities/negative tests, cost/teardown and no AWS/GCP core dependency; or documented deferral |
| R23 | Cover all eight required demonstration scenarios | M1 plan; M2–M12 evidence | Feature-to-reviewed-PR, real maintenance, masked dependency failure, config regression, failed release, unsafe issue/log input, durable recovery and performance/capacity evidence |
| R24 | Separate agent responsibilities and minimize orchestration | M1 design; later implementation | Triage, development, review, maintenance, SRE investigation, remediation coordination and recovery verification contracts; no custom framework without a concrete requirement |
| R25 | Evaluate application and agent behaviour | M1 plan; M2–M9 execution | Unit/integration/API/component/E2E/container/IaC/security/migration checks; evidence/uncertainty, malicious input, duplicates, permissions, unavailable inference/tools, time/usage limits and escalation |

## Engineering constraints

- A clean setup must use documented runtime versions, lockfiles and synthetic data.
- Separate read, propose and execute permissions. Inference access and repository
  writes are different capabilities; minimize tools and framework dependencies.
- Cloud resources and paid inference require explicit scope, identity plan, cost
  estimate and teardown approach before execution. Budget alerts are not spending
  caps. Prefer short-lived federation where supported.
- Treat telemetry, repository text, prompts, and tool responses as untrusted input;
  assess prompt injection, exfiltration, tool/input validation and unauthorized tool
  use from the M1 threat model through later execution gates.
- A successful API call alone does not prove correct diagnosis, successful
  remediation, recovery, or safe inference. Record observable outcomes separately.
- Native dependencies, images, npm packages, action versions and transitive licenses
  require review at adoption time. No dependency install or runtime verification
  occurred during M0.
- Persistence decisions cover durability, concurrency, migrations, replacement,
  backup/restore and rollback integrity. Static `/` health does not prove dependency
  health. Do not claim measured gains without recorded baselines.
