# M4C-C5-F1 — Local Semgrep CE feasibility evidence

Date: 2026-11-13 UTC. Base: `8ffb62d` (C5 planning commit on C4 `e9b5704`);
initial working tree clean, so there were no uncommitted changes to preserve.
Authority: owner direction to implement **only C5-F1, local Semgrep CE
feasibility**. Status: **locally executed (macOS arm64 only)**. This is
feasibility evidence, not C5-A1 acceptance. Azure deployment remains **NO-GO**.

No CI workflow, application, infrastructure, dependency lock, GitHub setting,
permission, account or paid service was changed or used. No Azure
authentication, provisioning or deployment happened. No source was uploaded:
scans ran under an OS network denial with metrics, version checks and tracing
disabled. Network use was limited to downloading public PyPI wheels and one OSV
advisory query (package names and versions only). Claims Processing was not
accessed. No commit or push.

[Machine-readable record](m4c-c5-f1-semgrep-feasibility.json) holds hashes,
counts and timings. Raw engine reports were kept private (mode 0600) under the
ignored `artifacts/sast-private/` and are not evidence for publication.

## Recommendation

**Conditional GO for a separately authorized CI integration slice; NO-GO for
mandatory blocking CI wiring until conditions G1–G3 are closed.** Semgrep CE
1.185.0 installs reproducibly from hash-locked binary wheels. It parses every
classified TS/TSX/MJS/Python target. All 40 positive controls are detected, all
19 negative controls stay clean, and the full source scan takes about 2 seconds.
However:

| ID | Condition before mandatory CI wiring | Owner decision needed |
| --- | --- | --- |
| G1 | The real source scan is **not clean**: one finding (below). A mandatory gate would fail now | Change the test code, or decide test-file scope. No waiver was created |
| G2 | Five MODERATE advisories in tool dependencies pinned by Semgrep itself; not fixable without changing the engine | Accept the tool-only exposure as an explicit decision, or wait for an upstream release. Not waived here |
| G3 | Linux x86_64 lock is resolved but **not executed**. `unshare --net` egress denial may be blocked by Ubuntu 24.04 AppArmor user-namespace restrictions on hosted runners | Authorize a bounded hosted or Linux trial; keep fail-closed if there is no denial |
| G4 | Semgrep parse success does not prove valid syntax (see engine findings). The CI job must run after the existing mandatory `typecheck`/`lint`, and keep the Python `ast` gate | Accept this ordering in the CI design |
| G5 | Six native libraries are bundled without their own licence files in the wheel | Record notices from upstream before adoption |

C5-A1 also still needs E03–E08 in the [plan](../milestones/m4c-c5-sast-plan.md)
and an independent coverage review. C5-A2 governance is untouched and stays
Blocked.

## Toolchain provenance, licence and compatibility

| Item | Verified result |
| --- | --- |
| Root wheel (macOS arm64) | `semgrep-1.185.0-…-macosx_11_0_arm64.whl`, SHA-256 `d54c7dc2…f1b4`. Matches the digest planned in C5 |
| Root wheel (Linux x86_64) | `…-manylinux_2_34_x86_64.whl`, SHA-256 `0eb6aaad…c02b`. Matches the plan; downloaded and locked only |
| Wheel metadata | `License-Expression: LGPL-2.1-or-later`; `Requires-Python >=3.10`; LGPL 2.1 text in `dist-info/licenses/LICENSE` |
| `semgrep-core` | Bundled native binary; installed SHA-256 `4bfb5ad1…e9f5` is byte-identical to the wheel member. Linux member `38fd0879…2f73` |
| Bundled native libraries | libdwarf, libpcre2-8, libzstd, libtree-sitter, libev, libgmp; **no per-library notices in the wheel** (G5) |
| Interpreter / platform | CPython 3.12.8, macOS 15 (Darwin 24.6.0) arm64. CI runners are `ubuntu-24.04` (system CPython 3.12) |
| Dependency closure | 67 distributions including the engine, all binary wheels for both platforms. `pip check` clean |
| Locks | [`requirements-sast-macos.txt`](../../requirements-sast-macos.txt), [`requirements-sast-linux.txt`](../../requirements-sast-linux.txt). Separate from application and delivery dependencies |
| Install method | `pip download --require-hashes --no-deps --only-binary=:all:`, then `pip install --no-index --no-deps --require-hashes` from the local wheelhouse into an isolated venv. Repeated from the lockfile alone into a fresh venv, with an identical control and source result |
| Signature | Upstream tag is unsigned (C5 assessment). Hashes prove integrity against PyPI, **not** publisher identity |

Licence inventory (metadata plus shipped licence text): Semgrep is
LGPL-2.1-or-later and certifi is MPL-2.0. The other 65 are permissive:
MIT/MIT-0, BSD-2/3-Clause, Apache-2.0, PSF-2.0 and dual Apache/BSD/MIT. Two
packages have no metadata expression: `face` (BSD-style text) and `peewee`
(MIT text). `opentelemetry-util-http` declares Apache-2.0 but ships no licence
file. Semgrep runs as a separate developer tool. It is not linked into,
distributed with or imported by the application, so no project relicensing
question arises. The per-package list is in
[`security/sast/toolchain.json`](../../security/sast/toolchain.json).

OSV advisory query (2026-11-13T10:47Z, 67 packages): **no HIGH/CRITICAL**.
Five MODERATE:

| Package | Advisories | Fixed in | Why it cannot be updated here |
| --- | --- | --- | --- |
| `mcp` 1.29.0 | GHSA-5h93-6whr-6q8j, GHSA-84m7-p3x7-pcfv, GHSA-rwrf-2pqf-9j8j, GHSA-w4fh-qvv9-3v23 | 1.30.0 | Semgrep pins `mcp==1.29.0`. These affect MCP HTTP client/server transports, which the scan path does not use (`semgrep mcp` was never invoked) |
| `opentelemetry-api` 1.37.0 | GHSA-xcq7-p3pf-p88h (tracestate parsing) | 1.45.1 | Semgrep requires `~=1.37.0`. Tracing is disabled (`--no-trace`, no endpoint) |

Exposure reasoning is analysis, not a waiver. The findings remain open (G2).

## Rules and harness

Fifteen original rules ([TypeScript](../../security/sast/rules/typescript.yml),
[Python](../../security/sast/rules/python.yml)) were written for this repository
under its MIT licence. No Registry or maintained rule-pack content was copied or
fetched. The engine was given only `--config <local file>`.
The [harness](../../scripts/sast/feasibility.py) (stdlib only, `python3 -I`):

* verifies the `semgrep-core` hash for the platform and each rule file's hash
  against the [toolchain manifest](../../security/sast/toolchain.json). It also
  requires the executed rule-ID set to equal the catalog;
* walks the filesystem, not Git, and classifies **every** code file. It blocks on
  an unclassified file, a symlink or path escape, or a target over 1 MiB.
  Generated directories are excluded by name only;
* runs the engine with an environment allowlist, a temporary HOME and settings
  file, and an OS network denial (`sandbox-exec deny network*`; Linux
  `unshare --net`, otherwise it refuses). It uses a 120 s deadline and the
  planned flags plus `--time --quiet`;
* rejects a scan if it has engine errors or skipped rules, if scanned paths do
  not exactly match the expected targets, if any target was not actually parsed
  (`parse_times`), if the executed catalog differs, or if the exit code
  contradicts the findings;
* compares findings with `ruleid:` / `ok:` / `todoruleid:` fixture annotations
  per line, and counts any unannotated finding as a false positive;
* runs an independent `ast.parse` syntax gate on every Python source target;
* writes an allowlisted summary (`artifacts/sast/c5-f1-summary.json`,
  ignored) holding rule ID, path, line, counts, hashes and timings only. A check
  confirmed it has no snippets, messages or dataflow fields.

| Rule | Plan control | + detected | − clean | Known miss |
| --- | --- | --- | --- | --- |
| `morrow.ts.sql-built-query` | M01 | 5/5 | 2/2 | 1 (SQL built in a helper function) |
| `morrow.py.sql-built-query` | M01 | 3/3 | 1/1 | — |
| `morrow.ts.tls-verification-disabled` | M02 | 4/4 (incl. constant alias) | 1/1 | — |
| `morrow.py.tls-verification-disabled` | M02 | 4/4 | 2/2 | — |
| `morrow.ts.jwt-decoded-without-verification` | M03 | 1/1 | — | — |
| `morrow.ts.jwt-verify-incomplete` | M03 | 4/4 (no options, no issuer, no audience, `none`) | 1/1 | 1 (options object built elsewhere) |
| `morrow.ts.child-process-shell` | M04 | 3/3 (TS + MJS namespace) | 3/3 | 1 (aliased `exec`) |
| `morrow.py.process-shell` | M04 | 2/2 | 1/1 | 1 (aliased run with variable `shell`) |
| `morrow.ts.unsafe-html-or-eval` | M05 | 5/5 (TSX parser, eval, `nosemgrep` case) | 2/2 | — |
| `morrow.py.unsafe-eval-or-deserialization` | M05 | 4/4 (incl. `nosemgrep` case) | 2/2 | — |
| `morrow.ts.sensitive-value-logged` | M06 | 3/3 | 2/2 | 1 (renamed value) |
| `morrow.py.sensitive-value-logged` | M06 | 2/2 | 2/2 | — |
| `morrow.parse-probe.{typescript,javascript,python}` | M07 | parse coverage | — | — |

Totals: **40/40 positives detected, 19/19 negatives clean, 0 unexpected
findings, 5 recorded blind spots** (`todoruleid`; never counted as detection).
`--disable-nosem` was confirmed: inline `nosemgrep` did not hide the TS or the
Python control.

## Engine behaviour findings that shape CI design

1. **Prefiltering hides parse failures.** A file without a rule's literal tokens
   is reported as `scanned` but is never parsed, so malformed files passed with
   zero errors. Literal-free `parse-probe` rules (`$A = $A`) force parsing. With
   them, all four malformed fixtures (TS, TSX, MJS, Python) fail with
   `PartialParsing` (exit 3 under `--strict`).
2. **Parser error recovery accepts some invalid code silently.** Three of seven
   probed invalid TS shapes and `def f(:` in Python produce no error. Four
   reproducible cases are kept in `fixtures/parser-gaps/`, and the engine
   accepted 4/4. Python is closed by the harness `ast.parse` gate (proven by
   mutation). TS relies on the existing mandatory `tsc`/ESLint jobs (G4).
3. **`.mts`/`.cts` are not targeted.** The tracked type-only
   `scripts/verify-auth-capture.d.mts` was silently omitted. The harness's
   exact path comparison caught it. Declarations are now classified explicitly.
   An executable `.mts` still blocks (A3). The C5 plan's count of 65 tracked
   code files missed this file; the actual count is 66.
4. **Import resolution crosses rule intent.** An imported bare
   `child_process` `exec(...)` matched the SQL rule's `$DB.exec(...)`. This was
   fixed with `pattern-not: exec(...)` and verified by controls.
5. **Rule-ID rewriting.** Without `--no-rewrite-rule-ids`, IDs are prefixed with
   the config path, which breaks exact catalog matching. The flag is required.
6. **Constant propagation helps.** Template SQL with module or local constant
   fragments, and even a ternary of literals (`database.ts` `${order}`), is not
   flagged. A boolean alias `const insecure = false` *is* resolved for TLS.

## Real source scan

Inventory: 89 code files, comprising **65 scanned**, 22 control fixtures
(scanned only through control profiles) and 2 excluded by explicit
classification outside the CE claim (`frontend/start.sh`, CE Bash is
experimental; the `.d.mts` declaration). Scanned classes: runtime-api 12,
runtime-frontend 6, app-test 20, app-config 5, app-tooling 7, delivery-python 15
(including the new harness). Every target was parsed; there were no errors,
skips or timeouts. Findings were identical across five repetitions.

| Rule | Location | Class | Assessment |
| --- | --- | --- | --- |
| `morrow.ts.sql-built-query` (ERROR, CWE-89) | `apps/octocat-supply/api/test/repository-sqlite.contract.test.ts:67` | app-test | Correct pattern match: `${operation}` is interpolated into `CREATE TRIGGER` SQL. `operation` comes from `it.each(["INSERT","UPDATE","DELETE"] as const)`, so it looks non-exploitable test code. **Not modified, suppressed or waived.** Owner direction needed (G1) |

There were **zero findings in runtime API/frontend source**. That includes the
constant-fragment SQL in `database.ts`/`sql.ts`, both fully optioned
`jwtVerify` calls, and request/CLI logging. The observed false-positive rate on
real code is 0 runtime findings and 1 arguable test finding. Absence of findings
is bounded by the single-function rules and is **not** proof of security.
Cross-module ownership, session or authorization properties (M20) are not
claimed. C1/C3 tests and independent review remain required.

## Execution time and resources

| Measure | Result (macOS arm64, local) |
| --- | --- |
| Source scan, 65 files / 351,038 bytes | 1.94, 2.10, 1.83, 1.79, 1.64 s wall (5 runs) |
| Control scan (22 files) / malformed scan | 1.50 s / 1.22 s |
| Full harness run (controls, gaps, 5 source scans) | 13.6 s wall |
| Peak engine memory (`max_memory_bytes`) | 153,627,072 bytes (~147 MiB) |
| Planned ceilings | 1 MiB/file, 30 s/file rule timeout, 120 s process deadline: no ceiling approached |

Hosted runner time is unmeasured. Install was about 51 MB for the root wheel
plus dependencies, about 100 MB downloaded per platform.

## Fail-closed checks (disposable repository copy, real engine)

| ID | Mutation | Result |
| --- | --- | --- |
| A1 (M09) | Append a comment to a rule file | BLOCKED: rule file hash changed |
| A9 (M09) | Rename/disable a rule and re-hash the file | BLOCKED: executed catalog differs from manifest |
| A2 (M08) | New unclassified `.ts` file | BLOCKED: unclassified code file |
| A3 (M08) | Executable `.mts` the engine cannot target | BLOCKED: scanned paths differ (missing 1) |
| A4 (M08) | Symlink to `/etc/hosts` | BLOCKED: symlink or path escape |
| A5 (M08) | Target over 1 MiB | BLOCKED: oversize target |
| A6 (M10) | Wrong `semgrep-core` hash in manifest | BLOCKED: binary hash mismatch |
| A7 (M07) | Malformed production Python accepted by the engine | BLOCKED by `ast.parse` gate |
| A7b (M07) | Malformed production TS accepted by the engine | **Not blocked by harness**: documented gap, relies on `tsc` (G4) |
| A8 (M08) | Unsafe `shell=True` in production with `# nosemgrep` | Detected (2 findings, non-zero exit) |
| A10 (M13) | Socket connect under the scan sandbox profile | Denied (`gaierror`). Same call without sandbox reachable |

## Regression and repository checks

| Check | Result |
| --- | --- |
| `python3 -m unittest discover -s tests/delivery` | 22 tests OK |
| `gitleaks dir --redact` (8.30.1, matches pin) on full tree incl. fixtures | No leaks before the JSON record was written. **Erratum (C5-F2):** the JSON later produced 11 false positives, which were fixed by a lossless reformat; see [F2](m4c-c5-f2-linux-feasibility.md#f1-evidence-correction) |
| `python3 scripts/check_repository.py`, `git diff --check`, untracked no-index whitespace | See final report in the JSON record |

Application (npm, browser, container, C3 P01–P15) suites were **not rerun**,
because no application, test or workflow file changed. C1/C3/C4 evidence is
preserved unchanged.

## Limitations and not done

* Linux execution, hosted-runner timing and Linux egress denial are unverified (G3).
* The plan's M11/M12 (engine crash/timeout/forged report), M14 (canary capture)
  and M15–M20 (workflow, aggregate, privilege, governance) were not exercised.
  The harness has validators for report shape, exit/finding contradiction and
  deadline, but these were not mutation-tested in F1.
* Rules are single-function and name-based for logging. The five `todoruleid`
  blind spots are representative, not exhaustive. Rules have not had an
  independent human review.
* `sandbox-exec` is deprecated by Apple but functional on macOS 15. The
  environment allowlist cannot prove the absence of all side channels.
* Semgrep wrote an anonymous settings ID only into the temporary HOME, which was
  deleted after each run.

## Reproduce

```sh
python3.12 -m pip download --require-hashes --no-deps --only-binary=:all: \
  -d "$TMP/wheels" -r requirements-sast-macos.txt
python3.12 -m venv "$TMP/venv"
"$TMP/venv/bin/python" -m pip install --no-index --no-deps --only-binary=:all: \
  --require-hashes --find-links "$TMP/wheels" -r requirements-sast-macos.txt
python3 -I scripts/sast/feasibility.py --semgrep "$TMP/venv/bin/semgrep" --repeat 5
```

The expected exit is 1 while G1 stays open (controls pass, source has 1 finding).
Exit 2 means a fail-closed BLOCK.
