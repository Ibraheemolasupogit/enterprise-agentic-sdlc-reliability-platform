# M4C-C3 — Local OIDC client, PKCE and verified sessions

Latest verification: 2026-11-12 UTC (original implementation: 2026-11-10). Base: `26e47b994c7dfa99216246e25e3ac8a967505beb`;
original implementation began clean; this resumed verification preserved all 44
pre-existing C3 files (25 tracked modifications and 19 untracked files). Authority: owner's **C3 local implementation-only**
request, superseding planning-only restrictions. Status: **C3-A1/A2/A3, P01–P15 and overall C3 local acceptance met
after the owner-authorized libxslt 1.1.43-r4 security patch**. Actual pinned client/cryptography/API/SQLite execute; provider
responses and HTTPS transport routing are **Simulated**. C6 real-provider execution
and other milestone work remain **Blocked / unauthorized**. M4A deployment NO-GO
is unchanged. No new hosted result is claimed for this uncommitted diff.

The [approved plan](../milestones/m4c-c3-oidc-plan.md) and its
[planning JSON](m4c-c3-planning.json) are preserved as historical design evidence.
[Execution JSON](m4c-c3-oidc.json) records exact source/config/schema/fixture hashes,
file manifest, cases, command times/exits, bundle comparison, scans and limitations.
Last verified hosted baseline remains run 42805606271 at `b56d9bd` (97 tests;
mandatory application/policy/containers/required passed, CodeQL skipped). No GitHub
setting, credential, service, workflow dispatch, commit or push was performed here.

## Independent local recheck of the existing repair — 2026-11-12

The owner's later request authorized inspection/rebuild/rescan and regression
verification of the existing C3 work. The `libxslt=1.1.43-r4` Dockerfile repair
**was already implemented** before this task. Every existing source-binding hash
matched the prior evidence. No Dockerfile, package/base pin, npm lock, application,
test, workflow or scanner-policy change was needed. Only this Markdown evidence
and its JSON were updated; all other initial tracked/untracked files are
byte-identical to the task-start snapshot.

Both verification images were rebuilt with the existing Compose/Dockerfiles,
then rescanned with the unchanged Trivy 0.72.0 HIGH/CRITICAL gate, including a
final scan after the container regression rebuild. Content-addressed build caches
were reused. Trivy's available DB was updated at 2026-11-12 18:57:38 UTC, with next
update at 2026-11-13 18:57:38 UTC. No suppression or ignore-unfixed option was added.

| Image | Final gate exit | HIGH | CRITICAL | Targeted libxslt findings |
| --- | --- | --- | --- | --- |
| Frontend | 0 | 0 | 0 | CVE-2026-125350, CVE-2026-87636 and CVE-2026-9947 not reported; SBOM confirms 1.1.43-r4 |
| API | 0 | 0 | 0 | None reported; libxslt absent from API SBOM |

Both fresh CycloneDX SBOMs have the same component identities as the prior patched
SBOMs. Final image IDs match the scan reports, SBOMs and unsigned local provenance.
The `securityReverification` JSON section binds current identities/hashes, exact
commands/times/exits, source preservation, package comparisons and fresh cases.
Ignored logs/reports are under `artifacts/m4c-c3/recheck-2026-11-12/`.

The first host-side pass selected system Node 22.17.1/npm 10.9.2 and was excluded
from acceptance. All relevant gates were repeated with the already installed
**Node 24.22.2/npm 11.19.1**; superseded logs are retained separately. The pinned
rerun passes **195/195 application tests in 13 files**, zero failed/skipped, with
all original 97 names preserved; **3 native + 7 capture-off OIDC + 3 container
browser journeys**; **4/4 harmful mutations rejected**; **13/13 delivery-security
tests**; proxy/TLS/hardening/persistence, capture before/after, format/lint/types/
build/licences/audit, actionlint, four-template offline Bicep, configuration scans
and provenance. Repository/JSON, tracked/every-untracked whitespace and redacted
history/tree secret checks also pass on the refreshed evidence.

**P01–P15, C3-A1/A2/A3 and overall C3 local acceptance are reconfirmed.** Provider
responses/HTTPS routing remain **Simulated**; this is local arm64 verification,
with no new hosted/x86_64 or real-provider result. Ten existing MODERATE npm
findings remain. CodeQL/SAST, governance, real SQL/provider and Azure gates remain
open; deployment stays **NO-GO**. No Azure action, real-provider authentication,
GitHub settings change, commit or push occurred. No other repository was accessed.

## P15 security acceptance — authorized single-package correction

Date: 2026-11-12 UTC. The owner explicitly authorized an exception only for the
frontend Alpine `libxslt 1.1.43-r4` package, conditional on trusted availability,
compatibility and a passing unchanged image gate. That exception supersedes the
package restriction only for this patch. **P15 and overall C3 local acceptance
are now met.** The earlier blocked verification is retained below and in JSON.

| CVE reported HIGH before | Before | Scanner-reported fix / installed after | After scan |
| --- | --- | --- | --- |
| CVE-2026-125350 | libxslt 1.1.43-r3 | 1.1.43-r4 | Not reported |
| CVE-2026-87636 | libxslt 1.1.43-r3 | 1.1.43-r4 | Not reported |
| CVE-2026-9947 | libxslt 1.1.43-r3 | 1.1.43-r4 | Not reported |

The existing image is Alpine 3.24.2/aarch64, configured for the official v3.24
main/community repositories. `apk policy` selects the fixed package from
`https://dl-cdn.alpinelinux.org/alpine/v3.24/main`; default signature verification
uses existing trusted keys. A disposable install and the final SBOM comparison
both show **only libxslt r3 → r4**, with no package additions/removals. API SBOM
component identities are unchanged. [Alpine metadata](https://pkgs.alpinelinux.org/package/v3.24/main/aarch64/libxslt)
records X11 terms and packaging revision `e85ecba78539486bd0a685963ca5da3e1652fbd0`;
the [third-party register](../../THIRD_PARTY_NOTICES.md#m4c-c3-p15-libxslt-security-patch--2026-11-12)
records provenance and retained obligations. Browser npm licence output is unchanged.

The sole implementation change adds `libxslt=1.1.43-r4` to the existing frontend
`apk add --no-cache` layer. The Nginx base digest remains
`sha256:f5116ed4606f3eb015dd4a8e28cb9b351476dc0ad4bc6e9f93b19cec130cdf03`;
all nine base filesystem layers are retained. Nginx stays **1.30.6**, and its binary
and `/usr/share/licenses/nginx/COPYRIGHT` are byte-identical. Library SONAMEs resolve,
runtime user stays 101 and image configuration is unchanged. Node dependencies,
other package pins, API recipe, proxy TLS/CSP/header controls and all application,
test, CI and scanner-policy source are unchanged. No repository/key change,
blanket upgrade, vulnerability suppression or reduced threshold was introduced.

Fresh post-patch checks pass: **195/195 tests in 13 files**, zero failed/skipped,
including all original 97 names and real SQLite contracts; **3 native + 7 OIDC +
3 container browser journeys**; **4/4 harmful mutations rejected**; **13/13 delivery
tests**; format/lint/types/build/licences/audit, capture before/after, container
hardening/persistence, HTTPS proxy, offline Bicep/actionlint, config scans,
repository/whitespace/secrets and unsigned local provenance. Both rebuilt images
pass the existing Trivy gate with **zero HIGH/CRITICAL findings**; both SBOMs are
retained. Ten MODERATE npm findings remain; image scans do not claim zero findings
below their unchanged HIGH/CRITICAL threshold.

Exactly nine existing files changed in this follow-up:

- `apps/octocat-supply/frontend/Dockerfile`
- `THIRD_PARTY_NOTICES.md`
- `README.md`
- `docs/capability-status.md`
- `docs/decisions/0007-application-identity.md`
- `docs/delivery.md`
- `docs/milestones/m4c-scope.md`
- `docs/evidence/m4c-c3-oidc.md`
- `docs/evidence/m4c-c3-oidc.json`

`p15SecurityAcceptance` in the JSON binds before/after scans and SBOMs, image
identities, preservation proof, exact commands/times/exits, per-case results and
the changed-file hashes. Ignored logs reside in
`artifacts/m4c-c3/p15-libxslt-2026-11-12/`. Execution is **local Linux arm64**;
no new hosted/x86_64 or real-provider validation is claimed. Provider responses
and HTTPS routing remain **Simulated**, with actual client/JOSE/Express/SQLite.
No real sign-in/production credential, Azure authentication, provisioning,
deployment, GitHub setting, commit or push was required or performed. No C2/C4/C5/C6
work started. SAST/governance, real SQL/provider and cloud gates remain open;
deployment stays **NO-GO**. Stop at P15.

## Verification before the P15 patch — historical blocked result

The existing implementation, fixtures and prior evidence were inspected without
restarting or discarding any work. All pre-resume source-binding hashes matched
the recorded evidence. No application, test, workflow, package, image or scanner
policy repair was needed within C3; only these seven existing documentation files
were refreshed: README, capability status, identity ADR, delivery, M4C scope and
the Markdown/JSON C3 evidence. Those were the original 44 C3 files; the current 46-file manifest includes the two
authorized P15 additions.

Fresh execution passed **195/195 application tests in 13 files**, zero failed or
skipped. A separate disposable `git archive` of `26e47b9` passed **97/97 in eight
files**, and a multiset comparison confirms every original name also passes in
the current suite. Current tests include eight Node responder, 43 protocol,
19 ID-token, 15 lifecycle, six API-session and 21 backend authentication cases;
the 33 real SQLite contracts/regressions and eight Simulated SQL tests pass.
These group counts overlap P01–P15 and are not additional totals. All three native,
seven capture-off simulated-provider and three production-container browser cases
pass, as do all four harmful mutations and 13 delivery/security tests.

The pre-patch required image scan **failed with exit 1**. The API image has zero
HIGH/CRITICAL findings. The frontend image reports **three HIGH, zero CRITICAL**
findings in `libxslt 1.1.43-r3`: `CVE-2026-125350`, `CVE-2026-87636` and
`CVE-2026-9947`; the scanner lists `1.1.43-r4` as fixed. Both scan reports and SBOMs
were produced. This supersedes the historical 2026-11-10 zero-finding scan result;
it is a vulnerability-gate failure, not unavailable tooling. At that point the pinned frontend Dockerfile/image inputs were unchanged and
`AGENTS.md` prohibited a package upgrade without separate authorization. **P15 was
Blocked**, despite A1/A2/A3 passing locally. The owner subsequently authorized the
single-package correction documented above; the old findings remain historical.

Fresh command times/exits, per-case outcomes, P01–P15 mappings, image/report hashes,
source preservation and clean-bundle comparison are in `resumeVerification` in the
JSON. Ignored raw tooling logs are under `artifacts/m4c-c3/resume-2026-11-12/`.
No real identity-provider sign-in, production credential, Azure authentication,
provisioning, deployment, GitHub settings change, commit or push is required or
performed. No C2/C4/C5/C6 implementation was started. Real-provider compatibility
and hosted execution of this diff remain unverified; deployment stays NO-GO.

## Implemented boundary

Retained `oidc-client-ts` **3.5.0**, `jose` **6.2.14** and the complete existing lock.
No npm package addition, upgrade or new framework. The separately authorized
P15 exception updates only the existing frontend OS libxslt package. Added JOSE's full MIT text to the
browser notice generator/output; dependency inventory remains byte-identical.

The controller uses actual library code flow/S256/state with an explicit random
nonce. It checks public config/page-origin equality and vetted single-origin HTTPS
metadata before constructing the manager; caller data/JWT key URLs never select
trust. It consumes a callback once, rejects ambiguous/foreign/expired/unsolicited
responses and uses a 300-second pending descriptor bound to deployment config.
Transient state keys encode only public config; cart namespaces SHA-256 hash the
verified ID issuer/client/subject. No raw identity claims/tokens enter persistent
storage. The retained RFC 7515 key/vector notice is reused only by Node fixtures;
no operational signing key or new credential was created/registered.

Raw library user events do not grant a session. JOSE verifies RS256 signature,
issuer, SPA audience, subject, nonce, expiry/nbf/iat and authorized-party constraints
before any protected UI/API publication. ID and API token subjects intentionally
differ in fixtures; API authority remains the verified access-token owner. API
claims/age policy, routes, repositories, SQL, pricing, App business components,
database migrations, IaC and production proxy trust/CSP/header stripping are unchanged.

Identity calls have 5s bounds, JWKS 1s and callback acceptance 15s. Browser expiry
uses the earlier ID/access lifetime, with bounded rescheduling, dispatch and resume
checks. API 401 invalidates the current generation and offers explicit sign-in;
403/503 remain distinct, without refreshing or replaying a mutation. Logout/unmount
abort owned requests, suppress late acceptance/responses and cannot erase a newer
sign-in's state. They cannot revoke a bearer or undo an accepted server write.

Only same-origin `/api/` requests get the current access token; cookies are omitted,
redirects rejected and IDs encoded. Legacy OIDC references migrate only after an
actual authenticated cart lookup: 200 copies the UUID, 404 removes a stale reference,
401 closes the session and 403/503/network failure preserves the reference with an
explicit retry state. Anonymous references are never claimed. Reload loses memory
authority; local logout affects this tab, not provider SSO or other signed-in tabs.

## Actual P01–P15 outcomes

P01–P15 **Pass locally**, including the patched-image security gate.
These outcomes do not represent real-provider integration.
Full executed case names/results are in the JSON, not inferred from this table.

| ID | Actual evidence |
| --- | --- |
| P01 | Actual UserManager/OidcClient produce fresh state/nonce/verifier/S256; independent Node SHA-256 verifies challenge at redemption; public-client-only exchange; browser reaches authoritative 31995p subtotal / 3199p discount / 28796p total |
| P02 | Unsafe/missing/page-origin/tenant/scope config and issuer/endpoint/PKCE/mode metadata fail before navigation/exchange; built-browser hostile metadata case stays closed |
| P03 | Missing/wrong/duplicate state/code/error, code+error, fragments, foreign path/origin, missing/corrupt/expired/future descriptor and unavailable storage denied; callback scrubbed before config load and on config failure; owned storage cleaned |
| P04 | Actual state consumption and controller single-flight give one exchange, including StrictMode; replay and swapped independent storage contexts fail; responder separately rejects wrong verifier/client/redirect/grant/code and code reuse |
| P05 | Denied consent/login, invalid grant, malformed JSON, missing tokens, wrong type/lifetime, unexpected refresh and metadata/token/JWKS faults fail closed. Controlled-clock tests start at the actual requested phase; aggregate deadline also rejects a late unabortable verification result |
| P06 | Real JOSE rejects bad signature/alg/key/issuer/audience/sub/nonce/azp/extra audience and expired/future/missing times. A stored/library-emitted user with wrong issuer never publishes Signed in. Browser rejects wrong audience/nonce/issuer/signature; token jku/x5u cannot change key destination |
| P07 | Missing/unsigned/tampered/expired/future/over-age/wrong issuer/audience and ID-audience tokens denied. Real Express responses prove safe 401/code, no stack/details; forged principal/owner fields remain rejected in original HTTP tests |
| P08 | Real HTTP role/scope denials are exact 403/FORBIDDEN; actual scp claim variant succeeds. Client preserves 403, does not log out/refresh automatically or retry the request |
| P09 | Real HTTP unresolved trusted-key outage gives safe 503/IDENTITY_UNAVAILABLE, with DB readiness still 200. Actual JOSE cache accepts a still-valid known key during outage, rejects expired/unresolvable keys and returns 401 for a healthy JWKS without the kid. Client retains distinct 503 behavior |
| P10 | Timer, dispatch and tab-resume expiry stop old tokens. API one-hour cap rejects a token with later browser expiry; Chromium requires explicit usable reauthentication. Same-subject new session uses a fresh access token, with no automatic mutation replay |
| P11 | Two browser contexts have separate cart namespaces/baskets and deliberately different ID/API subjects; both directions of cart read/set/remove/delete yield 404 through the real API. Legacy migration approval/404/503 and anonymous non-transfer are tested |
| P12 | Logout during exchange, component unmount, delayed old API response, new sign-in while an old callback finishes, tab independence and reload recovery are tested. No late session/storage restoration; no persisted/broadcast tokens |
| P13 | Encoded IDs remain on the approved API; request leases compose abort/deadline, use current token and omit cookies/owner fields. Real browser redirect attempt dispatches no request/bearer to the foreign origin. Isolated destination-check bypass is detected |
| P14 | Capture-off config/effective runtime guard, debug/CLI override rejection, preserved-output prohibition, sanitized reporter, no attachments, canary rejection and production-asset private-vector checks pass. Trace/video/screenshot/HAR/storage-state capture cannot be enabled silently |
| P15 | **Pass locally:** original 97 preserved within 195 passing tests; 3 native + 3 container + 7 OIDC browser cases, four rejected mutations, 13 delivery tests, format/lint/types/build/licensing/audit, workflow/offline IaC, proxy/config/secret/repository/provenance checks pass. Both rebuilt images have zero HIGH/CRITICAL findings after the authorized libxslt 1.1.43-r4 pin |

`npm run test:auth-mutations` copies only owned inputs to disposable directories,
links the existing installed packages and executes actual behavioral tests. Nonce
omission fails P01/P04; ID-verification bypass fails 15 P06 assertions; early session
publication fails P06; destination-check bypass fails P13. Compile/setup/no-test
failures cannot count as a detected mutation. Copies/reports are removed; retained
output contains only mutation name, contract ID, counts and rejection status.
The capture guard independently rejects unsafe capture/report/debug configurations
and deliberate non-live code/verifier/state/nonce/token/subject/private-vector canaries.

## Execution and security checks

Environment: macOS arm64; Node **24.22.2**, npm **11.19.1**, Vitest **5.0.5**,
Playwright **1.64.1**, SQLite **3.53.4**, Python **3.12.8**. Containers run on local
Docker Engine **28.3.3**, Linux arm64. Existing Bicep **0.48.1**, actionlint **1.7.12**,
Gitleaks **8.30.1**, Trivy **0.72.0** were reused. No tool/dependency install was
needed. The same existing tools were reused for the 2026-11-12 rerun. Exact UTC times/commands/exits and binding hashes are in the execution JSON.
Raw local output stays ignored under `artifacts/m4c-c3/`; delivery scripts retain
their existing `artifacts/m3/` and `artifacts/m4b/` reports. No raw OIDC trace/HAR,
storage export, screenshot/video or protocol values were retained by the OIDC profile.

| Command/check | Result |
| --- | --- |
| `npm run format:check`; `npm run lint`; `npm run typecheck`; `npm run build` | Pass; format/type discovery includes the new Node fixture tree and OIDC config |
| `npm test` with default/JSON reporters | **195 passed / 13 files**, zero failed/skipped, including all original 97 and real SQLite C1's 33 cases |
| `npm run test:auth-mutations` | All four isolated harmful mutations rejected by intended assertions |
| `npm run test:e2e` | Three original Chromium journeys pass with forced cold dependency optimization; original assertions unchanged |
| `npm run test:e2e:oidc` | Seven Chromium journeys pass, no retries/skips; actual built app/library/JOSE/API/SQLite with only simulated provider traffic |
| `npm run test:auth-capture` before/after OIDC browser run | Pass, including negative capture/canary controls and private-vector exclusion from built JS |
| `npm run licenses` and deterministic regeneration / inventory checks | Pass; only planned JOSE browser notice addition, lock/inventory unchanged |
| `npm audit --audit-level=high --json` | Pass: zero HIGH/CRITICAL; ten existing MODERATE findings remain, without waiver or unrelated upgrade |
| `actionlint -shellcheck=`; `python3 scripts/delivery/validate_infra.py` | Pass; all four existing Bicep templates compile/lint offline without warnings; no ARM command |
| `python3 -m unittest discover -s tests/delivery -v` | **13 passed**, including original 12 plus mandatory/order/no-skip/no-bypass mutations for C3 checks |
| `python3 scripts/delivery/verify_containers.py` | Pass: isolated images, twelve fixtures/pricing, hardening, API replacement persistence, three original browser journeys, own cart/project/volume cleanup |
| `python3 scripts/delivery/verify_proxy.py` | Pass: CA/host/SNI/bearer/header boundary, wrong-name API/readiness 503 with static 200, seven rejected unsafe configs; unchanged harness/production proxy |
| `python3 scripts/delivery/scan_config.py` | Pass: zero HIGH/CRITICAL in required configuration inputs |
| `python3 scripts/delivery/scan_images.py` | **Pass, exit 0:** both rebuilt images zero HIGH/CRITICAL; all three libxslt findings cleared. Both SBOMs generated; unchanged threshold, no waiver |
| `python3 scripts/delivery/provenance.py` | Pass: current source/image/report/SBOM identities bound; dirty local tree, unsigned and release-ineligible |
| Repository/JSON/tracked + every untracked whitespace and Gitleaks history/tree checks | Pass; no ignored findings, threshold reduction or security exceptions |

The clean production bundle increased from **301,598 to 328,048 bytes**; reproducible
gzip level 9 increased from **88,871 to 97,729 bytes**, **+8,858 bytes**, below the
approved 10 KiB review bound. All JS chunks (one in each build), method and hashes
are recorded. CSS/business assets and the dependency graph are unchanged. The real
bundle comparison replaces the planning-time selected-export estimate.

## Resolved findings and bounded harness adjustments

- During the resumed evidence refresh, a filename-to-hash dictionary triggered ten
  generic-key findings in the secret scanner. Inspection confirmed they were source
  SHA-256 digests. The inventory now uses explicit `path`/`sha256` records; the
  scanner and its exclusions are unchanged. The corrected tree scan passes.


- The Node fixture originally used `import.meta.url`; browser-test transformation
  produced a non-file URL. It now resolves the retained fixture from the explicit
  application working directory; it is still Node-only and absent from production
  assets. No new key/credential was generated to repair the fixture.
- Redirect-chain interception initially prevented a simulated provider callback
  from returning through the routing fence. The test responder now uses HTML
  refresh navigation, which starts a new intercepted navigation. It still executes
  actual full-page client callback/code/PKCE behavior, but is not proof of a real
  provider's HTTP 302/TLS/CORS handling. An automatic fixture installs the fence
  for every OIDC test, including cases not explicitly requesting its control API.
- A new JOSE import triggered cold Vite dependency reoptimization/reload during an
  unchanged anonymous search assertion. Only the **test server** changed: explicit
  vendor prebundle, graph warmup and readiness gating, with forced cold optimization.
  A warm-cache retry alone was not accepted. Production Vite config, browser
  assertions, timeouts and retries were not changed.
- Adversarial timing found that a cancelled callback's final cleanup could erase
  newer pending state. Cleanup is now generation-bound, the namespace is available
  synchronously for immediate cancellation, and explicit regressions cover newer
  sign-in state, unmount and stale responses. Fake clock tests wait for the real
  transport phase before advancing and route native timeout creation through the
  controlled unit-test clock. Browser/runtime timeout policy is unchanged.
- The capture guard accepts Playwright's normalized empty reporter-options tuple
  while still rejecting additional/options-bearing reporters and effective capture
  overrides. A declaration file provides real typechecking for the existing MJS
  toolchain; the extra mutation runner makes the approved negative controls repeatable
  and mandatory. These are local test-harness changes, not another milestone.

## Limits and C6 handoff

C3 proves **Locally tested client/crypto/API/SQLite behavior with Simulated provider
responses**. Virtual HTTPS routing has no real provider TLS handshake, registration,
consent, tenant, CORS, SSO/logout or rotation evidence. No real token/account, new
certificate/operational key, IdP deployment, SQL engine/MI, Azure session/resource,
GitHub setting, paid service, commit or push was used. SQL's eight recording tests
remain **Simulated**. This is not fresh hosted verification of the C3 diff.

Capture tests establish configured collection/reporting and known-canary rejection,
not universal leak detection, JS heap zeroization or immunity to same-origin XSS.
PKCE/state/nonce require provider-side one-use/binding behavior in C6; copied storage
under full same-origin compromise is not prevented by sessionStorage alone. Logout
is tab-local, cannot revoke a valid bearer or undo a request already accepted by the
API, and does not end provider SSO. Readiness remains a database check. Image/config
scans use the unchanged HIGH/CRITICAL policy and do not claim zero lower findings;
ten MODERATE npm findings remain. The pre-patch frontend image had three HIGH libxslt findings; the authorized
1.1.43-r4 update clears them, with zero HIGH/CRITICAL in both current images. CodeQL/SAST and independent governance remain
open under C5; no accepted exception or protected-release claim was invented.

C6 requires **new explicit owner authorization** for exact tenant/SPA/API registrations,
HTTPS callback and trust/CORS, token version/issuer/audience/role/delegated scope,
two approved users, bounded sign-in attempts, capture-off settings, observation and
cleanup. Recheck the single-origin HTTPS/RS256 profile against actual metadata;
incompatibility stops, without broadening CSP, trusting a token URL, using an ID token
as API authority, adding client secrets/refresh/offline grants or weakening TLS.
Prove actual two-owner journeys/denials, replay/PKCE/nonce, expiry/over-age reauth,
claim semantics and authorized failure behavior with sanitized evidence. Foreign-
tenant tests require a separately approved real foreign identity; published keys
must never be registered. No provider outage/key change may be induced by inference
from C3. SQL/private Azure/infrastructure/governance gates remain separate.

Stop after C3; M4A deployment remains NO-GO.

## Exact files changed

The complete repository-relative C3 manifest follows. The original 44 files were
retained; the P15 exception additionally changes the frontend Dockerfile and root
third-party register, for 46 files against the baseline. The nine paths changed
in the P15 follow-up are listed above. No pre-existing work was discarded. Application changes are limited to the five frontend authentication/
API/bootstrap files; API production/business/SQL/infra/proxy and original C1/browser
assertions are preserved. API auth tests strengthen existing status assertions and
add HTTP regressions. The same manifest and hashes appear in the execution JSON.

- `THIRD_PARTY_NOTICES.md`
- `apps/octocat-supply/frontend/Dockerfile`
- `.github/workflows/ci.yml`
- `AGENTS.md`
- `README.md`
- `apps/octocat-supply/api/test/auth.test.ts`
- `apps/octocat-supply/e2e/oidc/auth.spec.ts`
- `apps/octocat-supply/e2e/oidc/fixtures.ts`
- `apps/octocat-supply/frontend/public/third-party-notices.txt`
- `apps/octocat-supply/frontend/src/AuthApp.tsx`
- `apps/octocat-supply/frontend/src/api.ts`
- `apps/octocat-supply/frontend/src/idToken.ts`
- `apps/octocat-supply/frontend/src/main.tsx`
- `apps/octocat-supply/frontend/src/oidcSession.ts`
- `apps/octocat-supply/frontend/test/ApiSession.test.tsx`
- `apps/octocat-supply/frontend/test/IdToken.test.tsx`
- `apps/octocat-supply/frontend/test/OidcProtocol.test.tsx`
- `apps/octocat-supply/frontend/test/OidcSession.test.tsx`
- `apps/octocat-supply/frontend/test/oidcHarness.ts`
- `apps/octocat-supply/frontend/test/setup.ts`
- `apps/octocat-supply/package.json`
- `apps/octocat-supply/playwright.config.ts`
- `apps/octocat-supply/playwright.oidc.config.ts`
- `apps/octocat-supply/scripts/e2e-server.mjs`
- `apps/octocat-supply/scripts/licenses.mjs`
- `apps/octocat-supply/scripts/oidc-e2e-server.mjs`
- `apps/octocat-supply/scripts/oidc-reporter.mjs`
- `apps/octocat-supply/scripts/verify-auth-capture.d.mts`
- `apps/octocat-supply/scripts/verify-auth-capture.mjs`
- `apps/octocat-supply/scripts/verify-auth-mutations.mjs`
- `apps/octocat-supply/test/fixtures/oidc-provider.test.ts`
- `apps/octocat-supply/test/fixtures/oidc-provider.ts`
- `apps/octocat-supply/tsconfig.tests.json`
- `apps/octocat-supply/vitest.config.ts`
- `docs/architecture.md`
- `docs/capability-status.md`
- `docs/decisions/0007-application-identity.md`
- `docs/delivery.md`
- `docs/evidence/m4c-c3-oidc.json`
- `docs/evidence/m4c-c3-oidc.md`
- `docs/milestones/m4c-c3-oidc-plan.md`
- `docs/milestones/m4c-scope.md`
- `docs/roadmap.md`
- `docs/threat-model.md`
- `scripts/delivery/policy.py`
- `tests/delivery/test_security.py`
