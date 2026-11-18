# M4C-C5 — G5B toolchain SBOM and static component inventory

Date: 2026-11-17 UTC. Base: `2b050a1` plus the uncommitted, preserved F4R, E03,
G2 and [G5](m4c-c5-g5-native-library-assessment.md) work. Authority: owner
direction for an **offline, static investigation of existing verified
artifacts**. Machine-readable record: [JSON](m4c-c5-g5b-sbom-static-inventory.json).

The investigation was offline: no network access and no new downloads. Inputs
were the lock-verified wheelhouses and the binaries and evidence already
verified in F1–G5. There was no dependency, lockfile, rule, application, CI
workflow or GitHub setting change, no dispatch, no Azure work, no publication,
and no commit or push.

## Owner decisions in force

| Use | Decision |
| --- | --- |
| Local development | Conditionally accepted |
| Existing non-blocking trial | Conditionally accepted |
| Redistribution | Prohibited |
| Mandatory SAST CI | NO-GO |
| Vulnerabilities and licensing gaps | Not waived |

## Result

| Use | Recommendation after G5B |
| --- | --- |
| Local development | **GO** (unchanged conditional acceptance) |
| Non-blocking trial | **GO** (unchanged; no redistribution) |
| Mandatory SAST CI | **NO-GO** (G2, G5 and G5B-1 to G5B-6 open) |
| Redistribution | **NO-GO**: prohibited (G5-5, G5B-4, G5B-5) |

G5 stays **open**. Nothing is waived.

## Project-owned SBOM

[`security/sast/sbom/semgrep-toolchain-1.185.0.cdx.json`](../../security/sast/sbom/semgrep-toolchain-1.185.0.cdx.json)
is in CycloneDX 1.6 JSON format. The SHA-256 is recorded in the JSON record. It
contains 418 components, typed dependencies, compositions and 13 vulnerability
records.

* **Scope:**
  * the Python wheels for both locks (all 134 wheel files re-verified against
    the lock hashes);
  * the 33 bundled native libraries;
  * both `semgrep-core` binaries and their statically linked components;
  * statically linked code inside other wheels.

  The container runtime image and host system libraries are excluded.
* **Vulnerabilities:** every record has `analysis.state: in_triage`. None is
  marked `not_affected` or `resolved`, so the SBOM itself waives nothing.
* **Compositions:** the toolchain and `semgrep-core` are `incomplete`;
  wheel-internal static code is `unknown`.
* **Validation:** offline structural checks only:
  * every `bom-ref` is unique;
  * every dependency, vulnerability and composition reference resolves;
  * every hash is SHA-256 shaped;
  * licence entries are SPDX expressions only when every term is a known SPDX
    identifier, and are otherwise kept as declared names;
  * there are no local paths.

  The official CycloneDX JSON schema was not available offline.

| Evidence class | Components | Meaning |
| --- | --- | --- |
| Confirmed, cross-verified | 109 | 77 lock-verified wheel entries (67 packages; 10 platform-specific), 30 native libraries traced to signed RPMs or bottles (G5), 2 `semgrep-core` files |
| Build metadata | 86 | Linux opam package versions from DWARF build directories (84), and the OCaml runtime (2). Reproducible from the binary, but not cross-verified against source archives |
| Inferred | 89 | 3 tree-sitter runtime files, 84 macOS opam packages (from symbol parity with Linux), the libyaml-derived code in ruamel.yaml.clib, and the upb runtime in protobuf |
| Version claim only | 3 | libyaml in `semgrep-core` (2), OpenSSL inside `cryptography` |
| Present, version unknown | 78 | 34 grammars, backward-cpp, C++ standard-library header code and 3 Semgrep OSS libraries, per platform |
| Unknown | 53 | Libraries built in Semgrep's dune workspace (versions unknown), and Rust crates |

## `semgrep-core` static inventory

**Method.** The Linux binary (SHA-256 `38fd0879…672d`) keeps a full symbol table
(601,392 symbols) and DWARF debug data. All 2,070 DWARF compile units were
parsed for name, build directory and producer. They were built with GCC 11.5.0
(Red Hat 11.5.0-14) and GNU as 2.35.2. The macOS binary (SHA-256
`4bfb5ad1…e9f5`) has 596,247 symbols and no DWARF. Its composition is inferred
from symbol parity: 1,030 of 1,032 OCaml top-level modules are shared, and the
Linux-only `Eio_linux` and `Uring` are expected.

| Suspected or found | Result | Evidence |
| --- | --- | --- |
| **OCaml runtime** | **Present: `5.4.0+semgrep-fork@4046c817ed2ed5c2431300902d1bd306230bf3dd`** | Embedded string on both platforms; 345 Linux units from `ocaml-variants.5.4.0`. A **Semgrep fork**; its source is not verifiable offline |
| **libyaml** | **Present (statically linked); version claim 0.1.7** | 36 defined `yaml_*` functions on both platforms. `yaml_get_version` returns 0,1,7 and `yaml_get_version_string` returns `"0.1.7"` (compile-time constants). Linked via `yaml.3.2.0` (ocaml-yaml). The C sources carry no DWARF. Treated as a **claim**, not a confirmed revision |
| **SQLite** | **Not linked** | No `sqlite3_*` symbols on either platform. "SQLite format 3" is a magic-bytes entry next to `GIF89a` and `gimp xcf` in binary-file detection |
| **Mbed TLS** | **Not linked** | No `mbedtls_*` symbols. "MBEDTLS" appears only as `CURLSSLBACKEND_MBEDTLS` in the curl binding |
| **libstdc++** | Shared library, plus header templates compiled in | Linux: one C++ unit (`backward.cpp`, from `obackward.dev`) and 561 weak `std::` instantiations from the GCC 11 headers. macOS: Apple libc++ header code (712 symbols). **No `std::from_chars` or parallel-mode symbols** (the G5 ALSA-2026:98524 paths); fully inlined use cannot be excluded |
| OCaml TLS and crypto stack | Present | `tls` (version unknown), `x509.1.2.0`, `mirage-crypto*.2.4.1`, `asn1-combinators.0.3.3`, `ca-certs.1.0.3`, `digestif.1.4.1`, `kdf.1.1.2`. Network code, not used by offline scans; reachability not traced |
| opam packages | 84 versioned, including `zarith.1.14`, `ctypes.0.24.0`, `curl.0.10.0`, `lwt.6.1.2`, `eio.1.2`, `yojson.3.0.0` and `menhirLib.20230608` | Build-directory names in DWARF. Two are unreleased `dev` pins: `pcre2.dev` and `obackward.dev`. Full list in the JSON |
| Built inside Semgrep's dune workspace | 40 top-level groups: Semgrep's own code plus `cohttp*`, `http`, `lsp`, `jsonrpc`, `astlib` (ppxlib), `atdgen-runtime`, `lib_eio*` and `diff` | `/workspace_root` units. **Versions unknown** |
| Identified by symbol prefix only | Re, Sexplib, Ppxlib runtime, Tls, Opentelemetry, Memtrace, Testo and others | Versions unknown |
| Semgrep OSS libraries | `murmur3`, `process_limits`, `ocaml-tree-sitter-semgrep/core` | Compile units in `/src/semgrep-pro/...` |
| Tree-sitter grammars | 34 entry points (33 language directories; TypeScript and TSX share one) | ABI read from each `TSLanguage` structure: 28 use ABI 14 and 6 use ABI 15. The ABI 15 name pointers resolve correctly (for example "bash" and "swift"), which validates the layout. Embedded versions are `0.0.0`, so **grammar versions are unknown**. 23 have external scanners |

Dynamically resolved, not static: the tree-sitter runtime, PCRE2, GMP, curl,
Zstandard, libev, libdw/libelf, bz2, z, lzma, libunwind, libstdc++, libm and
`libgcc_s` (Linux `DT_NEEDED`).

## Static code inside other wheels

| Wheel | Component | Class | Notice |
| --- | --- | --- | --- |
| cryptography 50.0.2 | OpenSSL: string "OpenSSL 4.0.3 29 Sep 2026" on both platforms | Version claim | Wheel ships its own Apache/BSD licences; **no OpenSSL licence text** |
| cryptography, pydantic-core 2.50.4, rpds-py 2026.9.1 | Rust crates | Unknown (no `cargo-auditable` section) | Not present |
| ruamel.yaml.clib 0.2.15 | libyaml-derived C code | Inferred | MIT (Ruamel) only |
| protobuf 6.33.6 | upb runtime | Inferred | protobuf `LICENSE` |
| tomli, charset-normalizer, cffi, wrapt | First-party compiled code | n/a | Wheel licences |

## The three tree-sitter runtime binaries

**Confirmed:**

* the tree-sitter runtime, with an identical 149-function exported API on Linux
  and macOS (the two macOS files are byte-identical);
* the 0.25+ API is present (`ts_language_abi_version`, `ts_language_name`,
  `ts_language_metadata`);
* the 0.26 series, from the soname and install name;
* every one of the 31 runtime functions `semgrep-core` imports is exported.

**Inferred:** patch release 0.26.3, from the public pin seen in G5. Licence MIT,
per upstream at that tag.

**Unresolved:** the libraries were built in Semgrep's non-public tree and there
is no reproducible build offline. **OWNER REVIEW.** Identity and licence are
adequate for local and trial use.

## Licences, notices and source availability

* **Confirmed licences:**
  * the 67 Python distributions (F1 metadata and shipped licence files);
  * the 30 traced native libraries (G5).
* **Not verified offline:**
  * the OCaml runtime fork, the opam packages and the workspace-vendored code;
  * libyaml, backward-cpp and the grammars;
  * the Rust crates, the OpenSSL inside `cryptography`, and upb.

  The SBOM records these as `licence_status` properties rather than inventing
  licence conclusions.
* **Notices:** the distribution ships **none** for any static component of
  `semgrep-core`, or for the OpenSSL inside `cryptography`.
* **Source:**
  * third-party native libraries: available (AlmaLinux and EPEL SRPMs, Homebrew
    sources);
  * opam packages: archives are expected to be public, but this was not
    verified offline;
  * Semgrep-built code: not verifiable (below).

## Vulnerabilities

* **Carried forward unchanged, and none waived:**
  * 5 G2 advisories (`mcp` ×4 and `opentelemetry-api`; conditionally accepted
    until 2026-12-17);
  * 8 G5 records: 6 AlmaLinux ALSA advisories, libdwarf CVE-2026-116732 and
    PCRE2 OSV-2026-343.
* **Newly inventoried static components were NOT QUERIED,** because of the
  offline restriction (G5B-2):
  * the libyaml 0.1.7 claim, which is far older than the current 0.2.x line;
  * the OCaml 5.4.0 fork;
  * the 84 opam packages, including the TLS and crypto stack;
  * the OpenSSL 4.0.3 claim inside `cryptography`;
  * the Rust crates and the grammars.

## Blocked by non-public sources

* Correspondence between the `semgrep-core` binary and its LGPL-2.1 source
  (G5-5).
* The source of the OCaml runtime fork `4046c817`.
* The versions and origin of the workspace-vendored OCaml libraries.
* The tree-sitter runtime build, and the versions and licences of the 34
  grammars.
* Any reproducible rebuild of a Semgrep-built binary.

## Issues and recommendations

| ID | Issue | Recommendation |
| --- | --- | --- |
| G5B-1 | SBOM incomplete for static code: 53 unknown, 78 version-unknown, 3 version-claim components | OWNER REVIEW |
| G5B-2 | No advisory lookup yet for newly inventoried static components | REMEDIATE: authorise an online OSV/NVD lookup against this SBOM |
| G5B-3 | Embedded libyaml version claim 0.1.7 | OWNER REVIEW; REMEDIATE (report upstream) if confirmed |
| G5B-4 | OCaml runtime is a Semgrep fork whose source is not verifiable offline | OWNER REVIEW; BLOCK redistribution |
| G5B-5 | No notices for static components (`semgrep-core`, OpenSSL in `cryptography`) | OWNER REVIEW for use; BLOCK redistribution |
| G5B-6 | No Rust crate inventory | OWNER REVIEW |
| G5B-7 | SQLite and Mbed TLS suspected in G5 | **CLOSED: not linked** |

## Required owner decisions

1. Accept the SBOM as the project's current toolchain record. Its known
   incompleteness is marked as incomplete or unknown, not hidden.
2. Authorise an online advisory lookup against the SBOM (G5B-2) before any
   reconsideration of mandatory CI.
3. Decide whether to raise the libyaml version claim, the OCaml fork source and
   the missing static-component notices with Semgrep upstream. That would be
   outward-facing and is not done here.
4. Confirm that redistribution stays prohibited.

## G5D addendum (owner decision, 2026-11-17)

* The SBOM in this document, v1
  (`semgrep-toolchain-1.185.0.cdx.json`, SHA-256 `499477a2…3d81`), is
  **frozen and unchanged**.
* The owner adopted the schema-validated **v2**
  (`semgrep-toolchain-1.185.0.v2-candidate.cdx.json`, SHA-256 `70a38b40…8fe7`)
  from [G5C](m4c-c5-g5c-vulnerability-assessment.md) as the **current
  assessment baseline**.
* G5B-1 to G5B-6 remain open.
* **Decision record:** [G5D](m4c-c5-g5d-security-risk-decision.md#recorded-owner-decision-2026-11-17).

## Limits

* Offline: no new advisory, licence or source lookups.
* The macOS composition is inferred; it has no DWARF.
* opam versions are build metadata.
* Symbol and string evidence shows presence. It cannot rule out fully inlined
  code.
* The SBOM was not validated against the official schema.
* The analysis tools were scratch scripts; their hashes are in the JSON.

## Changed files (G5B)

* New:
  * `security/sast/sbom/semgrep-toolchain-1.185.0.cdx.json`;
  * this document and its [JSON record](m4c-c5-g5b-sbom-static-inventory.json).
* Modified (status lines only): `README.md`, `AGENTS.md`,
  `docs/capability-status.md`, `docs/milestones/m4c-c5-sast-plan.md`.
* Unchanged: locks, toolchain, inventory, rules, harness, driver, workflows,
  tests, application, and all F4R, E03, G2 and G5 files.
