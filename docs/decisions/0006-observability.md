# ADR 0006 — Journey signals before telemetry volume

Date: 2026-10-30. Status: accepted design; no telemetry implementation.
Requirements: R07–R11, R20, R25. Owner: repository owner.

## Decision

Use structured JSON application/proxy logs and bounded request metrics locally;
Azure Monitor/Log Analytics and Application Insights are the cloud target. Prefer
supported direct instrumentation/export in M6; no extra collector service until a
specific routing/control requirement needs it. OpenTelemetry JS is a candidate,
not an installed dependency. Reassess SDK/exporter versions and licensing in M6.

Generate/validate a request ID at the edge, carry it through API/repository and
responses, and correlate release SHA, image digest, revision and configuration
version with events. Treat caller-provided IDs as untrusted: bounded length/charset,
replace invalid values. Do not place bodies, tokens, cookies, raw queries,
cart/customer data or connection strings in telemetry. Log route templates, status,
duration, safe error code, service/environment and trace/request IDs. IDs are not
metric labels; cap cardinality and text size.

Separate startup/liveness from readiness. Process liveness must not restart the
whole service on a transient DB outage. API readiness checks DB/schema with a
1-second timeout; frontend readiness traverses its configured API path with a
2-second timeout. No recursive frontend/API health dependency. Synthetic product,
search and cart probes exercise the public frontend path and actual dependencies;
static `/` health cannot satisfy journey availability. The platform permits custom
HTTP dependency checks; see [ACA health probes](https://learn.microsoft.com/en-us/azure/container-apps/health-probes).

Use error counts/durations and explicit synthetic results without telemetry sampling
for SLI denominators. Traces may be sampled for diagnosis, initially 10% successes
with failure detail retained where supported; never compute availability from
sampled traces alone. Missing probe results count as unavailable under the
[measurement rules](../validation-strategy.md#reliability-objectives).

## Operations and cost

Initial design retention: 30 days redacted diagnostic logs/traces; 90 days
aggregate incident/release/SLO summaries; retain sanitized selected portfolio
evidence in the repository separately. Access is emit-only for runtime, read-only
for investigator, administrative changes for the owner. Validate Azure retention
minimums, ingestion limits and prices in M6 before approval; reduce collection or
revise targets explicitly rather than silently dropping required evidence.

Owner receives an actionable alert with affected journey/environment, recent
release/config, evidence query/time range, severity and runbook. Define SLO/error
budget and acknowledgement/escalation in the validation strategy. User-facing
checks drive incidents; telemetry pipeline health has its own alert. Fresh
independent probes after repair establish sampled recovery, not a claim of full
availability. Record who repaired, what changed and what remains uncertain.

Alternative full tracing/collector stack is rejected initially for cost/complexity.
Dashboard screenshots without raw query windows/denominators are insufficient
evidence. M2 needs local health/correlation contracts; cloud dashboards/export,
alerts and measured SLOs belong to M6 and incidents to M7–M9.
