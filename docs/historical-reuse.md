# Historical hackathon reuse assessment

Authority: [master brief](project/master-brief.md), section 5. The original
personal `octocat-supply-Agentic-AI` repository remains unavailable. The brief now
identifies the [event repository](https://github.com/MngEnvMCAP447224/microhack-sdlc-labuser-0039)
and historical runs/commits below. A read-only repository fetch returned 404 through
the current GitHub connection on 2026-10-30. That does not establish whether it was
deleted, private or inaccessible to this connection. Historical artifacts were not
recovered or executed; the brief is the source for their reported results.

The [current microhack reference](https://github.com/markharrison/microhack-sdlc/tree/ab5380ef37a5761413721f94334bff3127e75aa3)
provides starter/challenge context. Its current content does not prove the exact
historical event revision. The C1–C7 event roadmap is retired as the implementation
plan; the master brief's M0–M12 sequence governs this project.

## Preserved historical status

| Challenge | Historical status | Current evidence and reuse disposition |
| --- | --- | --- |
| C1 | Validated historically, per owner | Historical validation retained; original lab artifacts inaccessible; no import; revalidation required here |
| C2 | Validated historically, per owner | Historical validation retained; original lab artifacts inaccessible; no import; revalidation required here |
| C3 | Validated historically, per owner | Historical validation retained; original lab artifacts inaccessible; no import; revalidation required here |
| C4 | Validated historically, per owner | Historical validation retained; original lab artifacts inaccessible; no import; revalidation required here |
| C5 | Validated historically, per owner | Historical validation retained; original lab artifacts inaccessible; no import; revalidation required here |
| C6 | Validated historically, per owner | Historical validation retained; original lab artifacts inaccessible; no import; revalidation required here |
| C7 | Implemented/validated/compiled/pushed historically; real inference authorization failed | No useful triage comment; successful execution remains unverified; close with a genuine useful run in M5 |

These labels retain the brief's historical results without implying independent
verification or any current working capability. Do not infer exact lab files or
challenge-to-commit mappings beyond the supplied evidence.

## Historical references now preserved

| Reported result | Reference from the brief | Current disposition |
| --- | --- | --- |
| API-backed cart | [Commit 8d051f0](https://github.com/MngEnvMCAP447224/microhack-sdlc-labuser-0039/commit/8d051f0) | Historical; inaccessible source; full revision and file rights unverified |
| Product search/filtering | [Commit b500378](https://github.com/MngEnvMCAP447224/microhack-sdlc-labuser-0039/commit/b500378) | Historical; candidate behaviour for M1 requirements/M2 baseline |
| Tests/cart review fix | [Commit 8b4d207](https://github.com/MngEnvMCAP447224/microhack-sdlc-labuser-0039/commit/8b4d207) | Historical; useful test/review lesson, no code recovered |
| Deployment | [Commit ee54e55](https://github.com/MngEnvMCAP447224/microhack-sdlc-labuser-0039/commit/ee54e55), [successful run](https://github.com/MngEnvMCAP447224/microhack-sdlc-labuser-0039/actions/runs/40508682942) | Brief reports external frontend, internal API, SQLite migrations, 12 products, search/cart; not a current deployment |
| Agentic issue triage | [Commit 96d6021](https://github.com/MngEnvMCAP447224/microhack-sdlc-labuser-0039/commit/96d6021), [failed run](https://github.com/MngEnvMCAP447224/microhack-sdlc-labuser-0039/actions/runs/40531224826) | Workflow compilation/push succeeded; inference authorization failed; no useful triage output |

Portal status **7/7 complete** is separate from technical completion: C1–C6 were
validated; C7 successful execution was not. M5 needs supported authentication,
actual inference and useful repository output; a green workflow alone is inadequate.

## SRE lesson and personal rehearsal assets

The brief reports an `API_PORT` fault from `443` to `444`. Azure SRE Agent
correlated the frontend revision/config change, Nginx upstream timeouts and HTTP
504s, identified the port and proposed `443`. A **Codespaces watchdog performed
rollback**; the agent independently checked sampled recovery. It did not
autonomously apply the repair. The static `/` route remained healthy during the
API dependency failure, so it could not establish user-facing readiness.

Use the wrong-port/static-health gap as a local/container reproduction in M2 and
an input to M6 dependency checks before an authorized M7 live experiment. Do not
claim sampled recovery establishes full availability or durable recovery.

The personal rehearsal reportedly had cart/discounts, Playwright/tests,
Actions/security scans, images, Azure Container Apps, Bicep, OIDC, health checks and
KQL troubleshooting. None is present here. Reuse requires recovered source,
rights, current compatibility and fresh tests. Preserve their lessons; do not
invent working assets or import the lab's Owner role, identities, monitoring or
resource URLs as personal implementation defaults.

## Potential reuse, subject to evidence and rights

| Candidate material, if recovered | Potential value | Required treatment |
| --- | --- | --- |
| Challenge descriptions and validation checklists | Scenario design and acceptance criteria | Verify origin/rights; map definitions to requirements |
| Architecture decisions and troubleshooting notes | Explain constraints and prior failure modes | Remove stale resource references; reassess against current design |
| Prompts, tool contracts and runbooks | Inputs for later SDLC, diagnosis and remediation design | Review instruction safety, access scope and provenance; evaluate anew |
| Test data, fault scenarios and evidence formats | Repeatable local demonstrations | Use synthetic data; sanitize personal/environment identifiers |
| CI or infrastructure examples | Design reference for M3–M4 | Resolve licenses; rebuild identity, cost and teardown assumptions; do not copy credentials |
| C7 configuration or sample request | M1 design input; M5 execution proof | Require dated request/result, model/deployment identity, permissions and observable outcome |

Recovery procedure: recover accessible artifacts/full revisions behind the supplied
references, verify challenge definitions and permitted notices, map each to an R-ID,
reproduce relevant results in an isolated environment, then update the capability
matrix. Historical completion alone does not justify executing any cloud action.
