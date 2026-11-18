# M4C-C5 — U1B: Semgrep 1.186.0 pre-execution assurance

Date: 2026-11-18 UTC. Base: commit `268bc75`, plus the uncommitted
[C5-U1 preparation](m4c-c5-u1-semgrep-1.186.0-upgrade-preparation.md) and the
proposed [G5D addendum A1](m4c-c5-g5d-addendum-a1.md).

Machine-readable record: [JSON](m4c-c5-u1b-pre-execution-assurance.json).

**Status: ASSURANCE COMPLETE: 17/17 REBUILT LIBRARY IDENTITIES VERIFIED (R1
completed 2026-11-18). TEST PLAN PREPARED, NOT EXECUTED.**

* **Not run:** the Semgrep engine, the harness, any engine-backed test, any
  hosted dispatch.
* **Not done:** commit or push.
* **Unchanged:** the G5D decision (D1–D6), SBOMs v1 and v2, and
  `native-libraries.json`.
* **Still open or NO-GO:**
  * G2, G4 and G5 remain **OPEN**;
  * E04, E05, E06, release and redistribution remain **NO-GO**;
  * mandatory CI stays **red** on picomatch, not waived.

## 1. Signed-RPM verification of the 17 rebuilt Linux libraries

**Method:** the G5 chain, extended to the repository metadata. Scratch tool
`u1_rpm_verify.py`, SHA-256
`eee867d0e2597c3b5a9aaa3d22ece6646d5262d2ccb1a26f041bfdc555fcbfa5`. Each
`.gnu_debuglink` package name was treated as a **claim** only.

1. **Trust anchor.** The AlmaLinux 9 key is the file G5 fetched (SHA-256
   `387a8be6…1458`), with its fingerprint pinned to
   `BF18AC2876178908D6E71267D36CB86CB86B3716`, as recorded in G5.
2. **Repository metadata.** `https://repo.almalinux.org/almalinux/9/BaseOS/x86_64/os`:
   * `repomd.xml` (revision `1794920685`) has its detached OpenPGP signature
     **verified** with the pinned key;
   * `primary.xml.gz` SHA-256 equals the value in the signed `repomd.xml`
     (`d6022256…3a7b`);
   * 1,255 packages are listed.
3. **Package.** Each RPM's exact name, epoch, version, release and arch are
   listed in the signed metadata. The downloaded RPM's SHA-256 equals the
   metadata checksum.
4. **RPM header.** The header's RSA signature (SHA-256) verifies with the pinned
   key, and the header NEVRA equals the claim.
5. **Files.** Every extracted file's digest equals the file digest inside the
   signed header.
6. **Wheel library.** It has the same GNU build-id as the RPM file, and `.text`,
   `.rodata`, `.data`, `.init`, `.fini` and `.eh_frame` are **byte-identical**.

### Results

| RPM (signed AlmaLinux 9 BaseOS) | RPM SHA-256 | Wheel libraries | Result |
| --- | --- | --- | --- |
| `openssl-libs-1:3.5.9-1.el9_9` | `eb84165f8d20afa3aa122c630725c0059ff4a2bc6aa0be599ff5be45d7218d1a` | `libcrypto.so.3`, `libssl.so.3` | **VERIFIED** |
| `libcurl-minimal-7.76.1-43.el9` | `d12cbbe2211615a2ed3009d9bd4c7664fc9c7e49f86227308d1249fc839f6b13` | `libcurl.so.4` | **VERIFIED** |
| `elfutils-libs-0.195-1.el9.alma.1` | `ffbf9ffed4efed740824e529bb87aacb1939d9eba2c46d83aad15b1043b88239` | `libdw.so.1` | **VERIFIED** |
| `elfutils-libelf-0.195-1.el9.alma.1` | `8f56c2c48c436d89001f6adbcbd6fbf60d3415a600f3caf374cd581ea7ed5f2f` | `libelf.so.1` | **VERIFIED** |
| `libgcc-11.5.0-17.el9_9.alma.1` | `1248acf03287807e448174d8753b7b8a9b2cc46f40f237281c91f20fa2339386` | `libgcc_s.so.1` | **VERIFIED** |
| `libstdc++-11.5.0-17.el9_9.alma.1` | `204dea020caa78db9c8a6a39ccb0d7f105f33dc0f7931b7a06ed91ae6096d98c` | `libstdc++.so.6` | **VERIFIED** |
| `krb5-libs-1.21.1-10.el9_8.1` | `3c66fd5032b5c01b7ab4606615d5333059e177fcd8cb77a399fef2f6254cf162` | `libgssapi_krb5.so.2`, `libk5crypto.so.3`, `libkrb5.so.3`, `libkrb5support.so.0` | **VERIFIED** |
| `xz-libs-5.2.5-8.el9_9.1` | `ae121db95242bdb889ea6a6d1e8fef3f0f512b280d4d3f23d7695159ef857a3c` | `liblzma.so.5` | **VERIFIED** |
| `glibc-2.34-290.el9_9` | `6d0951f0e84df8f716f3f0736be376209a5c0cf9053aaa19e56a30b9b2e96401` | `libm.so.6`, `libresolv.so.2` | **VERIFIED** |
| `libnghttp2-1.43.0-8.el9` | `2848147039321aa4b0d2c1fbc2a6e45ab1b05540eb5c31c938aba249cb9bb44a` | `libnghttp2.so.14` | **VERIFIED** |
| `libselinux-3.6-4.el9` | `5a2a6183d18be0ceb9fd91a75f5af8caea7531fe9f94408268ceb19a44e66d5e` | `libselinux.so.1` | **VERIFIED** |
| (not an RPM) | — | `libtree-sitter.so.0.26` | **VERIFIED** by reproducible build (section 2) |

**16 of 16 AlmaLinux libraries are verified** against signed RPMs. Every claim
from the debug-link names is confirmed exactly, and no version differed from the
claim. With `libtree-sitter` (section 2), **17 of 17** rebuilt libraries are
verified.

**Sections that differ:**

* In every library, only `.dynamic`, `.dynstr` and `.dynsym` differ. This is
  consistent with Semgrep's `patchelf` change of `RUNPATH` to `$ORIGIN`, as G5
  found for 1.185.0.
* `libresolv` also differs in `.bss`, and `libselinux` in `.bss` and `.tbss`.
  These are `SHT_NOBITS` (zero-fill) sections with **identical address and
  size**. They have no file content, so the difference is only in
  section-offset bytes after relocation.

**Negative controls (all rejected as expected):**

* the 1.185.0 `libstdc++` does not match the -17 RPM by build-id;
* a one-byte change to an RPM header fails its signature;
* the EPEL key does not verify an AlmaLinux RPM;
* a one-byte change to `repomd.xml` fails the detached signature.

### Discrepancies found and resolved

| Discrepancy | Resolution |
| --- | --- |
| The glibc licence declaration (`libm`, `libresolv`) in SBOM v2 is cut at 200 characters by the G5B generator. The signed header has 571 characters, identical for -283 and -290 | v3 now carries the **full** signed-header `License` tag for all 16 verified libraries. v2 is left unchanged and the defect is recorded here |
| The U1 identity for the 16 libraries was INFERRED | Replaced in v3 and `native-libraries-1.186.0.json` by **CONFIRMED** (source RPM, RPM SHA-256 and URL, signer, RPM file path) |
| `openssl-libs` epoch 1 | Confirmed from the signed header; the v3 purl carries `epoch=1` |

## 2. `libtree-sitter.so.0.26`: verified by reproducible build (R1)

This library is built by Semgrep, not taken from an RPM. SBOM v2 already marked
its identity **inferred** ("0.26.x, 0.26.3 inferred"). As directed, this record
does **not** accept an inferred identity.

**Established:**

* **The code is unchanged from 1.185.0.** `.text`, `.rodata`, `.data`,
  `.eh_frame`, `.dynsym`, `.dynstr`, `.symtab` and every other
  content-bearing section are byte-identical to the 1.185.0 library. Only
  `.comment` (GCC -14 to -17) and the build-id differ.
* **The upstream source pin is verified.** At both tags v1.185.0 and v1.186.0,
  `libs/ocaml-tree-sitter-semgrep/core/tree-sitter-version` is `0.26.3` (blob
  `3f45a644…`). `scripts/download-tree-sitter` pins the release tarball to
  SHA-256 `7f4a7cf0a2cd217444063fe2a4d800bc9d21ed609badc2ac20c0841d67166550`.
  I downloaded `tree-sitter/tree-sitter` `v0.26.3.tar.gz`, and it **matches**
  that hash.
* **Reproducible build (R1, owner-authorised, completed).**
  * **First attempt:** the copy-out and comparison step was denied by the local
    permission policy. It was not worked around.
  * **Retry:** after explicit owner authorisation, a single narrowly scoped
    request (build and copy into the session scratch directory only) was
    **permitted**.
  * **Build:** in a disposable `linux/amd64` AlmaLinux 9 container
    (`almalinux@sha256:02df05719ef287ebd0df0a1eedb9172a00bd70703aed7b25660e426b8e0d6047`,
    `no-new-privileges`), with `gcc-11.5.0-17.el9_9.alma.1`,
    `glibc-devel-2.34-290.el9_9`, `binutils-2.35.2-72.el9` and `make-4.3-8.el9`,
    `make libtree-sitter.so` built the verified tarball with tree-sitter's own
    Makefile defaults (`-O3 -Wall -Wextra -Wshadow -Wpedantic
    -Werror=incompatible-pointer-types -std=c11 -fPIC -fvisibility=hidden`).
  * **Output:** 239,200 bytes, SHA-256
    `9e43a1a4e5670698d11d8b74f1a0196cf5b7492c9f355f56815b81b46fd29c43`.

**Comparison with the 1.186.0 bundled library** (SHA-256 `06e18ff1…e19e`,
247,472 bytes). This is static parsing only; neither binary was executed.

| Aspect | Result |
| --- | --- |
| GNU build-id | **Identical**: `80426ca18274dff89275c472b63846fa8cb889f3` |
| Code and data | **Byte-identical, same addresses:** `.text` (161,329 bytes), `.rodata`, `.data`, `.data.rel.ro`, `.init`, `.fini`, `.init_array`, `.fini_array`, `.eh_frame`, `.eh_frame_hdr`, `.plt`, `.got`, `.got.plt`, `.rela.dyn`, `.rela.plt`, `.gnu.version`, `.gnu.version_r` and `.gnu.hash`. `.bss` is `NOBITS` with the same address and size |
| Build metadata | **Byte-identical:** `.comment` (`GCC: (GNU) 11.5.0 20240719 (Red Hat 11.5.0-17)`), `.gnu.build.attributes` (288 bytes) and `.note.gnu.build-id`. Same `SONAME` (`libtree-sitter.so.0.26`); same `NEEDED` (`libc.so.6`) |
| `.dynsym` | 177 symbols, **semantically identical in order**. Only the `st_shndx` section indexes are renumbered |
| `.symtab` | 530 symbols, identical, except the **4 section symbols** of the relocated sections (`.dynamic`, `.dynstr`, `.gnu.hash`, `.note.gnu.build-id`), whose addresses moved. `.strtab` is byte-identical |
| `.dynamic` | The wheel adds `DT_RUNPATH $ORIGIN`. `STRSZ` is 4,011 → 4,019 (+8 bytes = `"$ORIGIN\0"`), and the `STRTAB` and `GNU_HASH` addresses moved. Every other entry is identical |

**Conclusion: CONFIRMED.** The bundled `libtree-sitter.so.0.26` is upstream
tree-sitter **0.26.3**, built from the Semgrep-pinned and hash-verified tarball
with GCC 11.5.0-17. It was post-processed only by `patchelf`, which set
`RUNPATH` to `$ORIGIN`; the same post-processing G5 found for the RPM libraries.
The result record is stored in scratch (`r1-result.json`, SHA-256
`26135d987d2113cabe49988650ed14fc2998aad332997bc77e42be0093f5abc7`).

**Out of scope:** the **macOS** `libtree-sitter` dylibs are byte-identical to
1.185.0. They keep v2's identity statement unchanged, which G5 recorded as
inferred for macOS tree-sitter. R1 covered the 17 rebuilt **Linux** libraries.

## 3. Prepared locks, manifest, inventory and SBOM v3

**Cross-consistency check:** an independent script ran **217 checks with 0
failures** across the locks, `toolchain.json`, `native-libraries-1.186.0.json`,
SBOM v3, `feasibility.py` and the PyPI release metadata. It checked:

* engine version: harness = manifest = `1.186.0`;
* each lock's SHA-256 equals the manifest, with 67 entries per lock;
* the `semgrep` wheel hash chain, for each platform:
  lock = manifest = PyPI digest = inventory = SBOM;
* the `semgrep-core` hash chain: extracted file = manifest = SBOM;
* every lock entry (67 × 2) appears in the SBOM with the same version and a
  hash from the lock;
* all 33 bundled libraries: extracted file = inventory = SBOM component hash;
* the manifest's inventory pointer, the controls catalogue hash and the rule
  hashes;
* SBOM v1, v2 and `native-libraries.json` are unchanged, and v3 has 23
  vulnerabilities with no ALSA entry.

**Regenerated artifacts:** both were regenerated from v2 and the 1.185.0 record
with the RPM evidence. Their earlier U1 hashes are superseded, and the U1
record has been updated to match.

| Artifact | SHA-256 |
| --- | --- |
| `security/sast/sbom/semgrep-toolchain-1.186.0.v3-candidate.cdx.json` | `7d534e90ad6fe45e2cd664ee786f56cc780a0f235566aec4e7ae7696d63424ca` (R1 revision) |
| `security/sast/native-libraries-1.186.0.json` | `2e7cb87088dca3d9c5068fd1b53a35fa91c4b02ba04ff8b601a22dd9cac2ceaa` (R1 revision) |
| `requirements-sast-linux.txt` | `a6472b7823e8e1c6442a05516b99c198be2244340867c410723bc41c9d42fc25` |
| `requirements-sast-macos.txt` | `c7381523700084a16ffa3cc9f51de277d72c490e83046cb510ec2630e21e74f2` |
| `security/sast/toolchain.json` | `91f9a3d0f31781c35911c7136b244b3c42f378f72ac19971f6676422d3d6603d` (U1E status-only edit; the LT-U1-tested file was `32eaef70…6357`) |
| `scripts/sast/feasibility.py` | `f7690a9aceadbe8e8be00b55ba105f8922c21bca26a7f66719432737a67bc3d0` |
| `tests/security/sast/test_g2_mitigation_guard.py` | `0ac3de5d0016ff3fab094d5bf4463cf2994d39c4b719e0c7aa19ea9aa513f286` (U1C test-design fixes; was `c03a7302…eab9f`) |

**SBOM v3 identities:**

* Linux native components: 16 CONFIRMED from signed RPMs, 1 CONFIRMED by
  reproducible build (`libtree-sitter`, version 0.26.3), and 9 CONFIRMED carried
  over (hash and build-id equal to v2).
* **Schema:** CycloneDX 1.6.2, **0 errors**.

## 4. Bounded local test plan (LT-U1). NOT EXECUTED

**Scope and environment:**

* **Platform:** the owner's macOS arm64 workstation. One Linux stage runs in the
  existing hardened container.
* **Engine:** Semgrep CE **1.186.0** only, from a scratch venv installed offline
  from the hash-locked macOS wheelhouse, then re-verified by the harness
  preflight. The Linux venv comes from `container-install`.
* **Inputs:** every run uses a **disposable copy** of the working tree in the
  session scratch directory. The repository is never written to.
* **Node:** `/usr/local/bin/node` (v22.17.1) with the lock-verified TypeScript
  6.0.3 in `apps/octocat-supply/node_modules/typescript`. The pinned v24.22.2
  is enforced only for hosted preflight.
* **Isolation:** the harness's macOS `sandbox-exec` deny-network profile in auto
  mode, and `--network none` with uid 1001, all capabilities dropped, a
  read-only root and `--ipc none` in container mode. The harness verifies
  isolation itself (exit 5 on failure).
* **Environment:** every command runs under `env -i` with only `PATH=/usr/bin:/bin`,
  a scratch `HOME`, `LANG`/`LC_ALL=C.UTF-8` and the named `C5_*` and `F3_*`
  variables.
* **Budget:** at most **90 minutes** wall-clock. At most **one** attempt per
  stage; no reruns without a new owner decision.

| Stage | Command (on a disposable copy `$COPY`; `$V` = verified 1.186.0 venv) | Expected result (anything else is a stop) |
| --- | --- | --- |
| S0 | No engine: same-day OSV recheck of all v3 components; the 217-check consistency script; the engine-free SAST suite (57 pass, 30 skip); `git status` snapshot | No new HIGH/CRITICAL or exploit; 217/217; suite OK; snapshot recorded |
| S1 Hardened harness | `python3 -I scripts/sast/feasibility.py --semgrep $V/bin/semgrep --repeat 1 --node /usr/local/bin/node` | **Exit 0.** Toolchain: 67 distributions, `pip check` pass, RECORD 0 mismatches, core hash. Isolation verified. TypeScript gate pass (49 parsed, 5 malformed rejected). Controls as catalogued (64 cases). Malformed fixtures rejected. **Parser-gap fixtures: all 4 still `engine_rejected: false`** (any change is exit 4, a stop and a review item; no catalogue edit). 0 source findings. Target count recorded |
| S2 G2 guard | `python3 -m unittest tests.security.sast.test_g2_mitigation_guard` | 8/8 (including the 1.186.0 metrics-URL and secret-hash cases) |
| S3 E03 | `C5_SEMGREP=$V/bin/semgrep C5_NODE=/usr/local/bin/node python3 -m unittest tests.security.sast.test_robustness_e03` | **29/29, 0 skipped.** No canary in the console or artifacts |
| S4 G4 | `C5_SEMGREP=$V/bin/semgrep C5_NODE=/usr/local/bin/node python3 -m unittest tests.security.sast.test_typescript_gate` | **14/14, 0 skipped**, including `HarnessEndToEnd`: malformed TypeScript stops with exit 3 and **zero Semgrep processes** |
| S5 F3 matrix | Scratch runner `f3_matrix_g4.py` (SHA-256 `bd0f88e09f46c7e8eaa82e4da44199e481f1c23a24accabaa1232cbe64323007`): `F3_TS_DIR=<copy>/apps/octocat-supply/node_modules/typescript F3_NODE=/usr/local/bin/node python3 -I f3_matrix_g4.py $BASE $V/bin/semgrep $V repo venv`, with `$BASE` a new `f3-matrix.*` directory holding a `pristine/` copy | **34/34 as expected:** B00=0; C01–C24=2; T01–T03=3; F01=1; K01–K02=4; P01–P03=2 |
| S6 Full suite | `C5_SEMGREP=$V/bin/semgrep C5_NODE=/usr/local/bin/node python3 -m unittest` (the five SAST modules) | **87/87, 0 skipped** |
| S7 Linux hardened container | On a disposable copy: `hosted_trial.container_run(<iid of c5f4r-sast-runtime:local>, <U1 Linux venv>, 1)`. Host TypeScript gate, then the in-container harness with the nonce-bound attestation, as in the G4 Docker scenarios | Exit 0, clean. Host gate passes. In-container gate is `host-attestation` (49/5), re-verified after the scan. Parser-gap expectations hold. 0 findings |
| S8 | Post-run: `git status` equals S0; scratch outputs kept; nothing uploaded | Unchanged |

**Out of scope:**

* hosted dispatch;
* any `ci.yml` change;
* rule or catalogue edits;
* reruns;
* the 1.185.0 toolchain, whose local scans stay blocked under A1/A5;
* any network use by the engine.

## 5. Security preconditions (all required before S1)

1. **Explicit owner authorisation** naming LT-U1. It is valid for **one
   execution** and expires **2026-11-20 23:59 UTC**. It covers local
   verification of the 1.186.0 toolchain only.
2. **An owner decision on 1.186.0 coverage.** Because of stop condition 7, the
   authorisation must state that G2 (V1, V2), V3–V6 and V8 (the same advisories
   as in G5D, unchanged under 1.186.0) are accepted **for LT-U1 only**, under
   G5D's controls. It must also record that the ALSA-2026:98475 trigger does
   not apply to 1.186.0 (section 1).
3. **The `libtree-sitter` identity is resolved.** **Satisfied** by R1 (section 2).
4. **Same-day OSV and upstream recheck:**
   * no HIGH or CRITICAL advisory for any v3 component;
   * no known exploit for V1–V8;
   * no new Semgrep, `cryptography` or `semgrep/ocaml` release beyond those
     reviewed.
5. **Hashes match this record.** The 217-check script passes, and the venv's
   `semgrep-core` hash equals the manifest.
6. **Environment:**
   * `env -i` as specified, with no credential or `SEMGREP_*`, `OTEL_*` or
     proxy variables;
   * the scratch `HOME` is new and empty;
   * no `~/.semgrep` settings are read.
7. **Clean state:**
   * `git status` is recorded;
   * the disposable copies are created from `git ls-files -co
     --exclude-standard` with `artifacts/` removed;
   * there is no concurrent hosted trial.

## 6. Immediate stop conditions (end LT-U1 at once; record; no rerun)

1. Any stage result differs from its expected exit code or count.
2. Harness exit 5 (isolation not verified), any evidence of a network attempt,
   or the sandbox or container isolation failing.
3. Harness exit 2 from a hash, RECORD or `pip check` mismatch, or any change to
   pinned files.
4. Exit 4 from parser-gap or control drift. Record the engine behaviour change;
   do not edit the catalogue without review.
5. A canary or secret-like value appears in console output or artifacts (E03
   M14).
6. Engine output contains unexpected fields: `secret_hash`, or Pro or Secrets
   findings.
7. Any write outside the disposable scratch copies; `git status` changes.
8. Any of G5D section 6 stop conditions 1–7 occurs for the 1.186.0 toolchain,
   including a new HIGH or CRITICAL advisory, reachability or redistribution.
9. The 90-minute budget or the authorisation expiry passes.

## 7. Reconciliation with X1 (addendum A1)

See [A1 section 7](m4c-c5-g5d-addendum-a1.md#7-reconciliation-with-the-c5-u1-upgrade-path-added-2026-11-18).

* ALSA-2026:98475 **does not apply** to 1.186.0: libstdc++/libgcc
  11.5.0-17.el9_9.alma.1 is verified above.
* X1's dispatch conditions **cannot be met** once U1 is committed.
* **Recommended path B:**
  * withdraw X1 (owner decision A6);
  * keep A1 sections 1–3 as the 1.185.0 record;
  * run LT-U1;
  * adopt 1.186.0 only if every criterion is met;
  * then run the G4H hosted verification on 1.186.0 under a new per-run
    authorisation.

## 8. GO/NO-GO

| Decision | Status | Criteria |
| --- | --- | --- |
| Execute LT-U1 | **NO-GO** until the owner authorises | Preconditions 1–7 in section 5 |
| Adopt 1.186.0 and SBOM v3 | **NO-GO** | LT-U1 S0–S8 all as expected; a recorded owner decision on the G2, V3–V6 and V8 acceptance for the 1.186.0 hashes. The `libtree-sitter` identity is resolved by R1 |
| G4H hosted dispatch (1.186.0) | **NO-GO** | Adoption, path B recorded, a same-day recheck and per-run authorisation |
| X1 dispatch (1.185.0) | **NO-GO** | Only under path A, with A1–A3 and A6 approved, and before U1 is committed |
| E04, release, redistribution | **NO-GO** | Unchanged: G5D section 7, green mandatory CI without waiver, governance |

## 9. Verification run (no engine)

| Check | Result |
| --- | --- |
| Signed-RPM chain (16 libraries, 11 RPMs) | 16/16 VERIFIED; 4/4 negative controls rejected |
| `libtree-sitter` reproducible build (R1) | VERIFIED: identical build-id; code, data and build metadata byte-identical; symbols semantically identical; only `patchelf` `RUNPATH` differs |
| Cross-consistency | 217/217; extended after R1 to 237/237 (adds identity, R1 and RPM artefact re-hash and evidence-hash checks) |
| SBOM v3 schema (CycloneDX 1.6.2) | 0 errors |
| SAST suite, `C5_SEMGREP` unset | 87 run: 57 pass, 30 skipped |
| `actionlint`, trial-workflow validator, `check_repository.py`, `git diff --check`, untracked whitespace, gitleaks, links | See the final report; all pass |

## 10. Changed files (U1B)

* **New:** this document and its JSON record.
* **Regenerated:** `security/sast/sbom/semgrep-toolchain-1.186.0.v3-candidate.cdx.json`
  and `security/sast/native-libraries-1.186.0.json`, regenerated again after R1.
* **Updated:**
  * the U1 record (hashes and identity statements);
  * A1 (section 7 and decision A6; still PROPOSED);
  * status lines.
* **Unchanged:** the G5D record, SBOMs v1 and v2, `native-libraries.json`,
  `ci.yml`, the trial workflow, the driver, the Dockerfile, the controls
  catalogue, the rules and the application.
