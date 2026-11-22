# M4C-C5 R2(a) P3 artifact verification

2026-11-22 UTC. Owner-directed P3 implementation and offline validation
against main baseline `cde7b64f11c0ce7b4a67a603156ab7f221219527`. The
baseline's mandatory CI succeeded. [CI run 44988089416](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/44988089416)

## Verification policy

The [approval manifest](../../security/sast/approved-trial-inputs.json)
pins the 11 recorded trial inputs to the full baseline commit. It also pins
the P1 trust configuration separately because the driver reads it before
recording those 11 hashes. A new approval is required if an approved input
or the trust configuration changes.

The [offline verifier](../../scripts/sast/verify_trial_artifact.py) checks the
ZIP SHA-256 before opening it. Its six flat JSON filenames match the unchanged
workflow allowlist. It reads those entries without extracting files and
rejects extra, duplicate, irregular, or unsafe entries, excessive sizes,
and invalid or ambiguous JSON.

For current P3 acceptance, Git must establish
`approved baseline ≤ run checkout ≤ independently obtained main tip`.
The verifier hashes each approved regular Git blob at the baseline and at
the run checkout, then compares the artifact's exact recorded input set
and hashes. It checks the workflow path and GitHub-hosted runner context,
the run and attempt IDs, the commit and main ref, and the owner-only
`workflow_dispatch` event against independent GitHub run-attempt metadata.
It checks the private repository and head repository identities, the owner,
the original actor, and the triggering actor by numeric ID and login.
All three container records must contain a successful hosted P1 decision.
The verifier also checks the nonce, clean exits, Docker restrictions, and
the embedded harness summary against the corresponding retained evidence.

## Independent evidence and invocation

Obtain the original ZIP and its expected digest from GitHub's artifact
metadata for the specific run and attempt. Confirm the artifact name and
`workflow_run` repository, branch, run ID and checkout against the
independently downloaded run-attempt record. Supply that raw REST JSON via
`--run-metadata`. Obtain the full main-tip SHA separately from the
authenticated repository ref and use a trusted local Git repository
containing the commit objects. Keep the owner-reviewed manifest and
verifier outside the downloaded artifact. [GitHub artifact metadata](https://docs.github.com/en/rest/actions/artifacts#get-an-artifact)
· [GitHub run-attempt metadata](https://docs.github.com/en/rest/actions/workflow-runs#get-a-workflow-run-attempt)
· [GitHub ref metadata](https://docs.github.com/en/rest/git/refs#get-a-reference)

```sh
python3 -I scripts/sast/verify_trial_artifact.py trial.zip \
  --expected-digest "$GITHUB_ARTIFACT_DIGEST" \
  --git-repo "$INDEPENDENT_GIT_REPO" --main-tip "$GITHUB_MAIN_TIP" \
  --manifest "$OWNER_REVIEWED_MANIFEST" --run-metadata "$RUN_ATTEMPT_JSON"
```

The verifier works offline and returns nonzero when validation fails.
Current acceptance is scoped to a completed, successful trial with complete,
consistent evidence. Git ancestry proves membership at the supplied main
tip. It cannot establish branch protection or independently approve a
subsequent commit or a hosted run. The validity of the owner-reviewed inputs
and separately sourced GitHub metadata remains part of the trust model.

## Historical Run 1

The [historical fixture](../../tests/security/sast/fixtures/g4h-run-44393309563.zip)
is the original retained ZIP for run `44393309563`, attempt `1`, artifact
`14469048127`. Its SHA-256
`388dc3baca1ba774e1a708514791aed36b45fca9d10ce0928af60c4cdf4e0cf8`
matched GitHub metadata and all six member digests matched the prior
closeout record. The extracted fixture passed redacted Gitleaks before
being added. [Historical closeout](m4c-c5-g4h-hosted-gate-execution.json)
· [GitHub artifact](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/44393309563/artifacts/14469048127)

The `--historical-run-1` mode requires that original digest and exact
checkout `2e0bd258a6b217572e86355a460d86dc5b479ce2` and uses its own
historical Git blobs. The output is historical integrity verified. Run 1
predates P1 and supplies no evidence of a successful P1 trust decision.
Current-policy positives use synthetic records in the offline suite.

## Results

| Check | Local result |
| --- | --- |
| P3 suite | **24/24**. Real historical replay, synthetic current acceptance, and rejection of archive, manifest, input, history, identity, trust-decision, and cross-record mutations. |
| P1 and P2 | **16/16** runtime trust and **27/27** trial-workflow tests. The workflow validator and actionlint passed. |
| G2 guard | **9/9** in the normal and cleared environments. |
| Complete engine-free SAST suite | **133 tests per environment**, 103 passed and 30 real-engine tests skipped. |
| U1E and workflow | **237/237** consistency. The 14 U1E bindings, all 11 runtime input hashes and the six-file upload allowlist are unchanged from their approved values. |
| Repository | Repository checker, Git object integrity, tracked and untracked whitespace, and redacted Gitleaks history and worktree scans passed. |

**GO for P3 owner review.** P4–P6, hosted dispatch, broader R2(a) approval,
mandatory SAST CI, release and redistribution remain NO-GO. G2 and G5
remain open. No Semgrep execution or hosted workflow dispatch took place.
