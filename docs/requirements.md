# Product and engineering requirements

Authority: [master brief](project/master-brief.md). Status: M2 local application contracts implemented/tested; later lifecycle
requirements remain planned or Design only as the capability matrix states.
R01–R25 remain the lifecycle requirements; the functional journeys and non-functional
contracts below refine their acceptance criteria. Actual results and limitations are in [M2 evidence](evidence/m2-baseline.md).
Existing R-IDs are retained. Targets identify where evidence belongs, not completed
implementation. Agent-assisted work and security apply across milestones.

| ID | Requirement | Target | Acceptance evidence |
| --- | --- | --- | --- |
| R01 | Establish independent foundation and source assessment | M0 | Charter, ADR, source register, roadmap, checks |
| R02 | Reconstruct a reproducible local supply-chain reference baseline | M2 | Independent original code/MIT, exact lock/runtime pins, clean container/local setup, journeys, meaningful tests and documented persistence |
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
| R17 | Protect credentials, scope and owner-controlled Git operations | All | No embedded secrets; M0/M1 have no cloud or paid-inference execution; commits/pushes performed by owner |
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
  require review at adoption time. M0/M1 had no application execution; M2 validation is recorded separately.
- Persistence decisions cover durability, concurrency, migrations, replacement,
  backup/restore and rollback integrity. Static `/` health does not prove dependency
  health. Do not claim measured gains without recorded baselines.

## Functional requirements and critical journeys

The [architecture](architecture.md) defines the proposed API contracts; these are
personal implementation targets, not a claim that the upstream already supplies
them. Validation IDs are in the [validation strategy](validation-strategy.md).

| Journey / functional ID | User behaviour and acceptance criteria | Errors / evidence |
| --- | --- | --- |
| J01 / FR01 — Catalogue | Show 12 synthetic products; known product detail and stable IDs; default page 20, maximum 100; explicit loading/empty states | Unknown ID 404, malformed ID/query 400; UI error is visible; V01/V06 |
| J02 / FR02 — Search | Trimmed case-insensitive name search; empty query restores catalogue; no match shows empty state; category filter all/feeding/play/everyday, allowlisted name/price sort with ID tie-break and pagination | Search >100 chars, invalid sort, negative offset or limit outside 1–100 rejected with 400; V02/V06 |
| J03 / FR03 — Cart | Create isolated opaque cart; add/set quantities 1–99, update without duplicate lines, remove/re-remove idempotently; refresh retains cart reference and API restart retains rows | Invalid quantities 400; unknown cart/product 404; empty cart total zero; no cross-cart leakage; V03/V04/V06 |
| J04 / FR04 — Pricing | Server computes GBP integer-minor-unit line/subtotals from canonical product prices; 2 units at 12999 plus 3 at 1999 subtotal is 31995, discount 3199 and total 28796; reject client price override | Owner-requested automatic 10% discount at >=30000p subtotal, rounding down; no coupons, stacking, tax, shipping or checkout; accessible display agrees with API, including zero/one/multiple lines; V03/V06 |
| J05 / FR05 — Dependency failure | Wrong frontend API port produces a visible API-backed journey error and failed dependency readiness, even when static `/` returns 200 | 2-second frontend readiness bound; safe error/request ID; restore port and independently confirm journey; V07 |
| J06 / FR06 — Data lifecycle | Explicit migration/seed/reset; repeat reset yields same 12 IDs/data; restart and container replacement retain data when volume retained | Changed migration checksum rejected; reset cannot escape designated local path or reach cloud; V05/V18 |

Product DTO: positive integer `id`, bounded `name` (1–120 chars), nonnegative integer
`unitPriceMinor` and `currency=GBP`. Cart requests contain product IDs and absolute
quantities; responses contain canonical price, line/subtotals, discount, cart total and currency;
request IDs are returned in response headers and JSON errors. Set maximum 100 distinct lines/cart, reject excess with a stable 400 error.
Cart transactions return authoritative results; UI applies the authoritative response and preserves the current cart on
failure. Product mutation needed by local fixture tests is not a public admin API.
Synthetic anonymous carts are not a real identity/payment/commerce system.

## Non-functional requirements

| ID | Contract / selected target | Verification and milestone |
| --- | --- | --- |
| NF01 reproducibility | Node.js 24.22.2 / npm 11.19.1; lockfiles and immutable container base digests; local Linux containers, one API process | M2 clean setup twice; V18 |
| NF02 validation/integrity | Parameterized queries, atomic cart updates, server prices, foreign keys, changed migrations refused; isolated test databases | M2 V01–V05/V08; Azure SQL contract suite separately in M4 |
| NF03 safe local exposure | Publish loopback only; same-origin proxy; body <=16 KiB; safe errors; no credentials/PII, real payments or external image calls | M2 V06–V08/V18; cloud Entra/private API/SQL required before M4 writes |
| NF04 reliability | Per-journey availability >=99.5% over declared rolling 28 days; read latency 95% <=500 ms and cart latency 95% <=1000 ms; missing probes bad | M6 measurement rules in validation strategy; short portfolio run cannot claim a 28-day pass |
| NF05 recovery | Local retained-volume restart/replacement retains rows; cloud RPO <=1 hour and RTO <=60 minutes are design targets requiring measured restore | M2 V05; M9 V16; ADR 0003 defines time/data boundaries |
| NF06 usable UI | Catalogue/search/cart keyboard operable, labelled controls and status/error messaging; useful loading/empty/failure states | M2 component/Playwright tests plus focused manual review; no full accessibility conformance claim |
| NF07 governance | Read/propose/execute/inference/write separated; task bounds 10 minutes/20 calls/<=2 read retries/one output; single-use target-bound approval expires in 15 minutes | ADR 0004; M5/M7/M8 V10–V13; paid spend cap must be separately approved |
| NF08 release integrity | Reviewed SHA/digests/schema, protected gate, least privilege/OIDC, fail-closed scan/smoke checks and compatible rollback | M3/M4 V09/V14/V18; no automated merge/deploy by inference output |
| NF09 evidence/privacy | Correlation and release/config IDs, redaction, no high-cardinality metric IDs; diagnostic retention 30 days, aggregate summaries 90 days subject to provider cost/limits | M6 V15/V18; ADR 0006; all statuses distinguish design/simulated/historical/executed |
| NF10 cost/scope | Owner-approved explicit execution scope, estimate, usage ceiling and teardown before paid/cloud actions; no AWS/GCP core dependency or custom framework without need | M3–M11 entry review; budget alerts are not caps |

M2 pins and tests Node 24.22.2/npm 11.19.1, using bundled SQLite instead of a
separately compiled native addon. This choice and release-candidate driver status
are recorded in M2 evidence. The original system Node 22 was not used as the
application baseline. Cloud reliability/performance objectives remain unmeasured.
