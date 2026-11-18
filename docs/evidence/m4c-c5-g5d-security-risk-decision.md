# M4C-C5 — G5D consolidated security-risk decision

Date: 2026-11-17 UTC. Base: `2b050a1` plus the uncommitted F4R, E03, G2, G5, G5B
and G5C work. This document consolidates
[G2](m4c-c5-g2-dependency-assessment.md),
[G5](m4c-c5-g5-native-library-assessment.md),
[G5B](m4c-c5-g5b-sbom-static-inventory.md) and
[G5C](m4c-c5-g5c-vulnerability-assessment.md). Its only new technical step is
the schema validation. There was no upgrade, dispatch, CI or GitHub change,
Azure work, external message, commit or push.

**E04 (mandatory CI), release and redistribution remain NO-GO.**

## Recorded owner decision (2026-11-17)

The owner approved the following. It is recorded verbatim in scope and is not a
waiver: every advisory stays open and visible.

| # | Decision |
| --- | --- |
| D1 | **G2 conditionally accepted, including GHSA-mf5v-w3w3-f6cg** (V1 and V2), for **local trusted-repository scans** and **separately authorised non-blocking trials** |
| D2 | **G5 findings V3–V8 conditionally accepted** for the same two uses |
| D3 | **Expiry: 2026-12-17.** All early-stop conditions (section 6) and mandatory controls (sections 2 and 4) apply unchanged |
| D4 | **SBOM v2 adopted as the current assessment baseline:** [`semgrep-toolchain-1.185.0.v2-candidate.cdx.json`](../../security/sast/sbom/semgrep-toolchain-1.185.0.v2-candidate.cdx.json) (SHA-256 `70a38b40fddcb7a460d96b5e1b5170927d2f695f4128cf50ba0c8eab5d668fe7`). Frozen v1 [`semgrep-toolchain-1.185.0.cdx.json`](../../security/sast/sbom/semgrep-toolchain-1.185.0.cdx.json) (`499477a22a78fe309b83fa289acf47cb93140fdd192f7a3509ecb4953ac93d81`) is preserved unchanged |
| D5 | **G2 and G5 remain OPEN.** All advisories remain visible; the SBOM `analysis.state` values are unchanged (27 `in_triage`, plus 2 Windows-only `not_affected`) |
| D6 | **Mandatory CI (E04), release and redistribution remain NO-GO** |

Notes on the record:

* **Scope.** The accepted uses are narrower than the earlier G2 wording ("local
  development and the existing non-blocking trial"), which this decision
  supersedes. Accepted scanning covers only the owner's trusted repository,
  through the hardened harness. Each hosted trial still needs its own owner
  authorisation; this decision authorises no dispatch.
* **SBOM file name.** The v2 file keeps its file name and its internal
  `c5:status` property ("CANDIDATE v2"). Changing either would alter the
  schema-validated, hash-recorded artifact. This decision record governs its
  baseline status.
* **Lapse.** On 2026-12-17, without a recorded renewal, both acceptances lapse
  and all scanning stops (section 6). An early-stop condition ends them at once.

## 1. Confirmed vulnerabilities in the pinned toolchain

"Confirmed" means the affected version **and** the affected code are present.
**None was shown reachable from scanned input**; the "Reachability evidence"
column states how strong that conclusion is.

| # | Component | Advisories | Severity (source) | Exploit prerequisite | Reachability evidence |
| --- | --- | --- | --- | --- | --- |
| V1 | `mcp` 1.29.0 (Python) | GHSA-5h93, -84m7, -rwrf, -w4fh | MODERATE | Acting as an MCP HTTP client or server | **Dynamic:** only a logger function called; no transport, session or auth code ran (G2) |
| V2 | `opentelemetry-api` 1.37.0 | GHSA-xcq7 (tracestate), **GHSA-mf5v (traceparent, new 2026-11-13)** | MODERATE | Attacker-controlled trace header reaching `extract()` | **Dynamic:** `extract()`/`from_header` never called; tracing no-op (G2) |
| V3 | OCaml runtime `5.4.0+semgrep-fork@4046c817` (Marshal) | OSEC-2026-01 (CVE-2026-28364), -18, -23 | CVSS 3.1 AV:L, C:H/I:L | Attacker-supplied marshalled data | **Static only:** callers limited to Parmap worker IPC, `Lwt_io.read_value`, profiling, natdynlink; no direct path from scanned files (G5C) |
| V4 | Same runtime (`Str`, `Unix.map_file`) | OSEC-2026-21, -22 | CVSS 4.0 AV:L, VA:H | Attacker-chosen regex input or mapping dimensions | **Static only:** no direct caller of `Str.string_partial_match`; `map_file` sizes are internal |
| V5 | Same runtime (`runtime_events` consumer) | OSEC-2026-25, -26 | CVSS 4.0 AV:L, high impact | Corrupt event ring read by a consumer | **Static only:** cursor creation has no caller |
| V6 | OpenSSL 4.0.3 inside `cryptography` 50.0.2 | CVE-2026-124709, -35190, -88822, -88823, -95691, -95692 | Up to CVSS 3.1 AV:N C:H or I:H (AES-GCM-SIV); QUIC AV:A | A QUIC or TLS-server peer, or app use of AES-GCM-SIV | **API and partial dynamic:** no QUIC or TLS-server API exposed; no AES-GCM-SIV user in the toolchain; only import-time Python helpers run (Rust calls not observable) |
| V7 | AlmaLinux builds bundled in the Linux wheel | 6 ALSA (curl, OpenSSL, glibc ×2, gcc/libstdc++, xz) | Moderate (vendor) | Network peers, loader or DNS, or (libstdc++/xz) crafted data | **By component:** network and loader paths unreachable offline; libstdc++ and liblzma not determined, but no `from_chars` or parallel symbols (G5, G5B) |
| V8 | libdwarf 2.3.3 (macOS wheel) | CVE-2026-116732 | CVSS 4.0, local, low | Crafted object file | **By component:** reads `semgrep-core`'s own debug data (G5) |

* **Potentially affected (applicability unconfirmed):**
  * PCRE2 OSV-2026-343: reported for the 32-bit library; only the 8-bit one is
    bundled.
  * Seven `dev` pins that can't be matched by version.
* **Demonstrably not affected:**
  * Windows-only OSEC-2026-05/-24, and the 4.x-only OSEC-2026-04;
  * mirage-crypto 2.4.1, `tls` 2.1.3 and `cohttp` 6.3.0 (at or above every
    fixed version);
  * SQLite and Mbed TLS, which are not linked;
  * the npm MAL reports, because npm is not used.

## 2. Controls that prevent or reduce exploitation

| Control | Verified by | Mitigates |
| --- | --- | --- |
| Network isolation, verified before every scan (macOS sandbox, Linux namespace, Docker `--network none`) | F3/F4R checks; G2 trace (no connect or DNS) | V1, V2, V6, V7 (all network-path issues) |
| Fixed `scan` subcommand, `--no-trace`, `--metrics=off`, `--oss-only` | G2 guard test (8/8, 17 mutations rejected) | V1, V2 |
| Exact engine environment allowlist; per-run scratch `HOME` (no stored login, caches or stale marshalled files) | G2 guard; E03 M14 | V2, V3 (no pre-existing marshalled input) |
| Hardened container (uid 1001, no capabilities, no-new-privileges, seccomp, read-only root, noexec tmpfs, limits) | F4R; hosted run 43478654843 | Impact of any memory-safety bug (V3–V8) |
| Hash-locked offline install, RECORD and engine hash, fatal `pip check` | F1–F3 | Substitution with worse code |
| Fail-closed harness (forged, partial or crashed output; evidence integrity) | E03 (28/28 per platform), 34-case matrix | Silent false "clean" results after a crash |
| Scanned input is the owner's own private repository; rules are local and reviewed | Repository governance | Attacker control of parser input |
| Non-blocking, dispatch-only trial; only six allowlisted JSON files uploaded | Trial validator, `actionlint` | Release impact; redistribution |

## 3. Evidence gaps and residual risk

* **Reachability is static only for V3–V5.** Closure-indirect OCaml calls,
  macOS, and native runtime tracing were not analysed. The Python trace cannot
  see Rust or C calls (V6).
* **Versions inferred, not proven:**
  * lockfile-inferred opam versions (84/84 corroborated);
  * a superset of Rust crates;
  * tree-sitter 0.26.3;
  * libyaml 0.2.5.

  Grammar versions and the `dev` pins are unknown.
* **Not assessed:** grammar sources, Semgrep's own and vendored code,
  backward-cpp, murmur3, upb, ruamel's libyaml-derived C. "No known advisory" is
  not proof of safety.
* **Provenance:** `semgrep-core`, the tree-sitter runtime and the grammars were
  built from a non-public tree with no reproducible build. No third-party
  notices ship.
* **Verification:** hosted acceptance used the pre-E03 harness; Linux results
  are partly emulated; there is no independent reviewer (C5-A2), `main` is
  unprotected and CodeQL is skipped.
* **Residual risk:** **Low** for offline scans of the owner's own repository
  under the controls above. It rises materially if scanned input becomes
  untrusted (third-party pull requests), if network or tracing controls drift,
  or if artifacts are redistributed.

## 4. Recommendations by use

| Use | Recommendation | Conditions |
| --- | --- | --- |
| **Local development** (toolchain installed; app development) | **GO** | The tool is never imported by or shipped with the application. No credentials in the tool environment |
| **Local Semgrep scans** | **GO, conditional** | Only through the hardened harness with isolation verified. Scan only owner-controlled repository content and local rules. G2 guard and SAST suite passing |
| **Existing non-blocking hosted trial** | **GO, conditional** | Dispatch only on explicit per-run owner authorisation. OSV and upstream recheck before each dispatch. Still non-blocking with the six-file artifact allowlist. The next run should re-verify the E03 fixes |
| **Mandatory CI (E04)** | **NO-GO** | See section 7 |
| **Redistribution** (wheels, venv, wheelhouse, image, mirror) | **NO-GO** | Licence and notice obligations unmet; `semgrep-core` source correspondence unverifiable (G5-5) |

## 5. Is the G2/G5 conditional acceptance defensible?

**Yes for local development, local scans and the non-blocking trial,** on four
grounds:

* there is no demonstrated reachability, and the prerequisites (network peers,
  MCP serving, trace headers, marshalled or crafted inputs) are absent or
  blocked;
* the controls are verified and regression-tested;
* scanned input is owner-controlled;
* no remediation is available to the project today. V1, V2, V3–V5 and V7 need a
  new Semgrep release; V6 needs a new `cryptography` release.

**Two adjustments are required:**

1. The current G2 acceptance names five advisories. It must explicitly add
   **GHSA-mf5v-w3w3-f6cg**, or local and trial use should pause.
2. V3–V8 have **no recorded acceptance yet**. They need an explicit owner
   decision with the same scope and expiry.

**Not defensible for mandatory CI:**

* a release gate would scan untrusted contributions;
* V3–V6 rest on static or partial reachability evidence;
* governance gaps (C5-A2, E06) and G4 remain open.

## 6. Early-stop conditions and expiry

**Proposed expiry: 2026-12-17**, aligned with the existing G2 acceptance, for G2
(including GHSA-mf5v) and V3–V8. Review earlier at the first of:

* a Semgrep release;
* a `cryptography` release built with patched OpenSSL;
* an update to `semgrep/ocaml`.

Without a recorded renewal the acceptance lapses, and every use other than
local development becomes **BLOCK**.

**Stop immediately (BLOCK all scanning) if any of these happens:**

1. A HIGH or CRITICAL advisory appears for any SBOM component, or a known
   exploit appears for V1–V8.
2. Any vulnerable path is shown reachable from scanned files or rules.
3. The G2 guard, E03 suite, 34-case matrix, isolation verification or
   `pip check`/RECORD/hash preflight fails.
4. The harness flags, environment, isolation, container hardening or artifact
   allowlist change without owner review.
5. Untrusted or third-party content would be scanned, or the trial is made
   blocking or triggered automatically.
6. Any toolchain artifact (wheels, venv, wheelhouse, image) is uploaded, cached,
   pushed or otherwise redistributed.
7. The lock, the engine or the SBOM no longer match their recorded hashes.

## 7. Minimum remediation before E04

All of the following are required. None is waived.

1. **Toolchain vulnerabilities:** move to a Semgrep release that:
   * clears `mcp` (≥ 1.30.0) and `opentelemetry-api` (≥ 1.45.2);
   * is built on an OCaml runtime containing the OSEC-2026-01/-18/-21/-22/-23/-25/-26
     fixes (≥ 5.5.2, or verified backports in `semgrep/ocaml`);
   * ships rebuilt AlmaLinux libraries.

   Also re-lock `cryptography` to a release built with patched OpenSSL; that is
   a separately authorised lock change. Any residual must have a recorded owner
   acceptance that names the CI scope.
2. **Re-verification on the new toolchain:**
   * F1–E03 checks, the 34-case matrix and the G2 guard;
   * a regenerated SBOM, schema-validated;
   * a fresh OSV and upstream query with no unreviewed confirmed-present
     advisory;
   * a native-Linux hosted run that verifies the E03 fixes.
3. **Reachability for untrusted input:** dynamic native tracing (or equivalent)
   of a scan over adversarial inputs, covering Marshal, PCRE2, libyaml and
   tree-sitter paths. Alternatively, an owner decision that CI only scans
   trusted branches.
4. **Licensing:** confirm that CI use involves no redistribution, and keep the
   artifact allowlist. Notices and the static inventory remain needed only for
   redistribution.
5. **Open gates:**
   * G4 (malformed TypeScript accepted by the engine; needs tsc/ESLint
     ordering);
   * C5-A1/A2 and E06 governance (branch protection, independent reviewer,
     CodeQL decision);
   * E05 independent coverage review.

## 8. SBOM v2 schema validation

| Check | Result |
| --- | --- |
| Official schema | CycloneDX `specification` tag **1.6.2** (commit `e833d732`): `bom-1.6.schema.json` SHA-256 `18f57f74…b37d`, `spdx.schema.json` `c4191719…dbe6`, `jsf-0.82.schema.json` `8bae002c…0aae` |
| Validator | `jsonschema` 4.25.1 (Draft 7, the schema's declared draft) with `referencing` 0.37.0 resolving the local copies; format checking enabled |
| **v2 candidate** (`70a38b40…8fe7`) | **Valid: 0 errors** |
| Frozen v1 (`499477a2…3d81`, read only, unchanged) | Valid: 0 errors |
| Negative controls (mutated copies in scratch) | 7 of 8 rejected: invalid analysis state, hash algorithm, component type, VEX justification, SPDX id, serial number, missing `bomFormat`. `specVersion` "9.9" is accepted because the schema leaves that field unconstrained |
| Formats not enforced by the validator | `date-time`, `uri`, `iri-reference` (optional libraries absent). Checked manually: timestamp is RFC 3339, and all 29 vulnerability source URLs are well-formed https |

The v2 candidate is schema-valid and suitable to adopt, if the owner chooses.
v1 remains the frozen record.

## Owner decisions (resolved 2026-11-17)

The four questions this paper raised are resolved by D1–D6 above:

1. G2 is extended to GHSA-mf5v.
2. V3–V8 are accepted for the same uses.
3. SBOM v2 is adopted.
4. E04, release and redistribution stay NO-GO until section 7 is met.

**Next review:** before 2026-12-17, or earlier on any early-stop condition or a
Semgrep, `cryptography` or `semgrep/ocaml` release.

## Changed files (G5D)

* New: this document. The owner decision (D1–D6) was added on 2026-11-17.
* Decision addenda: the G2, G5, G5B and G5C evidence (Markdown and JSON).
* Modified (status lines only): `README.md`, `AGENTS.md`,
  `docs/capability-status.md`, `docs/milestones/m4c-c5-sast-plan.md`.
* Unchanged: both SBOM files, all evidence, locks, toolchain, harness, tests,
  workflows and application.
