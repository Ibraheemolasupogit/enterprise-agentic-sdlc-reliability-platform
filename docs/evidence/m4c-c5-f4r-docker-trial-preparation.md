# M4C-C5-F4R — Network-isolated Docker SAST trial preparation

Date: 2026-11-13 UTC. Base: `188b8cd` plus the uncommitted, preserved
[F4 diagnosis](m4c-c5-f4-hosted-run-diagnosis.md). Authority: owner direction to
**prepare only** C5-F4R using diagnosis Option B (Docker network isolation).
Status: **prepared and locally validated (macOS host, Docker Desktop, linux/amd64
under Rosetta). The hosted trial has NOT been dispatched or rerun.** Mandatory SAST CI
and Azure deployment remain **NO-GO**.

Nothing was done with sudo or `unshare`. There were no GitHub setting changes, no
release-gate integration, no Azure, no paid services, and no commit or push.
`ci.yml` is byte-identical (`26e08322…14fbf`). Destructive tests ran only on copies
in confirmed disposable scratch directories (`mktemp -d`, resolved path checked,
pristine copy verified by hash).

## Design

| Layer | C5-F4R design |
| --- | --- |
| Trigger and guard | Unchanged from F4: `workflow_dispatch` only, confirmation phrase plus authorization reference passed via env, `contents: read`, pinned checkout and upload, 20-minute timeout, non-blocking |
| Host steps | Facts, then a hash-locked wheel **download** (no install on the host), then `container-build`, `container-install`, `container-run`, then `summarize` (`if: always()`), then the allowlisted upload (`if: always()`). All Docker use goes through [`hosted_trial.py`](../../scripts/sast/hosted_trial.py); the workflow contains no raw `docker`, `sudo`, `unshare`, `sysctl`, `setpriv` or `--privileged` |
| Runtime image | [`security/sast/container/Dockerfile`](../../security/sast/container/Dockerfile): `FROM ubuntu@sha256:77eb101c…57ec` (amd64 manifest of index `2198e4c6…caf5`). The build context holds only the Dockerfile, and there is no `ADD`/`COPY`. It installs pinned `ca-certificates` from the signed archive, then 11 pinned CPython 3.12.3 packages from APT snapshot `20261110T000000Z`. It ends with `USER 1001:1001` |
| Container hardening (every container) | `--rm --platform linux/amd64 --pull never --network none --user 1001:1001 --read-only --cap-drop ALL --security-opt no-new-privileges=true --ipc none --pids-limit 512 --memory 3g --memory-swap 3g --cpus 2 --tmpfs /tmp:rw,nosuid,nodev,noexec,size=512m`. Mounts use `--mount type=bind`, which fails if the source is missing: the repo read-only, the wheels read-only, the venv read-write only during install and read-only during the scan, and `artifacts/` read-write. Environment values pass by name only. The image is referenced by the ID it was just built with, never a tag |
| Install | Three separate network-less containers: `python3 -m venv` (failure: 6), `pip install --no-index --no-deps --only-binary=:all: --require-hashes --find-links /wheels -r requirements-sast-linux.txt` (failure: 2), then `pip check` (failure: 2, fatal) |
| Scan | `hosted_trial.py run --isolation container` runs the unchanged F3 harness. Rules, catalogue, lock, RECORD and inventory checks are unchanged |
| In-container isolation proof (new harness mode, fail closed with exit 5) | Only `lo` is up; any other interface must be one of the kernel's fallback tunnel devices (`tunl0`, `gre0`, `sit0`, …) and down. `connect` to 192.0.2.1 and 2001:db8::1 must be unreachable. DNS resolution must fail. `Uid` must not be 0. `CapEff`, `CapPrm`, `CapBnd` and `CapAmb` must all be 0. `NoNewPrivs` must be 1, `Seccomp` must be 2 and the root mount must be `ro`. The default macOS/`unshare` modes are unchanged |
| Evidence binding | The host passes a random nonce. The scan result counts only if `hosted-trial.json` carries that nonce and the same exit code |

**Exit codes are distinct.** 0 clean, 1 findings, 2 configuration, 3 tool, 4
control, 5 isolation unavailable or insufficient, **6** container build or runtime
error (Docker 125–127, 128+n, timeouts, missing Docker or image), **7** evidence
missing, stale or inconsistent. Docker's own codes never pass through as harness
codes.

## Image provenance and licences

| Item | Evidence |
| --- | --- |
| Base | `docker.io/library/ubuntu:24.04` linux/amd64 manifest `sha256:77eb101c607d6e3d4f5ad0c8a02c2136c689b98aba1f359e6502ba517e5c57ec`, created 2026-11-10. Its OCI annotations give the source as `git.launchpad.net/cloud-images/+oci/ubuntu-base` at revision `cb8ca376b19ad1ff943035430fbcb9d069789a5a` |
| Base attestation | A Docker Official Images attestation manifest (`1f54a21b…`) carries an SPDX-2.3 SBOM (creators Docker Inc., docker-scout 1.18.1, BuildKit). It lists 131 Debian packages with versions, for example `libc6 2.39-0ubuntu8.9` and `apt 2.8.4ubuntu0.1`. Its licence fields are `NOASSERTION` |
| Added packages | `ca-certificates=20260816ubuntu0.24.04.2` (live signed archive). From the snapshot: `python3`/`python3-minimal`/`libpython3-stdlib`/`python3-venv` `3.12.3-0ubuntu2.1`; `python3.12`/`-minimal`/`libpython3.12-minimal`/`libpython3.12-stdlib`/`python3.12-venv` `3.12.3-1ubuntu0.17`; `python3-pip-whl 24.0+dfsg-1ubuntu1.3`; `python3-setuptools-whl 68.1.2-2ubuntu1.2`. APT authenticates every index with signed `InRelease` and the image's `ubuntu-archive-keyring` |
| Built image | 112 packages, 46 MB, amd64, user 1001:1001, CPython 3.12.3 (the same build as the hosted runner and F2/F3). **The image ID is not reproducible**: four builds gave four IDs because of layer timestamps, even with the same pinned package set. Each run therefore binds to its own built ID, which is recorded in `container-image.json` |
| Licences | Every one of the 112 packages has `/usr/share/doc/<pkg>/copyright`, and none are missing. 91 are machine-readable. The most common declared licences are GPL-2+ (48), GPL-2 (33), BSD-3-clause (28), public-domain (27), LGPL-2.1+ (26), GPL-3+ (24), LGPL-2+/LGPL-3+ (16 each), X11, Expat, ISC and MIT. CPython's file is not machine-readable (PSF-style permissive texts); pip-whl is Apache-2.0/BSD/MIT/MPL-2/Python; setuptools-whl is Apache-2.0/BSD-3; ca-certificates is GPL-2+/MPL-2.0. The image is built ephemerally on the runner and **never pushed or uploaded**, so the trial redistributes nothing |
| Image scan | Trivy 0.72.0 `config` (Dockerfile): 26/27 pass. One **LOW** finding, DS-0026 (no `HEALTHCHECK`), is not applicable to a batch run-to-completion container. It is recorded, **not waived or suppressed**, and is below the repository's HIGH/CRITICAL threshold |

The Semgrep toolchain is unchanged: the same Linux lock, 67 wheels, and the
`semgrep-core` hash from the manifest. All 15 rules, the catalogue (23 fixtures, 64
cases) and the native-library inventory are unchanged.

## Local validation results

| Check | Result |
| --- | --- |
| Positive end-to-end: build, offline install, scan in the hardened container | Exit 0. 67 distributions equal the lock; 3,310 RECORD files verified; 223 files classified; controls 59/64 as expected (5 known misses); **69 targets, 0 findings**. Isolation evidence: "only lo up (kernel fallback tunnels down), non-local IPv4/IPv6 unreachable, DNS fails, non-root, no capabilities, NoNewPrivs, seccomp filter, read-only root" |
| First attempt (interface rule too strict) | Exit 5 because the kernel fallback tunnels were present. Diagnosed, and the rule was narrowed to "down fallback tunnels only" (fail closed throughout) |
| Real-container isolation tests (in-container harness launched with one property weakened) | **11/11 as expected**. Exact hardening exits 0. Bridge network exits 5 (`eth0`, route, DNS). Host network exits 5. uid 0 exits 5. Capabilities not dropped exits 5 (`CapBnd`). No `no-new-privileges` exits 5. Writable root exits 5. Seccomp unconfined exits 5. `--cap-add NET_RAW` exits 5. Raw probes: `--network none` gives `gaierror` (blocked); the bridge control is reachable |
| F3 34-case mutation matrix | **34/34 on macOS** (default mode) and **34/34 on Linux in container mode**, with the runner itself inside the hardened network-less container |
| Workflow validator and policy tests | `check_trial_workflow.py` passes. 23 local tests pass: 15 workflow mutations including raw docker, namespace tools, host install, step order, harness outside the container and summary always; plus 8 container tests covering Dockerfile mutations, hardening mutations and mocked exit mapping. The new tests found and closed two validator gaps: a snapshot-less `apt-get update`, and forbidden commands in parsed steps |
| Driver exit mapping (mocked Docker) | Install: hash mismatch 2, pip check 2, Docker 125 6, venv failure 6, non-empty venv 2, malformed image ID 2, missing image ID 6. Scan: harness 0–5 pass through; Docker 125/137 and timeout give 6; missing, stale-nonce or mismatched evidence gives 7 |
| Real failure checks | Tampered wheel: exit 2 at `pip-install` (hash mismatch recorded) |
| Host workflow simulation (actual `run:` steps, disposable copies) | **Authorized:** every step succeeds, 6/6 evidence files, job success. **Unconfirmed:** guard exit 2, summary exit 7, nothing executed. **Docker missing:** build exit 6, facts and image evidence uploaded. **Rule tampered:** build and install OK, scan exit 2 (configuration), 5/6 evidence files with `c5-summary.json` correctly absent |
| `actionlint` 1.7.12 (CI flags, both workflows) | Pass |

Timings (emulated amd64 on an arm64 host; not representative of native hosted runners):

| Measure | Value |
| --- | --- |
| Image build | 178 s (`--no-cache`, snapshot APT) |
| Source scans | 3.7–4.5 s |
| In-container harness | 32–39 s |
| Peak child RSS | ~288 MiB |

## Remaining risks (no waivers)

* **Docker daemon trust.** The runner user's `docker` access is effectively
  root-equivalent on the ephemeral VM. Isolation depends on the daemon honouring
  the flags. The in-container self-check verifies the outcome, not the daemon's
  integrity.
* **Hosted unknowns:**
  * the Docker `docker-default` AppArmor profile's interaction with Python and
    Semgrep;
  * whether `snapshot.ubuntu.com` and archive access from GitHub-hosted runners
    are reliable;
  * Docker Hub pull limits for the base image;
  * native build and scan time on 2 vCPU.

  Any of these causes exit 6 or another non-zero code, never a pass.
* **Image reproducibility.** The `ca-certificates` pin comes from the live
  archive; if it is superseded, the build fails closed (6) and needs a reviewed
  bump. The image ID is not reproducible, so the package set and base digest are
  the reproducible identity.
* **Supply chain.** The PyPI download still happens on the host before isolation
  (hash-pinned). Base image, APT and PyPI trust roots apply. The upstream Semgrep
  tag is unsigned (F1).
* **G2** (five MODERATE advisories), **G4** (engine-accepted malformed TS) and
  **G5** (bundled native libraries without notices or SBOM) remain open. Running
  in a container changes their exposure, because the scan has no network, no
  capabilities and a read-only root. It **does not close or waive** them.
* **Same-change tampering** of the driver, harness, validator and workflow
  remains a governance (C5-A2) control.

## Is a second hosted trial justified?

**Yes, for one more dispatch after explicit owner authorization.** The F4 blocker was
AppArmor denying an unprivileged user namespace. Option B never creates one from
the runner user: the Docker daemon creates the container's network namespace, and
the harness proves the resulting sandbox from inside. Every local positive and
negative test behaved as specified, and every failure class is distinguishable.
What only a hosted run can show is listed under hosted unknowns above, plus native
timing and memory on Ubuntu 24.04 (2 vCPU). A pass would still not authorize release,
mandatory CI, deployment or C5 acceptance.

Owner steps:

1. Review the F4R diff (files below) and confirm `ci.yml`'s SHA-256 begins
   `26e08322`.
2. Record authorization covering the Docker use (daemon root-equivalence),
   Docker Hub, Ubuntu archive/snapshot and PyPI downloads, Actions minutes and
   7-day artifacts.
3. Run `python3 scripts/sast/check_trial_workflow.py`,
   `python3 -m unittest discover -s tests/security/sast`,
   `python3 -m unittest discover -s tests/delivery`,
   `python3 scripts/check_repository.py` and `git diff --check`.
4. Commit and push manually, and wait for `ci.yml` to succeed.
5. Dispatch once:
   `gh workflow run c5-sast-hosted-trial.yml --ref main -f confirm=run-c5-f4-hosted-trial -f authorization_reference="C5-F4R owner approval 2026-11-DD"`.
6. Download `c5-f4r-hosted-sast-trial-<run-id>-1`. Interpret the exit codes above.
   Stop on any non-zero result and do not re-dispatch to turn a failure into a
   pass.

## Changed files in F4R

* New:
  * `security/sast/container/Dockerfile`;
  * `tests/security/sast/test_container_trial.py`;
  * this document and its JSON record.
* Modified:
  * `scripts/sast/feasibility.py`: adds the `--isolation container` mode;
    defaults are unchanged;
  * `scripts/sast/hosted_trial.py`: container build, install and run, summary,
    nonce, exit codes 6 and 7;
  * `scripts/sast/check_trial_workflow.py`: container and Dockerfile policy and
    the stricter step rules;
  * `.github/workflows/c5-sast-hosted-trial.yml`: install and scan moved into
    containers, plus the summary step and the upload list;
  * `tests/security/sast/test_trial_workflow.py`: updated and new mutations;
  * status lines in `README.md`, `AGENTS.md`, `docs/capability-status.md` and
    `docs/milestones/m4c-c5-sast-plan.md`.
* Unchanged: `ci.yml`, `scripts/delivery/*`, `tests/delivery/*`, application code,
  rules, locks, `toolchain.json`, `controls.json`, fixtures and
  `native-libraries.json`.
