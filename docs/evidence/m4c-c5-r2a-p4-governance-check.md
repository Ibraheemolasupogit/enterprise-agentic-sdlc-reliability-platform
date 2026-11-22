# M4C-C5 R2(a) P4 governance check

2026-11-22 UTC. Owner-directed P4 implementation and offline validation
against baseline `3d32d770653538a11d8981fd5d941057edcb42ca`. The live check
awaits owner authorization. [Baseline CI run 44989803926](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/44989803926)

## Acceptance checks

The [governance checker](../../scripts/sast/governance_check.py) requires the
pinned private, personally owned, non-fork repository with default branch
`main`. The complete collaborator response must contain exactly the pinned
owner as an admin, and the deploy-key inventory must be empty. It requires
Actions to be enabled, fork pull-request workflow execution and both
credential-sharing settings to be off, and the default workflow token
policy to be read-only with automated PR approval disabled.

The trial registration must be active under its approved path. At the
observed `refs/heads/main` commit, the trial workflow, driver and P1 trust
configuration must be regular Git files. The checker verifies their
blob identities against the commit's Git tree and compares the content
SHA-256 values with the trusted local P3 approval manifest. A second read of
the main ref detects a change in the observed tip during the check.
[P1 trust policy](m4c-c5-r2a-p1-trusted-input.md)
· [P2 workflow trust](m4c-c5-r2a-p2-workflow-trust.md)
· [P3 approval manifest](../../security/sast/approved-trial-inputs.json)

The checker returns nonzero for drift, ambiguous or incomplete data,
HTTP errors, timeouts, missing access, or redirects. Any pagination
header for the collaborator or deploy-key list leaves completeness
unverified and causes failure. The fork approval flag must be a Boolean.
Both Boolean values are safe for this check because fork workflow
execution itself is disabled.

## Exact planned API reads

Every suffix below is appended to
`https://api.github.com/repos/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform`.
The checker uses authenticated `GET` requests with GitHub REST API version
`2026-03-10`. A passing check issues 14 requests, including two reads of
the main ref.

| GET suffix | Fine-grained repository permission | Response exposure |
| --- | --- | --- |
| Repository root, empty suffix | Metadata (read) | Private repository metadata, repository and owner identities, fork and visibility status, default branch. [GitHub repository endpoint](https://docs.github.com/en/rest/repos/repos#get-a-repository) |
| `/collaborators?affiliation=all&per_page=100&page=1` | Metadata (read) | Collaborator logins, account IDs and repository roles. GitHub also requires the authenticated user to have write, maintain or admin privileges. [GitHub collaborators endpoint](https://docs.github.com/en/rest/collaborators/collaborators#list-repository-collaborators) |
| `/keys?per_page=100&page=1` | Administration (read) | Deploy-key public material and metadata if any exist. [GitHub deploy keys endpoint](https://docs.github.com/en/rest/deploy-keys/deploy-keys#list-deploy-keys) |
| `/actions/permissions` | Administration (read) | Whether Actions is enabled and which action source policy is configured. [GitHub repository Actions permissions](https://docs.github.com/en/rest/actions/permissions#get-github-actions-permissions-for-a-repository) |
| `/actions/permissions/fork-pr-workflows-private-repos` | Administration (read) | Booleans for fork workflow execution, write-token sharing, secret and variable sharing, and approval. [GitHub fork workflow settings](https://docs.github.com/en/rest/actions/permissions#get-private-repo-fork-pr-workflow-settings-for-a-repository) |
| `/actions/permissions/workflow` | Administration (read) | Default token access and whether workflows can create or approve PRs. [GitHub default workflow permissions](https://docs.github.com/en/rest/actions/permissions#get-default-workflow-permissions-for-a-repository) |
| `/actions/workflows/c5-sast-hosted-trial.yml` | Actions (read) | Trial workflow ID, canonical path, registration state, URLs and dates. [GitHub workflow endpoint](https://docs.github.com/en/rest/actions/workflows#get-a-workflow) |
| `/git/ref/heads/main` twice | Contents (read) | Main ref and target commit SHA. [GitHub ref endpoint](https://docs.github.com/en/rest/git/refs#get-a-reference) |
| `/git/commits/{main_sha}` | Contents (read) | One commit object, including tree SHA, parent SHAs, message, and author and committer metadata. [GitHub Git commit endpoint](https://docs.github.com/en/rest/git/commits#get-a-commit-object) |
| `/git/trees/{tree_sha}?recursive=1` | Contents (read) | Repository tree paths, file modes, sizes and object IDs. [GitHub Git tree endpoint](https://docs.github.com/en/rest/git/trees#get-a-tree) |
| `/contents/.github/workflows/c5-sast-hosted-trial.yml?ref={main_sha}` | Contents (read) | Workflow YAML bytes and blob metadata. [GitHub contents endpoint](https://docs.github.com/en/rest/repos/contents#get-repository-content) |
| `/contents/scripts/sast/hosted_trial.py?ref={main_sha}` | Contents (read) | Trial driver source bytes and blob metadata. [GitHub contents endpoint](https://docs.github.com/en/rest/repos/contents#get-repository-content) |
| `/contents/security/sast/trusted-inputs.json?ref={main_sha}` | Contents (read) | P1 trust configuration bytes and blob metadata. [GitHub contents endpoint](https://docs.github.com/en/rest/repos/contents#get-repository-content) |

For a later authorized run, use an owner-supplied, repository-scoped
fine-grained credential with **Metadata, Administration, Actions and
Contents (read)**, provided through the process environment as
`P4_GITHUB_TOKEN`. The account privilege on the collaborator endpoint
is separate from the credential's permission grants. No write permission
is required. The CLI entry point is
`python3 -I scripts/sast/governance_check.py --live`.

The credential is sent in the Authorization header to `api.github.com`
only. The checker reads responses into memory and emits only result,
timestamp, repository ID, workflow ID, and main commit on success, or a
bounded diagnostic on failure. It retrieves setting flags rather than
secret values. It neither writes raw responses nor follows redirects.

## Limitations and recommendation

These endpoints establish the visible collaborator and deploy-key inventories.
They cannot demonstrate the absence of GitHub App grants or independently
verify who controls the owner's credentials. Results describe the observations
made during the check. Settings can change between API reads and after the
check. Branch protection and independent release approval remain outside
P4, and approval of P4 confers no dispatch authority.

**GO for P4 owner review.** Live governance remains **unverified** and
hosted dispatch remains **NO-GO** pending separate authorization and a
successful live check. P5–P6 and broader R2(a) approval remain pending.

## Offline results

| Check | Result |
| --- | --- |
| P4 fixtures | 28/28. Expected GET sequence, valid posture, permission denials and other HTTP failures, access and policy drift, incomplete and contradictory responses, and local and remote approval drift. |
| Existing P1, P2 and P3 | 16/16, 27/27 and 24/24. |
| G2 guard | 9/9 in the normal and cleared environments. |
| Engine-free SAST | 161 tests per environment, with 131 passed and 30 engine-dependent tests skipped. |
| U1 and P3 integrity | 237/237 consistency. All 14 U1E bindings and the P3 manifest, 11 runtime inputs and separate trust configuration binding were preserved. The six-file workflow upload allowlist and mandatory CI remained byte-identical to baseline. |
| Repository checks | Repository checker, Git object integrity, whitespace, and redacted Gitleaks history and worktree scans passed. |

No live governance request, hosted dispatch, or Semgrep execution took
place. No settings, dependencies, workflows, or waivers changed.
