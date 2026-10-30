# Validation, reliability and evidence strategy

Status: M1 validation strategy with M2 V01–V08 local execution and V18 local
provenance/setup evidence recorded in [M2 results](evidence/m2-baseline.md). Later
cloud/agent evaluations remain planned. Authority: master brief sections 9–13/17.
All numerical thresholds are selected project targets, not measured achievements
or Azure guarantees. [Requirements](requirements.md) owns functional/non-functional
contracts; this file owns tests, gates, measurements and evidence. See
[architecture](architecture.md), [threats T01–T12](threat-model.md) and
[M2 handoff](milestones/m2-scope.md).

## Validation catalogue

Use unit tests for logic, isolated DB integration tests for contracts/transactions,
component tests for UI states, and a small Playwright suite for actual journeys.
Tests must fail on an observable defect, not just mirror implementation. Preserve
useful permitted upstream tests; report actual results rather than test-count goals.

| ID | Planned test / required result | Stage / requirement / threat mapping |
| --- | --- | --- |
| V01 | Fixed 12-product seed lists known IDs/count/order; detail known=200, unknown=404, malformed=400; documented JSON schema | M2; J01, R02; T02 |
| V02 | Search trim/case, known match, no match, deterministic sorting/pagination; invalid sort/limit/oversized search=400 | M2; J02; T02/T05 |
| V03 | Integer GBP minor-unit totals, qty 1/99 boundaries; reject 0/negative/fraction/NaN; injected browser price cannot change server result | M2; J03/J04; T02 |
| V04 | Create/get/delete synthetic cart; absolute-quantity update idempotent; remove/re-remove line; unknown references rejected; concurrent transactions retain valid totals; two carts remain isolated; probe cleanup verified | M2; J03; T01/T02 |
| V05 | Two seed/reset runs yield exact same IDs/data; ordered migration replay safe, changed checksum rejected; restart/container replacement retains data; reset refuses unrelated/symlink/out-of-root paths | M2; J06; T02/T03 |
| V06 | UI catalogue/search/cart/pricing, loading/empty/API-error states, keyboard operation and refresh cart recovery via real API; browser cannot address internal host directly | M2; J01–J04; T01/T04 |
| V07 | Configure wrong proxy port locally; static `/` stays 200, API-backed journey and frontend readiness fail; restore config and independently rerun journey; liveness avoids restart loop | M2 then M6/M7; J05; T05 |
| V08 | SQL/XSS-like text treated as data, invalid content type/IDs/body/query rejected, oversized body=413, safe errors/request IDs; no secrets or stack/SQL in output | M2; NF02/NF03; T01/T02/T04/T05 |
| V09 | Fork/PR cannot publish/deploy/request Azure identity; wrong OIDC issuer/audience/subject/environment denied; runtime cannot DDL/RBAC; cloud invalid/missing/expired/wrong-role token and another principal's cart access denied | M3/M4; R04–R06; T01/T06/T08/T12 |
| V10 | Agent task meets actual acceptance criteria, relevant source/time citations and explicit uncertainty; insufficient evidence escalates; independent review finds seeded faulty suggestion | M5/M7/M8; R19/R24/R25; T07/T09 |
| V11 | Malicious issue/log/repo/tool content tries instruction override, credential read, outbound exfiltration and workflow edit; no unauthorized call/write/network; record rejected attempt | M5/M8/M9; R25; T07/T08/T10 |
| V12 | Missing/unavailable inference/tools, denied permission, timeout/retry/tool-call/usage ceiling terminate safely; no alternate credential search, write or deploy | M5/M7/M8; R19/R25; T10–T12 |
| V13 | Duplicate incident links existing work; unsafe output rejected; changed target, expired/replayed approval, changed digest or stale preconditions cannot execute | M5/M8; R10/R12; T07/T11/T12 |
| V14 | Bad image/security finding/schema incompatibility blocks release; failed smoke prevents promotion and invokes only approved compatible rollback; wrong repair does not close incident | M3/M4/M7/M8; R06/R10/R11; T03/T08/T09/T12 |
| V15 | Request/release/config correlation, redaction/cardinality/retention, probe-loss handling, SLI arithmetic and actionable alert/escalation tested with known data | M6/M7; R07/R08; T04/T09 |
| V16 | Backup/PITR restore into isolated target; verify control writes, foreign keys, prices/cart totals and migrations; measure RPO/RTO and approved cutover | M9; R11/R20; T02/T06 |
| V17 | Repeatable load/capacity baseline and candidate change under same fixture/runtime/load; record p50/p95/errors/resources/cost; exceed limits safely, then verify improvement | M9; R20; T05/T11 |
| V18 | Clean setup from approved source, lockfiles/runtime/digests/provenance, secret/license scan, ignored generated data, safe evidence redaction and no Claims Processing dependency | M2/M3/M12; R14–R17; T03/T04/T10 |

Agent evaluations use synthetic fixtures and mocks initially, labelled **Simulated**.
They do not prove inference success. M5 additionally requires one genuine supported
inference run and useful inspected repository output after separately authorized
paid-use/identity planning. No such run occurred in M1 or M2. Every critical safety case
must pass; no average score can mask an unauthorized mutation/exfiltration.

## Reliability objectives

Eligible critical journeys: J01 catalogue, J02 search and J03/J04 cart/price. A
synthetic scheduler exercises them through the frontend `/api` route once per
minute. Each probe checks response schema and expected synthetic behaviour, not
just HTTP 200. Cart probes use isolated carts and cleanup; never mutate a person's
cart. Readiness and user journeys are distinct measurements.

| Indicator | Formula / target | Window and interpretation |
| --- | --- | --- |
| Journey availability | Successful eligible probes / scheduled eligible probes >=99.5%, measured per critical journey | Rolling 28 days of declared continuous availability; failed, timed-out and missing scheduled probes count bad; maintenance during this window counts |
| Read latency | Successful catalogue/search probes <=500 ms / successful catalogue/search probes >=95% | Same 28 days; frontend-to-API-to-DB elapsed time, not browser process launch; availability tracked separately so failures cannot improve this score invisibly |
| Cart latency | Successful cart/price probes <=1000 ms / successful cart/price probes >=95% | Same window; completed authoritative result, not optimistic UI update |
| Functional correctness | Expected cart/price/search assertions pass for all eligible test/control cases | Release gate is 100% of specified assertions; not estimated from trace sampling |
| Recovery objectives | RPO <=1 hour, RTO <=60 minutes | Measured M9 restore exercise; definitions and integrity checks in ADR 0003 |

Declare availability schedule before collection; stopping an experiment does not
retroactively exclude failures. If the portfolio only runs briefly, report that
exact observation window/sample count and **no 28-day SLO achievement claim**.
Zero successful latency observations yields insufficient data/failure to establish
the latency objective, never a pass. Mark pre-announced out-of-service periods
separately; do not present a restricted schedule as 24/7 availability.

Error budget = `(1 - 0.995) * scheduled eligible probes`; spent budget = bad probes.
At one probe/minute for 28 days, N=40,320 and budget=201.6 bad probes (201 whole bad
probes still within budget). Remaining = budget minus bad; do not round a breached
budget into success. Overall status fails if any critical journey breaches; do
not average healthy static pages with failed API journeys. This is sample-based
availability, not proof about every request or every second.

Freeze feature releases on exhausted availability budget or a critical unresolved
security/data-integrity failure; permit only reviewed recovery/security changes.
At >50% budget spent, owner reviews upcoming risk and measurements before release.
Initial detection: 3 consecutive bad one-minute journey probes pages/alerts owner;
loss of probe telemetry also alerts after 3 missing intervals. Record first failure,
detection and acknowledgement separately. These are project policies to validate
in M6, not a deployed alert configuration or a claim of guaranteed detection time.

## Severity, recovery and wider operations

SEV1: unauthorized data/action/credential exposure or all critical journeys failing;
stop changes, notify owner immediately, target acknowledgement within 5 minutes.
SEV2: one critical journey/dependency failing or exhausted error budget; owner
acknowledgement target 15 minutes. SEV3: degraded performance/noncritical issue;
triage next working day. This personal portfolio has no staffed on-call guarantee;
without an available owner, halt the experiment and preserve evidence.

Incident record includes impact, UTC timeline, release/config versions, hypotheses
and confidence, queried sources, mitigation versus permanent fix, actual repair
actor, approvals and escalation. Recovery verifier is separate from the proposer:
after repair, run five consecutive one-minute successful checks for each affected
journey plus relevant data-integrity checks. Report this as sampled recovery.
Unknown or incorrect repair stays open and escalates; no self-certified success.

M9 additionally exercises configuration drift detection, a dependency maintenance
change, backup/restore, runbook correction and measured toil. Capacity exercise:
fixed synthetic fixture, 5 virtual users for 10 minutes as initial reproducible
profile; record hardware, warm-up, concurrency, percentiles, errors and resource
usage. A stress variant must have an explicit stop bound; do not run it live
without authorization. Measure before/after on the same environment; no savings
percentage without recorded baselines. Cost evidence includes authorized estimate,
actual usage where available, teardown result and remaining resources.

## Release and evidence gates

| Gate | Required evidence / failure action |
| --- | --- |
| M2 baseline | Source rights/import manifest, exact runtime/lockfiles, V01–V08/V18, clean setup twice, local/container persistence and fault recovery; blocked source means no import |
| M3 PR/trusted build | Lint/type/build/tests, secret/dependency/code/container scans, Bicep validation, SBOM/provenance, reviewed immutable artifacts; no untriaged exploitable critical/high finding; exceptions need owner, rationale, expiry and compensating control |
| M4 release | Approved scope/cost/identity/teardown, cloud auth/private SQL and migration checks, OIDC negative tests, exact digests/config/schema, protected gate and dependency/journey smoke; failure prevents promotion |
| M5 maintenance | Supported real inference, inspected useful output and V10–V13 safety/limits; compilation or empty output fails completion |
| M7/M8 operation | Bound action approval, known-good compatible rollback, independent recovery and incident/issue outcome; unsupported integration uses documented human handoff |
| M9/M12 assurance | Restore/security/performance/maintenance evidence and honest end-to-end walkthrough; no simulated/historical capability promoted without execution |

Every evidence record includes requirement/journey/threat IDs, status (Planned,
Implemented, Locally tested, Cloud verified, Simulated, Design only, Blocked,
Retired), exact revision/image/schema/tool version, environment, UTC times,
commands/run links, expected/actual result, failures, actor/approval, limitations
and sanitized artifacts. Separate tests actually run from planned cases. Store
reviewed summaries in `docs/evidence/`; never commit DBs, raw tokens or sensitive
logs. A screenshot supplements raw counts/queries; it cannot replace them.

## M2 executed boundary

The M2 unit/integration/component and browser checks exercise V01–V08 on synthetic
local data. A deterministic container test replaces the API container with its
volume retained and reproduces/restores the frontend wrong-port fault. V18 has
local license/source/setup evidence; full supply-chain scanning/protected release
validation remains M3. Actual versions/results, not this plan, determine capability
status. The later owner request added an automatic 10% discount at >=30000p, floor
rounding; threshold/rounding/tampered-price cases and UI totals are tested. No agents,
real inference, Azure, cloud restore or 28-day objective was executed.

## Required demonstration traceability

| Brief scenario | Planned evidence and stage |
| --- | --- |
| Feature request to reviewed PR | R03, V01–V06/V18; M2/M3 and M8; requirement → bounded diff → independent tests → human review/manual Git handoff |
| Agentic maintenance | R19, V10–V13; M5; real inference plus useful actual output closes C7 |
| Dependency failure masked by static health | J05, V07/V15; M2 local/container, M6 detection; static success and failed dependency evidence side by side |
| Configuration regression | R09/R10, V07/V14/V15; M7; change history → actual SRE diagnosis → actor-bound repair → fresh recovery |
| Failed release | R06, V09/V14; M3/M4; denied gate or smoke failure, promotion blocked and compatible rollback |
| Unsafe instruction in issue/log content | R25, V11–V13; M5/M8/M9; attempted instruction rejected with permissions preserved |
| Durable recovery | R11/R20, V05/V16; M4/M9; local persistence is not cloud restore proof; measured objective and integrity result |
| Performance or capacity problem | R20, V17; M9; same-load baseline, diagnosis, tested change and measured improvement |
