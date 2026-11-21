# M4C-C5 R2(a) P2 workflow trust

**Status:** Implemented and locally verified on 2026-11-21 UTC on macOS arm64.
**Authorization:** Owner-directed P2 only, based on `8f89d4125a1546ad01b2dfd2af4731ae128d1c4e`.
[Machine-readable evidence and next-trial hashes](m4c-c5-r2a-p2-workflow-trust.json).

## Controls

1. The trial retains `workflow_dispatch` as its sole trigger and
   `contents: read` as its sole permission. The job predicate requires a
   dispatch on `refs/heads/main`, the private repository and owner IDs pinned
   in P1, and the owner as both the original actor and the triggering actor.
   The original actor must also match the owner's numeric ID.
2. Explicit confirmation and checkout are followed immediately by
   `python3 -I scripts/sast/hosted_trial.py trust-check`. The check uses the
   native GitHub Actions environment and event file. A rejection stops runner
   facts, Node/npm setup, wheel downloads, image build, installation and
   scanning. The existing final evidence summary and upload retain
   `always()` and the exact six-file allowlist.
3. The validator matches the job predicate against the existing P1 trust
   configuration. It rejects duplicate YAML mapping keys, changes to the
   confirmation/checkout/trust sequence, checkout target overrides, env and
   shell overrides, and conditions that could let setup or scanning proceed
   after rejection. It checks the dispatch-only trigger and read-only
   permissions, and retains the container and artifact controls.

The [R2(a) proposal](m4c-c5-g2g5-r1-remediation.md#4-draft-r2a-decision-owner-controlled-main-only-refined-2026-11-19-proposed-not-approved)
describes a wider trigger set. P2 applies only to the existing dispatch-only
trial. The `github` context supplies both actor fields for the job predicate.
[GitHub Actions contexts reference](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#github-context).

## Verification

| Check | Result |
| --- | --- |
| `actionlint -shellcheck=""` (1.7.12) and `python3 -B scripts/sast/check_trial_workflow.py` | Pass |
| Workflow mutations and P1 trust tests | 27/27 workflow and 16/16 trust tests. Mutations cover trigger changes, branch and tag refs, repository and owner IDs, actor clauses, private visibility, permission escalation, duplicate keys, checkout inputs, step order, soft failure, env overrides and artifact scope |
| G2 guard | 9/9 in both the normal and cleared environments |
| Engine-free suite | 109 tests in each environment, 79 passed and 30 engine-dependent tests skipped. Normal run unset `C5_SEMGREP`. The cleared environment used `env -i PATH=/usr/local/bin:/usr/bin:/bin` |
| macOS isolation test | The initial run inside Codex's sandbox could not start `sandbox-exec` (exit 71). The complete suites passed outside that outer sandbox with the harness's own sandbox active |
| U1 cross-consistency and bindings | 237/237 using the prior read-only U1 check and its retained verification artifacts. All U1E section 3 bindings and P1 runtime files match the baseline |
| Repository and security | Git object integrity, documentation and links, tracked and untracked whitespace, JSON parsing, 22/22 delivery-policy tests and redacted Gitleaks history and source checks passed |

## Next trial input binding

The sole change in the 11-entry runtime `input_sha256sum` is the workflow
entry, from `d445ce5c19e76e54226bb57db7d4fbbac5002384c48a0a1687b4b6b9342bf684`
to `005f7781edd50a5a6d86fd90785ecbb985635fcb174e02cf3c5f7ac621e334f3`.
The JSON provides the complete ordered list and the P1 trust-config hash for
owner review. U1E needs no rebinding. The hosted payload path and the new
job predicate have local evidence only. Main remains unprotected, so owner
review and hash comparison are still needed.

## Owner review

**GO for P2 owner review.** The change is limited to the dispatch-only
workflow, its validator and regression tests, this evidence pair and the
status references in `AGENTS.md`, `README.md`, `docs/capability-status.md`
and `docs/milestones/m4c-c5-sast-plan.md`.

**NO-GO for hosted dispatch, P3–P6, broader R2(a) approval, mandatory SAST CI,
release and redistribution.** A future hosted run requires owner commit and
push, the same-day U1E recheck and separate per-run authorization. G2 and G5
remain open. This verification used no Semgrep execution or hosted dispatch.
