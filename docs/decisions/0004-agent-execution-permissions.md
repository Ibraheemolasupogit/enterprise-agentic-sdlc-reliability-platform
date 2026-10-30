# ADR 0004 — Existing agent surfaces with separate authority

Date: 2026-10-30. Status: accepted design; integrations unverified.
Requirements: R03, R09–R10, R12, R19, R24–R25. Owner: repository owner.

## Decision

Use the existing coding-assistant surface for bounded engineering tasks, GitHub
Agentic Workflows (gh-aw) as the M5 maintenance candidate, and actual Azure SRE
Agent for M7 investigation. No custom orchestration framework, always-on agent
service or separate service per role is justified. Deterministic CI handles
build/test/release; an LLM interprets evidence and proposes work.

Roles have distinct contracts even when one interface hosts several roles:

| Role | Read | Propose/output | Execute boundary |
| --- | --- | --- | --- |
| Triage | Sanitized issue/context | Classification, missing information, cited next step | No deploy, shell or permission grant |
| Development | Scoped repository/files/tests | Local diff and tests; branch/PR proposal | Edit authorized paths; owner commits/pushes manually |
| Review | Diff, requirements, independent check results | Findings and unresolved risk | Cannot self-approve or merge its proposal |
| Maintenance | Bounded repository context | Validated deduplicated issue/comment via restricted output | Separate output job; no cloud identity or arbitrary writes |
| SRE investigation | Time-bounded telemetry/config/release reads | Impact, timeline, hypotheses with confidence | Read-only scope; no repair identity |
| Remediation coordination | Finding, approved runbook/actions | Exact target/preconditions/action/expiry/rollback | Human approval before a narrowly scoped deterministic executor |
| Recovery verification | Fresh signals after action | Independent journey/data outcome | Read/test only; no mutation except approved synthetic probe cleanup |

Issue text, repository files, logs, tool output and generated code are untrusted
data. They cannot expand scope, change trusted instructions, inject commands or
grant permissions. Tool calls validate schema, allowlisted target/path/action and
output size; never construct shell commands from issue/log text. Redact tokens and
personal identifiers before model input. Default deny external network/tool access.

## Limits and approvals

Initial design limits per maintenance/investigation task: 10 minutes wall time,
20 tool calls, at most 2 retries per read with backoff, one output issue/comment,
no recursive delegation. Paid use also needs an approved currency/usage ceiling
and kill condition; no invented token-to-cost equivalence. Hitting any limit stops
execution, records partial evidence and escalates; no fallback credential search.

Approval record binds actor, environment, target IDs, incident, exact action or
artifact/config diff, preconditions, expiry (15 minutes), single execution,
maximum duration/retries and verification/rollback criteria. Changed targets,
expired approval or stale preconditions require a new decision. Operational
mutation is off by default; broad/destructive access changes require separate
owner review. An agent output is never approval.

gh-aw's [execution model](https://github.com/github/gh-aw/blob/c8152951950bbaf0d6205e02c51efd9ac5ab0b1a/README.md)
separates reasoning from scoped safe outputs. Select/pin a supported engine and
authentication mechanism in M5 after checking current documentation/entitlement;
do not assume repository `GITHUB_TOKEN` grants inference. Inference identity,
repository output identity and Azure operational identity remain separate.
Authorization failure yields no write and a human-readable failure record. A
compiled workflow or empty successful run does not close C7.

## Deferred integration decisions

Exact gh-aw engine/version/auth and paid-use cap: owner, before M5, affects R19.
Actual SRE Agent read scopes, region/cost and connector/assignment support: owner,
before M7/M8, affects R09/R12. Default handoff is human-created issue/assignment
from a reviewed packet if native integration is unsupported. Recheck dedup/output
rules and untrusted-input isolation before enabling any write integration.

Alternative custom multi-agent service is deferred unless these contracts cannot
be met. Separation is enforced by tools and identities, not role names/prompts.
