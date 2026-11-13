# M4C-C5-F3 — Local SAST harness hardening

Date: 2026-11-13 UTC. Base: `8ffb62d` plus the uncommitted, preserved
[F1](m4c-c5-f1-semgrep-feasibility.md) and [F2](m4c-c5-f2-linux-feasibility.md)
work. Authority: owner direction to implement **only C5-F3**. Status:
**locally executed on macOS arm64 (native) and Linux x86_64 (Rosetta
emulation)**. This is not hosted CI evidence and not C5-A1 acceptance. Azure
deployment remains **NO-GO**.

There were no CI workflow, GitHub setting, Azure, paid service, dependency
upgrade or advisory waiver changes, and no commit or push. Production
application code is unchanged; one application **test** file changed (G1).
Destructive mutations ran only on copies inside one explicitly created
disposable directory. The runner rejected empty paths, symlinked paths and
paths outside that directory, and the repository was never mutated.

## Outcome

| Gap | F3 result |
| --- | --- |
| **G1** SQL test finding | **Resolved.** Complete literal statements are used and the real source scan is clean (0 findings) on both platforms. There was no suppression, rule change or waiver |
| **G6** harness fail-open | **Resolved for the F2 cases**: catalogue, exhaustive classification, exit codes, fatal `pip check`, plus installed-file RECORD verification. 31/31 (macOS repo group) + 3/3 (macOS venv group) and 34/34 (Linux) mutation cases behave as specified. Residual limits are listed below |
| **G3** isolation diagnostics | **Improved, still unverified on a hosted runner.** The isolation probe fails closed with exit 5 and precise facts, and sudo is never invoked |
| **G5** native libraries | **Not resolved.** The [inventory](../../security/sast/native-libraries.json) of 33 native files is complete. The wheels and the pinned public source tree have no notices or SBOM, and versions are heuristic only |
| **G2** dependency advisories | **Open and unchanged**, not in F3 scope (no upgrades or waivers) |
| **G4** engine-accepted malformed TS | Open by design. Mutation T03 still passes the harness, so the job must follow the mandatory `tsc`/ESLint jobs |

**Hosted trial readiness: ready for a separately authorized, dispatch-only,
non-blocking hosted trial.** Such a trial is needed to settle G3 on a real
runner and to measure native timing. It requires a workflow change, which is
not made here. **Mandatory SAST CI remains NO-GO** until G3 is verified on
hosted runners, G2 has an explicit owner decision, and G5 notices or an SBOM
are resolved or formally decided.

## G6 repairs (harness `scripts/sast/feasibility.py`)

| Requirement | Implementation |
| --- | --- |
| Exact control catalogue | [`security/sast/controls.json`](../../security/sast/controls.json) lists 23 fixtures (path, SHA-256, kind) and the exact 64 expected cases. It also records parser-gap engine and `ast` expectations. Its SHA-256 is pinned in [`toolchain.json`](../../security/sast/toolchain.json). `--emit-catalogue` prints a candidate for human review and writes nothing |
| Missing, renamed, altered or extra fixtures | The fixture set on disk must equal the catalogue, and every hash must match. Kinds must match locations; unsupported fixture types and security rules without a positive control are rejected. Parsed annotations must equal the catalogued cases. Parser-gap behaviour drift exits 4 |
| Exhaustive classification | Every file outside the named generated directories is classified (213 files). Scanned: `.ts/.tsx/.js/.jsx/.mjs/.cjs/.py` by reviewed class. Explicit exclusions: one reviewed shell script and `.d.mts/.d.cts` declarations. Non-code files use reviewed extension and name lists, and they reject an executable bit or shebang. Unsupported executable extensions (`.mts/.cts/.pyw/.go/…`), unknown types and unreviewed `.sh` files exit 2 |
| Exit codes | 0 clean · 1 findings · 2 configuration error · 3 tool error · 4 control failure · 5 isolation unavailable |
| Fatal `pip check` | A non-zero `pip check` in the tool venv exits 2. The installed distribution set must equal the platform lock exactly, and the lock hash must match the manifest |
| Additional integrity | Every installed file with a RECORD hash is verified: 3,224 on macOS and 3,310 on Linux, including Semgrep's Python code and entry script. The engine is launched with the verified venv interpreter, not via the entry script's shebang |
| Safe outputs | The summary (`artifacts/sast/c5-summary.json`, ignored) uses `"sha256  path"` lines, avoiding the F1 gitleaks false positive. Raw reports stay 0600 under `artifacts/sast-private/c5/` |

## Isolation diagnostics (G3)

Before any scan, the harness runs a loopback probe inside the isolation wrapper.
The probe connects to `127.0.0.1:9`, so it creates no external traffic. It
accepts only `EPERM`, `EACCES` or `ENETUNREACH` as proof of isolation.

| Profile | Result |
| --- | --- |
| macOS `sandbox-exec deny network*` | Probe `EPERM` → scan proceeds |
| Linux uid 1001, user namespaces permitted (L3) | `unshare --net --map-root-user`, probe `ENETUNREACH` → exit 0 |
| Linux uid 1001, Docker default seccomp (L2) | **Exit 5:** `unshare failed: Operation not permitted` with `max_user_namespaces=31322, unprivileged_userns_clone=absent, apparmor_restrict_unprivileged_userns=absent, seccomp_mode=2, euid=1001, container=yes`. The message states that sudo is never invoked automatically |
| Linux root, default seccomp, no CAP_SYS_ADMIN (L1) | Exit 5 with the same diagnostic, euid=0 |
| Linux root with CAP_SYS_ADMIN (L5) | Operator-chosen root run: `unshare --net` without a user namespace, probe `ENETUNREACH` → exit 0. The harness never escalates by itself |

A connection that is refused or succeeds means the network is not isolated,
and the harness exits 5. Hosted Ubuntu 24.04 AppArmor policy still cannot be
reproduced locally because this kernel has no AppArmor.

## G1 fix

`apps/octocat-supply/api/test/repository-sqlite.contract.test.ts` (+12/−3): a
`failureTriggers` constant maps `INSERT`/`UPDATE`/`DELETE` to three **complete
literal** `CREATE TRIGGER … RAISE(FAIL, 'contract injected post-write failure')`
statements. The test calls `store.db.exec(failureTriggers[operation])`. Test
names, the `it.each` cases, the RAISE message and all assertions are unchanged,
and no production file changed.

| Check | Result |
| --- | --- |
| File before / after | 33/33 → 33/33 |
| Intent mutation (temporary, restored by hash) | `UPDATE` trigger set to fire on INSERT → S01/UPDATE **fails**. Restored file passes 3/3 S01 |
| Prettier / ESLint / `tsc -p tsconfig.tests.json` | Pass |
| SAST source scan | macOS and Linux: **0 findings**, exit 0 |

## G5 native-library inventory

[`security/sast/native-libraries.json`](../../security/sast/native-libraries.json)
records each bundled library: wheel member, SHA-256, size, SONAME or install
name, upstream project, heuristic version and evidence type, build evidence,
expected upstream licence (marked *unverified*) and `licence_text_in_wheel:
false`.

* **Linux (26):**
  * OpenSSL libssl/libcrypto (3.5.8 string);
  * curl 7.76.1, zlib 1.2.11, xz 5.2.5, nghttp2 1.43.0;
  * MIT Kerberos (4 libraries), keyutils 1.6.3, com_err, libselinux 3.6;
  * elfutils libdw/libelf, libunwind, libev 4.33, gmp 6.2.0;
  * pcre2 10.40, zstd 1.5.5, bzip2, tree-sitter 0.26;
  * glibc libm/libresolv, GCC libstdc++/libgcc_s.

  The only build marker is Red Hat GCC 11.5.0-14, and the versions are
  consistent with RHEL 9-family packages. Those **backport fixes**, so
  version-based advisory matching is unreliable without the builder's SBOM.
* **macOS (7):** libdwarf, libev, gmp, pcre2, zstd (1.5.7) copied from Homebrew
  (`/opt/homebrew/opt/<formula>` install names), plus tree-sitter, built in a
  `semgrep-proprietary` CI checkout. libcurl and libc++ come from the system.
* **Evidence of absence:**
  * Neither wheel has a notice or SBOM member; macOS ships only Semgrep's own
    LICENSE.
  * The pinned public tree `9240f708` has no third-party notice or SBOM for
    these libraries.
  * `scripts/build-wheels.sh` packages a prebuilt `semgrep-core`.
* Expected copyleft or exception licences include elfutils, GMP, glibc
  libraries, keyutils, libdwarf and the GCC runtime. Obligations would
  matter if the wheelhouse were ever **redistributed**, for example as a cached
  CI artifact.

G5 closure needs one of three things: the publisher's SBOM and notices, an
owner decision to obtain upstream licence texts at confirmed versions, or a
formal risk decision. Unconfirmed heuristic data was not presented as an SBOM.

## Fail-closed mutation matrix

Disposable directory: `scratchpad/f3-matrix.NOsDQY`. It was created with
`mktemp -d`, its resolved path was confirmed, and its pristine snapshot was
verified against all 213 repository files. The scratch runner (`f3_matrix.py`,
not in the repo) refused an empty base, the repository path, the scratchpad
root and a `/tmp` symlinked path before any case ran. Each case used a fresh
copy that was deleted afterwards. The repository was never mutated. Ranges in
the ID column cover consecutive case IDs.

| ID | Mutation | Expected = actual (macOS and Linux) |
| --- | --- | --- |
| B00 | Unmodified copy | 0 |
| C01–C03 | Rule altered; toolchain manifest missing (F2 F06); manifest malformed | 2 |
| C04–C06 | Catalogue missing; catalogue altered without re-pin; jwt cases dropped **with** re-pinned hash | 2 (the last via annotation/catalogue mismatch) |
| C07–C12 | Positive fixture deleted (F2 F07); malformed fixture deleted (F2 F08); fixture renamed; annotation flipped; uncatalogued fixture; unsupported fixture type | 2 |
| C13–C21 | `.go` (F2 F16); `.pyw` (F2 F17); `.mts`; `.cts`; `.xyz`; extensionless shebang script; non-code file with exec bit; shebang in `.txt`; unreviewed `.sh` | 2 |
| C22–C24 | Symlink escape; oversize target; lock altered | 2 |
| T01, T02 | Malformed production Python (ast gate); engine-rejected malformed TS | 3 |
| T03 | Engine-accepted malformed TS (G4, documented) | 0 (known gap) |
| F01 | Production `shell=True` with `# nosemgrep` | 1 |
| K01, K02 | Rule weakened **and** re-pinned (control missed); parser-gap expectation drift and re-pinned | 4 |
| P01–P03 | Dependency uninstalled from venv copy (`pip check` fatal); tampered `semgrep/cli.py` (RECORD); tampered `semgrep-core` | 2 |

Totals: macOS 31/31 repo cases plus 3/3 venv cases, and Linux 34/34 (L3).

## Measurements

| Measure | macOS arm64 (native) | Linux x86_64 (Rosetta, L3) |
| --- | --- | --- |
| Source scan, 65 files, 5 runs (s) | 1.69, 2.02, 1.79, 1.89, 1.49 | 3.37, 3.40, 3.54, 3.51, 3.44 |
| Control scan (s) | 1.56 | 2.76 |
| Full harness incl. toolchain/RECORD/probe (s) | 14.2 | 27.5 |
| Engine `max_memory_bytes` | 174,753,408 | 151,445,824 |
| Peak process RSS | 245,399,552 B (`time -l`) | 294,740 KiB (`getrusage`); about the same in exit-5 runs, so it comes from preflight, not the engine |

## Regression and security checks (working tree)

| Check | Result |
| --- | --- |
| `npm test` | 13 files, **195/195** |
| `npm run typecheck` / `lint` / `format:check` / `test:auth-mutations` | Pass / pass / pass / all mutations rejected |
| `npm audit --audit-level=high` | Exit 0. The 10 moderate advisories are pre-existing; no dependency changed |
| `python3 -m unittest discover -s tests/delivery` | 22 OK |
| `actionlint` 1.7.12, `validate_infra.py` (bicep 0.48.1), `scan_config.py` (Trivy 0.72.0) | Pass. Tools were installed by `install_tools.py` with pinned SHA-256 into a scratch directory |
| `gitleaks dir` and `gitleaks git --log-opts=--all` (8.30.1) | No leaks |
| `check_repository.py`, `git diff --check`, untracked no-index whitespace | See [JSON record](m4c-c5-f3-harness-hardening.json) |

Not rerun: Playwright browser/OIDC journeys, container builds/proxy/image
scans. No application runtime, container or proxy file changed.

## Changed files in F3

* New:
  * `security/sast/controls.json`, `security/sast/native-libraries.json`;
  * this document and its JSON record.
* Modified:
  * `scripts/sast/feasibility.py` (hardening);
  * `security/sast/toolchain.json` (catalogue pin, inventory pointer, purpose);
  * `apps/octocat-supply/api/test/repository-sqlite.contract.test.ts` (G1);
  * status lines in `README.md`, `AGENTS.md`, `docs/capability-status.md` and
    `docs/milestones/m4c-c5-sast-plan.md`.
* Unchanged: rules, locks, fixtures, CI workflows and production application code.

## Remaining limitations

* **Same-change tampering:** anyone who can edit the harness, rules,
  catalogue and manifest together can change the verifier. K01/K02/C06 show
  that consistent re-pinning is still caught when controls or annotations
  disagree, but governance (C5-A2) remains the real control.
* RECORD verification detects modification, but an attacker who also rewrites
  RECORD evades it. Wheel hashes are enforced only at install time.
* Engine-accepted malformed TS (G4), HTML inline script, workflow YAML,
  Bicep/KQL and shell are outside the CE claim and rely on other checks.
* There is no reviewed source-target manifest, so a deleted source file is not
  flagged. Deleted code cannot hide a finding.
* The executable-bit check depends on the checkout preserving file modes.
* Linux results are emulated, there is no AppArmor locally, and
  `sandbox-exec` is deprecated by Apple.
* The isolation probe proves loopback denial, which implies interface
  removal on Linux; it does not test every side channel.
* G2 and G5 are open, and the five `todoruleid` blind spots and
  single-function limits remain.
