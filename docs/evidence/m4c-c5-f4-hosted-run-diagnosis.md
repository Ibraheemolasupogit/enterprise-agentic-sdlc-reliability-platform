# M4C-C5-F4 — Hosted trial failure diagnosis (run 43432851816)

Date: 2026-11-13 UTC. Commit under test: `188b8cd63a790bdbdb7489f7440ee34e61c4db6a`
(main). Authority: owner direction for **read-only diagnosis only**. Status: **diagnosed;
no remediation implemented, no rerun.** Mandatory SAST CI and Azure deployment remain
**NO-GO**.

Actions taken: GitHub reads only (`gh run view` metadata and log; `gh run download` of the
allowlisted artifact into session scratch). No workflow edit, rerun, dispatch, sudo, GitHub
setting, Azure, paid-service, commit or push. Three public web pages were read for
attribution. This document is the only repository change besides status lines.

## Result

**Exact cause: Ubuntu 24.04's AppArmor restriction on unprivileged user namespaces
(`kernel.apparmor_restrict_unprivileged_userns=1`) denied the capability needed to write
`/proc/self/uid_map` after `unshare --net --map-root-user` created the namespace.** It is not
seccomp, not the generic user-namespace sysctls, not GitHub token permissions and not a
toolchain/harness defect. The harness failed closed exactly as designed (exit 5).

## Evidence

[Run 43432851816](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/43432851816):
`workflow_dispatch` on `main`, attempt 1, 13:20:38–13:21:10Z, conclusion failure.
Runner image `ubuntu-24.04` **20261101.360.1** (provisioner 20261028.624), `RUNNER_ENVIRONMENT=github-hosted`;
token permissions shown as `Contents: read`, `Metadata: read` only.

| Step | Result |
| --- | --- |
| Owner confirmation guard | success (reference `C5-F4 owner approval 2026-11-13`) |
| Checkout (pinned, no persisted credentials) | success |
| Runner facts | success |
| Hash-locked wheel download | success (all 67) |
| Offline `--require-hashes` install + `pip check` | success; "No broken requirements found." |
| Harness | **exit 5** after 1.42 s; peak child RSS 288,700 KiB |
| Allowlisted upload (`if: always()`) | success: `hosted-runner-facts.json` (SHA-256 `35413cfa…bad91`), `hosted-trial.json` (`c1332a11…db0bc`); `c5-summary.json` correctly absent (no scan ran) |

Harness diagnostic (verbatim):

```text
STOP [5 isolation-unavailable]: Linux unshare --net --map-root-user could not start
(unshare: write failed /proc/self/uid_map: Operation not permitted)
[max_user_namespaces=28076, unprivileged_userns_clone=1,
apparmor_restrict_unprivileged_userns=1, seccomp_mode=0, euid=1001, container=not detected]
```

All eight input hashes recorded by the run (harness, driver, toolchain, catalogue, both rule
files, Linux lock, workflow) equal the files in `188b8cd` and the F4-prepared hashes, so the
run tested exactly the reviewed code. Because the harness checks preflight → inventory →
catalogue → `ast` gate **before** isolation, reaching exit 5 also shows (by code path, not by a
recorded summary) that on the native hosted runner the installed set matched the lock, `pip
check` and RECORD verification passed, all files classified and the control catalogue verified.

## Cause attribution

| Candidate | Observed fact | Verdict |
| --- | --- | --- |
| **AppArmor userns restriction** | `apparmor_enabled=Y`, `apparmor_restrict_unprivileged_userns=1`; the failure occurs at the **uid_map write**, i.e. after namespace creation, the signature of a capability denial inside the new namespace for an unconfined process | **Cause** (high confidence) |
| Generic user namespaces disabled | `unprivileged_userns_clone=1`, `max_user_namespaces=28076` | Excluded |
| Seccomp | `seccomp_mode=0` on the runner (contrast: local Docker default seccomp gave `unshare failed`, a different, earlier failure) | Excluded |
| Permissions (GitHub token / file) | Token `contents: read` is irrelevant to kernel namespaces; process euid 1001 unprivileged by design | Excluded as cause; unprivileged execution is the intended state |
| Container / other sandbox | `container=not detected`; GitHub-hosted VM | Excluded |
| Toolchain / harness defect | Install, `pip check`, preflight succeeded; inputs hash-match | Excluded |

Supporting sources: Ubuntu introduced the restriction in 23.10 and enabled it by default in
24.04; affected programs are unconfined unprivileged processes, and Canonical's recommended
allowance is a per-application AppArmor profile with a `userns,` rule (root required to load),
with system-wide sysctl disabling discouraged
([Ubuntu blog](https://ubuntu.com/blog/ubuntu-23-10-restricted-unprivileged-user-namespaces),
[Ubuntu discourse](https://discourse.ubuntu.com/t/understanding-apparmor-user-namespace-restriction/58007),
[Launchpad 2046477](https://bugs.launchpad.net/bugs/2046477)). The same class of failure on
hosted `ubuntu-24.04` runners is recorded in
[actions/runner-images#10443](https://github.com/actions/runner-images/issues/10443).
**Limit:** the run did not capture kernel audit/`dmesg` lines, so the exact denied capability
and AppArmor profile name are inferred from the failure stage and sysctls, not observed.

## Comparison with F4 expectations

| Fact | F4 expectation / local simulation | Hosted actual |
| --- | --- | --- |
| OS / arch / glibc / Python | Ubuntu 24.04, x86_64, glibc 2.39, 3.12.3 | Ubuntu 24.04.5 LTS, x86_64, glibc 2.39, 3.12.3 — **as expected** |
| Kernel | linuxkit 6.10 (local) | `7.0.0-1017-azure` |
| CPU / memory | 14 CPUs (Docker host) | AMD EPYC 9V74, **2 vCPU**, 8,122,984 kB |
| Seccomp | 2 under Docker default; 0 unconfined | **0** |
| AppArmor | absent locally ("cannot reproduce") | **enabled, restrict_unprivileged_userns=1** — the risk F2/F3/F4 flagged as unverifiable (G3) is now confirmed |
| Toolchain install | succeeded in emulation | **succeeded natively** (download 13:20:43–:53, install/check by 13:21:05) |
| Fail-closed behaviour | exit 5, evidence still uploaded | **exactly as designed**; no scan, no partial "success" |
| Native scan timing / engine memory | to be measured | **not obtained** (blocked before scanning) |

## Safe alternatives (evaluated, NOT implemented)

| # | Alternative | Privilege / change | Assessment |
| --- | --- | --- | --- |
| A | Root creates only the network namespace, then **drops to uid 1001 before any tool runs**: `sudo -n unshare --net -- setpriv --reuid=1001 --regid=<gid> --init-groups --no-new-privs --bounding-set=-all -- <harness in pre-established-isolation mode>` | One narrowly shaped `sudo`; no user namespace needed (root has CAP_SYS_ADMIN), so AppArmor userns policy is **untouched** | **Recommended**, subject to explicit owner authorization (reverses the current no-sudo rule). Scan stays unprivileged; same `ENETUNREACH` evidence; smallest change |
| B | Docker `--network none` container (runner user is in the `docker` group): offline install from mounted wheelhouse and scan inside a digest-pinned Python image | No `sudo` command, but the Docker daemon is root and docker-group membership is root-equivalent; new pinned image enters the supply chain | **Viable fallback** if `sudo` is refused. Needs a new harness "external isolation" probe (container `lo` is up, so the loopback probe returns `ECONNREFUSED`; must instead verify no non-loopback interface and `ENETUNREACH` to a non-local address) |
| C | Load a per-application AppArmor profile (`flags=(default_allow) { userns, }`) for `unshare` via `sudo apparmor_parser` | Root + MAC policy change on the VM | Canonical-recommended pattern, but broader than A (any process on the VM may then use `unshare` userns) and adds profile maintenance. Not preferred |
| D | `sudo sysctl kernel.apparmor_restrict_unprivileged_userns=0` | Root; disables the protection VM-wide | **Not recommended** (broadest; sources discourage) |
| E | `bwrap` via Ubuntu's `bwrap-userns-restrict` profile | Unknown presence on runner image; installing needs root | Unverified; not recommended without read-only confirmation of image contents |
| F | `ubuntu-22.04` runner | Changes target platform | Not recommended: abandons the Ubuntu 24.04 target |
| G | Scan without OS isolation (flags/env only) | None | **Rejected**: violates the fail-closed egress requirement |
| H | Self-hosted/larger runners or third-party egress actions | Paid/infra or new supply chain | Out of scope |

## Narrowly scoped remediation plan (proposed, not executed)

Proposed slice **C5-F4R** (requires separate owner authorization that explicitly permits one
`sudo` form for namespace creation only):

1. **Harness** (`scripts/sast/feasibility.py`): add `--isolation=preestablished` that never
   wraps commands; it **refuses euid 0**, requires `NoNewPrivs: 1` and an empty `CapEff`
   (from `/proc/self/status`), verifies `/proc/net/dev` lists only `lo` plus inactive tunnel
   devices, and requires the loopback probe to return `ENETUNREACH`; otherwise exit 5. The
   existing `unshare --map-root-user` mode stays the default.
2. **Workflow**: replace only the harness step's command with the single privilege-dropping
   form in alternative A (wheels/venv already prepared unprivileged; `GITHUB_STEP_SUMMARY`,
   `RUNNER_TEMP` passed explicitly). No other step, trigger, permission or upload changes.
3. **Validator/tests**: allow `sudo` **only** as exactly `sudo -n unshare --net -- setpriv
   --reuid=1001 … --no-new-privs --bounding-set=-all -- python3 -I …`; mutations reject other
   sudo forms, missing privilege drop, `sysctl`, `apparmor_parser`, `--privileged`, root scan.
4. **Local validation**: Ubuntu 24.04 container as root with `--cap-add SYS_ADMIN` executing the
   exact command → harness runs as uid 1001 in the namespace (expected exit 0); negative cases
   (no drop → refused; still root → exit 5; network present → exit 5); F3 34-case matrix rerun.
5. **Owner steps**: review, commit/push, one dispatch; capture native timing/memory and
   `dmesg`-free evidence as before. Stop on any non-zero exit.

Acceptance for the slice: hosted exit 0 (or a documented 1 with triage), isolation evidence
`ENETUNREACH` with euid ≠ 0 and empty `CapEff`, controls 64/64 as catalogued, unchanged
`ci.yml`, no waiver of G2/G5.

If `sudo` is not authorized, the next-best scoped option is B, with its added image and probe
work; C/D are not recommended.

## Unchanged risks

G2 (five MODERATE advisories), G4 (engine-accepted malformed TS) and G5 (bundled native libraries
without notices/SBOM) remain open and are not waived. The hosted run did not reach the
scan, so it adds no evidence about them. Same-change tampering remains a governance (C5-A2)
control.
