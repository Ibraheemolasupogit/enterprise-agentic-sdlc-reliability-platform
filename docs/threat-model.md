# Application and agent STRIDE threat model

Status: **Design only**, M1, 2026-10-30. Authority: master brief sections 10–12.
Scope: [architecture](architecture.md), [requirements](requirements.md),
[ADRs 0002–0006](decisions/0002-source-reuse.md). All mitigations below are planned;
none is claimed enforced. Repository owner owns each risk/approval until a named
operator is assigned. Validation IDs refer to [validation strategy](validation-strategy.md).

## Assets, inputs and trust boundaries

Protect source/release integrity, synthetic cart/data integrity, availability,
cloud/repository identities, inference budget and trustworthy evidence. No real
customer, financial or Claims Processing data is admitted.

Untrusted inputs include browser/query/body/cookie/cart IDs, forwarded headers,
dependencies/images, pull requests, issue/comments, repository instructions,
telemetry/configuration descriptions, tool output and model-generated code/text.
Treat a tool response as data even when it contains an instruction or URL.

| Boundary | Authority that must not be inferred from input |
| --- | --- |
| Browser → frontend/API | A cart ID, price, proxy header or loopback test is not a cloud user identity |
| API → repository/DB | Valid HTTP is not permission to run SQL/DDL or reset arbitrary files |
| Fork/issue/repository → agent/runner | External content cannot grant tools, secrets, network or trusted workflow status |
| Reasoning job → output adapter | A proposal cannot publish arbitrary content or choose wider repository permissions |
| CI → registry/Azure/Entra | Build success does not grant deployment, federation or role administration |
| Investigator → executor → verifier | Diagnosis is not approval; execution success is not recovery proof |

## STRIDE assessment

S = spoofing, T = tampering, R = repudiation, I = information disclosure,
D = denial of service, E = elevation of privilege. High risks can change data,
authority, cost or releases; Medium risks primarily impair diagnosis/local demos.

| ID / surface | STRIDE / initial risk | Concrete threat | Planned control and validation | Residual risk / decision stage |
| --- | --- | --- | --- | --- |
| T01 application | S / High | Attacker forges cart/principal headers or calls internal API from another container | Local M2 loopback/synthetic boundary; M4 Entra issuer/audience/expiry/role validation, ignore forged principal headers; V08/V09 | Local cart IDs are not authentication; cloud mutation blocked until M4 auth passes |
| T02 application | T / High | SQL injection, browser-supplied price, conflicting cart edits or changed migration corrupt data | Parameterized SQL, schema/quantity/ID validation, server prices, atomic writes, checksummed migrations, fixture isolation; V03–V05/V08 | SQLite and SQL dialects need separate contract tests; M2/M4 |
| T03 application | R / Medium | Unrecorded reset/release prevents attribution of data loss | Request/release/config IDs, migration log, explicit reset path/flag, actor/time/digest audit; V05/V14/V18 | Logs are not tamper-proof evidence; retain reviewed summaries; M2/M3 |
| T04 application | I / High | Errors/logs/images expose tokens, SQL credentials, personal data or secret files | Safe errors, header/body redaction, synthetic-only fixtures, image/secret scanning, no browser DB access; V08/V18 | Redaction can fail on new fields; negative fixtures required; M2/M3/M6 |
| T05 application | D / High | Large queries/bodies, cart flooding, DB locks or recursive health checks exhaust capacity | Query limit <=100, search <=100 characters, body <=16 KiB, bounded timeouts, single local writer, non-recursive health; V07/V08/V17 | Local unauthenticated demo is not internet-hardened; rate/identity controls before M4 |
| T06 application | E / High | Runtime identity gets DDL/Owner rights or public admin/reset routes | Separate runtime/DDL/bootstrap/deploy identities, no cloud reset route, internal ingress plus auth, restricted release path; V09/V14 | RG bootstrap Contributor remains powerful; owner-only time-bound bootstrap; M3/M4 |
| T07 agents | S / High | Malicious issue impersonates owner or spoofs telemetry/tool results to authorize repair | Trusted scope/identity outside issue text, cited source/time checks, independent evidence and explicit human approval; V10–V13 | Authenticated contributors can still submit malicious data; M5/M7/M8 |
| T08 agents | T / High | Prompt injection edits workflows, substitutes artifact, poisons retrieved context or tool arguments | Context as data, path/action/target allowlists, no interpolated shell, pinned artifacts, protected trusted workflows; V09/V11/V14 | Prompts alone are insufficient; enforce outside model; M3/M5/M8 |
| T09 agents | R / High | Agent claims success without actual output or hides watchdog repair | Record tool/run IDs, principal, approval, action/diff and fresh verifier result; distinguish design/simulation/historical; V10/V14/V15 | Provider logs may expire; retain sanitized result summaries; M5–M9 |
| T10 agents | I / High | Issue/log asks agent to print secrets or send them to an external endpoint | Secret-free context, deny-by-default egress/tools, redacted bounded input/output, no token discovery fallback; V11/V12/V18 | Allowed destinations and external models still require data-scope review; M5 |
| T11 agents | D / High | Recursive delegation, retries, duplicate issues or unbounded inference consume budget | 10-minute/20-call bounds, <=2 read retries, one output, dedup key, currency ceiling and kill condition; V12/V13/V17 | Billing may lag; budget alerts are not caps; owner authorization before M5 |
| T12 agents | E / High | Model converts read-only diagnosis into deploy, reuses approval or uses repository token for broader access | Separate read/propose/execute/inference/write identities, single-use target-bound 15-minute approval, reject changed/stale/expired requests; V09/V12–V14 | Supported integration/permission enforcement not yet tested; fail closed; M5/M7/M8 |

## Human controls and review gates

The owner approves task scope and source rights before copying; a human reviews
the diff and independent test/security evidence before manual commit/push. Release
approval binds exact trusted SHA/image digests/configuration/schema. A changed
artifact or target invalidates approval. Agent review cannot substitute for human
acceptance; test results created by the proposer require independent execution.

Read telemetry with scoped access; evidence-backed repair suggestions have no
mutation authority. Issue creation is a separate sanitized/deduplicated output
permission. Runtime changes require a bounded action record; destructive restore,
data-loss acceptance and broad identity changes require a separate owner decision.
No identity/credentials or paid-inference fallback is created on authorization
failure. Unavailable tools produce an explicit handoff with limitations.

## Acceptance and remaining risk

M2 must prove V01–V08/V18 on the local synthetic boundary before calling it locally
tested. M3/M4 must prove identity, supply-chain and cloud-auth controls before
deployment. M5–M9 test agent attacks and action/recovery boundaries with expected
denials. Do not enable a control merely because its prompt describes it.

Open blockers: source rights/original license (owner before M2), actual Entra/OIDC
claims/roles/protection entitlement/private SQL costs (owner before M3/M4), supported
inference identity and spend cap (owner before M5), SRE/connector capabilities and
safe executor semantics (owner before M7/M8). Each is tracked in the
[design review](evidence/m1-design-review.md). No production-readiness, compliance
certification or universal prompt-injection immunity is claimed.
