# M4B application Playwright installation reliability repair

Date: 2026-11-10 UTC. Base: committed `3abbf63`; initial working tree clean.
Status: **Implemented and Locally tested; new hosted execution unverified.**
Deployment remains **NO-GO**. Scope is the application job's hosted browser
installation timeout; no application/package/container/proxy implementation changes.
Exact hashes, versions and results: [JSON evidence](m4b-playwright-ci-repair.json).

## Hosted failure and cause

Read-only metadata and full application logs were inspected for
[run 42763141078](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/42763141078),
application job `129653308605`. The runner was Ubuntu 24.04.5 x64, image
`20261101.360.1`. Checkout/setup-node, locked install, license drift, formatting,
lint, types, all 64 tests, build and the high-severity npm audit passed. Application
was cancelled during installation; E2E and containers were skipped, policy passed,
CodeQL skipped and required failed correctly. No browser execution is established
by that run.

At 05:37:29 UTC, `npm exec -- playwright install --with-deps chromium` began OS
dependency setup. The locked Playwright 1.64.1 implementation unconditionally runs
`apt-get update` before `apt-get install -y --no-install-recommends`. It does this
even when runtime libraries are already present. The log shows repeated ignored
requests to `http://azure.archive.ubuntu.com`, subsequent HTTPS archive responses,
and an ignored `noble-updates/main amd64 Packages` request. Progress ceased after
05:37:54; cancellation occurred at 05:56:16, within the application job's existing
20-minute timeout behavior. No Chromium download started. This is an apt repository
index-fetch stall, rather than a failed application assertion or browser launch.
The logs do not identify a deeper mirror/network cause or missing package list.

The [exact runner inventory](https://github.com/actions/runner-images/blob/ubuntu24/20261101.360/images/ubuntu/Ubuntu2404-Readme.md)
lists Chrome, Chromium, Xvfb and some libraries/fonts. That suggests many browser
libraries already exist, but does not establish the complete dependency/font set
for this Playwright revision. The install command catches host-validation errors
as warnings after download; real launch still fails on missing requirements.
Simply removing `--with-deps` on the host would therefore rely on unverified runner
contents. Retrying mirrors or increasing the job limit would retain the failed
network operation. Neither approach was selected.

## Exact correction and supported environment

Only the application job gains a container: official
`mcr.microsoft.com/playwright:v1.64.1-noble`, immutable index digest
`sha256:2f05f8a734509a7b3f26a912639488ee08f58a7b292d14d62271bcff9038768f`,
with `--user 1001`. [Playwright's documented CI container pattern](https://playwright.dev/docs/ci#via-containers)
supplies browser system dependencies and browser binaries in advance. The reviewed
[versioned image recipe](https://github.com/microsoft/playwright/blob/cfe490d941f992655948eee8fd4fd94e1c4234bf/utils/docker/Dockerfile.noble)
installs those dependencies at image-build time and places browsers in
`/ms-playwright`. The Playwright npm package is still installed from our existing
lockfile, not assumed to be included in the image.

The application install step becomes `npm exec -- playwright install chromium`,
named to identify its no-runtime-apt purpose, with a five-minute step limit. It
uses the version-matched bundled Chromium/headless shell and FFmpeg. Existing
setup-node still selects Node 24.22.2; all quality, audit and `npm run test:e2e`
commands remain. The application job limit stays **20 minutes**. No timeout was
increased, package upgraded, browser channel substituted, launch flag added,
host-requirement check bypassed or E2E test skipped.

The three locked packages `@playwright/test`, `playwright` and `playwright-core`
remain 1.64.1; browser manifest revision remains 1248, Chromium 156.0.8078.4.
Image/index/source revision/rights were recorded in the
[third-party register](../../THIRD_PARTY_NOTICES.md#m4b-application-ci-browser-environment)
before local use. No upstream recipe was executed as an installer or copied into
an application image. The selected image is unmodified testing infrastructure.

Workflow policy now requires a digest-pinned Noble Playwright image matching the
lockfile, UID 1001 and the browser-only install command. Four added mutation cases
reject a mutable image, version mismatch, container privilege escalation and
restoration of the apt-based application install. Existing permission/trigger/
action-pin/gate/scanner and E2E policy assertions remain intact.

## Local verification

| Executed check | Result and limit |
| --- | --- |
| actionlint `-shellcheck=""` | PASS workflow syntax/context; no shellcheck execution |
| `python3 -m unittest discover -s tests/delivery -v` | 12 passed, including 4 additional mutation subcases; no inflated test-count claim |
| `python3 scripts/delivery/policy.py` | PASS current workflow and existing compiled-template invariants; templates unchanged |
| Application format/lint/types/test/build | PASS; 64 tests in 7 files, original application source/tests untouched |
| Native browser suite | All 3 unchanged cases passed on macOS arm64 |
| Clean Linux image reproduction | PASS as UID 1001 on the selected image's arm64 manifest; checksum-verified exact Node 24.22.2/npm 11.19.1, fresh `npm ci --ignore-scripts`, build, browser-only install and all 3 unchanged browser journeys |
| Actual Linux browser | Debug log shows `/ms-playwright/chromium_headless_shell-1248/...`; bundled browser launched and exited 0; no apt or browser-download phase in installation |
| License generation/drift | PASS, 417 locked records and retained browser notices unchanged |
| npm high-severity audit | PASS threshold: 0 HIGH/CRITICAL; existing 10 moderate findings remain open |
| Required-gate failure matrix | Existing executable mutation tests still reject failed/cancelled/skipped mandatory dependencies |
| Preservation review | Other four jobs structurally identical; app source/lock/config/E2E, container/proxy code, image recipes, security settings and IaC byte-identical |
| Repository/secrets/whitespace | Final results in JSON, including each new untracked text file |

Linux browser setup timestamps were 08:02:56.798–08:02:57.176 UTC; this is an
observed local bundled-browser operation, not a hosted duration guarantee. The
clean run used an isolated Linux volume and removed only its own volume/container.
Native Playwright emitted the existing NO_COLOR/FORCE_COLOR warning. Linux debug
output included D-Bus/GPU warnings; all assertions and browser process exit passed.
No new browser flags or error suppression was introduced.

## Limits and bounded stop

The host is macOS arm64/Docker Desktop, with Linux arm64 Noble execution. The MCR
index also identifies an amd64 manifest, but no GitHub Ubuntu x64 job-container
startup, checkout/setup-node action integration, runner mount permissions or
fresh hosted execution was reproduced. Those remain unverified until the owner
commits/pushes and reviews a new run. No workflow was triggered here. Registry
pulls and npm access remain network dependencies; this change removes runtime apt
from the application browser setup, not every possible CI network failure.

The **containers job remains unchanged**, including its separate host-side
`npm exec -- playwright install --with-deps chromium`. It was skipped in this run
and retains the same mirror exposure. Its browser setup, production browser smoke,
proxy, image scans and provenance must still pass in a subsequent hosted run.
This application-only repair neither certifies nor bypasses them. No new local
container/proxy/image-scan result is claimed; their source/recipes were unchanged.
SAST/CodeQL and the broader release-governance/cloud integration gaps remain open.

Ignored raw evidence is retained under `artifacts/m4b-playwright-ci-repair/`.
Changes are limited to the workflow, browser policy/mutations, delivery guidance,
upstream CI image register and this evidence pair. No authentication to Azure,
credentials, deployment, GitHub settings, application dependency changes, commit
or push occurred. Stop at this bounded CI reliability repair.
