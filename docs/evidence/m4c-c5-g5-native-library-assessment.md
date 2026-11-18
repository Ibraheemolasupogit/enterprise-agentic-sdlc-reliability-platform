# M4C-C5 — G5 native library licensing and provenance assessment

Date: 2026-11-17 UTC. Base: `2b050a1` plus the uncommitted, preserved F4R, E03
and G2 work. Authority: owner direction for **investigation and evidence
documentation only**. Machine-readable record with per-library detail:
[JSON](m4c-c5-g5-native-library-assessment.json).

There was no dependency, lockfile, rule, application, CI workflow or GitHub
setting change, no hosted dispatch, no Azure work, and no commit or push. Public
packages were downloaded into fresh scratch directories and parsed as data. No
downloaded code was executed. The F3 inventory
[`security/sast/native-libraries.json`](../../security/sast/native-libraries.json)
is unchanged.

## Decision

| Use | Recommendation |
| --- | --- |
| Local development (running the hash-locked wheels from PyPI) | **GO, subject to owner review.** No licence blocker identified |
| Existing non-blocking, dispatch-only CI trial | **GO with the no-redistribution conditions** below |
| Mandatory CI (E04) | **NO-GO** until the owner decides G5-3, G5-4, G5-6, G5-7 and G5-8 (together with G2) |
| Redistribution of the wheels, venv, wheelhouse or container image | **NO-GO (BLOCK)** until G5-1, G5-2, G5-4 and G5-5 are remediated |

G5 stays **open**. No vulnerability or licence obligation is waived.

## Inputs re-verified

* Wheels: macOS arm64 SHA-256 `d54c7dc2…f1b4` and Linux x86_64
  `manylinux_2_34` SHA-256 `0eb6aaad…c02b`, matching the lock. All 33 library
  hashes match the F3 inventory.
* Semgrep public source: tag `v1.185.0` resolves to commit `9240f708`, as
  recorded in F1.

## Method

**Linux (26 libraries).** Each `.gnu_debuglink` names an exact RPM build (for
example `libcurl.so.4.7.0.minimal-7.76.1-40.el9_8.8`). Those embedded names were
treated as **claims** and checked independently:

1. Fetched the 20 named RPMs from `repo.almalinux.org`, `vault.almalinux.org`
   and Fedora EPEL over HTTPS. URLs and SHA-256 hashes are in the JSON.
2. Verified each RPM's header RSA signature (SHA-256) in pure Python against the
   officially published keys:
   * AlmaLinux 9: `BF18AC28 76178908 D6E71267 D36CB86C B86B3716` (19 RPMs);
   * EPEL 9: `FF8AD134 4597106E CE813B91 8A3872BF 3228467C` (`libunwind`).
3. Checked that each extracted library's SHA-256 equals the file digest inside
   the signed header (25/25).
4. Compared each wheel library with the RPM file. The GNU build-id matches, and
   `.text`, `.rodata`, `.data`, `.init`, `.fini` and `.eh_frame` are
   byte-identical. Only `.dynamic`, `.dynstr` and `.dynsym` differ, consistent
   with Semgrep's `patchelf` change of `RUNPATH` to `$ORIGIN`.

**macOS (7 files).** Five dylibs carry Homebrew install names. Their Mach-O
`LC_UUID` matches a Homebrew `arm64_sequoia` bottle, and `__TEXT,__text` is
byte-identical. Each bottle blob's SHA-256 equals its GHCR OCI digest. Homebrew
build attestations were not verified.

**Licences.** For each library the evidence records:

* the packager's declaration: the signed RPM `License` tag, or the Homebrew
  formula `license`;
* the licence texts shipped in the package or bottle, with SHA-256;
* where a text was missing or ambiguous, the upstream licence file at the exact
  tag.

**Vulnerabilities:**

* OSV AlmaLinux 9 querybatch with the exact package versions (2026-11-17T09:54Z).
  Red Hat-family builds backport fixes, so upstream version numbers are not used;
* OSV commit queries for the upstream release commits of tree-sitter, PCRE2,
  Zstandard, libdwarf and libunwind.

## Confirmed licence coverage

**Provenance confirmed for 30 of 33 files** (25 Linux, 5 macOS). Licence texts
are available for all 33. For 30 they come from the matched signed package or
bottle. For the three tree-sitter files they come from the upstream licence at
the inferred version.

| Platform | Library | Confirmed package / bottle | Packager licence declaration | Licence text |
| --- | --- | --- | --- | --- |
| Linux | libbz2.so.1 | bzip2-libs 1.0.8-11.el9 | BSD | RPM `LICENSE` |
| Linux | libcom_err.so.2 | libcom_err 1.46.5-8.el9 (e2fsprogs) | MIT | RPM `NOTICE` |
| Linux | libcrypto.so.3, libssl.so.3 | openssl-libs 1:3.5.8-2.el9_8 | Apache-2.0 | RPM `LICENSE.txt` |
| Linux | libcurl.so.4 | libcurl-minimal 7.76.1-40.el9_8.8 | MIT | RPM `COPYING` |
| Linux | libdw.so.1, libelf.so.1 | elfutils-libs / -libelf 0.194-1.el9.alma.1 | GPL-2.0-or-later OR LGPL-3.0-or-later | RPM `COPYING-GPLV2`, `COPYING-LGPLV3` |
| Linux | libev.so.4 | libev 4.33-6.el9 | BSD or GPLv2+ | RPM `LICENSE` |
| Linux | libgcc_s.so.1, libstdc++.so.6 | libgcc / libstdc++ 11.5.0-14.el9.alma.1 | GPLv3+ with exceptions (and others) | `libgcc` RPM incl. `COPYING.RUNTIME`; `libstdc++` RPM ships none (same gcc source RPM) |
| Linux | libgmp.so.10 | gmp 1:6.2.0-13.el9 | LGPLv3+ or GPLv2+ | RPM `COPYING*` |
| Linux | libgssapi_krb5, libk5crypto, libkrb5, libkrb5support | krb5-libs 1.21.1-10.el9_8 | MIT | RPM `LICENSE` |
| Linux | libkeyutils.so.1 | keyutils-libs 1.6.3-1.el9 | GPLv2+ and LGPLv2+ | RPM `LICENCE.LGPL` |
| Linux | liblzma.so.5 | xz-libs 5.2.5-8.el9_8.1 | Public Domain | RPM `COPYING` |
| Linux | libm.so.6, libresolv.so.2 | glibc 2.34-283.el9_8 | LGPL-2.1-or-later AND … (full SPDX expression in JSON) | RPM `COPYING`, `COPYING.LIB`, `LICENSES` |
| Linux | libnghttp2.so.14 | libnghttp2 1.43.0-6.el9_8.2 | MIT | RPM `COPYING` |
| Linux | libpcre2-8.so.0 | pcre2 10.40-7.el9_8 | BSD | RPM ships none; upstream `LICENCE` at `pcre2-10.40` (BSD-3-Clause with binary library-like exemption) |
| Linux | libselinux.so.1 | libselinux 3.6-3.el9 | Public Domain | RPM `LICENSE` |
| Linux | libunwind.so.8 | libunwind 1.8.0-4.el9 (EPEL) | MIT | RPM `COPYING` |
| Linux | libz.so.1 | zlib 1.2.11-40.el9 | zlib and Boost | RPM `README` |
| Linux | libzstd.so.1 | libzstd 1.5.5-1.el9 | BSD and GPLv2 | RPM `LICENSE`, `COPYING` |
| macOS | libdwarf.2.dylib | dwarfutils 2.3.3 | BSD-2-Clause AND LGPL-2.1-or-later AND GPL-2.0-or-later (package) | bottle `COPYING`; upstream `LIBDWARFCOPYRIGHT`: "version 2.1" |
| macOS | libev.4.dylib | libev 4.33 | BSD-2-Clause OR GPL-2.0-or-later | bottle `LICENSE` |
| macOS | libgmp.10.dylib | gmp 6.3.0 | LGPL-3.0-or-later OR GPL-2.0-or-later | bottle `COPYING*` |
| macOS | libpcre2-8.0.dylib | pcre2 10.47 | BSD-3-Clause | bottle `LICENCE.md`, `COPYING` |
| macOS | libzstd.1.dylib | zstd 1.5.7_1 | (BSD-3-Clause OR GPL-2.0-only) AND BSD-2-Clause AND MIT | bottle `LICENSE`, `COPYING` |

**Confirmed vs inferred versions.** Confirmed versions are package builds (for
example `7.76.1-40.el9_8.8`). They contain distribution backports, so they are
not the plain upstream releases. Embedded version strings from F3 were
consistent with every confirmed package. Two Homebrew details were refined: the
Zstandard bottle is revision `1.5.7_1`, and PCRE2 is 10.47 while the current
formula is 10.49.

**Licence declaration discrepancies.** All are recorded, none resolved by
assumption; details are in the JSON:

* **libdwarf:** Homebrew declares LGPL-2.1-or-later for the package, but the
  upstream library text grants "version 2.1" only. It is treated conservatively
  as **LGPL-2.1-only**, which matches F3.
* **Legacy RPM short names** ("BSD", "BSD and GPLv2", "GPLv2+ and LGPLv2+",
  "zlib and Boost") are less precise than the shipped texts. The shipped texts
  govern.

## Unresolved libraries and components

| ID | Item | Status | Recommendation |
| --- | --- | --- | --- |
| G5-3 | `libtree-sitter.so.0.26` (Linux), `libtree-sitter.0.26.dylib` and `libtree-sitter.dylib` (macOS; byte-identical) | **Provenance inferred.** Semgrep-built; build paths name `semgrep-pro`/`semgrep-proprietary` trees. Public pin `tree-sitter-version` = 0.26.3 at `9240f708`, upstream licence MIT at `v0.26.3`. The binary-to-source correspondence cannot be verified (no reproducible build) | OWNER REVIEW |
| G5-4 | Code statically linked into `semgrep-core` (Linux 266 MB, macOS 219 MB) | **Not inventoried.** Strings indicate libyaml, SQLite and Mbed TLS, plus OCaml libraries. The `ocaml-tree-sitter` binding is LGPL with the OCaml linking exception. No notices | REMEDIATE (inventory) before mandatory CI or redistribution; OWNER REVIEW for current use |
| G5-5 | LGPL corresponding source for `semgrep-core` | Built from a non-public tree; correspondence to the public LGPL source not verifiable | BLOCK redistribution; not applicable to local or CI use |
| G5-1 | Wheels ship no third-party notices or SBOM | Upstream distribution gap (the macOS wheel ships only Semgrep's own `LICENSE`; Linux ships none) | OWNER REVIEW for use; REMEDIATE before redistribution; optionally report upstream |
| G5-2 | No project SBOM for the scanner toolchain | Data now exists in this record | REMEDIATE: generate SPDX or CycloneDX (needs authorisation for a repository file) |

Host-provided libraries, not bundled and not assessed here:

* Linux: `libc.so.6` and `ld-linux-x86-64.so.2`.
* macOS: `/usr/lib/libcurl.4.dylib`, `libc++.1.dylib`, `libSystem.B.dylib` and
  `libz.1.dylib`.

## Vulnerability findings

All bundled libraries are loaded at startup, because the `DT_NEEDED` closure
covers all 26 Linux libraries. Being loaded does not mean the code runs: scans
run offline with network isolation and read only repository files.

| ID | Library | Advisory | Rated | Fixed in | Reachable in our offline scans |
| --- | --- | --- | --- | --- | --- |
| G5-6 | libcurl.so.4 | ALSA-2026:92907 (CVE-2026-8932, mTLS connection reuse) | Moderate | 7.76.1-40.el9_8.9 | No: needs a network peer |
| G5-6 | libcrypto.so.3, libssl.so.3 | ALSA-2026:98484 (12 CVEs: TLS/DTLS/QUIC, CMP, CRL DP, EC/SM2 timing) | Moderate | 1:3.5.9-1.el9_9 | No: needs network peers or attacker-supplied certificates |
| G5-6 | libm.so.6, libresolv.so.2 | ALSA-2026:95618, ALSA-2026:98512 (DNS stub resolver, nscd, dynamic loader `$ORIGIN`/AT_SECURE) | Moderate | 2.34-284.el9_8.4 / 2.34-290.el9_9 | No for the bundled files: nscd and `ld.so` are not bundled (the host loader is used), DNS fails offline, and `semgrep-core` is not setuid |
| G5-6 | libstdc++.so.6 (advisory also lists libgcc) | ALSA-2026:98524 (CVE-2026-114690/114691/115456: parallel algorithms, integer wrap, `std::from_chars`) | Moderate | 11.5.0-17.el9_9.alma.1 | **Not determined.** Template code may be compiled into `semgrep-core`, so an updated `.so` alone may not fix it |
| G5-6 | liblzma.so.5 | ALSA-2026:98486 (CVE-2026-34743, index decoding) | Moderate | 5.2.5-8.el9_9.1 | **Not determined, low.** Reached through ELF compressed-section decoding by libdw/libelf, not through scanned source |
| G5-7 | libdwarf.2.dylib (macOS) | CVE-2026-116732 (out-of-bounds read on crafted object files) | CVSS 4.0, local, low | Upstream commit `71f04013`, **no release** | Unlikely: reads `semgrep-core`'s own debug data |
| G5-7 | libpcre2-8.0.dylib (macOS) | OSV-2026-343 (OSS-Fuzz, `pcre2_compile_32`) | Unrated | Upstream commit `e19e76ad` | Applicability to the bundled 8-bit library unconfirmed. Patterns come from the reviewed local rules |

* Sixteen Linux libraries come from 11 packages that have since been superseded
  in the AlmaLinux repositories (listed in the JSON). Newer builds exist, but only
  Semgrep can rebuild the wheel. No HIGH or CRITICAL rating was found.
* **Coverage gaps (G5-8):**
  * EPEL `libunwind` has no OSV distribution ecosystem (its upstream commit
    query was clean);
  * GMP and libev have no OSV git coverage;
  * statically linked code was not checked.

  The absence of a record is not evidence of safety. Recommendation:
  **OWNER REVIEW**, re-checking on every Semgrep release.

## Obligations by use

These are licence-condition readings, not legal advice.

* **Local use:**
  * The project runs unmodified copies obtained from PyPI.
  * GPL and LGPL conditions attach to conveying or distribution: GPL-3.0 §2 and
    LGPL-2.1 §0 do not restrict running.
  * The notice conditions of the permissive licences attach to copies and
    redistribution made by the distributor (Semgrep).
  * **No project obligation identified.** The missing notices in the wheels
    are an upstream distribution observation.
* **CI use:** the same, provided the runner downloads from PyPI and only the six
  allowlisted JSON files are uploaded. The current trial workflow meets this: no
  cache, no image push, no binary artifact. Any upload, cache or push of the
  venv, wheelhouse or image would be redistribution.
* **Redistribution** (publishing an image, vendoring wheels, an internal mirror,
  shipping to others) would require:
  * licence texts and copyright notices for every component, including Semgrep
    and the statically linked code;
  * for LGPL components (GMP, elfutils, keyutils, glibc `libm`/`libresolv`,
    libdwarf, Semgrep and the `ocaml-tree-sitter` binding): corresponding
    source or a written offer, and the ability to relink;
  * the GCC Runtime Library Exception texts for `libgcc`/`libstdc++`;
  * Apache-2.0 terms for OpenSSL;
  * corresponding source for `semgrep-core` itself.

  AlmaLinux source RPMs and Homebrew source URLs provide the third-party source.
  Corresponding source for `semgrep-core` is unresolved (G5-5).

## Required owner decisions

1. Accept that local use and the existing non-blocking trial may continue under
   the no-redistribution conditions (recommended).
2. Decide on G5-3 (inferred tree-sitter provenance), G5-6 and G5-7 (moderate
   advisories with fixed builds or commits available but not deliverable without
   a new Semgrep release; libstdc++ and liblzma reachability not determined), and
   G5-8 (coverage gaps). These gate mandatory CI together with G2.
3. Authorise G5-2 (a project SBOM file) and G5-4 (an inventory of statically
   linked components) if mandatory CI or redistribution is pursued.
4. Confirm that redistribution stays prohibited (G5-5), or seek counsel review.
5. Optionally report G5-1 and G5-6 to Semgrep upstream. This is outward-facing
   and not done here.

## G5D addendum (owner decision, 2026-11-17)

* **V7** (six AlmaLinux ALSA advisories against the bundled Linux libraries)
  and **V8** (libdwarf CVE-2026-116732, macOS) are **conditionally accepted**,
  together with V3–V6 from [G5C](m4c-c5-g5c-vulnerability-assessment.md).
  The accepted uses are **local trusted-repository scans** and **separately
  authorised non-blocking trials**. The acceptance expires **2026-12-17**,
  under the G5D early-stop conditions and mandatory controls.
* **Licensing items** G5-1 to G5-5 are unchanged. Redistribution remains
  prohibited and **NO-GO**.
* **Status:** G5 remains **OPEN**, and nothing is waived. Mandatory CI and
  release remain NO-GO.
* **SBOM baseline:** the adopted baseline is SBOM v2. The F3 inventory
  `security/sast/native-libraries.json` is unchanged.
* **Decision record:** [G5D](m4c-c5-g5d-security-risk-decision.md#recorded-owner-decision-2026-11-17).

## Limits

* Licence conclusions rest on packager and upstream declarations and the shipped
  texts. They are not legal advice.
* Homebrew licence metadata is the current formula. Versions match, except
  PCRE2 (10.47 bundled, 10.49 current) and the Zstandard revision.
* Build-ID or UUID plus section equality proves identical compiled code. It does
  not prove the integrity of the upstream build environment. Homebrew
  attestations were not verified.
* Static components were identified from strings only.
* Only the macOS arm64 and Linux x86_64 wheels were assessed. There was no
  hosted re-verification.
* OSV data and upstream status are as fetched on 2026-11-17.

## Changed files (G5)

* New: this document and its [JSON record](m4c-c5-g5-native-library-assessment.json).
* Modified (status lines only): `README.md`, `AGENTS.md`,
  `docs/capability-status.md`, `docs/milestones/m4c-c5-sast-plan.md`.
* Unchanged: `security/sast/native-libraries.json`, locks, toolchain, rules,
  harness, driver, workflows, tests, application, and all F4R, E03 and G2 files.
