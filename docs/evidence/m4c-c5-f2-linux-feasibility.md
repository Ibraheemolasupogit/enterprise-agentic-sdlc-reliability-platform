# M4C-C5-F2 — Linux SAST feasibility verification

Date: 2026-11-13 UTC. Base: `8ffb62d` plus the uncommitted, preserved
[C5-F1](m4c-c5-f1-semgrep-feasibility.md) changes. Authority: owner direction to
implement **only C5-F2**. Status: **locally executed on Linux x86_64 under
emulation**. This is not hosted-runner evidence and not C5-A1 acceptance.
Azure deployment remains **NO-GO**.

There were no CI workflow, application, GitHub setting, permission, paid service
or Azure changes. No source was uploaded, and there was no commit or push. F1
rules, harness, toolchain manifest, locks and fixtures were **run unchanged**. All
36 F1 files were byte-identical before and after F2; their SHA-256 values are in
the [JSON record](m4c-c5-f2-linux-feasibility.json). The F1 evidence documents are
preserved as the F1 snapshot. F2 only added status lines to README, AGENTS,
capability status and the plan.

Network use was limited to these public downloads, with no source or project
data sent:

* the `ubuntu:24.04` image;
* Ubuntu `python3`/`python3-venv` packages;
* the hash-locked Linux wheels;
* one OSV query (package names and versions);
* one PyPI metadata read.

Every scan ran inside a network namespace with no egress.

## Recommendation for mandatory SAST CI

**NO-GO for mandatory SAST CI now.** Linux technical feasibility is **GO**. The
pinned x86_64 toolchain installs offline, and results match macOS exactly. Run
time and memory are small. The blockers are specific and bounded:

| ID | Blocker | Status after F2 | Closure needs |
| --- | --- | --- | --- |
| G1 | Real-source finding at `api/test/repository-sqlite.contract.test.ts:67` | Reproduced on Linux. Reconciled as a correct rule match that is not exploitable. A scratch-only remediation clears it without suppression | Owner authorization for that test-file change, then a test run |
| G2 | Five MODERATE advisories (`mcp` 1.29.0 ×4, `opentelemetry-api` 1.37.0) | Still present at 11:22Z. 1.185.0 is still the latest release and still pins both. **Correction to F1:** a scan *imports* the affected modules (see G2) | Explicit owner risk decision with compensating controls, or an upstream release. Not waived |
| G3 | Linux egress denial on the real runtime | Linux toolchain and `unshare --net` denial were verified locally. Default Docker seccomp prevents the namespace, and the harness then fails closed with a misleading message. Hosted Ubuntu 24.04 AppArmor policy is **unverifiable here** | Harness probe or `sudo -n unshare --net` fallback, then a dispatch-only hosted trial (needs workflow authorization) |
| G6 (new) | Harness fail-open gaps: deleted control fixtures and unknown file extensions pass silently (F07/F08/F16/F17) | Found by the F2 mutation matrix | Harness hardening slice: control catalog, exhaustive file classification, distinct exit codes |
| G4 | Engine-accepted malformed TS | Reconfirmed on Linux (F11) | CI ordering after mandatory `tsc`/ESLint |
| G5 | Native notices and SBOM | **Broadened**: the Linux wheel bundles 26 native libraries, including OpenSSL, libcurl and Kerberos, without notices or an SBOM | Notice and advisory review of the bundled libraries |

Mandatory wiring is reasonable once G1, G2, G3 and G6 are closed and G4 is
designed into the job order.

## Runtime

| Item | Value |
| --- | --- |
| Host | macOS 15 arm64, Docker Desktop 28.3.3, linuxkit kernel 6.10.14, builtin seccomp, **no AppArmor** |
| Linux platform | `--platform linux/amd64` through Rosetta (`/proc/cpuinfo`: VirtualApple). x86_64 is **emulated, not native** |
| Image | `ubuntu@sha256:2198e4c65076e9cb0b3d695219df667c0e3b0072da64ca3c2648aca17dcecaf5` (24.04.5 LTS, glibc 2.39) |
| Python | System `python3` 3.12.3-0ubuntu2.1, `python3-venv`, util-linux 2.39.3 (`unshare`). Non-root uid 1001 for scans |
| Local images (not pushed) | `c5f2-ubuntu-python:local` `2c69a924…`, `c5f2-sast:local` `d5a756a9…` |

## 1. Linux toolchain validation

```sh
python3.12 -m pip download --require-hashes --no-deps --only-binary=:all: \
  --platform manylinux_2_34_x86_64 --platform manylinux_2_28_x86_64 \
  --platform manylinux_2_17_x86_64 --platform manylinux2014_x86_64 \
  --platform manylinux_2_5_x86_64 --platform manylinux1_x86_64 \
  --python-version 3.12 --implementation cp --abi cp312 --abi abi3 --abi none \
  -d "$WHEELS" -r requirements-sast-linux.txt
docker run --platform linux/amd64 --network none -v "$WHEELS:/wheels:ro" ... \
  sh -c 'python3 -m venv /opt/sast && /opt/sast/bin/python -m pip install --no-index \
  --no-deps --only-binary=:all: --require-hashes --find-links /wheels -r requirements-sast-linux.txt \
  && /opt/sast/bin/python -m pip check'
```

* All 67 wheels were hash-verified (84 MB). The offline install succeeded and
  `pip check` was clean. The venv is 375 MB.
* The installed `semgrep-core` SHA-256 is `38fd0879…2f73`, equal to the F1
  manifest. `semgrep --version` reports 1.185.0.
* `ldd` shows only `libc.so.6` and the loader resolve from the OS. All other
  libraries come from 26 bundled `semgrep/bin/libs` files, including libssl and
  libcrypto (OpenSSL 3.5.8 by string), libcurl, libnghttp2, Kerberos, libstdc++,
  libselinux, zstd (1.5.5), bzip2 (1.0.8) and gmp. Versions are string-derived
  and **unverified**. The wheel has no SBOM, so OSV/PyPI queries do not cover
  these libraries (G5).

## 2. F1 harness on Linux (unchanged)

```sh
docker run --rm --platform linux/amd64 --user 1001 --security-opt seccomp=unconfined \
  -v "$COPY:/repo" -w /repo c5f2-sast:local \
  python3 -I scripts/sast/feasibility.py --semgrep /opt/sast/bin/semgrep --repeat 5
```

`$COPY` is a disposable copy of the tracked and untracked files, verified
against the F1 hashes. Compared with the macOS F1 summary, the following were
**identical**:

* rule IDs, rule hashes, flags and inventory;
* all 64 control cases (40 detected, 19 clean, 5 known misses, 0 unexpected);
* malformed controls: 4/4 rejected, exit 3;
* parser gaps: 4/4 silently accepted;
* the Python `ast` gate (15 files);
* source targets, classes, per-file hashes, the single finding and exit 1.

## 3. Parse and classification coverage

All 89 code files are classified as follows:

* **65 source targets:** each is reported scanned and has non-zero `parse_times`
  on Linux, with 0 errors and 0 skips.
* **22 control fixtures:** scanned only under the control profiles.
* **2 explicit exclusions:**
  * `frontend/start.sh` (CE Bash is experimental);
  * `scripts/verify-auth-capture.d.mts` (the engine does not target `.mts`/`.cts`).

An executable `.mts` (F13) or `.cts` (F14) is rejected by the exact
scanned-path comparison. A `.d.cts` declaration (F15) is excluded as designed.
Files whose extension the harness does not list are **not inventoried at all**
(F16/F17, G6).

## 4. Fail-closed matrix (Linux, disposable copies, real engine)

| ID | Mutation | Result |
| --- | --- | --- |
| F01 | Rule file content changed | BLOCKED exit 2 (rule hash) |
| F02 | Manifest `semgrep-core` hash wrong | BLOCKED exit 2 |
| F03 | Installed `semgrep-core` tampered (1 byte appended) | BLOCKED exit 2 |
| F04 | `semgrep-core` missing | BLOCKED exit 2 |
| F05 | Rule file missing | BLOCKED exit 2 |
| F06 | `toolchain.json` missing | Fails (traceback, **exit 1**): not a classified BLOCK, and the exit code is the same as "findings" (G6) |
| F07 | Positive-control fixture `jwt.ts` deleted | **Passes with 57 cases: fail-open on control coverage** (G6) |
| F08 | Malformed fixture `broken.py` deleted | **Passes: fail-open** (G6) |
| F09 | Runtime source `auth.ts` deleted | Scans 64 targets. No reviewed target manifest to compare against; deleted code cannot hide a finding, but the plan's manifest requirement remains open |
| F10 | Malformed production Python accepted by the engine | BLOCKED exit 2 (`ast.parse`) |
| F11 | Malformed production TS accepted by the engine | Not blocked (G4) |
| F12 | Malformed production TS the engine rejects | BLOCKED exit 2 (engine error) |
| F13 / F14 | Executable `.mts` / `.cts` | BLOCKED exit 2 (missing from scanned paths) |
| F15 | `.d.cts` declaration | Excluded by explicit classification |
| F16 | `.go` file with shell injection | **Silently ignored** (G6) |
| F17 | Python in `.pyw` with `os.system` | **Silently ignored** (G6) |
| F18 / F19 | Symlink to `/etc/passwd` / target over 1 MiB | BLOCKED exit 2 |
| I1 | Engine wheel tampered | pip hash mismatch, not installed |
| I2 | Dependency wheel missing | `--no-index` cannot satisfy it, not installed |
| I3 | Lock requests another engine version | Not satisfiable, not installed |
| I4 | Lock omits a dependency | `--no-deps` install **succeeds**. `pip check` reports `semgrep requires mcp`, so the future installer must treat `pip check` failure as fatal |

## 5. Network isolation on the Linux runtime

| Profile | `unshare --net --map-root-user` | Harness outcome |
| --- | --- | --- |
| L1 root, default seccomp | `Operation not permitted` | BLOCKED exit 2, but reported as "malformed or empty engine JSON" |
| L2 uid 1001, default seccomp | `Operation not permitted` | Same as L1 |
| L4 root, `--network none` | `Operation not permitted` | Same; container isolation alone is not accepted by the harness |
| L3 uid 1001, seccomp unconfined | Works | Full pass. Inside the namespace only `lo` and inactive tunnel devices exist, and a socket connect fails (`gaierror`). Outside it the network is reachable |

The harness fails closed whenever the restriction is unavailable. However, it
checks only that `unshare` exists, so the operator sees a misleading cause (G3,
G6). This kernel has no AppArmor, so **the Ubuntu 24.04 AppArmor
user-namespace restriction that may apply on hosted runners could not be
reproduced or excluded**. A root `sudo -n unshare --net` path, which needs no
user namespace, was not exercised because the harness does not offer it.

## 6. Time and memory (emulated x86_64; native hosted runners unmeasured)

| Measure | Linux (Rosetta) | macOS F1 (native) |
| --- | --- | --- |
| Source scan, 65 files | 3.55, 3.34, 3.30, 3.55, 3.38 s | 1.64–2.10 s |
| Control scan (22 files) | 2.63 s | 1.50 s |
| Full harness (controls, gaps, 5 source scans) | 25.6 s | 13.6 s |
| Engine `max_memory_bytes` | 152,386,944 (~145 MiB) | 153,627,072 |
| Peak RSS of any child process (`getrusage`) | 288,636 KiB (~282 MiB) | not measured |
| Offline venv + install + `pip check` | 9.6 s | not measured |

All values sit far below the planned 30 s per-file, 120 s process and 10 min job
ceilings. `--jobs 2` was used, and the container saw 14 CPUs.

## 7. G1 and G2 reconciliation (no suppression, no waiver)

**G1.** At lines 59–69, `it.each(["INSERT","UPDATE","DELETE"] as const)` passes
`operation` into a callback parameter, which is then interpolated into
`CREATE TRIGGER … AFTER ${operation} …`.

* The rule contract (no non-constant interpolation into SQL text) is
  **correctly violated**. CE single-function constant propagation does not carry
  TS literal-union types or `it.each` arrays into callback parameters.
* Exploitability: none was identified. The values are fixed test literals
  against a local test SQLite database, and no external input reaches them.
* This is a test-hygiene finding, not a runtime vulnerability. It remains open.

| Option | Assessment |
| --- | --- |
| A. Test-file change: constant lookup of three complete literal SQL statements, `store.db.exec(failureTriggers[operation])` | Scratch copy only. Linux engine: 0 errors, parsed, **no finding**. The original still flags line 67. Not compiled or run as a test. **Recommended**; needs owner authorization because it changes application test code |
| B. Teach the rule to trust literal-union parameters | Weakens detection for real code. Not recommended |
| C. Exclude `app-test` from the mandatory scan | Removes 20 files of coverage. Not recommended |

**G2.** These facts are verified; the advisories stay open.

* The OSV re-query at 2026-11-13T11:22:58Z returned the same 5 MODERATE IDs and
  no HIGH or CRITICAL.
* PyPI shows that 1.185.0 (2026-11-10) is still the latest release, and it
  still requires `mcp==1.29.0` and `opentelemetry-api~=1.37.0`. **There is no
  upstream fix path today.** Overriding pins would break the engine's declared
  contract and was not attempted.
* **Correction to F1:** with `PYTHONPROFILEIMPORTTIME`, a normal `semgrep scan`
  imports about 1,400 modules. This includes the affected
  `mcp.client.streamable_http`, `mcp.server.auth.middleware.bearer_auth` and
  related modules, plus `opentelemetry`, because `semgrep/cli.py:25` registers
  the `mcp` subcommand eagerly. F1's statement that "the scan path does not use"
  MCP was incomplete: the code is **loaded but not invoked**. No MCP server or
  client is started, `--no-trace` is set, and egress is denied.
* Compensating controls for an owner decision:
  * network namespace;
  * environment allowlist with no tokens;
  * read-only checkout;
  * tool never shipped with the application.
* Bundled Linux native libraries add unassessed exposure (G5).

## F1 evidence correction

The F2 regression run of `gitleaks dir` (8.30.1, the CI pin) found **11
`generic-api-key` hits** in `m4c-c5-f1-semgrep-feasibility.json`. Each hit was a
SHA-256 file hash keyed by a source path containing `auth`, `Token` or `api`.
F1's "no leaks" result was obtained before that JSON was written. The mandatory
CI `policy` job runs `gitleaks dir` and `gitleaks git`, so this would have failed
CI once committed. The fix stores the 65 source hashes as `"<sha256>  <path>"`
lines (shasum format); no value was removed. There is no allowlist,
`.gitleaks.toml` change or waiver. After the fix, `gitleaks dir` on the full tree
reports no leaks. The F1 JSON's `changed_file_sha256` values describe the F1
snapshot. Files edited later (README, AGENTS, capability status, plan and this
F1 JSON/Markdown) intentionally differ from those values.

## Changed files in F2

* New: this document and [its JSON record](m4c-c5-f2-linux-feasibility.json).
* Modified (status only): `README.md`, `AGENTS.md`,
  `docs/capability-status.md`, `docs/milestones/m4c-c5-sast-plan.md`.
* Corrected F1 evidence: `docs/evidence/m4c-c5-f1-semgrep-feasibility.json`
  (lossless hash reformat) and an erratum row in `m4c-c5-f1-semgrep-feasibility.md`.
* Unchanged: all F1 rules, harness, manifest, locks and fixtures; CI;
  application; tests.

## Limitations

* x86_64 ran under Rosetta, so timings are not hosted-runner timings.
* The kernel has no AppArmor, and Docker seccomp differs from a runner VM.
* There was no hosted run, because that would need a workflow change.
* Bundled native library versions are heuristic, and there is no advisory
  review of them.
* The G1 candidate was not compiled or tested.
* Plan items M11/M12/M14–M20 are still not exercised.
