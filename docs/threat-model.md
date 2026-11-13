# Application and agent STRIDE threat model

Status: assessed 2026-11-10 with M2/M4B local and hosted CI evidence; real provider,
SQL/Azure and agent controls remain unverified. C1 SQLite contracts are locally
tested; C3 client/crypto behavior is now locally tested against Simulated providers.
See the [readiness assessment](evidence/m4c-readiness-assessment.md).
Authority: master brief sections 10–12.
Scope: [architecture](architecture.md), [requirements](requirements.md),
[ADRs](decisions/0002-source-reuse.md) and [application identity](decisions/0007-application-identity.md).
The original assessment below is supplemented by the implementation status table.
Repository owner owns each risk/approval until a named
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

Source strategy is resolved as independent original MIT code, with no OctoCAT import.
Open blockers: actual Entra/OIDC
claims/roles/protection entitlement/private SQL costs (owner before M3/M4), supported
inference identity and spend cap (owner before M5), SRE/connector capabilities and
safe executor semantics (owner before M7/M8). Each is tracked in the
[design review](evidence/m1-design-review.md). No production-readiness, compliance
certification or universal prompt-injection immunity is claimed.

## M4B application control evidence and residual risks

| Existing threats | Implemented boundary / local evidence | Remaining risk and release gate |
| --- | --- | --- |
| T01 / T06 | Cryptographically verified RS256, exact issuer/audience, time/role/scope; hash issuer/subject owner on every cart method. Missing/other-owner carts both 404. Ignore identity headers. Migration keeps old anonymous rows separate | Real provider/tenant claims and browser code flow unverified; anonymous demo intentionally shared/local-only; no claim that internal ingress alone authorizes users |
| T02 / T06 | SQLite transaction/ownership integration tested; SQL parameterized contract, owner-row locks, serializable callbacks, checksums and explicit separate DDL entrypoint simulated | Actual SQL binding/T-SQL/concurrency/transaction rollback and least-privilege SQL grants must be verified on supported real engine; no runtime DDL/reset fallback |
| T04 | Memory-only browser tokens; per-subject cart references; no token/raw-owner logs; public non-secret config; safe 401/403/503; callback URL removed; actual browser/package license texts retained | XSS can still steal an active token; local sign-out neither revokes a bearer nor ends IdP SSO. Refresh requires sign-in. No real identity token captured/retained |
| T01 / T04 | Fixed HTTPS host:443, CA/name/SNI verification, constrained resolver/config/CSP; bearer forwarded, spoofed principal/forwarding removed; API trust proxy false. Real local TLS success/name-denial tested | ACA routing/DNS and egress restrictions unverified. CSP allows one reviewed IdP connection origin. Config and trust store remain privileged inputs |
| T05 | Pool max 4, 1s driver bounds, shared aggregate 1s SQL readiness; frontend 2s dependency check; DB failure fails access/readiness but not liveness | SQL timing test uses fake clock; actual cold start/performance and denial-of-service/rate limits unproven. Readiness does not exercise IdP/sign-in; separate journey probe required |
| T08 / T09 | Compiled app config rejects cloud anonymous/SQLite fallback; hosted run 42794873352 at `40a6353` passed mandatory checks and reports CodeQL skipped | SAST has not run; main reports protection disabled, rulesets plan-restricted, detailed protection unreadable through integration and environments not re-read. No accepted security exception or release authority |

Agents remain Planned; M4B adds no tools, inference rights or mutation authority.
See [ADR 0007](decisions/0007-application-identity.md) and
[M4B results](evidence/m4b-local-preparation.md) for exact scope and executed versus
simulated evidence. C4 subsequently adds local network/bootstrap/diagnostic
definitions and static checks; live enforcement remains pending.

## C3 browser control evidence and remaining limits

[C3 plan G01–G12/P01–P15](milestones/m4c-c3-oidc-plan.md) maps T01/T04/T05/T06
to the planning-time gaps. [C3 execution](evidence/m4c-c3-oidc.md) now proves local
nonce/S256/state binding, JOSE ID signature/claims before publication, vetted
metadata, one-time/clean callbacks, bounded expiry/401/logout/stale generations,
hashed scoped references and protected same-origin API requests. API cryptographic
policy/ownership is unchanged. Capture-off settings, canaries and adversarial
mutations are mandatory checks. Provider responses and transport routing are
Simulated; real client, crypto, Express and isolated SQLite execute.
Hosted run 42805606271 at `b56d9bd` passed mandatory jobs; CodeQL skipped. Those
dated hosted results are not execution of the C3 diff. C3 does not close real
provider, SAST/governance, private SQL/Azure or deployment gates. Same-origin XSS
can still steal an active bearer; browser hashing is pseudonymization, not secrecy.
Tab sign-out/abort cannot revoke a bearer or undo an already accepted server write.
The capture guard proves the implemented profile/reporters/canaries, not universal
secret detection. No real-provider traces or operational signing keys were used.

## C4 infrastructure definitions and residual threats

Assessed 2026-11-13 under C4-only authority at `e537eff`. The owner supplies hosted
run 43308294860 with mandatory jobs passed and CodeQL skipped; that run was not
independently re-read and does not verify the C4 diff. The
[C4 record](evidence/m4c-c4-infrastructure.md) and
[infrastructure contract](../infra/README.md) separate static controls from live proof.

| Threats | Defined/static-checked boundary | Remaining gate |
| --- | --- | --- |
| T01/T06 | API ingress internal/TLS, frontend TLS plus required /24–/32 client CIDR; five distinct managed identities; no shared runtime/migrator or pull-token endpoint | Actual ACA ingress/IP/MI endpoint denials, provider authorization and rights remain C6/C7; IP restriction does not authorize a cart owner |
| T02/T06 | SQL public access disabled, Entra-group admin/only authentication, TLS, separate PE/DNS/NSGs, Proxy policy, runtime object permissions and no DDL; manual one-replica/600s/no-retry migration definition | No engine/driver/MI or role grant executed. ALTER dbo is broad within the dedicated synthetic schema; time-bound DDL and verify actual grants/ownership/Graph needs in C2/C7 |
| T04 | No secret slots/inline values/connection strings, no shared-key workspace auth; export defaults off; proposed ingestion projection drops payload and unknown fields; payload canaries test a Python reference model | Not KQL/ingestion proof. Raw stdout/live stream/provider transport still exists; platform metadata must use validated names/digests. Enable no export before live schema/canary/order/role checks; source must avoid sensitive emission |
| T04/T08 | Workspace-only query access and unapplied operations table-read manifest; no exec/listSecrets/logstream/sharedKeys, other export destination or raw HTTP/query/audit collection | RBAC action support/effective denials and unrelated diagnostic settings need live inventory. A complete workspace update can remove its DCR; export must be stopped before changes, and initial bootstrap must not overwrite a linked workspace |
| T05 | Consumption 0–1 replicas, fixed Basic/2-GB SQL, seven-day Local backups, 30-day Analytics retention and 0.1-GB/day safeguard | No throughput/HA/restore/RPO/RTO proof; cold starts/locks and cap-induced loss of visibility remain risks. Replicas/expiry/tags/caps do not enforce a hard spending ceiling or automatic teardown |
| T04/T06 | Dedicated subnet/NSG attachments; only ACA-to-SQL Proxy 1433; no service-endpoint/public-SQL fallback or paid network appliance | External ACA public ingress bypasses subnet NSGs. Outbound Internet HTTPS and public ACR/Monitor remain explicit exposure; no FQDN firewall/private registry claim. C7 must review ACR/NSG compatibility and reprice if private ACR is required |
| T08/T09 | Exact eight-template/resource inventories, source/output freshness hashes, parameter checks, retained old invariants and harmful compiled/manifest/CI mutations | Static checks do not evaluate ARM, Kusto, DNS, Azure Policy/RBAC, regions/quotas or real network routes. No SAST/independent governance or cloud-readiness claim follows |

No C2/C5/C6/C7 execution, Azure auth/ARM request, credential/principal creation,
paid service, GitHub setting change or release is authorized or performed. M4A
deployment remains NO-GO. Existing C1/C3 application/proxy/capture behavior is preserved.
