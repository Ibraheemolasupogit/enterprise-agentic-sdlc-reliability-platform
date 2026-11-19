# M4C-C5 — R2(a) P1: offline trusted-input runtime enforcement

Date: 2026-11-19 UTC. Baseline: `3274090` (`origin/main`, clean). CI for
`3274090` (run 44434808986) passed.

Machine-readable record: [JSON](m4c-c5-r2a-p1-trusted-input.json).

**Scope:** R2(a) step **P1 only**, owner-directed. P2–P6 are not implemented.

* **Not decided:** R2(a) itself is **not approved**.
* **Unchanged:**
  * G2 and G5 remain **OPEN**;
  * G4 remains **closed for TypeScript only**;
  * E04, E05, E06, release and redistribution remain **NO-GO**.
* **Not done:** no Semgrep execution, dispatch, dependency change, commit,
  push or waiver.

## Basis checked before editing

* **GitHub default variables** ([docs](https://docs.github.com/en/actions/reference/workflows-and-actions/variables)):
  * `GITHUB_ACTIONS` is always `true` in Actions.
  * `GITHUB_ACTOR_ID` is the account that triggered the *initial* run.
  * `GITHUB_TRIGGERING_ACTOR` is the user who initiated this run, and can
    differ on a re-run.
  * `GITHUB_REPOSITORY_ID` and `GITHUB_REPOSITORY_OWNER_ID` are numeric IDs.
  * **Default `GITHUB_*` and `RUNNER_*` variables cannot be overwritten.**
    Attempts are ignored.
* **`workflow_dispatch` payload** (canonical schema in `octokit/webhooks`,
  `payload-schemas/api.github.com/workflow_dispatch/event.schema.json`):
  * required properties are `inputs`, `ref` ("the branch ref from which the
    workflow was run"), `repository`, `sender` and `workflow`;
  * `repository` requires `id` (integer), `fork` (boolean), `private`
    (boolean) and `owner`;
  * `owner` and `sender` require `id` (integer) and `login`.
* **Pins** (read-only API, 2026-11-19): repository ID `1439889276` and owner ID
  `181765037`. The repository is private, not a fork, with default branch
  `main`.
* **U1E-bound inputs that P1 must not touch:** `feasibility.py`, the G2 guard,
  the locks, `toolchain.json`, the controls, the rules, the inventory and
  SBOM v3. The driver (`hosted_trial.py`), workflow and validator are **not**
  U1E-bound.

## Changes

| File | Change |
| --- | --- |
| `security/sast/trusted-inputs.json` (new; SHA-256 `1f067b0a…c840a`) | Schema `c5-trusted-inputs/1`: `repository_id` 1439889276, `repository_owner_id` 181765037, `ref` `refs/heads/main`, `events` `["workflow_dispatch"]`, `require_private` true |
| `scripts/sast/hosted_trial.py` (`6dde3e0d…` → `a4f29c12e98665ae5e0969aaa7c9d727d587a89e05f6292cd0873b19c3c9d7d2`) | **Additive only** (120 lines added, 0 removed). Adds `load_trusted_inputs()`, `trusted_context()`, a new `trust-check` subcommand, and a trust check as the **first statement** inside `typescript-preflight`, `container-build`, `container-install` and `container-run`. `CONTEXT_KEYS`, `HARDENING`, `INPUT_HASHES` and `PIP_ENV` are unchanged |
| `tests/security/sast/test_trusted_input.py` (new; `44127e6e…44cd`) | 16 tests with many sub-cases, using synthetic environments and payloads in temporary directories |

### Trust decision (`trusted_context`)

1. **Local or hosted?** If none of the markers `GITHUB_ACTIONS`, `GITHUB_RUN_ID`,
   `GITHUB_EVENT_NAME`, `GITHUB_EVENT_PATH`, `GITHUB_WORKFLOW_REF` or
   `RUNNER_ENVIRONMENT` is present, the run is **local** (owner workstation)
   and nothing further is required. This preserves local development.
   `ACTIONS_*` tokens, `GITHUB_TOKEN` and `CI` are deliberately **not**
   markers. They never establish trust, and the G2 guard's hostile environment
   keeps passing.
2. **With any marker present,** each of the following must hold, or the step
   fails with **exit 2**:
   * the pinned configuration is valid: exact keys and schema, IDs that are
     integers (not booleans), the reviewed ref, events and privacy flag, and
     the file is not a symlink;
   * `GITHUB_ACTIONS` is exactly `true`; anything else is contradictory;
   * all 10 required variables are present and non-empty;
   * the event is exactly `workflow_dispatch`;
   * the ref is exactly `refs/heads/main`;
   * the numeric IDs are well formed: the repository ID and owner ID equal the
     pins, and the actor ID equals the owner ID;
   * the logins are well formed: `GITHUB_ACTOR` and `GITHUB_TRIGGERING_ACTOR`
     both equal `GITHUB_REPOSITORY_OWNER`;
   * the event payload is an absolute, non-symlink, regular file of at most
     1 MiB, in UTF-8 JSON, shaped like `workflow_dispatch`;
   * the payload's `ref` equals `GITHUB_REF`;
   * the payload's `repository.id` equals the pin, `fork` is exactly `false`
     and `private` is exactly `true`;
   * the payload's `owner.id` equals the pin and `owner.login` equals the
     owner;
   * the payload's `sender.id` equals the owner ID and `sender.login` equals
     the triggering actor.
3. **Recording:** each rejection message is bounded and contains no payload
   dump. The three Docker steps record `trusted_input` (mode, event, ref, IDs)
   in their existing evidence file. The upload allowlist stays exactly six
   files.

**Fail-closed placement:** the check raises `Fail(2)` inside each step's
existing `try`. The step therefore records its normal failure evidence (exit 2,
`configuration-error`, with a reason) and returns 2 **before** any `node`,
`pip`, `docker`, host TypeScript gate or Semgrep harness call.

## Verification (no engine)

| Check | Result |
| --- | --- |
| New trusted-input tests | **16/16**, covering:<br>• positive: owner dispatch on `main`; local development, including hostile token noise; the pinned configuration;<br>• untrusted events (11), refs (9), repositories (11) and actors (7);<br>• each of the 10 required variables missing or empty;<br>• contradictory markers, including every lone marker;<br>• malformed IDs and logins (8);<br>• bad payloads (malformed, not an object, not UTF-8, oversized, ref contradiction, missing `inputs` or `workflow`, wrong type, relative path, missing, symlink);<br>• altered configuration (11) |
| Entry points fail closed | For each of the 4 steps × 6 untrusted contexts: exit 2, **`subprocess.run` and `Popen` never called**, and an evidence record with exit 2 and a reason. A trusted context proceeds to the step's normal (mocked) work |
| Mutation checks (disposable copies) | The tests catch a disabled check (133 failures), a missing gate in `container-run` (6) and a dropped actor-ID comparison (6) |
| Existing driver tests | 14/14 |
| G2 guard (normal shell and `env -i PATH=/usr/bin:/bin`) | **9/9** in both. The guard file is unchanged (`42672fd9…`) |
| Engine-free SAST suite (normal shell and `env -i`) | **104 run: 74 pass, 30 skipped (engine)** in both |
| `actionlint` and the trial-workflow validator | Pass. The workflow and validator are unchanged |
| Consistency | **237/237** |
| Adopted inputs | All U1E section 3 hashes are unchanged. The harness, G2 guard, workflow, validator and existing workflow and driver tests are byte-identical to `3274090` |
| Local `trust-check` | `ok (local: no hosted CI context)`, exit 0 |

## Binding consequences

* **U1E:** none. No adopted input changed and no rebinding is needed.
* **Next hosted trial:** `hosted_trial.py` is one of the 11 trial inputs, so
  the expected `input_sha256sum` changes for that entry only (`a4f29c12…`).
  The list recorded in the G4H execution JSON is superseded for the next run.
  The new list is in this record's JSON.

## Limitations (P1)

* **The first gate on a hosted run comes after some earlier steps.** The
  workflow is **unchanged**, so on a hosted run the first driver gate is
  `typescript-preflight`. It runs **after** checkout, runner facts,
  `setup-node` and `npm ci`, which installs the application lockfile with
  integrity checking and no scripts. The wheel download, image build, install
  and scan all come after the gate, and the job stops at the first failing
  step. Moving a dedicated `trust-check` step and a job-level `if:` before
  `setup-node` is **P2**.
* **Not checked in the container.** The in-container `run` subcommand is not
  gated (only `container-run` starts it, after its own check), so the G2-pinned
  container environment is unchanged.
* **Offline evidence only.** The hosted positive path (that GitHub populates
  these variables and the payload as tested) needs one authorised hosted run
  (**P5**). Hosted negative paths cannot be produced with a single
  collaborator, so they rest on these offline tests.
* **No platform enforcement.** Without branch protection, a pushed change to
  the driver or configuration could weaken this check. That is detectable only
  after the push, through the trial input hashes (**P3**) and owner review.

## P1 recommendation

**GO for P1** (to commit, as the owner's action): all checks pass, nothing
adopted changed, and the change is additive and fail-closed.

**Still NO-GO, pending separate owner direction:** P2–P6, R2(a) approval, any
hosted dispatch and E04.
