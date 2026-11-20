# Frontend image: nginx 1.30.7 security remediation (CI run 44635482434)

Date: 2026-11-20 UTC. Baseline: `73db9b4` (`origin/main`).
Machine-readable record: [JSON](m4c-frontend-nginx-1.30.7-remediation.json).

Owner-approved remediation of the mandatory CI `containers` failure in run
**44635482434**.

* **No waivers:** no threshold change, no ignore entry, no `--ignore-unfixed`;
  `security/exceptions.json` stays `[]`.
* **Scope:** no unrelated dependency changed.
* **Not done:** no Semgrep, dispatch, commit, push, release or redistribution.
* **Unaffected:** R2(a) P2 is not started. C5 gates are unaffected.

## Cause (from the read-only investigation)

* **New vulnerability intelligence, not a repository change.** The image
  inventory was identical to the last green run (44434808986): same pinned
  base `nginxinc/nginx-unprivileged:stable-alpine@sha256:f5116ed4…`, nginx
  `1.30.6-r1`. Six nginx CVEs published on 2026-11-18 made the `trivy image`
  HIGH/CRITICAL gate fail.
* **The findings:**
  * CRITICAL: CVE-2026-113425, CVE-2026-121810, CVE-2026-123007,
    CVE-2026-123633;
  * HIGH: CVE-2026-118899, CVE-2026-123634;
  * all fixed in nginx `1.30.7`.
* **Not caused by `73db9b4`** (R2(a) P1), which changed no image, application
  or CI file.
* **Why the base wasn't simply bumped:** `nginx-unprivileged` had not yet
  published a 1.30.7 image (its `stable-alpine` tag still equals the pinned
  digest). nginx.org's signed Alpine 3.24 repository already serves 1.30.7.

## Change

`apps/octocat-supply/frontend/Dockerfile` (+7 lines, 0 removed). In the
existing `USER root` section of the runtime stage, a second exact-version
`apk add` follows the existing pinned-patch line:

```
RUN apk add --no-cache --repository https://nginx.org/packages/alpine/v3.24/main \
    nginx=1.30.7-r1 nginx-module-geoip=1.30.7-r1 nginx-module-image-filter=1.30.7-r1 \
    nginx-module-njs=1.30.7.1.0.2-r1 nginx-module-xslt=1.30.7-r1
```

**Unchanged:**

* the base digest and build stage;
* `USER 101`, `EXPOSE 8080`, the entrypoint, the copied files and the nginx
  configuration;
* the existing Alpine patch pins.

The nginx.org repository is passed **for this one command only**; it is not
persisted in `/etc/apk/repositories`.

## Package source and signature trust

| Check | Result |
| --- | --- |
| Signing key | The base image's `/etc/apk/keys/nginx_signing.rsa.pub` is **byte-identical** to `https://nginx.org/keys/nginx_signing.rsa.pub` (SHA-256 `ff7cf138acc09f2a5029300ab713fe6a1440605fca72e2bab76a4da9206fec87`) |
| Repository index | `apk update` with the nginx.org repository accepted "NGINX/OSS stable" on x86_64 and aarch64 with no untrusted-signature warning. `1.30.7-r1` is listed |
| Package signatures | `apk verify` reports **OK** for all five 1.30.7 packages on **both** x86_64 and aarch64 (base apk-tools 3.0.8) |
| Negative control (key removed) | `apk verify` gives **UNTRUSTED signature** (exit 5). The real `apk add` refuses: index "UNTRUSTED signature", "unable to select packages" (exit 5). The build cannot fall back to an unverified source |

**Package hashes (SHA-256):**

| Package | x86_64 | aarch64 |
| --- | --- | --- |
| `nginx-1.30.7-r1` | `1113c374…0e7b` | `7119131b…46a6` |
| `nginx-module-geoip-1.30.7-r1` | `231e993f…8ec8` | `2c1467f4…7dab` |
| `nginx-module-image-filter-1.30.7-r1` | `692b15af…960a` | `ec6ac9c7…6c81` |
| `nginx-module-njs-1.30.7.1.0.2-r1` | `b10ab852…a6ec` | `f33eef3a…1ffd` |
| `nginx-module-xslt-1.30.7-r1` | `1f97d4ff…4928` | `003dad0f…e4e6` |

Full hashes are in the JSON record.

## Validation

All runs used a disposable copy of the working tree, with the CI-pinned tools
installed SHA-verified: Trivy 0.72.0, bicep 0.48.1, actionlint 1.7.12 and
gitleaks 8.30.1.

| Check | Result |
| --- | --- |
| `verify_containers.py` (CI `containers` step): build, migrate and seed, 12 fixtures and authoritative discount total through the proxy, non-root/read-only/`cap-drop ALL`, only loopback 8080 published, persistence across API replacement, **3/3 browser e2e** through the production images | **PASS** |
| `verify_proxy.py` (TLS proxy, including `nginx -T` of `/app/nginx.conf`) | **PASS** |
| `scan_images.py` (CI image gate; `--severity HIGH,CRITICAL --exit-code 1`) | **Exit 0**: frontend **0** and API **0** HIGH/CRITICAL |
| The six reported CVEs | **Absent.** A full-severity scan of the frontend shows **no nginx finding of any severity** |
| CI architecture (`linux/amd64` build of the frontend) | x86_64, uid 101, `nginx/1.30.7`, all five packages at 1.30.7. The Trivy HIGH/CRITICAL gate **exits 0** (0 findings) |
| `validate_infra.py`, then `scan_config.py` (CI policy order; Trivy Dockerfile rules) | Pass. Frontend and API Dockerfiles: **0** HIGH/CRITICAL misconfigurations |
| `provenance.py` (run against the repository's git metadata, read-only) | Pass |
| Built frontend image (arm64, `sha256:982b242a…`) | `nginx/1.30.7`; **all five** nginx packages at 1.30.7 together; uid 101; `EXPOSE 8080/tcp`; entrypoint `/bin/sh /app/start.sh`; module files identical to the pinned base (13 entries); apk repositories unchanged; nginx signing key present |
| Trivy vulnerability DB | v2, updated 2026-11-19T19:04:59Z |

**Evidence file hashes** (local scratch copies; the CI artifacts of the next
run are authoritative):

| File | SHA-256 prefix |
| --- | --- |
| `frontend-vulnerabilities.json` | `164659df` |
| `api-vulnerabilities.json` | `e4eb1a6d` |
| `frontend-sbom.cdx.json` | `c4549312` |
| `api-sbom.cdx.json` | `a11ce448` |
| `container-smoke.json` | `0b7e0c42` |
| `provenance.json` | `a1fb73bb` |
| `frontend-configuration.json` | `f5618ce2` |

## Residual risks

* **OpenSSL MEDIUM findings remain.** 10 MEDIUM OpenSSL findings stay in the
  frontend image: `libcrypto3`/`libssl3` `3.5.9-r0`, with CVE-2026-107496,
  -88822, -88823, -95691 and -95692 (fixed in `3.5.9-r1`). They come from the
  Alpine base, are below the unchanged HIGH/CRITICAL gate, and were not
  changed, as no unrelated dependency is touched. Track them separately.
* **Mixed package sources.** nginx now comes from nginx.org at 1.30.7, while
  the base image metadata still says 1.30.6. **Remove the five pins once the
  pinned `nginx-unprivileged` base digest itself ships nginx ≥ 1.30.7.**
* **Build-time network fetch.** The build depends on nginx.org availability at
  build time, and a mismatch fails the build closed. If nginx.org withdraws or
  supersedes `1.30.7-r1`, the build fails rather than silently changing.
* **Local architecture.** Local validation was on arm64, with an additional
  amd64 frontend build and scan. CI's amd64 run on push is the authoritative
  confirmation.
* **Exposure (context only; the gate is version-based):**
  * the frontend config uses `resolver` (relevant to CVE-2026-123634) and
    `try_files`/`alias` (nginx 1.30.7 also fixes CVE-2026-125283, not yet in
    Trivy's data);
  * HTTP/2, HTTP/3, TLS and mail are not enabled in the frontend.

## Bindings

* U1E adopted hashes and the C5 consistency check are unaffected (see the
  final verification in the JSON).
* The frontend Dockerfile's previous hash (`a08099f8…`) appears only in
  historical, point-in-time evidence (C3, C4, C5 readiness). No live gate
  binds it.

## Changed files

* **Modified:** `apps/octocat-supply/frontend/Dockerfile`.
* **New:** this document and its JSON record.
