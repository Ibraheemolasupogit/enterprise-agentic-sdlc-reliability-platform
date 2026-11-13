# M4C-C5-F4 — Hosted Linux SAST trial preparation

Date: 2026-11-13 UTC. Base: `8ffb62d` plus the uncommitted, preserved F1–F3
work ([F1](m4c-c5-f1-semgrep-feasibility.md), [F2](m4c-c5-f2-linux-feasibility.md),
[F3](m4c-c5-f3-harness-hardening.md)). Authority: owner direction to **prepare
only** C5-F4. Status: **prepared and locally validated; the hosted trial has
NOT been executed.** Azure deployment remains **NO-GO**; mandatory SAST CI
remains **NO-GO**.

Nothing was committed, pushed or dispatched. No GitHub setting, permission,
paid service, Azure resource or deployment was touched. The existing
`ci.yml` is **byte-identical**; its SHA-256 is recorded in the
[JSON record](m4c-c5-f4-hosted-trial-preparation.json). Destructive local tests
ran only on copies inside confirmed disposable scratch directories.

## Trial design

[`.github/workflows/c5-sast-hosted-trial.yml`](../../.github/workflows/c5-sast-hosted-trial.yml):

| Property | Design |
| --- | --- |
| Trigger | `workflow_dispatch` **only**. Two required string inputs: `confirm` must equal `run-c5-f4-hosted-trial`, and `authorization_reference` must be 8–80 safe characters. No push, PR, schedule or `workflow_run` trigger |
| Owner guard | The first step fails (exit 2) before checkout logic runs if either input is wrong. Inputs reach scripts only via `env`, never `${{ }}` inside `run:` |
| Runner | `ubuntu-24.04` hosted (x86_64), one job, 20-minute timeout, serialized by `concurrency` |
| Permissions | Workflow-level `contents: read`. No job overrides, `id-token`, `security-events`, secrets, environments or `continue-on-error` |
| Actions | Only the two SHAs already reviewed in `ci.yml`: checkout `d23441a4…` (`persist-credentials: false`) and upload-artifact `cf430e03…` (v7.0.2, Node 24) |
| Toolchain | Wheels are downloaded with `--require-hashes --no-deps --only-binary=:all:` from `requirements-sast-linux.txt`. They are then installed into a fresh venv **offline** (`--no-index --require-hashes`), followed by a **fatal** `pip check` |
| Execution | `scripts/sast/hosted_trial.py run` runs the F3 harness unchanged with `--repeat 5`. Rules, catalogue, RECORD and isolation checks all apply. The step exit code is the harness exit code |
| Isolation | The harness must establish `unshare --net --map-root-user` and see a loopback-probe `ENETUNREACH`. Otherwise it **fails closed with exit 5** and diagnostics. There is no sudo or root fallback |
| Evidence | `hosted_trial.py facts`, written before any download, records kernel, OS, glibc, CPU, memory, seccomp, user-namespace and AppArmor sysctls, and allowlisted GitHub metadata. `run` records the harness exit and result, wall time, peak child RSS, controls and source results, and input SHA-256s. The job summary also records the result |
| Upload | `if: always()`, three explicit files under `artifacts/sast/`, retained for 7 days. Raw engine reports (`artifacts/sast-private/`) are never uploaded |
| Non-blocking | Separate file. `ci.yml` and its `required` gate are unchanged and never reference it. No branch protection consumes it, and its result cannot authorize release, deployment or C5 acceptance |

The new [`check_trial_workflow.py`](../../scripts/sast/check_trial_workflow.py)
statically enforces all of the above, including `ci.yml`'s
`required.needs == [application, policy, containers, codeql]`.
[`test_trial_workflow.py`](../../tests/security/sast/test_trial_workflow.py)
contains 13 mutation tests covering 40+ variants:

* automatic triggers;
* permission, OIDC and security-events escalation;
* unpinned or unreviewed actions and credential persistence;
* expression injection, and a missing or weak guard;
* unhashed, online or unchecked installs;
* `sudo`, `curl` or `wget`, and `continue-on-error`;
* runner, container or `needs` changes and `secrets`;
* private, wildcard or long-retention uploads;
* harness before install, and the trial being made blocking.

These tests live outside `tests/delivery`, so the mandatory CI discovery is
unchanged.

## Local validation (prepared, not hosted)

| Check | Result |
| --- | --- |
| `check_trial_workflow.py` | PASS |
| `python3 -m unittest discover -s tests/security/sast` | 13 OK |
| `actionlint -shellcheck=""` (1.7.12, CI flags, both workflows) | Pass. It first caught an unquoted `: ` in an input description, which was fixed |
| F3 harness on macOS (new files classified: `sast-tooling-test`) | Exit 0. 219 files classified, 68 targets, **0 findings**; controls 59/64 as expected with 5 known misses. The new test file was first **blocked** as unclassified (exit 2) until it was explicitly classified |
| F3 fail-closed mutation matrix, re-run (new disposable dir) | **34/34** as expected |

**Workflow simulation.** `f4_simulate.py` is a scratch tool that is not in the
repo. It rendered the workflow's actual `run:` steps, passing inputs via env as
GitHub does. They ran in a fresh `ubuntu:24.04` x86_64 container (Python
3.12.3, no Semgrep preinstalled, Rosetta emulation) against a disposable copy.
Checkout and upload were simulated.

| Scenario | Outcome |
| --- | --- |
| Wrong confirmation phrase | Step 0 exit 2; all later steps skipped; job failure. The upload step still runs (files absent, warn) |
| Malformed reference containing `$(id)` | Step 0 exit 2. The value was never evaluated as code |
| Authorized, user namespaces permitted (uid 1001, seccomp unconfined) | Download, offline install and `pip check` pass. Harness **exit 0**: probe `ENETUNREACH`, 67 distributions = lock, 3,310 RECORD files, 68 targets, 0 findings; source scans 3.08–3.14 s; harness 26.5 s; peak child RSS 294,744 KiB; job success; 3 files would be uploaded |
| Authorized, Docker default seccomp (uid 1001) | Install passes. Harness **exit 5** (`unshare` EPERM, `seccomp_mode=2`); job failure. Facts and the trial record would still be uploaded |

Simulated artifacts were checked: gitleaks found no leaks, and there were no
secret-like keys, snippets, messages or environment dump. GitHub metadata is
limited to the allowlisted run, ref, runner and image fields.

The simulation **cannot** reproduce three things: the hosted runner's AppArmor
policy, real image contents (pip and venv availability), and native timing.
Those are exactly what the hosted trial measures.

## How to read the hosted result

| Harness exit | Meaning for F4 | Next action |
| --- | --- | --- |
| 0 | Hosted isolation, toolchain, controls and a clean source scan are all verified on native Ubuntu 24.04 | Record F4 execution evidence; a mandatory-CI decision still needs G2/G5 |
| 1 | Isolation and controls are fine; real source findings exist | Triage each finding; no suppression or waiver |
| 2 | Configuration problem (manifest, lock, install, inventory, catalogue) | Fix the configuration under a new scope |
| 3 | Engine or tool problem (crash, timeout, parse, incomplete report) | Investigate; do not retry it into a success |
| 4 | Control failure (missed, false positive or drift) | Engine or rule behaviour differs on hosted Linux; stop |
| 5 | Unprivileged user namespaces unavailable on hosted runners | Record the facts (AppArmor sysctl). Any root or `sudo unshare` design needs **separate** authorization |

A failed guard or download/install step also fails the job before the harness
runs. The uploaded facts file explains why.

## G2 / G5 risk register (no waivers granted)

| Risk | Status for the trial | Exposure in the trial and its limits |
| --- | --- | --- |
| G2: `mcp` 1.29.0 (GHSA-5h93-6whr-6q8j, GHSA-84m7-p3x7-pcfv, GHSA-rwrf-2pqf-9j8j, GHSA-w4fh-qvv9-3v23) and `opentelemetry-api` 1.37.0 (GHSA-xcq7-p3pf-p88h), all MODERATE | **Open, not waived.** Semgrep 1.185.0 pins them, and no upstream fix exists (F2) | The modules are imported but not invoked. The scan runs in a network namespace with no tokens (`persist-credentials: false`, no secrets) and read-only repository permission. This analysis is not an acceptance |
| G5: 26 bundled Linux native libraries (OpenSSL, curl, Kerberos, glibc parts, GCC runtime…) without notices or SBOM; versions heuristic and RHEL-backported ([inventory](../../security/sast/native-libraries.json)) | **Open, not waived** | The libraries run on an ephemeral hosted runner. The wheelhouse is not uploaded or redistributed (only three JSON files are), so the trial creates no redistribution of copyleft components. Advisory exposure of these libraries remains unassessable |
| Supply chain | Hashes are pinned. The upstream tag is unsigned; RECORD files can be rewritten together with code | PyPI downloads happen on the runner before isolation. The hash check prevents substitution, not publisher compromise |
| Same-change tampering | Unchanged (C5-A2) | The workflow, harness, catalogue and validator can be edited together. The owner's review of the exact commit is the control |

Running the trial does **not** close G2 or G5 and does not make SAST a release
gate.

## Cost

Each dispatch consumes private-repository GitHub Actions Linux minutes. The
expected time is under 10 minutes, including about 84 MB of wheel downloads; a
20-minute timeout applies. Artifact storage is about 30 KB for 7 days. No
free quota or price is assumed. There are no other paid services and no Azure
use.

## Manual steps to authorize and run (owner only)

1. **Review** the F1–F4 diff, especially the trial workflow, `hosted_trial.py`
   and `check_trial_workflow.py`. Confirm `ci.yml` is unchanged:
   `shasum -a 256 .github/workflows/ci.yml` should print `26e08322…14fbf`.
2. **Decide and record authorization** outside this repository's automation,
   for example in an issue or decision note. It should cover a dispatch-only
   trial, the Actions-minute cost, PyPI downloads from the runner and 7-day
   artifact retention. Choose a reference string such as
   `C5-F4 owner approval 2026-11-DD`.
3. **Re-run the local checks** on the exact tree to be committed:
   `python3 scripts/sast/check_trial_workflow.py`,
   `python3 -m unittest discover -s tests/security/sast`,
   `python3 -m unittest discover -s tests/delivery`,
   `python3 scripts/check_repository.py`, `git diff --check`, and the F3
   harness command from the [F3 evidence](m4c-c5-f3-harness-hardening.md).
4. **Commit and push manually** to `main`. `workflow_dispatch` is only
   available once the file is on the default branch. The push runs the
   existing `ci.yml` (policy, application, containers and required, with
   CodeQL still skipped). The trial does **not** run on push. Wait for `ci.yml`
   to succeed; its `actionlint` step also lints the trial workflow.
5. **Dispatch once**: Actions → "C5-F4 hosted SAST feasibility trial
   (non-blocking)" → Run workflow on `main`, with `confirm` set to
   `run-c5-f4-hosted-trial` and `authorization_reference` set to your
   reference. Equivalent command:
   `gh workflow run c5-sast-hosted-trial.yml --ref main -f confirm=run-c5-f4-hosted-trial -f authorization_reference="C5-F4 owner approval 2026-11-DD"`.
6. **Collect evidence**: `gh run watch <run-id>`, then
   `gh run download <run-id> -n c5-f4-hosted-sast-trial-<run-id>-1`. Note the
   run URL, head SHA, job conclusion and harness exit code.
7. **Stop and report** with the table above. Do not re-dispatch to turn a
   failure into a success, and do not add root or sudo isolation without new
   authorization. Record results in a separate F4 execution evidence document.
8. **Optional**: to retire the trial, delete the workflow file in a later
   reviewed commit. It never runs unless dispatched.

## Changed files in F4

* New:
  * `.github/workflows/c5-sast-hosted-trial.yml`;
  * `scripts/sast/hosted_trial.py`, `scripts/sast/check_trial_workflow.py`;
  * `tests/security/sast/test_trial_workflow.py`;
  * this document and its JSON record.
* Modified:
  * `scripts/sast/feasibility.py`: one line classifying
    `tests/security/sast/` non-fixture files as `sast-tooling-test`;
  * status lines in `README.md`, `AGENTS.md`, `docs/capability-status.md` and
    `docs/milestones/m4c-c5-sast-plan.md`.
* Unchanged: `ci.yml`, `scripts/delivery/policy.py`, `tests/delivery/`,
  application code and tests, rules, locks, catalogue, fixtures and toolchain
  manifest.

## Limitations

* The hosted trial is unexecuted. Local results used Docker Desktop with
  Rosetta, no AppArmor and a minimal Ubuntu image, not the GitHub runner image.
* The validator is string- and structure-based. It complements `actionlint`
  and review; it is not a proof of workflow semantics.
* The trial verifies one runner image at one point in time. Runner images
  change, so a later mandatory job must re-verify isolation on every run (the
  harness does this).
* G2, G4 and G5 and the governance gates remain open.
