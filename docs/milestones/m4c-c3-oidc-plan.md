# M4C-C3 — OIDC client, PKCE and safe session implementation plan

Date: 2026-11-10 UTC. Status: **Design only; planning authorized, implementation
not authorized**. Authority: owner's C3 planning request and the
[master brief](../project/master-brief.md). Baseline:
`b56d9bd189bcf9d3d077fa969c1bca2285d43742`, initially clean working tree.
[Hosted run 42805606271](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/42805606271)
has successful application/policy/containers/required jobs and skipped CodeQL.
Read-only job metadata and application logs confirm that SHA, 97 tests across
eight files and three browser journeys. Artifact contents and settings were not
reverified. This plan adds no application change, dependency, credential, provider
sign-in, resource, setting, commit or push. Deployment remains **NO-GO**.

Read with [M4C scope](m4c-scope.md), [readiness assessment](../evidence/m4c-readiness-assessment.md),
[identity ADR](../decisions/0007-application-identity.md),
[threat model](../threat-model.md) and [delivery guidance](../delivery.md#m4b-local-configuration).
[Planning evidence](../evidence/m4c-c3-planning.json) records inspected files,
source hashes, library metadata, bundle probe and documentation checks. C1's real
SQLite contracts remain accepted; SQL engine C2 is independent of this local
identity work. Neither C3 nor C6 establishes Azure SQL/managed-identity readiness.

## Recommendation and evaluated libraries

**Retain exactly `oidc-client-ts` 3.5.0.** It is already pinned and integrated with
React 19.3.1/TypeScript 6.0.3/Vite 8.3.5, implements browser code flow/PKCE and
supports explicit memory user storage plus sessionStorage transaction storage.
The [upstream release](https://github.com/authts/oidc-client-ts/releases/tag/v3.5.0)
and [documentation](https://authts.github.io/oidc-client-ts/) were reviewed. Version
3.5.0 uses browser Web Crypto and adds nonce checking **when a nonce is supplied**.
Keep PKCE/state/code exchange in the library. Add a small application session
controller and use the already pinned **`jose` 6.2.14** for browser ID-token
signature/claim verification; do not write a JWT verifier or fork library internals.

| Candidate | Stack, dependency and licence assessment | Decision / security and bundle implications |
| --- | --- | --- |
| `oidc-client-ts` 3.5.0 | Framework-neutral TypeScript; Apache-2.0; runtime dependency `jwt-decode` ^4, locked at 4.0.0 (MIT); no React peer or new package needed | Recommended existing engine. Requires HTTPS/Web Crypto. Application must supply nonce, constrain metadata, validate the ID token and gate session publication; library adoption alone does not do that |
| `react-oidc-context` 3.3.1 | Maintained AutoTS React wrapper; MIT; peers `oidc-client-ts` ^3.1.0 and React >=16.14.0 admit this stack, although inspected upstream development tests use React 18 | Adds a wrapper, lifecycle/provider API and bundle code over the same engine. Does not replace engine validation or artifact controls. No installation or measured application delta; not needed for this small boundary |
| `@azure/msal-react` / `@azure/msal-browser` | Maintained Microsoft Entra SDKs; MIT; inspected `dev` manifests show React 5.8.1, browser 5.29.0 and common 16.16.1. React peers admit ^19.2.1 and Node >=20. These are observed development manifests, **not selected release pins** | Strong Entra-specific alternative with PKCE/account/lifecycle support. Would replace the integration and introduce browser/common/wrapper packages, provider-specific cache/renewal behavior and retesting. No measured application delta. Not justified for C3's portable OIDC/local-fixture boundary |

Primary manifests: [AutoTS wrapper](https://github.com/authts/react-oidc-context/blob/main/package.json),
[MSAL React](https://github.com/AzureAD/microsoft-authentication-library-for-js/blob/dev/lib/msal-react/package.json),
[MSAL browser](https://github.com/AzureAD/microsoft-authentication-library-for-js/blob/dev/lib/msal-browser/package.json).
Microsoft documents [MSAL React integration](https://learn.microsoft.com/en-us/entra/msal/javascript/react/getting-started)
and [cache choices](https://learn.microsoft.com/en-us/entra/msal/javascript/browser/caching);
their defaults are not this application's memory-token policy. No alternative was
installed, licensed by inference, benchmarked or selected as a fallback.

The current lock has both recommended libraries; **zero new runtime/dev packages
or version upgrades are proposed**. `jose` is MIT, Web Crypto/browser compatible
and has no runtime package dependencies. Its new frontend import expands the
browser's cryptographic code and JWKS requests even though the dependency graph
does not grow. Retain Apache/MIT notices and regenerate/check the existing licence
inventory during implementation; do not copy upstream application/source examples.

An isolated export-only probe used installed Rolldown 1.2.16/Node 24.22.2 with
browser target, ESM, minification, no sourcemap and gzip level 9. Existing OIDC
exports measured **68,249 minified / 16,967 gzip bytes**; adding `jwtVerify` and
`createRemoteJWKSet` measured **86,447 / 23,491 bytes**, a **6,524-byte gzip** increase
in that probe. These are not production chunk sizes or a promised application
delta. Existing ignored build JS measured 301,598 / 88,901 bytes; it was not rebuilt
or promoted as a clean baseline. Future implementation must compare clean Vite
builds of the baseline and proposed revision, record all initial/lazy JS chunks,
raw/gzip sizes and hashes, and explain growth. A proposed review bound is **<=10 KiB
gzip additional total JS** for this slice; exceeding it requires review, never
removing signature validation to meet a size target.

## Current implementation: facts and precise gaps

These are **source-inspection findings**, not newly executed provider tests.
Existing browser tests are three boundary checks; they do not drive a real
`UserManager` authorization/callback round trip. Existing backend tests execute
real JOSE cryptography and SQLite, with published non-live keys and simulated JWKS.

| Gap | Exact current surface / consequence | Proposed bounded response |
| --- | --- | --- |
| G01 PKCE/nonce | `AuthApp.tsx` sets code flow and `disablePKCE:false`, but calls `signinRedirect()` without nonce. Pinned library emits/checks nonce only if supplied | Keep library-generated verifier/challenge/state; supply a fresh Web Crypto nonce on each explicit sign-in and assert S256/verifier binding end to end |
| G02 ID token | Pinned `ResponseValidator._validateIdTokenAttributes` decodes the JWT and checks subject/optional nonce; it does not perform initial signature/issuer/audience/expiry validation. `addUserLoaded` publishes the User before the callback promise resolves | Verify with existing JOSE against vetted metadata/JWKS before publishing any authenticated session, cart namespace or API token provider. No direct UI publication from raw library events |
| G03 metadata/config | `parseAuthConfig` checks HTTPS/openid but not actual page-origin equality, bounded client/scope values, offline scope, discovery issuer/endpoints or supported PKCE/response modes. CSP restricts connections but is not semantic metadata validation | Bind origin/client/issuer and review one identity origin; preflight metadata and pass the validated object to the manager before navigation/exchange |
| G04 callback | Only path is checked; duplicate/ambiguous parameters, fragments, unsolicited/expired transactions and effect re-entry are not explicitly guarded/tested. URL is cleaned only after asynchronous callback success/failure; config-fetch failure bypasses that cleanup | Snapshot then scrub callback URL at startup, validate one query code-or-error/state transaction, process once, suppress stale completions and clean up on every exit |
| G05 transaction lifetime | sessionStorage holds library state; app sets no state prefix/age or identity request timeout. Library cleans stale records on new requests, but the callback path does not itself enforce transaction age | App-owned namespace, one pending transaction, explicit deadline and cleanup; bound identity network operations; unavailable storage fails closed |
| G06 token lifecycle | `SignedIn` closes over its initial User; UI checks expiry but a same-subject replacement need not remount. Backend's one-hour token age can reject before browser expiry | Read current controller session per request; expire on timer and access/resume; any API 401 invalidates that session and offers explicit reauthentication without replaying a write |
| G07 logout/races | `removeUser()` clears local memory/events, but does not cancel pending callback or in-flight API work. Already dispatched requests retain a valid bearer | Invalidate a session generation, abort owned requests, clear owned pending state/timers and ignore late results. Do not claim server rollback or bearer revocation |
| G08 cart namespace | `userStorageKey` persistently exposes encoded ID-token issuer/subject and omits client ID. App API owner is independently derived from the verified access-token subject | Use a versioned hashed issuer/client/ID-sub namespace; preserve references only through an API-authorized legacy migration. Never derive API authority from browser storage or claim anonymous carts |
| G09 protected requests | `api.ts` constructs relative API paths and adds bearer, but has no session-401 callback, generation guard or explicit redirect/cookie policy; mutations lack a session abort signal | Restrict OIDC requests to same-origin `/api/`, reject redirects, omit cookies and compose session/request deadlines; retain anonymous behavior and HTTP APIs |
| G10 exact denials | Eight backend invalid-claim variants assert only an arbitrary numeric status; one-hour-versus-later-browser-expiry, valid-cache outage and specific browser rejection paths are not proved | Assert exact 401/403/503 and safe codes; drive recovery and controlled JWKS/cache cases without weakening server claims/time limits |
| G11 capture | Default Playwright retains failure traces; no credential-safe provider profile/canary guard exists | Separate OIDC capture-off profile, sanitized reporters/logging and deliberate published-vector canaries, preserving anonymous trace coverage |
| G12 browser notices | `scripts/licenses.mjs` includes the OIDC client/decoder browser notices but currently treats JOSE as API-only | Add JOSE to the browser notice generator when its exports enter the frontend; retain its full MIT notice without adding/upgrading a package |

Pinned primary source corroboration:
[ResponseValidator](https://github.com/authts/oidc-client-ts/blob/v3.5.0/src/ResponseValidator.ts),
[OidcClient](https://github.com/authts/oidc-client-ts/blob/v3.5.0/src/OidcClient.ts),
[SigninRequest](https://github.com/authts/oidc-client-ts/blob/v3.5.0/src/SigninRequest.ts).
OIDC Core permits reliance on authenticated token-endpoint TLS in specified code-flow
circumstances; lack of client-side signature checking alone is not a demonstrated
exploit. Missing issuer/audience/time checks and premature session publication still
require explicit controls. This plan selects stricter browser signature verification
through JOSE; the API remains the authority for access-token authorization.

## Proposed session and protocol behavior

The following is a proposed application policy requiring the later bounded C3
implementation request. It is not a description of controls already implemented.
Use public library APIs; no subclassing private validators, fetch monkey-patching,
hand-written PKCE/JWT implementation, new identity server or production test switch.

1. **Bootstrap and trusted metadata.** On exactly `/auth/callback`, capture the full
   URL only in memory and immediately `replaceState` to that bare path before config
   fetch. No protected shop mounts until config and callback checks pass. Require
   `location.origin === publicOrigin`, exact HTTPS issuer with no credentials/query/
   fragment and a bounded public client ID/scope. Reject `offline_access`, implicit/
   hybrid flows and caller-supplied issuer/return URL. For Entra, only the separately
   selected tenant-specific issuer is eligible; `common`/`organizations` are not.
   Fetch discovery only from the configured issuer's well-known URL with a five-second
   bound, omitted credentials and rejected redirects. Require exact metadata issuer,
   code/query and S256 support; optional capability fields may be absent where the
   standard allows, but advertised plain-only/unsupported flows fail. Always use a
   public-client token request without a secret. A discovery token-authentication
   method list alone does not prove or disprove an individual SPA registration;
   C6 must verify that registration and successful public exchange. Never supply
   credentials as a fallback. Require authorization/token/JWKS endpoints on the single approved
   HTTPS identity origin, without credentials/fragments; no URL selected from token
   headers, query, callback or unreviewed metadata. Pin the validated metadata object
   for the transaction. A provider needing another origin stops for review; no CSP
   expansion. Browser CSP remains required for library transport, including denial
   of redirects to unapproved origins; do not claim a library-wide redirect-rejection
   setting that it does not expose.

2. **Begin one explicit redirect.** A disabled busy button/controller guard permits
   one pending attempt per tab. Generate an independent nonce with Web Crypto,
   supply it through the supported `nonce` argument, and let the library generate
   high-entropy state/verifier/S256. Store only a short-lived pending descriptor
   (nonce, creation/deadline, configuration binding and local attempt ID) alongside
   the library record in an app/issuer/client-specific sessionStorage namespace.
   No credential/token or arbitrary return path enters this descriptor. Set a
   **300-second transaction age** and clear expired records before callback use,
   not just when starting another sign-in. Failed/cancelled navigation removes
   owned pending records; denied storage produces a safe error, no persistence
   fallback. Human/provider interaction time is bounded by the transaction age.

3. **Consume callback once.** Require the exact configured origin/path, query mode,
   one nonempty state, exactly one code or OAuth error, and no duplicate security
   parameters or fragment token/code. Reject malformed/unsolicited/expired responses
   before exchange; never display raw provider `error_description`. A controller
   single-flight promise survives React effect re-entry; remount/StrictMode tests
   must prove only one exchange. Call actual `signinRedirectCallback(capturedUrl)`;
   the library binds and consumes stored state. Never retry the same code after
   error/timeout. Check generation after each await; sign-out invalidates any pending
   completion. Success, denial, bad metadata, missing config/storage and exceptions
   all leave a clean `/` URL and no owned PKCE/state/nonce residue. Refresh halfway
   through a scrubbed callback safely requires a fresh sign-in; do not reconstruct
   codes from storage/history. Tests cover copied/cross-context state and replay;
   sessionStorage is not an absolute defence against opener copying or same-origin
   XSS. Provider one-use code enforcement is also required in C6.

4. **Verify before session publication.** Use `jose.jwtVerify`/trusted remote JWKS
   with **RS256**, exact issuer, SPA client audience, required nonempty bounded sub,
   exp/iat and expected nonce; validate finite times, expiry/nbf and future iat with
   **five-second skew**. Check `azp` when present, and require it to identify this
   client for multiple audiences; reject untrusted additional audiences under this
   single-client profile. Require nonce equality to the app pending descriptor as
   well as library checking. JWKS URI comes only from vetted metadata, never JWT
   `jku`/`x5u`; one-second JWKS timeout, bounded five-minute cache/30-second unknown-key
   cooldown, no unbounded retries or trust fallback. Reject malformed/missing ID or
   access tokens, non-Bearer token type, invalid/nonpositive/nonfinite lifetime and
   unexpected refresh token. Disable UserInfo, iframe session monitoring, silent
   renewal and token revocation calls. Do not set the UI user from `userLoaded`;
   the manager can store/emit an unaccepted User during callback. Quarantine it,
   publish only the verified session, and remove it on any further failure. Validation
   failure must produce zero protected API requests and zero persisted tokens.

5. **Memory and expiry.** ID/access tokens and claims remain in a fresh per-tab
   in-memory User store. No local/sessionStorage token cache, cookies, IndexedDB,
   service worker, refresh token, storage-state export or token-bearing broadcast.
   Clear references/timers on sign-out; do not promise JavaScript heap zeroization.
   Effective client expiry is the earlier of validated ID expiry and the finite
   access-token response expiry. Check current session/time for every API request
   and after visibility resume, as timers can be throttled. A page reload loses
   tokens and shows Sign in; remembered cart references do not restore authority.
   The API's one-hour age cap remains unchanged and is independent of browser
   lifetime. On 401, invalidate the active session and show a user-initiated Sign in
   action; do not auto-redirect in a loop, refresh silently or replay a mutation.
   403 is insufficient permission, not a refresh opportunity. 503 is a safe transient
   dependency error, with no anonymous fallback or automatic identity reset.

6. **API and account isolation.** The OIDC client obtains the current verified
   session's access token at dispatch, never an ID token or a stale captured User.
   Only same-origin `/api/` paths receive it; encode cart identifiers, reject HTTP
   redirects and omit cookies. Compose the existing six-second request deadline
   with caller and session AbortSignals. Each completion is tied to its generation;
   old-account responses cannot update the new account UI or storage. Already
   accepted server writes may finish after abort/logout; make no revocation/undo
   claim and require fresh authoritative reads after reauthentication. API owner
   remains SHA-256 of the exact verified access-token issuer/sub; do not decode the
   access token in the SPA to assign ownership or assume ID/access subjects match.

7. **Cart references and local sign-out.** Hash `[issuer, clientId, verified ID sub]`
   into a versioned browser storage key; only its cart UUID is persisted, no raw
   subject/claims/cart contents. Hashing is pseudonymization, not a secrecy guarantee.
   For the current verified user only, a legacy OIDC reference can migrate after a
   real authenticated cart GET: 200 copies the UUID to the new key and removes the
   legacy key; 404 drops the stale reference; 401 follows session invalidation; 503
   offers retry without creating/reassigning a cart. Never import the anonymous
   reference or enumerate/delete unrelated storage. Local sign-out clears visible
   basket/session, pending transaction, timers and owned requests, preserving only
   the scoped UUID reference for the same user's later authorized lookup. It is
   **this-tab application sign-out**, not provider logout, global tab logout,
   revocation or prevention of SSO at the next explicit login. Tabs never exchange
   tokens or choose an active account for one another. Provider/RP logout endpoints
   and registered post-logout redirects are deferred to a separate C6 decision.

Identity metadata/token requests get a five-second per-request bound; JWKS gets
one second; callback processing after arrival gets a **15-second aggregate bound**.
Timeout invalidates the generation, consumes/discards owned state and suppresses
late acceptance; an underlying library request must remain bounded even when it
cannot be cancelled immediately. No retries. Test clocks may allow up to 250ms
scheduler tolerance in wall-clock assertions, reported separately. These proposed
bounds do not change backend JWKS/HTTP/readiness timeouts or bypass failures.

Protocol bases: [OIDC Core §3.1.3.7](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation),
[PKCE RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636#section-4.6) and
[OAuth Security BCP RFC 9700](https://datatracker.ietf.org/doc/html/rfc9700#section-4.1).
The policy above is deliberately narrower than all options those standards permit.

## Deterministic local provider fixtures and negative matrix

Use a **test-only protocol responder**, not an installed IdP/realm/account. No new
signing credential or certificate is needed. Reuse the retained
[RFC 7515 vector and notice](../../apps/octocat-supply/api/fixtures/README.md),
loading its private component only in Node test fixtures. Never bundle it into
frontend assets or register it anywhere. JWKS responses contain only the public
component. Use the existing JOSE implementation to create synthetic ID and API
tokens; different audiences and deliberately different ID/access subjects prove
that browser profile identity cannot authorize the API.

The responder provides discovery, authorization, token and JWKS behavior for fixed
`.example.test` HTTPS URLs, with two synthetic actors and an isolated per-test
authorization-code ledger. Authorization binds client/redirect/S256 challenge/
nonce; redemption checks the exact client, redirect and verifier against the saved
challenge and rejects reuse. Runtime cryptographic state/nonce/verifier remain
random; determinism means controlled responses, owned data, injected time, no live
network and stable expected outcomes, not weakening randomness. Use fake time for
claim boundaries and fixed published keys; do not log protocol values for debugging.

Vitest must execute actual `UserManager` with only its public redirect navigator
substituted and fetch routed to the responder. Do not mock the manager, callback
method, signature verifier, state comparison or protected API authentication into
success. Chromium must execute the built app/actual library across full-page
authorization/callback navigation using test-owned routes for approved virtual
HTTPS app/issuer URLs. Abort all other destinations, including real Entra. A
Node-only loopback bridge relays `/api/` requests unchanged to the real Express API,
real JOSE authenticator and owned migrated/seeded SQLite fixture; never substitute
`authenticate: () => owner`. Fixture HTTPS routing simulates transport and provider
responses: it does **not** prove a real TLS handshake, provider CORS/registration or
an Entra session. Existing production proxy TLS tests remain separate and unchanged.

Every row below is **Planned / not executed**. Expected status is asserted where
HTTP applies; other rows assert a closed client state, no unintended request and
cleanup rather than inventing an HTTP response.

| ID | Acceptance test / negative variants | Required observable result |
| --- | --- | --- |
| P01 | Successful actual-library navigation, captured authorization and code exchange | code/query/public client, unique state/nonce, RFC-length verifier, S256 matches; no secret/offline/refresh grant; one exchange; exact clean callback and no transient leftovers |
| P02 | Missing/malformed/wrong-origin config; metadata issuer mismatch; missing token/JWKS endpoint; insecure/foreign endpoint; advertised plain-only PKCE/unsupported flow | Closed shop; no navigation/token POST or bearer to unapproved origin; safe retry text |
| P03 | Missing/wrong/duplicate state, duplicate code/error, code+error, fragment tokens, unsolicited callback, transaction >300s, disabled/corrupt storage | No accepted session/protected API call; no retry of code; URL and owned storage cleaned, including config-fetch failure |
| P04 | Correct callback then replay; two callback invocations/remount/StrictMode; swapped callbacks between independent tabs/contexts; redemption with wrong verifier/client/redirect | At most one exchange/session; fixture rejects invalid/reused code; denied attempt never switches another user |
| P05 | Provider access_denied/login_required; invalid_grant; malformed JSON; missing/empty tokens; wrong token type/lifetime; unexpected refresh token; discovery/token timeout | Safe closed state and cleanup; no raw upstream text, fallback or automatic reauthentication loop |
| P06 | ID token bad signature/alg/unknown key, wrong/missing issuer/audience/sub/nonce, bad azp, extra audience, expired/future times; malicious jku/x5u | JOSE denies before protected UI/API publication; only trusted JWKS consulted; `userLoaded` cannot bypass validation |
| P07 | Access token missing/tampered/unsigned/expired/future-nbf/over-age/wrong issuer/audience; ID token sent to API; forged principal/owner fields | Exact safe 401 for authentication failures, 400 for forbidden owner body shape; no cart data/anonymous authority |
| P08 | Valid signature but missing/wrong role or delegated scope; Entra scp variant | Exact 403 for authorization failure; correct role+scope succeeds; no logout/refresh loop to bypass permissions |
| P09 | JWKS unavailable cold/unknown key; cached still-valid known key; expired key cache, timeout; unknown kid with healthy JWKS | Actual unresolved-key network dependency: safe 503; healthy JWKS without matching kid: 401; valid cached key may succeed within policy. Invalid cryptographic tokens still denied. Readiness remains DB-only |
| P10 | Browser expiry; API 401 at age >3600+skew with browser expiry still later; tab resume; same-subject session replacement | Block further old-token calls; explicit usable reauthentication; new token used after login; no automatic replay of a failed cart mutation |
| P11 | Alice/Bob and deliberately different ID/API subjects; legacy/anonymous/cart namespace; all cross-owner read/set/remove/delete calls | Two independent baskets; exact cross-owner/missing 404; API remains authority; only successful authorized legacy lookup migrates a reference |
| P12 | Logout/unmount during callback or API work; delayed old-user response after next login; independent signed-in tabs; reload/blocked cart storage | No late session/data restoration or cross-user UI write; no token persistence/broadcast; tab-local logout/reload behavior honest and usable |
| P13 | External API path/redirect, credentials/owner injection, request abort/deadline | Bearer only at approved same-origin API; no cookies, token in URL/body or unintended retry; new session cannot reuse old client's bearer |
| P14 | Canary code/verifier/state/nonce/token/claims/private-vector content through error/log/reporter/artifact paths | Captures off, no raw canaries in retained outputs or built assets; sanitized failure diagnostics retain case ID/category/status only |
| P15 | Entire unchanged baseline and release/security checks | Original 97 tests, three anonymous and three container browser journeys, C1 contracts, proxy and scanners pass; new contracts are mandatory and never skipped for missing setup |

At least five additional Chromium journeys must cover happy code+PKCE/cart pricing,
denial/replay, two actors, over-age 401/reauthentication, and logout/reload/races.
Detailed variants belong in fast actual-library/JOSE/component tests; count cases
only from executed results, never report table rows as passed tests. Add meaningful
negative controls: nonce omission/ID-verification bypass/early session publication,
external bearer target and capture-enabled mutations must each fail their relevant
assertion. Use controlled test configuration or an isolated mutation copy; do not
weaken production code or mutate the owner's worktree to demonstrate sensitivity.

## Exact proposed implementation surface and order

All paths below are **future work only**, relative to `apps/octocat-supply/` unless
explicitly repository-rooted. No placeholder implementation is added by this plan.

| Order | Exact files | Purpose / exit condition |
| --- | --- | --- |
| 1 — pin current evidence and responder | New `test/fixtures/oidc-provider.ts`, `test/fixtures/oidc-provider.test.ts`; existing `vitest.config.ts` / `tsconfig.tests.json` | Node-only ledger/discovery/token/JWKS/published-vector fixtures; add an explicit fixture test project/include and type inclusion, so no test is silently undiscovered. Negative verifier/code/redirect cases pass; no network/credential creation |
| 2 — exercise actual engine and verifier | New `frontend/test/OidcProtocol.test.tsx`, `frontend/test/IdToken.test.tsx`; new `frontend/src/idToken.ts`; existing `frontend/test/setup.ts` | Tests drive public navigator/real manager and JOSE; reproduce G01–G05/G10, then implement bounded ID verification. Reset owned sessionStorage, mocks, clocks and pending timers between tests; no private library patch or mock success |
| 3 — bound session lifecycle | New `frontend/src/oidcSession.ts`, `frontend/test/OidcSession.test.tsx`; existing `frontend/src/AuthApp.tsx`, `frontend/src/main.tsx`, `frontend/test/AuthApp.test.tsx` | Controller/metadata/pending descriptor, nonce, capture-and-clean bootstrap, single-flight callback, verification-before-publish, generation/expiry/logout, hashed reference migration. Preserve existing three boundary tests and anonymous rendering |
| 4 — bind protected API calls | Existing `frontend/src/api.ts`; new `frontend/test/ApiSession.test.tsx`; existing `api/test/auth.test.ts` | Optional OIDC session hooks/abort/401 handling with existing anonymous defaults; exact API status/claim/JWKS tests. `api/src/auth.ts`, app routes, repository/SQL and business components remain unchanged |
| 5 — browser and capture controls | New `e2e/oidc/auth.spec.ts`, `e2e/oidc/fixtures.ts`, `scripts/oidc-e2e-server.mjs`, `playwright.oidc.config.ts`, `scripts/verify-auth-capture.mjs`; existing `playwright.config.ts`, `package.json` scripts only | Test-owned bridge/SQLite lifetime, five browser journeys, separate capture-off profile and canary verifier. Explicitly exclude OIDC directory from anonymous config and run it via its own mandatory command, retaining original three tests/traces |
| 6 — mandatory CI and policy | Repository-root `.github/workflows/ci.yml`, `scripts/delivery/policy.py`, `tests/delivery/test_security.py` | Add `npm run test:e2e:oidc` plus capture guard to existing application job; enforce presence/no bypass with policy mutations. Keep pinned Playwright image, timeouts, container/proxy/scanner jobs, permissions and required gate behavior unchanged |
| 7 — licence/evidence freeze | Existing `scripts/licenses.mjs`, `frontend/public/third-party-notices.txt`; repository-root `docs/evidence/m4c-c3-oidc.md`, `docs/evidence/m4c-c3-oidc.json`, this plan, `docs/milestones/m4c-scope.md`, `docs/capability-status.md`, `docs/decisions/0007-application-identity.md`, `docs/threat-model.md`, `docs/delivery.md` | Add JOSE to the explicit browser-notice list and regenerate full text; `dependencies.json` and the lock must remain unchanged. Review case results, versions/hashes, clean bundle delta, capture controls, failures and C6 blockers; label only actual local execution Locally tested / Simulated |

The shared `test/fixtures/oidc-provider.test.ts` needs explicit Node discovery because
current Vitest includes only `api/test/**/*.test.ts` and `frontend/test/**/*.test.tsx`.
Include the new fixture tree and `playwright.oidc.config.ts` explicitly in test
typechecking; none is covered merely by adding a file with a familiar suffix.
Bridge helpers import fixture code through existing `tsx` where TypeScript is needed;
use the current toolchain, no additional test runner/mock server dependency. Never
import test/private-vector modules through a production frontend entry. Exact proposed
npm scripts are `test:e2e:oidc` (the separate config) and `test:auth-capture` (guard and
canary validation). CI must run both without `continue-on-error`, optional env skips
or increased job timeout. If the added bound cannot fit the current job, stop with
timings and request a separate workflow decision rather than weakening coverage.

Do not change `App.tsx`, business/pricing behavior, SQL adapter/migrations, Bicep,
production proxy startup/TLS/CSP or package versions under this boundary. A proven
defect needing any additional production surface or library migration stops for
a new bounded review. Browser nonce/ID-token validation, stricter config/expiry,
401 UX and namespace migration are proposed security behavior changes explicitly
listed here for the owner's later implementation scope; the existing C3 outline
does not itself authorize them.

## Acceptance, evidence and safe C6 handoff

**C3-A1** is met only when P01–P06/P10–P13 execute the actual pinned library plus
the verified-session gate, with exact redirect/exchange counts, negative cases,
storage cleanup and two synthetic owners. **C3-A2** requires P07–P10 exact statuses,
unchanged API issuer/audience/role/scope/age policy, cached-key nuance and usable
over-age reauthentication. **C3-A3** requires P14 capture canaries and a separately
configured capture-off profile that refuses unsafe artifact/log settings. **P15**
is mandatory regression/security acceptance. Until then all C3 implementation
criteria remain **Planned**, even though the planning deliverable is complete.

Future commands: format/lint/typecheck, `npm test`, `npm run build`, licences and
unchanged-file check, high-severity npm audit, original `npm run test:e2e`, new
`npm run test:e2e:oidc` and `npm run test:auth-capture`; repository/whitespace checks,
actionlint, offline Bicep, all delivery/security tests, container/proxy checks,
configuration/image scans and secret scans. Preserve C1's 27 shared/six SQLite
tests and the eight explicitly **Simulated** SQL recording tests. No quarantined,
skipped, expected-failure or optional-configuration success may satisfy C3.

Evidence must bind reviewed SHA/diff, package lock, Node/library/browser/tool versions,
fixture/vector/notice/schema/config hashes, case IDs/expected/actual outcomes,
request/exchange counts, timing limits, exact API statuses and clean-build bundle
sizes. Store sanitized case/status/category records, not raw protocol packets,
tokens, callback URLs, subjects, storage dumps or fixture private material in test
reports. Keep raw local tooling output ignored and access scoped; secret scanning
does not by itself prove absence of codes/state/PII. Fail a capture guard before
running any real-provider profile. Disable trace/video/screenshots/HAR/storage-state,
verbose library logs and Playwright protocol debugging for OIDC. Do not change the
anonymous profile's retained failure traces. Diagnostic exceptions must never print
the original OAuth error, URL, token response or request headers.

Completed C3 would be **Locally tested client/crypto behavior with Simulated provider
responses**, not Entra-verified integration. C6 needs a new authorization binding
tenant, public SPA/API registrations, exact HTTPS callback/CORS, API token version/
issuer/audience/delegated scope/role, two approved users, bounded sign-in attempts,
capture controls and cleanup. Revalidate the single-origin metadata/JWKS/RS256
profile against that provider; mismatch is a blocker, not permission to widen trust.
No client secret, refresh grant, offline access, copied token or password automation.
Real C6 must prove code/PKCE/state/nonce/code replay, actual token/claim semantics,
API ID-token rejection, both owners' cart denials, expiry/401/reauthentication and
provider/JWKS failure behavior using already authorized principals. Distinct ID/API
subjects must be handled honestly; real foreign-tenant denial needs an approved
foreign identity, not merely a tampered fixture. Do not induce provider outages/key
rotation without specific scope. Natural observations and simulated faults retain
their separate labels. Provider-wide logout remains a separately selected feature.

## Blockers, governance and costs

- The next step is a **new C3 implementation-only request** adopting this bounded
  surface/security policy. Recommended first sub-boundary: actual-library responder
  and negative tests, then the listed minimal fixes; no real provider or SQL target.
- No local external account or paid service is intrinsically needed. Existing Node/
  Chromium/Web Crypto and published vector suffice. Fixture support for secure-context
  routing and the full capture guard must be proved during implementation. Do not
  add insecure browser flags, self-signed trust bypasses or a test auth route to fix it.
- Zero dependency upgrades/installs are proposed. Any needed upstream fix/new library
  needs exact release/provenance/licence/audit/notice and bundle review first. Actual
  new bundle cost and added CI runtime remain unmeasured; the standalone probe is an
  estimate of selected exports, not their final application impact.
- Current hosted success preserves the CodeQL **skipped** coverage gap. Prior private
  repository/branch/ruleset/environment observations remain dated assessment facts;
  settings/entitlements were not reread or changed. C5 SAST/governance review and an
  independent release reviewer remain necessary. No waiver, billing, visibility,
  entitlement or automated publishing change follows from a library recommendation.
- Local compute/storage and extra hosted CI minutes are potential C3 costs; no new
  Azure/provider consumption or paid library is selected. C6 user/admin/consent or
  premium identity requirements depend on actual approved entitlements; no price or
  free-tier availability is assumed. Azure resources/costs remain a later boundary.
- C2 engine, C4 infrastructure/diagnostics, C5 governance and C6 real provider proofs
  remain open. M4A deployment is NO-GO. C3 planning neither completes those gates
  nor authorizes credentials, cloud sign-in, provisioning, deployment, commit or push.

## Planning-only verification

This task inspected sources/installed manifests, fetched primary public references
and hosted job metadata/application logs, and ran the standalone bundle probe in a
temporary directory. No application/protocol suite, browser/provider rehearsal,
image build/scan or cloud command was run for this documentation-only task.
Repository/JSON/whitespace checks, working-tree secret scan and preservation hashes
are recorded in the planning JSON. Source files, dependencies, lock, tests, workflows,
IaC and delivery/security implementations remain byte-identical to the initial
snapshot. Stop at this plan; implementation acceptance remains unearned.
