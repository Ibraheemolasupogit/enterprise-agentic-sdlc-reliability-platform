# M4B hosted proxy verification repair

Date: 2026-10-31 UTC. Base: `1e8d92d69a7947a2d7bbf301886580d5c95d8254`.
Scope: investigate/fix CI verification only. Deployment remains **NO-GO**.
Original local evidence is preserved in [M4B preparation](m4b-local-preparation.md).
Detailed local hashes/results are in [repair results](m4b-ci-repair.json).

**Latest validation: 2026-11-09 UTC.** The prepared repair was preserved and
independently reproduced/retested; see [resumed validation](#resumed-validation--2026-11-09).
Proxy/application/container checks pass locally. The refreshed frontend image
scan is **BLOCKED** by seven HIGH package findings; no exception or dependency
change was made. The original 2026-10-31 results below remain historical snapshots.

## Hosted observations

Read-only GitHub job metadata and decoded logs were inspected for
[run 41198119793](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/41198119793).
Application and policy passed, containers failed, required correctly failed,
CodeQL skipped. No rerun or GitHub setting change was made. Containers job
`124528678377` used Ubuntu 24.04.5/x64 and checked out the exact base SHA.
Its production container/browser smoke passed all three cases. The following TLS
step failed at 11:48:57 UTC with `/api/echo never reached 200`; image scans and
provenance were then skipped. Its artifact upload succeeded with only the preceding
container-smoke result. This is not a passing hosted M4B result or a CodeQL scan.

The old harness captured subprocess output without displaying it and deleted both
containers/network in `finally` before recording any failure evidence. Hosted peer
logs, exit state, HTTP response and generated Nginx config cannot be recovered from
that run. The diagnosis below is a controlled reproduction of the code's Linux
permission defect, not a claim that those missing hosted diagnostics were observed.

## Reproduced cause before applying the fix

`TemporaryDirectory` creates a private `0700` directory. The harness bind-mounted
that directory as `/fixtures`; the TLS peer used the API image's non-root `node`
user (UID 1000). On Linux, a different owner UID cannot traverse it to load
`peer.mjs` or the published certificate/key. The local Docker Desktop bind-mount
path had passed earlier and did not establish native Linux permission portability.
References: [Python temporary directories](https://docs.python.org/3/library/tempfile.html#tempfile.mkdtemp),
[Docker bind mounts/Desktop sharing](https://docs.docker.com/engine/storage/bind-mounts/).

Before editing repository code, the unchanged harness was replayed against a Linux
Docker volume with directory mode `0700`, owner UID/GID 1001 and peer UID 1000.
Fixture contents, images, non-root user, cap-drop/read-only settings, network aliases,
proxy configuration and TLS policy were retained. Only the fixture backing filesystem
was changed to make Linux UID/mode enforcement explicit on this macOS arm64 host.
UID 1001 was a controlled reproduction input; the original job did not record its UID.

| Captured observation | Actual result |
| --- | --- |
| Peer startup | Exited 1; Node reported `Cannot find module '/fixtures/peer.mjs'` because the directory was not traversable |
| Frontend startup | Running as UID 101 |
| HTTP | Static `/` 200; `/api/echo` and `/health/ready` 503, safe `UPSTREAM_UNAVAILABLE` JSON |
| Nginx errors/network | `agent1 could not be resolved (3: Host not found)` after the peer exited; the stopped peer was absent from active network membership |
| Generated Nginx config | Fixed `https://agent1:443`, trusted host, SNI, CA file and `proxy_ssl_verify on`; no TLS bypass or port/config error |
| Original harness outcome | Same `/api/echo never reached 200` error after polling |

This establishes a deterministic native-Linux fixture permission defect and the
best-supported explanation for the hosted-only failure. A fresh hosted execution
is still needed to confirm the repair on GitHub's actual runner.

## Exact changes

1. [verify_proxy.py](../../scripts/delivery/verify_proxy.py): explicitly set only
   the three **public non-live** fixture files and test server to `0644`, and their
   dedicated temporary directory to `0755` before mounting. This changes no image,
   runtime user, capability, application configuration, trusted host or TLS policy.
   It neither creates operational credentials nor applies recursive permission changes.
2. The same harness now reports Docker stderr, the last bounded HTTP response or
   connection error, and an early container exit instead of only a polling timeout.
   On failure, before cleanup, it writes/prints a FAIL record with container states/
   users, bounded logs, `nginx -T`, resolver, network membership and file-mode probe.
   Unavailable diagnostics are recorded independently. The non-live bearer is
   redacted; no environment dump or certificate/private-key contents are collected.
   The existing always-upload step already includes `artifacts/m4b/proxy.json`.
3. The wrong-host negative case additionally requires Nginx's actual certificate-name
   rejection. Generic upstream/DNS/startup 503 can no longer satisfy that TLS check.
4. [test_proxy.py](../../tests/delivery/test_proxy.py): four regressions exercise
   fixture permissions without touching unrelated files, early exit plus HTTP detail,
   last connection error, and best-effort/redacted retained failure diagnostics.
5. This evidence, its JSON results and the original evidence's link are the only
   documentation changes. Application, frontend proxy config, Dockerfiles, dependencies,
   workflow/release gate, infrastructure and business behavior are unchanged.

## Verification and limits

The repaired harness passed on the same Linux volume with owner UID 1001 and peer
UID 1000, using the new actual `0755`/`0644` modes. TLS, bearer/header isolation,
dependency readiness, certificate-name rejection and all seven unsafe-config cases
passed. A separate reinjected `0700` fault then produced an early peer-exit failure
with HTTP 503 and saved states/logs/config/network diagnostics **before cleanup**.
The final normal harness was rerun successfully after that fault.

| Executed check | Result |
| --- | --- |
| Application format, lint, typecheck, production build | PASS |
| Application tests | 64 passed; original M2 cases unchanged |
| Native Playwright | 3 passed |
| Full delivery/security suite | 12 passed: original 8 plus 4 harness regressions |
| Bicep lint/build/policy | All four templates pass; no Azure/ARM validation |
| actionlint | PASS, shellcheck not invoked |
| Isolated production container smoke | PASS, including all 3 browser cases, fixtures/pricing, runtime hardening and API-replacement persistence |
| Repaired TLS harness | PASS normal local run and Linux-volume replay; injected permission fault fails closed with retained evidence |
| Trivy configuration checks | PASS both Dockerfiles and finite registry-access ARM coverage; policy covers all four compiled templates |
| Final image scans/SBOM/provenance | Both images zero reported HIGH/CRITICAL; unsigned local evidence, not release authorization |
| Secret/documentation/whitespace checks | See final JSON results; tracked and untracked files included |

Raw diagnostic evidence remains in ignored `artifacts/m4b-ci-repair/`; the final
successful proxy record is in `artifacts/m4b/proxy.json`. The JSON summary retains
selected responses/errors and hashes. No private key content is committed. Tests
cleaned only their owned containers, volumes and networks; the M2 demo was untouched.

Host: macOS 15.6.1 arm64, Docker Desktop 28.3.3, Linux arm64 test images, Node
24.22.2/npm 11.19.1. This reproduces Linux filesystem semantics, not an Ubuntu x64
GitHub runner. Updated hosted CI, hosted image scans/provenance and CodeQL remain
unverified; the previous development minimatch advisory is not waived or repaired
by this harness-only change. No Azure authentication/resources, paid service,
deployment, settings change, commit, push or workflow rerun occurred.

## Resumed validation — 2026-11-09

Initial HEAD remains `1e8d92d`; the working tree already contained exactly the five
repair files listed above. Their work was preserved. The harness and regression
test remain byte-identical to their state at resume; only this evidence and its
JSON summary were refreshed. No additional application, workflow or image-recipe
correction was justified. Read-only job metadata and full containers logs were
inspected again; the failed step and missing hosted peer/HTTP diagnostics match
the original observations. No hosted rerun was triggered.

Before changing evidence, the committed failing harness was loaded from Git and
replayed using an isolated Linux volume: owner 1001, directory `0700`, peer UID
1000, with the original separate frontend CA-file mount retained. It reproduced
the exact timeout. Captured **before cleanup**: peer exit 1/module-not-found,
static 200, API/readiness 503, Nginx DNS failure after peer exit, and generated
`https://agent1:443`/CA/SNI/name verification configuration. Replaying the prepared
repair with the same volume owner and actual `0755`/`0644` modes passed. A separate
`0700` injection produced an immediate peer-exit error including HTTP 503 and
saved the FAIL record, logs, config, state and network before cleanup. The normal
unmodified invocation subsequently passed. This isolates a harness fixture/startup
defect; it does not establish the discarded hosted runner state with certainty.

| Freshly executed check | Result |
| --- | --- |
| Node 24.22.2/npm 11.19.1 application format/lint/types/build | PASS; official Node archive checksum verified |
| License generation/drift | PASS; 417 locked records, retained notices unchanged |
| Application tests | 64 passed; initial sandbox loopback EPERM resolved by authorized execution |
| Native browser journeys | 3 passed |
| Bicep lint/build/policy and actionlint | PASS all four templates; no Azure access; shellcheck not invoked |
| Delivery/security tests | 12 passed, including four harness regressions and fail-closed mutation/canary checks |
| Production container smoke | PASS including all 3 browser cases, runtime hardening, pricing and replacement persistence |
| Proxy | PASS Linux-volume replay and normal run; injected permission failure correctly retains diagnostics |
| npm audit high/critical gate | PASS threshold: 0 HIGH/CRITICAL, 10 moderate development-graph findings; no waiver |
| Trivy configuration scan | PASS two Dockerfiles and finite registry-access ARM coverage; authorized retry refreshed public checks after sandbox fallback |
| Trivy image gate / SBOMs | **BLOCKED**: API 0 HIGH/CRITICAL; frontend 7 HIGH package findings, 0 CRITICAL; both SBOMs generated |
| Provenance | Not regenerated after the image gate failed; the earlier provenance/hashes above are historical |
| Secret/history, repository and whitespace checks | Results recorded in the resumed JSON summary, including all untracked text files |

The refreshed vulnerability DB was updated 2026-11-09 13:58:27 UTC and downloaded
18:06:21 UTC. Frontend findings: `libexpat` 2.9.0-r0 has
CVE-2026-113351, CVE-2026-115506, CVE-2026-117610 and CVE-2026-118370 (reported
fix 2.10.0-r0); `musl` and `musl-utils` 1.2.6-r2 each have CVE-2026-107891
(reported fix 1.2.6-r3); `zlib` 1.3.2-r0 has CVE-2026-85091 (reported fix
1.3.2-r1). These are scanner observations, not a reachability assessment or an
accepted exception. Package/base-image remediation needs a separate bounded task;
this repair does not change image recipes or weaken the gate.

Fresh raw records and the isolated replay helper are retained locally under
ignored `artifacts/m4b-ci-repair/resume/`; selected values and SHA-256 hashes are
in the JSON summary. The original ignored records were preserved. Docker 28.3.3
still runs Linux arm64 under macOS; this is not an Ubuntu x64 hosted execution.
Test-owned resources were removed and pre-existing stopped M2 containers/volume
were untouched. New hosted CI, CodeQL and all cloud integration remain unverified.
The proxy repair is **Locally tested**; release remains **BLOCKED / NO-GO**. No
cloud authentication, credentials, settings change, deployment, commit or push
was performed. Stop at this bounded repair.
