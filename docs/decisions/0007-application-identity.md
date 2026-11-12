# ADR 0007 — Configured OIDC and separate cart owners

Date: 2026-10-31. Status: Implemented; cryptographic/API boundaries Locally tested.
External provider sign-in and Azure authorization are unverified. Requirements:
R06, R11, NF03; threats T01, T04–T06; validation V05/V08/V09.

C3 execution update, 2026-11-10: the [approved plan](../milestones/m4c-c3-oidc-plan.md)
is implemented and [locally tested](../evidence/m4c-c3-oidc.md) using Simulated provider
responses and real client/JOSE/API/SQLite execution. Browser sign-in now supplies
nonce, vets metadata and verifies RS256 ID-token signature/issuer/client audience/
times/subject/nonce before publishing a session. Raw library user events grant no
shop/API access. API claims/ownership policy is unchanged. No real provider claim.

Local verification refresh, 2026-11-12: P01–P14 pass against simulated providers.
The subsequent owner-authorized libxslt 1.1.43-r4 pin clears all three frontend
HIGH findings. Both rebuilt images pass the unchanged image gate; P15 and overall
C3 local acceptance are met. Authentication behavior remains locally
tested; no real provider or production credential is needed for these checks.

## Decision

Use `oidc-client-ts` 3.5.0 for browser Authorization Code + PKCE (S256), and `jose`
6.2.14 for browser ID-token and API access-token signature/JWKS/claim verification. Do not implement an identity
provider, password store or hand-written JWT verifier. Pin one HTTPS issuer,
audience and JWKS endpoint per deployment. A tenant-specific issuer supplies the
single-tenant boundary; never use Entra `common` or token-selected discovery.
Only RS256 access tokens are accepted. Require `sub`, `iat`, `exp`, validate
issuer/audience/nbf/expiry, allow five seconds clock skew and at most one-hour token
age. Require the configured role in top-level `roles` and delegated scope in
`scope` or Entra `scp`. Other provider claim layouts require an explicit adapter
decision; never infer roles from display names, headers or ID tokens.

API owner key is `oidc:` + SHA-256 of the JSON pair `[exact issuer, sub]`. This
binds stable issuer/subject without storing raw claims or a caller-selected owner.
Use that API access-token subject consistently; an ID-token subject used for browser
storage may be pairwise/different and never authorizes API access. All cart methods,
including cleanup deletion, require the owner and return 404 for absent/other-owned
carts. Owners cannot be supplied in bodies. JWKS requests have one-second timeout,
five-minute cache and 30-second refresh cooldown; trusted-key service errors fail
closed with safe 503, invalid tokens 401, insufficient scope/role 403.

Anonymous mode is an explicitly local, shared synthetic demonstration under
`anonymous:v1`, with no user isolation promise between anonymous visitors. It rejects
bearer identity at the API; local proxy strips Authorization. SQLite migration 3
assigns existing demo carts to that namespace without changing migrations 1–2.
There is no anonymous cart claiming/transfer at sign-in. `APP_ENV=cloud` requires
OIDC and SQL; SQL refuses anonymous owners. Never silently fall back on failed auth,
configuration, database connection or migration.

## Browser and proxy consequences

Tokens live in memory, not localStorage. SessionStorage holds transient PKCE/state/
nonce and a 300-second configuration-bound pending descriptor. Its namespace encodes
public deployment configuration, not identity claims. The real library consumes
state/code; JOSE verifies the ID token before controller publication. Identity
requests have 5s bounds, JWKS 1s and callback acceptance 15s. Callback URLs are
scrubbed before config fetch and cleaned on failure; duplicate/unsolicited/expired
callbacks fail closed. Refresh requires explicit sign-in. A protected API 401 clears
the current generation without replay; 403/503 remain distinct. Logout/unmount
cancel owned work and suppress stale responses; accepted server writes may still
finish. Sign-out is this-tab application-only, without provider logout/revocation.
Refresh/offline grants are rejected. Only cart UUID references persist under a
hashed `[verified ID issuer, client ID, ID subject]` namespace; legacy OIDC references
migrate only after a real authenticated API lookup. They never replace API
authorization. Browser configuration failure closes the shop, rather than entering
anonymous mode. Same-origin API requests use only the current access token, omit
cookies and reject redirects. Proxy access logging
is disabled and API logs omit tokens, queries and raw owner identifiers.

The production proxy has two explicit modes: Docker HTTP/anonymous and fixed
HTTPS/OIDC. HTTPS requires exact approved host, port 443, trusted CA verification,
SNI and a reviewed resolver. It forwards bearer Authorization, strips identity/
forwarding headers and sets fixed Host/protocol. API `trust proxy` is false;
forwarding never grants authority. CSP permits self and one configured HTTPS
identity connection origin; discovery/token endpoints must fit that reviewed origin.
Providers needing multiple connection origins are currently unsupported. No wildcard
script/connection policy or TLS bypass is provided.

## Alternatives and release limits

Easy Auth alone would still require a trustworthy ingress/header boundary and cart
ownership. Explicit JWT verification is portable and deterministically testable.
Cookie/BFF sessions would add session/CSRF/secret management beyond this baseline.
Bearer theft through XSS remains a residual risk; CSP, memory storage and short-lived
tokens reduce exposure without claiming immunity. Anonymous mode is loopback-only.
No rate limiter/distributed revocation or enterprise identity lifecycle is claimed.

The provider registration, exact claim semantics, API audience/scope/role assignment,
redirect URI/CORS, tenant restrictions, sign-out/session behavior and denied tokens
need a separately authorized real-provider rehearsal before release. No registration,
credential, sign-in or paid inference was created/executed here. See
[configuration and permissions](../delivery.md#m4b-local-configuration) and
[evidence](../evidence/m4b-local-preparation.md).

Primary protocol/library references: [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html),
[PKCE RFC 7636](https://www.rfc-editor.org/rfc/rfc7636),
[oidc-client-ts documentation](https://authts.github.io/oidc-client-ts/),
[jose](https://github.com/panva/jose).
