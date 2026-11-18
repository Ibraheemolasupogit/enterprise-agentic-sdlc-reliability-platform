# M4C-C5 — G2 Semgrep dependency security assessment

Date: 2026-11-17 UTC. Base: `2b050a1` plus the uncommitted, preserved
[F4R execution closeout](m4c-c5-f4r-hosted-trial-execution.md) and
[E03 robustness](m4c-c5-e03-robustness.md) work. Authority: owner direction for a
**read-only G2 investigation** (evidence and status documentation only). A later
owner direction the same day conditionally accepted G2 and authorized one
regression test ([section 6](#6-owner-decision-and-mitigation-regression-guard)).
Machine-readable record: [JSON](m4c-c5-g2-dependency-assessment.json).

There was no dependency upgrade, lockfile change, suppression, waiver, CI or
GitHub setting change, Azure work, hosted dispatch, commit or push. All tracing
ran against a disposable copy of the repository in a scratch directory.

## Decision

| Item | Result |
| --- | --- |
| Advisories verified against the pins | **5/5 confirmed**: `mcp` 1.29.0 and `opentelemetry-api` 1.37.0 are inside every affected range |
| Vulnerable code paths reachable during our offline scans | **Not reached** on either platform (dynamic trace with a positive control, plus code reading) |
| Patched versions usable today | **No.** Semgrep 1.185.0 (latest) pins `mcp==1.29.0` and the OpenTelemetry 1.37 family. No compatible fixed set exists |
| Recommendation | **ACCEPT FOR OWNER REVIEW** (tool-only, bounded, with conditions), then **REMEDIATE** as soon as an upstream Semgrep release clears the pins. Not BLOCK on current evidence |
| **Owner decision (2026-11-17)** | **Conditionally accepted** for local development and the existing non-blocking, dispatch-only trial only. **Expires 2026-12-17.** See [section 6](#6-owner-decision-and-mitigation-regression-guard) |
| G2 status | **Open for mandatory CI (E04)** and every other use. Not waived: the five advisories stay open in every scanner and alert |
| **G5D decision (2026-11-17, supersedes the scope above)** | Conditionally accepted, **including GHSA-mf5v-w3w3-f6cg** (sixth advisory, G5C), for **local trusted-repository scans** and **separately authorised non-blocking trials**. Expires 2026-12-17. G5D early-stop conditions and controls apply. G2 OPEN; E04, release and redistribution NO-GO. See [G5D](m4c-c5-g5d-security-risk-decision.md#recorded-owner-decision-2026-11-17) |

## 1. Advisory verification

Sources: OSV API records fetched 2026-11-17T08:22Z, and PyPI metadata. The
installed versions were confirmed in both tool venvs (`mcp` 1.29.0,
`opentelemetry-api` 1.37.0, `opentelemetry-sdk` 1.37.0, `semgrep` 1.185.0).

| Advisory (CVE) | Package and affected range | Fixed in | CVSS 3.1 | Prerequisite for exploitation |
| --- | --- | --- | --- | --- |
| GHSA-5h93-6whr-6q8j (CVE-2026-116685) | `mcp` 1.8.0–1.29.x | 1.30.0 / 2.2.0 | AV:N/AC:H/PR:N/UI:N/C:H (CWE-200) | The process acts as an MCP **HTTP client** (`streamablehttp_client`, `sse_client`, `ClientSessionGroup`, `create_mcp_http_client`) and an endpoint redirects cross-origin |
| GHSA-84m7-p3x7-pcfv (CVE-2026-59951) | `mcp` 1.8.0–1.29.x | 1.30.0 / 2.2.0 | AV:N/AC:L/PR:N/UI:N/A:H (CWE-400/770/772) | The process **serves** MCP over stateful Streamable HTTP to untrusted clients |
| GHSA-rwrf-2pqf-9j8j (CVE-2026-116686) | `mcp` 1.10.0–1.29.x | 1.30.0 / 2.2.0 | AV:N/AC:L/PR:N/UI:R/A:H (CWE-918) | The process is an MCP **client** (`ClientSession`) calling tools on an untrusted server |
| GHSA-w4fh-qvv9-3v23 (CVE-2026-116684) | `mcp` 1.10.0–1.29.x | 1.30.0 / 2.2.0, plus opt-in configuration | AV:N/AC:H/PR:L/UI:N/C:H/I:H (CWE-863) | The process **serves** MCP over HTTP with SDK bearer auth. Upgrading alone does not fix it |
| GHSA-xcq7-p3pf-p88h (CVE-2026-114603) | `opentelemetry-api` 0–1.45.0 | 1.45.1 | AV:N/AC:L/PR:N/UI:N/A:L (CWE-1333/400) | An **attacker-controlled W3C `tracestate` header** reaches `TraceState.from_header` (normally through server instrumentation calling `propagate.extract`) |

All five need a network peer or attacker-supplied trace headers. All five are
rated MODERATE, and OSV lists no HIGH or CRITICAL advisory for these packages.

## 2. Reachability during our scans

### How the engine runs

`semgrep scan` with the harness flags replaces itself with the compiled
`osemgrep` binary, which then **falls back to the Python `pysemgrep`**. With
`PYTHONPROFILEIMPORTTIME`, that run imports 1,401 modules, including
`semgrep.commands.mcp`, `mcp.client.streamable_http`,
`mcp.server.auth.middleware.bearer_auth` and `opentelemetry.trace.propagation`.
This is because `semgrep/cli.py:25` imports the `mcp` subcommand eagerly
(confirming F2). Importing a module runs only its module-level code.

### Dynamic trace

A scratch tracer (`sys.monitoring` `PY_START`, plus an audit hook) ran
`pysemgrep` in process. It used the harness's exact `FLAGS` and both rule files
on `apps`, `scripts` and `tests` (75 files, including controls and malformed
fixtures). It ran on macOS (`sandbox-exec` deny-network) and in the hardened
Linux container (`--network none`, uid 1001, no capabilities, no-new-privileges,
read-only root). The tracer separates module bodies, class bodies (definitions
at import) and real function calls. Tracer SHA-256:
`268b876295458fad7e46ce8a4d32b76e7a661879ffc14b13a94acb22d1b82ef6`. It is a
scratch tool and is not committed.

| Observation | macOS | Linux container |
| --- | --- | --- |
| `mcp` modules imported / `opentelemetry` modules imported | 84 / 98 | 84 / 98 |
| Class bodies defined in advisory-relevant modules (definitions, not calls) | 47 | 47 |
| **`mcp` functions called** | **1**: `mcp/server/fastmcp/utilities/logging.py:get_logger` ×5 (logger lookup) | identical |
| `opentelemetry` functions called | 59 distinct: `NoOpTracer`/`ProxyTracer.start_as_current_span`, `NonRecordingSpan`, resource detection, attribute cleaning, context lookup (`get_current_span` ×21), default `TraceState.__init__` | identical set |
| **`TraceState.from_header`, `propagate.extract`, `TraceContextTextMapPropagator.extract`** | **not called** | **not called** |
| MCP client or server transports, `ClientSession`, `create_mcp_http_client`, `BearerAuthBackend`, `StreamableHTTPSessionManager`, `FastMCP.__init__`, OTLP exporters | **not called** (classes defined only) | **not called** |
| Network audit events | one `socket.bind(('::1', 0))`. This is urllib3's import-time IPv6 capability probe (`urllib3/util/connection.py:137`). No connect, DNS lookup or HTTP request | identical |
| Child processes | `git` ×2, `semgrep-core` ×8 | identical |

**Positive control:** the same tracer, with a deliberate call to each vulnerable
function and no network I/O, recorded `TraceState.from_header`,
`propagate.extract`, `TraceContextTextMapPropagator.extract` and
`create_mcp_http_client`. The tracer therefore detects these calls when they
happen.

### Code reading (installed Semgrep 1.185.0)

* All `mcp` imports are under `semgrep/mcp/` and `semgrep/commands/mcp.py`. They
  are used only by the `semgrep mcp` subcommand. The harness argv always starts
  with the fixed `scan` subcommand (`scripts/sast/feasibility.py` `FLAGS`).
* `semgrep/telemetry.py` builds the tracer provider, OTLP exporters and
  instrumentors only when tracing is enabled. `--no-trace` is in `FLAGS`, and
  the trace confirms the no-op tracer. Even when tracing is enabled, Semgrep's
  only `propagate.extract` call builds a carrier containing **only
  `traceparent`**, taken from `SEMGREP_TRACE_PARENT_*`. With no `tracestate`
  value, `TraceState.from_header` is not reached. The harness environment is an
  explicit allowlist that excludes `SEMGREP_TRACE_PARENT_*` and `OTEL_*`. E03
  M14 proved token and OTLP variables are absent from the engine environment.

| Advisory | Reachable in our scans? | Why |
| --- | --- | --- |
| GHSA-5h93 | No | No MCP HTTP client is created. Even if one were, egress is denied |
| GHSA-84m7 | No | No MCP server is started. No listening socket exists |
| GHSA-rwrf | No | No `ClientSession` is created and no tool is called |
| GHSA-w4fh | No | No MCP HTTP server or bearer auth |
| GHSA-xcq7 | No | No inbound headers. Tracing is no-op, and even with tracing the carrier has no `tracestate` |

## 3. Patched versions and compatibility

| Package | Pinned | Fixed | Constraint |
| --- | --- | --- | --- |
| `mcp` | 1.29.0 | 1.30.0 (2026-09-07; same dependency list as 1.29.0), 2.2.0 | Semgrep 1.185.0 requires **`mcp==1.29.0`** exactly. Installing 1.30.0 violates that pin, so the harness's fatal `pip check` fails (exit 2) |
| `opentelemetry-api` | 1.37.0 | 1.45.1 (latest 1.45.2) | Semgrep requires `opentelemetry-api~=1.37.0`, `opentelemetry-sdk~=1.37.0`, `opentelemetry-exporter-otlp-proto-http~=1.37.0` and instrumentation `~=0.58b0`. `opentelemetry-sdk` 1.37.0 requires **`opentelemetry-api==1.37.0`**. The fix needs the whole family moved outside Semgrep's declared range |

* **Upstream:** Semgrep 1.185.0 (2026-11-10) is the latest release and keeps
  both pins. Open, unreviewed community pull requests:
  [semgrep/semgrep#12057](https://github.com/semgrep/semgrep/pull/12057) bumps
  `mcp` 1.30.0 and OpenTelemetry 1.45.1/0.66b1 (an earlier attempt, #12020, was
  closed), and #12080 makes the MCP import lazy. Issue #12018 tracks the
  downstream impact. There is no maintainer response or release date.
* **Downgrading does not help.** Semgrep 1.100–1.130 require
  `opentelemetry-api~=1.25.0`, which is still inside GHSA-xcq7's affected range
  (`0`–1.45.0). They drop `mcp` but also drop a year of engine fixes and the
  verified F1–E03 baseline.
* **Local overrides** (installing patched packages with `--no-deps` against
  Semgrep's metadata) would break the engine's declared contract and fail the
  fatal `pip check`. Making them pass would need a harness change. This was not
  attempted and is not recommended.

## 4. Existing isolation and mitigation controls

| Control | Where enforced | Effect on G2 |
| --- | --- | --- |
| Fixed `scan` subcommand, with `--no-trace`, `--metrics=off`, `--disable-version-check`, `--oss-only` | `FLAGS` constant in the harness; published in `c5-summary.json` | MCP subcommand never runs; tracer is no-op |
| Explicit environment allowlist (no inherited variables) | `tool_env()` plus Semgrep settings; E03 M14 canary tests | No tokens, OTLP endpoint or trace-parent injection |
| Network isolation, verified before scanning | macOS `sandbox-exec` deny-network; Linux namespace or Docker `--network none` (non-local unreachable, DNS fails) | Even reached code has no peer |
| Hardened container (uid 1001, no capabilities, no-new-privileges, read-only root, noexec tmpfs, limits) | `HARDENING` in the driver, validated by `check_trial_workflow.py` | Limits the impact of any code-execution bug |
| Hash-locked offline install, RECORD verification, engine hash, fatal `pip check` | Harness preflight | Prevents substitution of the vulnerable packages with worse code |
| Tool never shipped with or imported by the application | Repository layout and licence review (F1) | No production exposure |

**Gap (closed in section 6):** at assessment time, no regression test pinned the
G2-relevant flags and environment. The owner then authorized the guard described
below.

## 5. Residual risk and recommendation

**Residual risk: Low** for the current local and dispatch-only, non-blocking use.
The vulnerable functions are loaded but not executed. Their prerequisites
(network peers, MCP serving or client use, attacker-supplied trace headers) are
absent and also blocked by isolation. The remaining exposures are:

* the module and class-body code of 84 `mcp` and 98 OpenTelemetry modules runs
  at import (not affected by these advisories);
* a future change to the harness flags or environment allowlist could re-enable
  tracing; the gap above has no automated guard;
* advisory scanners and Dependabot keep reporting five open alerts. These must
  stay visible and are not waived;
* same-change tampering and reviewer independence remain governance issues
  (C5-A2).

| Option | Assessment |
| --- | --- |
| **REMEDIATE** now | Not possible without breaking Semgrep's declared pins or using a harness override. **Do it when upstream releases** a version clearing both pins: re-lock, then re-run the F1–E03 verification, the 34-case matrix and the OSV query |
| **ACCEPT FOR OWNER REVIEW** (recommended) | Owner records a time-bound, tool-only risk acceptance with the conditions below. Alerts stay open, and this is not a scanner suppression |
| BLOCK | Justified only if G2 must be zero before **any** use, or if a condition below fails. Not warranted by reachability |

Recommended acceptance conditions (to be confirmed by the owner):

1. Scope limited to local runs and the dispatch-only, non-blocking trial at the
   current harness, flag and isolation configuration.
2. Re-run the OSV query and recheck upstream before each dispatch and on each
   Semgrep release. Any new HIGH/CRITICAL advisory, or evidence that a path is
   reachable, ends the acceptance (BLOCK).
3. Remediate in the first upstream Semgrep release that clears both pins.
4. A pinning test for the G2-relevant flags and environment, before any
   mandatory-CI (E04) decision.
5. Revisit for E04 separately: a release gate needs its own explicit G2 decision.

## 6. Owner decision and mitigation regression guard

**Decision (owner, 2026-11-17):** the five MODERATE advisories are **conditionally
accepted** for local development and the existing non-blocking, dispatch-only
hosted trial **only**. This is a scoped risk acceptance, not a waiver or
suppression:

* **Expiry: 2026-12-17.** On or before that date the owner must renew, remediate
  or block. Without a recorded renewal, the acceptance lapses and G2 is treated as
  BLOCK for any use.
* **G2 remains OPEN for mandatory CI (E04).** A release gate needs a separate
  owner decision.
* The acceptance ends early, becoming BLOCK, if any of these happens:
  * a HIGH or CRITICAL advisory appears for the pinned set;
  * a vulnerable path is shown to be reachable;
  * the regression guard below fails;
  * the harness flags, environment or isolation change without new owner
    review.
* Re-run the OSV query and the upstream check before each dispatch and on each
  Semgrep release. Remediate (re-lock and full re-verification) in the first
  Semgrep release that clears both pins.
* The owner records this acceptance alone. Reviewer independence remains a
  governance gap (C5-A2).

**Regression guard:**
[`tests/security/sast/test_g2_mitigation_guard.py`](../../tests/security/sast/test_g2_mitigation_guard.py)
is a local test module. Like the other SAST tests it is outside CI discovery, and
it needs no engine. It drives the harness's real `run_engine` with only
`subprocess.run` intercepted, and checks the exact process the engine would get:

| Property pinned | How |
| --- | --- |
| Exact Semgrep flag list, `scan` subcommand, `--oss-only`, `--metrics=off`, `--disable-version-check`, `--no-trace`, numeric `--max-target-bytes` | Exact tuple equality, plus a forbidden-argument pattern (`mcp`, `login`, `ci`, `--trace*`, `--metrics=on/auto`, `--pro*`, `--secrets`, `--supply-chain`, registry or URL configs, `auto`) |
| Configs are only the two catalogued local rule files; targets follow the final `--` and contain no options | Exact list equality |
| Venv interpreter in isolated mode (`-I`) and an allowed isolation wrapper (`sandbox-exec` with the exact deny-network profile, `unshare --net … --`, or none in verified container mode) | Shape check |
| Engine environment is **exactly** 15 keys with fixed values (`PATH=/usr/bin:/bin`, `SEMGREP_SEND_METRICS=off`, `SEMGREP_ENABLE_VERSION_CHECK=0`, pip and Python isolation, `NO_COLOR`), with `HOME`, `SEMGREP_SETTINGS_FILE` and `XDG_*` inside the per-run scratch home (no stored login token) | Exact key set, values and paths. Tool environment (pip check, RECORD, probes) pinned the same way |
| A hostile caller environment (GitHub, Actions OIDC, Semgrep app, Azure and AWS tokens, OTLP endpoint and exporter, trace parent, MCP token, proxy, `PYTHONPATH`, `PYTHONSTARTUP`, widened `PATH`, foreign `HOME`, metrics and version-check overrides) never reaches the engine | Canary values absent from argv and both environments |
| No CLI passthrough: the harness rejects `--trace`, `--metrics=on`, `mcp`, `--config auto`, `--flags`, `--env` and any `-- …` extras with argparse exit 2. `tool_env()` reads nothing from `os.environ` | Real argument parser |
| The hosted driver forwards into the container exactly the 11 non-secret context names plus `TRIAL_AUTHORIZATION_REFERENCE` and `C5_TRIAL_NONCE`, never values in argv, and a fixed in-container command | Captured `docker run` argv with a hostile environment |

Negative tests apply 17 source mutations to a **disposable copy** of the
harness. Each is rejected for its intended reason:

* tracing re-enabled, or a trace endpoint added;
* metrics on;
* version check on;
* `--oss-only` removed;
* `--pro`;
* the `mcp` subcommand;
* a registry config;
* the interpreter not in isolated mode;
* the caller's environment inherited;
* the engine metrics variable turned on;
* the real user settings file;
* an app token forwarded;
* an OTLP endpoint forwarded;
* `PATH` widened;
* a tool-environment token;
* a weakened `sandbox-exec` profile (macOS only).

Each mutation anchor must occur exactly once in the source and the mutation must
change it, so no mutation can silently stop applying. A further 20 synthetic
argv and environment overrides are also rejected. Temporary copies are removed
after the run.

| Run | Result |
| --- | --- |
| Guard module, macOS arm64 | **8/8 pass** (6 positive, 2 negative covering 17 mutations and 20 overrides) |
| Guard module, Linux x86_64 (hardened `--network none` container, read-only repository, emulated) | **8/8 pass**. Exercises the `unshare` wrapper path. Found and fixed a guard bug before acceptance: the target separator is the final `--`, because `unshare` wrappers end with their own `--` |
| Full SAST suite, macOS with the real engine | **60/60** (8 guard, 9 container and driver, 15 workflow, 28 E03 robustness) |
| Without `C5_SEMGREP` | 32 pass, 28 explicitly skipped |
| Delivery tests, trial-workflow validator, `actionlint` 1.7.12 | Pass |

E03 protections are unchanged. The harness, driver and E03 test files are
byte-identical to the E03 record. In the Linux container, the existing workflow
and container test modules cannot import PyYAML, which is absent from both the
image and the tool venv. This is an environment limit unrelated to G2; those
modules pass on macOS.

**What the guard does not prove:** it checks the process the harness *would*
launch, not Semgrep's internal behaviour. Semgrep's response to these flags and
environment is covered by the dynamic reachability trace in section 2. A
consistent edit of both the harness and this test in one change remains a
governance issue (C5-A2).

## 7. G5D addendum (owner decision, 2026-11-17)

* **Advisories in scope:** the five above, plus **GHSA-mf5v-w3w3-f6cg**
  (`opentelemetry-api` `traceparent` ReDoS; MODERATE; fixed in 1.45.2;
  published 2026-11-13; see
  [G5C](m4c-c5-g5c-vulnerability-assessment.md)). It reaches the same
  `extract()` path traced in section 2 as never called during scans.
* **Uses:** local trusted-repository scans, and non-blocking trials that are
  each separately authorised. This replaces the section 6 wording "local
  development and the existing non-blocking, dispatch-only trial".
* **Expiry and stopping:** expires **2026-12-17** (unchanged). The early-stop
  conditions and mandatory controls in
  [G5D](m4c-c5-g5d-security-risk-decision.md#recorded-owner-decision-2026-11-17) apply. They include the section 6 conditions and require
  the guard test to keep passing.
* **Status:** G2 remains **OPEN**, and all six advisories remain visible and
  not waived. E04, release and redistribution remain NO-GO.

## Limits

* Reachability covers the harness's `scan` invocation on this repository's file
  set, with both rule files. Other Semgrep subcommands, flags or targets were not
  traced.
* The Linux trace ran under Rosetta emulation and was not hosted. Results
  matched macOS exactly.
* Upstream pull request and issue status is a point-in-time read of public data
  (2026-11-17), not a commitment from the maintainers.
* Native-library exposure (G5) is outside this assessment.

## Changed files (G2)

* New:
  * this document and its [JSON record](m4c-c5-g2-dependency-assessment.json);
  * `tests/security/sast/test_g2_mitigation_guard.py` (guard, section 6).
* Modified (status lines only): `README.md`, `AGENTS.md`,
  `docs/capability-status.md`, `docs/milestones/m4c-c5-sast-plan.md`.
* Unchanged: dependency versions, locks, toolchain, rules, harness, driver,
  workflows, existing tests, application, and all F4R and E03 files.
