# M4C-C5 — G4 TypeScript syntax-validation gap: option assessment

Date: 2026-11-17 UTC. Base: `2b050a1` plus preserved uncommitted C5 work.
Authority: owner direction for an **assessment only**. Nothing was implemented.
There was no dependency, lockfile, harness, driver, workflow, GitHub setting or
Azure change, no dispatch, and no commit or push. Machine-readable record:
[JSON](m4c-c5-g4-typescript-syntax-gate-assessment.json).

## The gap

Semgrep CE 1.185.0 recovers from some TypeScript syntax errors without reporting
them. Malformed files therefore look "parsed and clean"
([F1](m4c-c5-f1-semgrep-feasibility.md), [F3](m4c-c5-f3-harness-hardening.md) T03).
The harness cannot detect this from Semgrep's output alone.

## Recommendation

**Option A: a syntax-only TypeScript compiler gate, using the already-pinned
`typescript` 6.0.3.**

* It runs on exactly the harness's TypeScript target set before Semgrep, and the
  scan fails closed on any syntax diagnostic.
* For E04, add **Option D** as well: the SAST job hard-depends on the existing
  mandatory `lint`/`typecheck` job.

Neither option is implemented. Both need separate owner authorisation (harness;
workflow).

## Evidence

| Measure | Result |
| --- | --- |
| Coverage of existing tooling | All **42** application `.ts`/`.tsx` files Semgrep scans are in a `tsc` project and linted with the typescript-eslint parser. `scripts/verify-auth-capture.d.mts` is already excluded by the harness. The 12 TypeScript fixtures are harness controls |
| Corpus (scratch only) | 42 originals, the 3 G4 parser-gap fixtures plus F3 T03, and **792 token-level mutants**. Mutations target real tokens located with the TypeScript scanner: 11 operators, 2 positions per file, fixed seed |
| Offline | Every run (Node tools and Semgrep) ran inside a deny-network sandbox. 838 files took 0.26–0.6 s per tool |

**Detection:**

| Tool | False positives (42 originals) | G4 cases (4) | Invalid mutants detected (755 per TypeScript's parser) |
| --- | --- | --- | --- |
| **Semgrep 1.185.0** (current state) | 0 | **0** | 567. **188 silently accepted (25%)**: deleted `)`, `]` or `}`, and duplicated commas |
| **A. TypeScript syntax-only** | 0 | **4** | 755 (the oracle) |
| B. ESLint + typescript-eslint parser, no rules | 0 | 4 | 755 (identical to A; no disagreements) |
| C. esbuild | 0 | 4 | 753 (missed 2) |

Of the 37 mutants that TypeScript's parser accepts, most are still-valid syntax,
such as array holes, type literals and type references. esbuild additionally
flags 7 of them as JavaScript early errors (invalid assignment target,
uninitialised `const`). TypeScript reports those as type-check errors (TS2364,
TS1155), which the existing CI `typecheck` already catches. Adding checker
grammar errors (TS1xxx) to Option A found 1 more case, with no false positives,
at about 3× the run time. That extension is optional.

## Option comparison

| Criterion | A. TypeScript syntax-only | B. ESLint parser | C. esbuild | D. CI ordering on existing `lint`/`typecheck` |
| --- | --- | --- | --- | --- |
| Accuracy | Reference TypeScript parser; all G4 cases | Same as A (uses TypeScript's parser) | Different parser; missed 2; extra early errors | Full parse **and** type check of all 42 targets |
| Offline reproducibility | Yes: pure JavaScript, lock-pinned | Yes | Yes once installed | CI only |
| macOS and Linux | Platform-independent JavaScript; Linux shown by the existing CI job (run 43477343929 `application` passed) | Same | Per-platform native binary (26 optional packages) | Linux CI |
| Supply chain and licensing | **1 package, Apache-2.0, no install script**, already pinned with sha512 integrity | 95 packages, 6 licence types (permissive), no install scripts | **Install script plus native binaries** (MIT) | Nothing new |
| Fail-closed | Explicit file list; any diagnostic, missing file, missing Node or version/hash mismatch fails | Config ignores or unmatched globs can **silently skip** files unless an explicit config is forced | Stops at the first error | Only if the SAST job hard-depends on it; does not protect local harness scans |
| Integration effort | Small: a Node checker plus a harness preflight. Container mode needs Node in the image, or a host-side preflight | Like A, with more parts | Small | Minimal: a workflow `needs:` dependency |
| Verdict | **Recommended** | Acceptable alternative, no accuracy gain | Not recommended | **Add for E04** |

## Proposed design (for later authorisation only)

* Pin `typescript` 6.0.3 by recording the SHA-256 of
  `node_modules/typescript/lib/typescript.js` in the toolchain manifest, and
  verify it before use. No new dependency is needed.
* Check exactly the harness inventory's `.ts`/`.tsx` targets. Fail closed if:
  * the target list is empty or mismatched, or
  * any syntactic diagnostic is reported, or
  * Node is missing, or the version or hash differs, or
  * the check times out.
* Report only paths and `TS` codes, not message text, in line with E03 M14.
* Hosted trial and container mode need either Node in the scan image (a
  Dockerfile change) or the gate on the host before `container-run` (a driver
  change). Each is a separate decision.

## Limits

* This ran on macOS with Node 22.17.1, not the pinned 24.22.2. Linux evidence
  comes from the existing CI job, not this corpus.
* The oracle is TypeScript's own parser. ESLint is not independent of it; esbuild
  is the only independent parser.
* The corpus is synthetic (single-token edits). Multi-edit and adversarial
  inputs were not covered.
* Semgrep misanalysing *valid* code is out of scope.

## Status

G4 remains **open**. E04, E05, E06 and release remain **NO-GO**.

**Owner decision requested:** authorise implementing Option A in the harness,
and choose host-side preflight or Node in the container. Also decide whether D
is required for E04.

## Changed files (G4 assessment)

* New: this document and its [JSON record](m4c-c5-g4-typescript-syntax-gate-assessment.json).
* Modified (status lines only): `README.md`, `AGENTS.md`,
  `docs/capability-status.md`, `docs/milestones/m4c-c5-sast-plan.md`.
* Unchanged: dependencies, lockfiles, harness, driver, workflows, both SBOMs and
  all earlier evidence.
