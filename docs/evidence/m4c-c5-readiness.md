# M4C-C5 — Read-only SAST and governance readiness assessment

Date: 2026-11-13 UTC. Base: `e9b5704a2601d4ebb8a2ad9fcf079405c51e60bd`;
initial working tree clean. Authority: owner's **assessment and planning ONLY**
request. Status: **Design only; planning delivered, C5-A1/A2 not met**. C1/C3/C4
retain their distinct local/static boundaries. Azure deployment remains **NO-GO**.
No application, workflow, infrastructure, scanner, dependency or test implementation
was changed. No SAST engine was installed or executed. No GitHub setting, plan,
visibility, permission, account or subscription was changed; no Azure action,
paid service, commit or push occurred. Claims Processing was not accessed.

[Execution evidence](m4c-c5-readiness.json) binds GET results/times, source hashes,
upstream metadata, preservation and document verification. The
[bounded proposed plan](../milestones/m4c-c5-sast-plan.md) is not implementation
authority. Existing C4 evidence is preserved as its original dated snapshot.

## Verified baseline and why CodeQL is skipped

GitHub connector job metadata and GET-only CLI reads independently confirm
[run 43407086701](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/43407086701)
is a completed successful **push/main** run at `e9b5704`, attempt 1. Policy,
application, containers and required succeeded; codeql was skipped with no steps.
The required-job log reports an empty `CODEQL_ENABLED`, a skipped CodeQL conclusion
and the explicit security-coverage notice. It does not report an attempted CodeQL
analysis or licensing failure. Artifact contents were not downloaded/reverified.

The checked-in job condition requires all three: non-PR event, `refs/heads/main`
and `vars.CODEQL_ENABLED == 'true'`. The first two hold for this run; the flag does
not. Its specific variable GET returns 404; a separate successful repository
variable listing reports **total_count 0**, confirming the flag is absent. Thus
**the immediate skip is the intentional opt-in condition**, not an observed
CodeQL runtime failure. PRs are excluded by the current condition even if the flag
were later enabled. Its configured language is JavaScript/TypeScript, leaving
Python delivery code outside that CodeQL profile. The final `required` job deliberately permits this disabled
CodeQL state while issuing a coverage warning. A green aggregate is not SAST proof.

Entitlement is an independent blocker. The repository is **private, User-owned**.
Code-scanning default-setup and analyses GETs return 403, saying code scanning is
not enabled. Repository `security_and_analysis` is not returned, and the current
owner profile omits its plan field: neither omission establishes an exact billing
plan or an enabled/disabled Code Security purchase. No billing/private credential
surface was inspected. Current [GitHub eligibility documentation](https://docs.github.com/en/code-security/reference/code-scanning/troubleshoot-analysis-errors/private-repository-enablement)
requires an eligible Team/Enterprise arrangement with Code Security enabled for
private code scanning; Free/Pro public eligibility does not cover this private
personal configuration. No eligible private arrangement is established here.
Flipping a variable would not fix entitlement, PR coverage or governance.
[Local CodeQL CLI use](https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-cli)
is not a licensing workaround. No SARIF upload, trial, activation or transfer is proposed as an automatic step.

## Read-only GitHub observations

Reads were made on 2026-11-13 around 10:21–10:22 UTC using existing authorization;
only HTTP GET was used. The connector supplied repository/jobs/required-log reads;
existing `gh api --method GET` supplied governance endpoints unavailable through
the connector. Initial sandbox networking failed; authorized network access then
succeeded. There was no login, token discovery, credential refresh or fallback.

| Read | Result | Interpretation / limit |
| --- | --- | --- |
| Repository | 200; private, owner type User, default main; current connection reports admin permissions | Repository access is not Code Security entitlement or effective protection |
| Current owner profile | 200; owner login matches; plan not returned | Exact Free/Pro/billing plan remains unknown |
| Main branch | 200; SHA matches; `protected=false`, protection disabled, status-check enforcement off, contexts/checks empty | No required-check enforcement is established, despite successful check runs |
| Main protection | 403 with explicit private-plan upgrade/public-repository restriction | Approval count, stale dismissal, admin bypass and force-push/deletion settings cannot be positively verified |
| Rulesets including parents / effective main rules | Both 403 with the same plan restriction | Do not reinterpret unreadable rulesets as a successful empty ruleset inventory |
| Environments | 200; total_count 0 | No environment reviewer/self-review/bypass/branch policies exist to verify |
| CODEQL_ENABLED | Specific GET 404; variable list 200 with zero variables | Flag absent; hosted resolved context was empty |
| Code-scanning default setup / analyses | Both 403: scanning not enabled | No readable CodeQL/SAST analysis; this is not a clean scan or exact billing-plan proof |
| Commit check runs | 200; five checks from github-actions App ID 15368 | Exact current names: policy, application, containers, required success; codeql skipped |
| Collaborators | 200; only owner, role admin | No independent repository collaborator/reviewer is currently established; an off-repository reviewer is not ruled out but is unverified |
| PRs associated with C4 commit | 200; empty | No associated PR approval evidence for this commit; not proof that no independent review could exist elsewhere |
| CODEOWNERS / SAST files locally | No tracked CODEOWNERS or existing SAST configuration | No code-owner requirement or mandatory source scan can be inferred from local files |

Three feature decisions must remain separate:

- [Private branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) can be supported by Pro/Team/Enterprise, but it is not enforced on the observed main branch.
- Private CodeQL/code-scanning eligibility needs the supported Code Security arrangement, not merely a successful workflow or an admin token.
- [Private environment required reviewers](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments) are not supplied by ordinary Free/Pro/Team private environments. An environment existing would not itself prove reviewer support; here none exists.

The read-only workflow has no Azure login, publishing, deployment or OIDC issuance
job. The protected-release design remains unapplied. An independent reviewer and
an explicitly selected protected route or ADR 0005 owner-operated fallback are
still required. Owner self-review or assistant-generated approval does not meet
that independence requirement. This assessment does not select/activate the fallback.

## SAST alternative and coverage assessment

Recommend a separately authorized **Semgrep CE 1.185.0 pilot with original local
MIT rules**, before committing to C5 closure. The
[standalone CE guidance](https://docs.semgrep.dev/deployment/oss-deployment) supports
local rules without the proprietary platform. No registry rules, paid engine,
AI triage, account, remote config or source upload is needed for that proposed
profile. Existing lint/audit/Trivy/behavioral tests are complementary, not evidence
that a SAST engine has run.

Public metadata inspected, without downloading/installing a wheel:

| Item | Observed metadata / interpretation |
| --- | --- |
| Release | [v1.185.0](https://github.com/semgrep/semgrep/releases/tag/v1.185.0), published 2026-11-10; release API reports immutable |
| Annotated tag / peeled source commit | Tag object `18866f410389ff28d02310adeb770e9b3c59da56`; commit `9240f708f8d7e2fbd38b67aa6cd17704b1f81e14`; tag verification reports unsigned, not a verified signing identity |
| Engine rights | [Pinned source license](https://github.com/semgrep/semgrep/blob/9240f708f8d7e2fbd38b67aa6cd17704b1f81e14/LICENSE) is LGPL 2.1 text; [PyPI version metadata](https://pypi.org/pypi/semgrep/1.185.0/json) declares LGPL-2.1-or-later and Python >=3.10 |
| Platform candidates | PyPI lists non-yanked macOS arm64 and manylinux_2_34 x86_64 wheels with SHA-256; exact filenames/URLs/digests are in JSON and the plan |
| Remaining supply-chain work | No binary or transitive tool dependency has been installed/verified/audited. Full wheel-only dependency locks, hashes/notices, interpreter compatibility and tool vulnerability review precede execution |
| Rules | Semgrep-maintained rules have a separate [Rules License](https://semgrep.dev/legal/rules-license/); no rule pack was copied. Proposed rules must be independently authored and kept local, with provenance/notices recorded before adoption |

The official [CE language matrix](https://docs.semgrep.dev/semgrep-ce-languages)
classifies JavaScript/TypeScript/JSX/Python as community supported with
single-function analysis; Bash/YAML are experimental. CE does not provide the
proprietary cross-function/cross-file analysis. This repository's actual TS 6/TSX/
MJS constructs, installed wheel and chosen rules have **not been parser-tested**.
No CodeQL-equivalent coverage or scan-runtime estimate is asserted. Unsupported
syntax, incomplete target discovery or unproved critical controls must block the
pilot/closure rather than be silently ignored.

Source inventory: **65 tracked code files**: 33 TS, nine TSX, eight MJS, 14 Python,
one shell. The 18 API/frontend source files are the highest-priority runtime
surface. There are also fixture/test/config/tool files requiring explicit
classification. See the plan for per-boundary coverage, test fixtures and retained
Bicep/KQL/proxy/policy coverage. Semantic authorization, owner separation and
lifecycle safety cannot be certified by a syntactic pattern pack. Existing C1/C3/C4
tests and independent review must remain, with CE's finite coverage explicitly
reviewed before C5-A1 can be met. This is not an accepted scanner exception.

## Recommendation, acceptance and cost limits

**Conditional GO** for a later, explicitly authorized local CE toolchain/rule/
coverage pilot and then mandatory CI wiring under the bounded plan. Owner selection
of the engine/licensing/coverage proposal and the execution scope is still needed.
**NO-GO for C5 acceptance, automatic release and Azure deployment now.** C5-A1 has
no actual reviewed-SHA source scan or seeded detection results; C5-A2 has no
verified enforced independent governance route/reviewer. C2/C6/C7 gaps also remain.

The recommended private/no-purchase direction is CE with original rules and
ADR 0005's owner-operated release route **only if separately selected**, with an
independent reviewer and authentic approval bound to exact artifacts. A locally
validated approval JSON cannot prove human authenticity or replace GitHub
server-side protection. If a protected route is selected instead, its eligibility,
settings and denials need new explicit human authorization; this plan changes none.
No public conversion, organization transfer, trial or paid upgrade is selected.

There was no Azure/paid service consumption in this assessment. A future local CE
pilot needs local compute/storage/downloads and maintenance of owned rules; private
Actions minutes/artifacts and independent review have real potential costs. Tool
installation/advisory review and CI duration are unmeasured. No price/free-quota,
GitHub/Code Security entitlement or budget is assumed. Do not infer zero cost
from the standalone engine license. No software/project dependency upgrade is
needed merely to produce this plan.

Only read-only metadata/source inspection and document/JSON/link/whitespace/secret/
preservation checks were performed. No SAST command, malicious fixture execution,
application/browser/container regression, infrastructure compilation or release
rehearsal was run in C5 planning. The historical passing suites remain dated C4
and hosted evidence, not new C5 test results. All proposed cases remain Planned.
The JSON records actual local verification and the exact documentation-only
changed-file manifest. Stop after planning; implementation requires new direction.
