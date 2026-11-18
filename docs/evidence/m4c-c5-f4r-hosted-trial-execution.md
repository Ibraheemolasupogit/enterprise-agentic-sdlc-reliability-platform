# M4C-C5-F4R — Hosted Docker SAST trial: execution evidence and closeout

Date: 2026-11-13 UTC. Reviewed commit: `2b050a140ae558bc11e6e5b7c252cdb3fbbfb6f0`
(main; local HEAD identical, working tree clean before this review). Authority: owner
direction for **evidence review and closeout only**. Inputs: the owner-downloaded
artifact at `/tmp/c5-f4r-evidence-43478654843`, plus read-only GitHub GETs. There was
no dispatch, rerun, workflow, settings, dependency, rule, production-code, Azure,
commit or push action. This closes the hosted feasibility question raised by the
[F4 diagnosis](m4c-c5-f4-hosted-run-diagnosis.md) and prepared in
[F4R](m4c-c5-f4r-docker-trial-preparation.md).

## Decisions

| Decision | Result |
| --- | --- |
| **Hosted SAST feasibility (C5-F series) on GitHub-hosted `ubuntu-24.04` with Docker `--network none` isolation** | **GO — formally accepted as feasibility evidence** (scope and limits below) |
| C5 plan gate E02 (feasibility: real engine, parser coverage, exhaustive classification, actual scan, M01–M06 controls) | **Met**, both locally (F1–F3) and hosted |
| E03 (robustness M07–M14) | **Partly met**. M07–M10 and M13 were exercised with the real engine (F3/F4R, local). M11/M12 were exercised only with mocks. The M14 canary capture test was not exercised |
| E04 mandatory CI integration | **NO-GO**: not implemented and not authorized. The trial remains dispatch-only and non-blocking |
| E05 independent coverage/finding review, E06 governance | **Blocked** |
| C5-A1 / C5-A2 acceptance | **NO-GO** |
| Release, Azure deployment | **NO-GO** (unchanged) |

## 1. Run identity, commit and evidence integrity

| Check | Result |
| --- | --- |
| Run | [43478654843](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/43478654843): "C5-F4R hosted SAST feasibility trial (Docker network isolation, non-blocking)", `workflow_dispatch`, `main`, attempt 1, 18:02:17–18:04:03Z, **conclusion success**; all 10 steps succeeded |
| Commit | `headSha`, the facts `GITHUB_SHA` (host and container) and `GITHUB_WORKFLOW_REF` (`…/c5-sast-hosted-trial.yml@refs/heads/main`) all equal the expected `2b050a1…` |
| Authorization | Guard passed. Reference recorded as `C5-F4R owner approval 2026-11-13`. Token permissions were `Contents: read`, `Metadata: read` |
| Artifact | `c5-f4r-hosted-sast-trial-43478654843-1`, id 14064591168, 11,698 bytes, expires 2026-11-20. GitHub `digest` `sha256:a86a6026…afa2` equals the SHA-256 of the independently fetched zip |
| Provided copy | All 6 files are byte-identical to the zip members and to a fresh `gh run download` |
| Completeness | 6/6 allowlisted files present. No raw engine report was uploaded |
| Inputs | All 9 `input_sha256sum` entries equal `2b050a1`: harness, driver, toolchain, catalogue, both rule files, Linux lock, Dockerfile, workflow. `c5-summary.json` per-file hashes for all 69 source targets also equal `2b050a1` |
| Leakage | gitleaks 8.30.1 over the evidence: no leaks. No secret-like keys, snippets/messages or environment dump |

Evidence file SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `hosted-runner-facts.json` | `f0c89eec…90ab` |
| `container-image.json` | `fc313b7a…9dae` |
| `container-install.json` | `3d750496…f8f7` |
| `container-run.json` | `0b191fcc…6b93` |
| `hosted-trial.json` | `159d9dd8…6654` |
| `c5-summary.json` | `96739ec3…02fa` |

The full values are in the [JSON record](m4c-c5-f4r-hosted-trial-execution.json).
The mandatory CI run for the same commit, [43477343929](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/43477343929)
(push, 17:54Z), succeeded: application, policy (including `actionlint` of the trial
workflow), containers and required all passed; CodeQL was skipped. The trial is not
part of that gate.

## 2. Isolation and security controls (hosted)

| Control | Hosted evidence |
| --- | --- |
| Host restriction that broke F4 | Still present: `apparmor_restrict_unprivileged_userns=1`, AppArmor enabled, host seccomp 0, runner euid 1001. Option B works **despite** it, because no user namespace is created by the runner user |
| Container hardening (install and scan, identical lists) | `--rm --platform linux/amd64 --pull never --network none --user 1001:1001 --read-only --cap-drop ALL --security-opt no-new-privileges=true --ipc none --pids-limit 512 --memory 3g --memory-swap 3g --cpus 2 --tmpfs /tmp:rw,nosuid,nodev,noexec,size=512m --workdir /repo` |
| In-container self-verification (harness, fail closed) | "only lo up (kernel fallback tunnels down), non-local IPv4/IPv6 unreachable, DNS fails, non-root, no capabilities, NoNewPrivs, seccomp filter, read-only root" |
| Container facts | euid 1001, seccomp mode 2, AppArmor enabled, same kernel as the host |
| Offline install | Three network-less stages: venv 0, `pip install --no-index --require-hashes …` 0, `pip check` 0 ("No broken requirements found.") |
| Toolchain integrity | 67 distributions equal `requirements-sast-linux.txt`; 3,310 installed files match RECORD; `semgrep-core` `38fd0879…` equals the manifest; Semgrep 1.185.0 |
| Engine flags | Unchanged F1–F3 flags (`--oss-only --metrics=off --disable-version-check --no-trace --disable-nosem --no-rewrite-rule-ids --strict …`) |
| Evidence binding | The run nonce in `container-run.json` equals the one in `hosted-trial.json`, and docker exit 0 equals harness exit 0 |
| Runtime image | Built from `ubuntu@sha256:77eb101c…57ec`; Dockerfile `58d35549…` (= `2b050a1`); image `sha256:27d6877f…44c4`, amd64, user 1001:1001, 112 packages, 0 missing copyright files. `ca-certificates=20260816ubuntu0.24.04.2` and Python `3.12.3-1ubuntu0.17` were installed as pinned |

## 3. Harness results

| Measure | Hosted result |
| --- | --- |
| Harness exit | **0 (clean)**. Container-run exit 0, docker exit 0 |
| Inventory | 226 files classified (exactly the 226 tracked files at `2b050a1`). Two explicit exclusions: `frontend/start.sh` and `verify-auth-capture.d.mts`. `ast` gate: 19 Python files |
| Controls | Pass: 23 catalogued fixtures; 40 detected, 19 clean, 5 known misses; **0 missed, 0 false positives, 0 unexpected**; malformed fixtures rejected; parser-gap drift 0 |
| Source scan | **69 targets, 0 findings**, 420,218 bytes |
| Scan timing (5 runs) | 2.762, 2.762, 2.784, 2.749, 2.765 s |
| Controls scan | 1.533 s |
| Harness wall time | 19.53 s |
| Step durations | Build 50.14 s, install 9.69 s, scan step 19.68 s; whole job about 1 min 41 s |
| Memory | Engine `max_memory_bytes` 164,209,856 (~157 MiB). Peak child RSS 288,952 KiB (~282 MiB, dominated by the preflight `pip check`/RECORD process, as in F2/F3) |
| Runner | `ubuntu-24.04` image 20261111.127.1, kernel `7.0.0-1014-aws`, Intel Xeon 6975P-C, 2 vCPU, 7,962,904 kB RAM, glibc 2.39, Python 3.12.3 |

## 4. Comparison with F4R local expectations

| Item | F4R local expectation | Hosted actual | Assessment |
| --- | --- | --- | --- |
| Isolation proof string | Identical text expected | Identical | Match |
| Distributions, RECORD | 67, 3,310 | 67, 3,310 | Match |
| Controls | 59/64 as expected (40/19/5) | Identical | Match |
| Source | 69 targets, 0 findings | 69, 0 | Match |
| Inventory | 223 (simulation copy) / 224 (matrix copy) | 226 | **Explained**: the hosted checkout is the committed tree, which also contains the F4R evidence documents and test module that did not exist when the local copies were taken. 226 = tracked files at `2b050a1` |
| Image ID | Not reproducible (4 local IDs) | New ID `27d6877f…` | Expected; same base digest, Dockerfile and pinned package set |
| Build time | 178 s (emulated, `--no-cache`) | 50.1 s | Native faster, as expected |
| Scan per run | 3.7–4.5 s (emulated) | 2.75–2.78 s | Native faster |
| Harness wall | 32–39 s | 19.5 s | Native faster |
| Peak child RSS | ~294,500 KiB | 288,952 KiB | Consistent |
| Engine memory | 151–175 MB | 164 MB | Consistent |
| Hosted unknowns (F4R): docker-default AppArmor, snapshot/archive reachability, Docker Hub pulls, 2-vCPU timing | Unverified | Build, install and scan succeeded; no APT, pull-limit, retry or error lines in the log | Resolved **for this run** |
| Host kernel/CPU | Not predicted | AWS kernel and Intel CPU (the F4 run used an Azure kernel and AMD EPYC) | The hosted fleet is heterogeneous; the restriction is present on both |

**Discrepancies.** None affect the result. The inventory count difference is fully
explained above. The only log warning is Git's informational default-branch hint
during checkout.

## 5. Scope and limits of the acceptance

* This is one successful sample on one runner image version (20261111.127.1).
  Runner images and fleet hardware change, so any future job must re-verify
  isolation on every run, which the harness already does.
* The container's AppArmor profile name (`/proc/self/attr/current`) was not
  recorded. Docker's default profile is presumed but not evidenced.
* The trial is non-blocking. It proves feasibility, not enforcement: nothing
  prevents a merge or release on a SAST failure.
* "0 findings" reflects 15 original single-function rules with five documented
  blind spots, not CodeQL-equivalent or cross-file coverage (M20). No independent
  coverage review has occurred.
* The wheel download still happens on the host before isolation (hash-pinned).
  Docker access is root-equivalent on the VM.

## 6. Remaining blockers (not waived)

| ID | Blocker | Status |
| --- | --- | --- |
| **G2** | `mcp` 1.29.0 (GHSA-5h93-6whr-6q8j, GHSA-84m7-p3x7-pcfv, GHSA-rwrf-2pqf-9j8j, GHSA-w4fh-qvv9-3v23) and `opentelemetry-api` 1.37.0 (GHSA-xcq7-p3pf-p88h), all MODERATE. Imported but not invoked; pinned by Semgrep 1.185.0 with no upstream fix (F2) | **Open.** The hosted run executed them inside a network-less, capability-free, read-only container. Exposure is reduced but **not accepted or waived**; an owner risk decision or upstream release is still required |
| **G4** | Semgrep CE silently accepts some malformed TS; Python is covered by the `ast` gate, but TS relies on mandatory `tsc`/ESLint ordering | **Open.** Must be designed into any mandatory job order |
| **G5** | 26 bundled Linux native libraries (OpenSSL, curl, Kerberos, glibc parts, GCC runtime…) without notices or SBOM; heuristic, RHEL-backported versions ([inventory](../../security/sast/native-libraries.json)). Also the runtime image: 112 Ubuntu packages, SPDX base SBOM with `NOASSERTION` licences, 21 non-machine-readable copyright files, one LOW Trivy finding (DS-0026) | **Open.** Nothing was redistributed (the image was not pushed and the wheels were not uploaded). Publisher SBOM/notices or a formal owner decision is required |
| **Governance (C5-A2/E06)** | Per the [C5 readiness assessment](m4c-c5-readiness.md) (not re-read in this review): `main` unprotected; rulesets unreadable; no environments; no independent reviewer; owner-only collaborator. Same-change tampering of workflow, harness, rules and catalogue is not independently controlled. CodeQL is still skipped and private Code Security eligibility is unestablished | **Blocked.** Requires an owner-selected route (protected or ADR 0005 owner-operated with an independent reviewer) and its own authorization |
| E04 / E05 | Mandatory `source-security` job with a strict aggregate (M15–M17); independent human coverage and finding review (M20) | Not started; separate authorization |

## Changed files (this closeout)

* New: this document and its [JSON record](m4c-c5-f4r-hosted-trial-execution.json).
* Modified (status only): `README.md`, `AGENTS.md`, `docs/capability-status.md`,
  `docs/milestones/m4c-c5-sast-plan.md`.
* Unchanged: workflows, scripts, rules, locks, catalogue, Dockerfile, tests,
  application, and all earlier F1–F4R evidence.
