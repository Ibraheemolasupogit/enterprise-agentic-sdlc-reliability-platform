# M4C-C5 — U1E addendum 1: G2 guard-hash rebinding

Date: 2026-11-19 UTC. Baseline commit: `9e4bedb` (`origin/main`), plus the
uncommitted [G2/G5 R1](m4c-c5-g2g5-r1-remediation.md) change.
Machine-readable record: [JSON](m4c-c5-u1e-addendum-1-guard-rebinding.json).

**Status: APPROVED by the owner on 2026-11-19.** The approval covers a narrow
rebinding of one U1E section 3 hash only.

* All other U1E decisions (E1–E8), the scope, the expiry (2026-12-17) and the
  stop conditions are **unchanged**.
* G2 and G5 remain **OPEN**. G4 remains **closed for TypeScript only**. E04,
  E05, E06, release and redistribution remain **NO-GO**.
* Nothing is waived.

## Rebinding

| Item | Value |
| --- | --- |
| File | `tests/security/sast/test_g2_mitigation_guard.py` |
| Previous adopted SHA-256 (U1E section 3; the file LT-U1 S2/S6 executed) | `0ac3de5d0016ff3fab094d5bf4463cf2994d39c4b719e0c7aa19ea9aa513f286` |
| **New adopted SHA-256** | **`42672fd941fde28e387d4dd461e3b5d216e64597c0cc7bb20549f37ca6b04a79`** |
| Reason | R1 strengthened `PositivePolicy.test_engine_invocation_platform_wrapper` |
| Change | The test now runs with the deterministic hostile caller environment (`MUTATION_CALLER_ENV`, caller `PATH` `/c5g2/bin:/usr/bin:/bin`). It asserts that this caller `PATH` differs from the pinned `/usr/bin:/bin`, and that both the tool and engine `PATH` equal the pin. It then applies the unchanged `check_engine`, plus `check_tool_env`. The fail-closed branch for unsupported operating systems is preserved |
| Weakening | **None.** One line was replaced by a strict superset (an explicit `environ=` argument). No assertion was removed or relaxed |
| Evidence of effect | Passes on the unchanged harness, both in the normal shell and in `env -i PATH=/usr/bin:/bin`. **Fails** on a disposable copy with the harness `PATH` pin removed, in both environments (previously it passed in `env -i`). Against that copy, 6 guard tests now fail (previously 5) |

## Why U1E E5(a) applied, and what this clears

* U1E E5(a) requires an immediate stop if any section 3 hash changes. The R1
  edit changed this file's hash, so E5(a) applied. No Semgrep scan was planned
  or run while it applied.
* This addendum records the owner-approved new value. **The E5(a) stop is
  cleared for this file only**, once the consistency check verifies the new
  binding (237/237).
* Any further change to any section 3 hash triggers E5(a) again.

## Other adopted inputs (verified unchanged, 2026-11-19)

All of the following equal U1E section 3, both in the working tree and at
`9e4bedb`:

* both locks;
* `toolchain.json` (`91f9a3d0…`);
* `native-libraries-1.186.0.json`;
* SBOM v3 (`7d534e90…`);
* `feasibility.py`;
* `controls.json`;
* both rule files.

The Linux and macOS wheels and both `semgrep-core` binaries (scratch copies)
also equal their U1E hashes.

## Bindings updated (current consistency only)

* **[U1E](m4c-c5-u1e-adoption-decision.md):** the section 3 guard row and the
  JSON `toolchain_hashes` entry now carry the new value, annotated with this
  addendum and the previous hash. Nothing else in U1E changed.
* **[U1B](m4c-c5-u1b-pre-execution-assurance.md):** the guard entry in
  `artifacts_sha256`, which the U1 consistency check reads, and its table row
  now carry the new value, annotated with the previous one. The same pattern
  was used for the U1E `toolchain.json` status edit.

**Historical records preserved unchanged:**

* [U1](m4c-c5-u1-semgrep-1.186.0-upgrade-preparation.md);
* [U1C](m4c-c5-u1c-lt-u1-execution.md), which records `0ac3de5d…` as the
  post-fix guard;
* [U1D](m4c-c5-u1d-lt-u1-verification.md), the LT-U1 run;
* the LT-U1 scratch outputs;
* [G5D](m4c-c5-g5d-security-risk-decision.md);
* the G4H records.

**LT-U1 executed the `0ac3de5d…` guard.** The rebound file is a later,
strengthened version. Its changes are verified without the engine, and the
G2 guard never invokes the engine.

## Verification

See the JSON record and the [R1 record](m4c-c5-g2g5-r1-remediation.md).
Summary:

* consistency **237/237**;
* G2 guard 9/9 and engine-free SAST modules 88 run, 58 pass, 30 skipped, in
  both environments;
* `actionlint`, the validator, documentation, integrity and security checks
  pass.
