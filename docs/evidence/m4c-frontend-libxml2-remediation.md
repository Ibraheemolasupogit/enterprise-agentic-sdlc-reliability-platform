# Frontend libxml2 remediation for CVE-2026-86144

2026-11-22 UTC. Baseline `e735d70`. **GO for manual commit after owner review.**
The earlier signature uncertainty is resolved and the local gates passed.

## Cause and patch

The SHA-256-verified artifacts show that the frontend moved from zero gate
findings in run `44721643767` to one HIGH finding in run `44897096660`.
Alpine SecDB identifies `libxml2` `2.13.9-r2` as affected by
`CVE-2026-86144` and `2.13.9-r3` as the fix. The API had zero HIGH or
CRITICAL findings in both runs. Each image's package inventory matched across
runs, including the affected frontend package. The evidence points to new
vulnerability intelligence for an existing package. The artifacts do not
record the exact Trivy database revisions. P2 changed the separate hosted SAST
trial rather than the image inputs or the mandatory image gate.
[Passing artifact](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/44721643767/artifacts/14622277072)
· [Failing artifact](https://github.com/Ibraheemolasupogit/enterprise-agentic-sdlc-reliability-platform/actions/runs/44897096660/artifacts/14704637909)
· [Alpine SecDB](https://secdb.alpinelinux.org/v3.24/main.json)

The [frontend runtime Dockerfile](../../apps/octocat-supply/frontend/Dockerfile)
adds `libxml2=2.13.9-r3` to the existing exact-version `apk add` command.
The one-token change preserves the base digest, nginx `1.30.7` package set,
existing package pins, user `101`, port `8080`, and runtime configuration.
The [image gate](../../scripts/delivery/scan_images.py), [P1 and P2 trusted-input
controls](m4c-c5-r2a-p2-workflow-trust.md), and [U1E adopted bindings](m4c-c5-u1e-adoption-decision.md)
remain byte-identical to the baseline.

## Signed package provenance

The pinned base ran as `linux/amd64`. `uname -m` and `apk --print-arch`
reported `x86_64`, and the base reported Alpine `3.24.2` and APK `3.0.8-r0`.
APK accepted the official `v3.24/main` package and signed index offline using
the base's built-in `alpine-devel@lists.alpinelinux.org-6165ee59.rsa.pub`
key, whose SHA-256 was
`207e4696d3c05f7cb05966aee557307151f1f00217af4143c1bcaf33b8df733f`.
The `arm64` variant of the same pinned base lacks this key, which explains
the prior `UNTRUSTED signature` result for the x86_64 APK. The arm64 APK
passed against its own trust store. Both architectures were available for
verification. The amd64 build subsequently used the normal signed Alpine
repositories. [Official Alpine x86_64 repository](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/x86_64/)
· [Official Alpine aarch64 repository](https://dl-cdn.alpinelinux.org/alpine/v3.24/main/aarch64/)

| Verified input | SHA-256 |
| --- | --- |
| x86_64 `libxml2-2.13.9-r3.apk` | `8b37229c4761cf0eef5089045283526ef43bf335073050515010d34a313186ed` |
| x86_64 `APKINDEX.tar.gz` | `edaea06c2fc31b1a15bfd9c02274bd74b882a4410d6b157e08a5b260c9e8aba8` |
| aarch64 `libxml2-2.13.9-r3.apk` | `3e12146a2f15e27a22d70d21f8f52be29966105ce304c55bab2bfe75604981a9` |

```sh
BASE='nginxinc/nginx-unprivileged:stable-alpine@sha256:f5116ed4606f3eb015dd4a8e28cb9b351476dc0ad4bc6e9f93b19cec130cdf03'
mkdir -p "$SCRATCH/alpine-main/x86_64"
for file in APKINDEX.tar.gz libxml2-2.13.9-r3.apk; do
  curl --proto '=https' --fail --silent --show-error --location --max-time 45 \
    "https://dl-cdn.alpinelinux.org/alpine/v3.24/main/x86_64/$file" \
    -o "$SCRATCH/alpine-main/x86_64/$file"
done
docker pull --platform linux/amd64 "$BASE"
docker run --rm --platform linux/amd64 --network none --read-only --cap-drop ALL \
  --mount "type=bind,source=$SCRATCH/alpine-main,target=/alpine-main,readonly" \
  --entrypoint /bin/sh "$BASE" -ec '
    test "$(uname -m)" = x86_64
    test "$(apk --print-arch)" = x86_64
    sha256sum /etc/apk/keys/*.pub
    apk --no-network --repositories-file /dev/null verify \
      /alpine-main/x86_64/libxml2-2.13.9-r3.apk /alpine-main/x86_64/APKINDEX.tar.gz
    sha256sum /alpine-main/x86_64/*'
```

An initial local directory-repository `apk fetch` could not select an entry.
The direct `apk verify` command authenticated both files independently. The
authenticated index lists `libxml2` `2.13.9-r3` for `x86_64` and confirms that
it provides `libxml2.so.2=2.13.9`, which `libxslt` `1.1.43-r4` requires.

## Build, scans and regression checks

Both images built in an isolated checkout using
`DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose --progress plain -p morrow-supply-m3-verify -f apps/octocat-supply/compose.yaml -f security/compose.verify.yaml build`.
`docker image inspect` confirmed `linux/amd64` for both images and UID `101`,
`8080/tcp`, and `/bin/sh /app/start.sh` for the frontend. In the patched
frontend, the installed APK database showed the exact `libxml2`, `libxslt`
and five nginx pins. `ldd /usr/bin/xsltproc` resolved `libxml2.so.2`,
`xsltproc --version` reported matching compiled and runtime libxml2 `21309`,
and an offline `xsltproc /tmp/check.xsl /tmp/input.xml` returned `abi-ok`.

Trivy `0.72.0` used database v2, updated `2026-11-22T01:10:45Z`.
The local registry DNS lookup failed, so the database was retrieved over
HTTPS from Aqua's official GHCR repository. The OCI layer size and digest
`sha256:8331cc423db3352f93569bcf249f403f8df51cd8bbffe0a7a54d73c0a14dde6a`
matched its manifest. `NextUpdate` was `2026-11-23T01:10:45Z`. The local
cache was populated with that fresh database and `TRIVY_SKIP_DB_UPDATE=true`
was scoped to the scan to avoid repeating the failed registry lookup. The
gate command, severity threshold and finding handling were retained.

| Image | Failed CI before patch | Local amd64 after patch |
| --- | --- | --- |
| Frontend | 1 HIGH (`CVE-2026-86144`), 0 CRITICAL | 0 HIGH, 0 CRITICAL |
| API | 0 HIGH, 0 CRITICAL | 0 HIGH, 0 CRITICAL |

With `TRIVY_PLATFORM=linux/amd64` and `TRIVY_IMAGE_SRC=docker`,
`python3 scripts/delivery/scan_images.py` passed. An independent frontend
scan using `trivy image --quiet --skip-version-check --scanners vuln --timeout 15m --format json --output "$SCRATCH/frontend-all-severities.json" morrow-supply-web:m3-verify`
confirmed `CVE-2026-86144` was absent at every severity.
`python3 scripts/delivery/provenance.py` bound both reports and SBOMs to
the scanned images.

| Local command | Outcome |
| --- | --- |
| `DOCKER_DEFAULT_PLATFORM=linux/amd64 python3 scripts/delivery/verify_containers.py` | PASS. Migration, seed, readiness, 12 fixtures, cart totals and persistence, non-root/read-only/cap-drop, loopback exposure and 3/3 browser E2E through the production images. |
| `DOCKER_DEFAULT_PLATFORM=linux/amd64 python3 scripts/delivery/verify_proxy.py` | PASS. TLS peer validation, wrong-host refusal, header handling, and seven unsafe configuration rejections. |
| `npm run build && npm run test:auth-capture && npm run test:e2e:oidc && npm run test:auth-capture` | PASS with Node `24.22.2`, npm `11.19.1`, and Playwright `1.64.1`. Seven simulated-provider browser cases and both capture checks passed. The first capture check, run before generating host build assets, had exited nonzero. |
| `python3 scripts/delivery/validate_infra.py && python3 scripts/delivery/scan_config.py` | PASS. Eight Bicep templates and their output bindings checked. Trivy reported zero HIGH/CRITICAL configuration findings on both Dockerfiles and evaluated the ARM targets it supports. |
| `actionlint -shellcheck=""` and `python3 -m unittest discover -s tests/delivery -v` | PASS. Workflow lint and 22/22 delivery-policy tests. |
| `gitleaks git --redact --exit-code 1 --log-opts=--all .` and `gitleaks dir --redact --exit-code 1 .` | PASS. No findings in Git history or the worktree. |
| `git fsck --full`, `python3 scripts/check_repository.py`, `git diff --check`, and `git diff --no-index --check -- /dev/null docs/evidence/m4c-frontend-libxml2-remediation.md` | PASS. Git objects, repository text and links, tracked and untracked whitespace. |
| `python3 scripts/sast/check_trial_workflow.py` and `python3 -m unittest discover -s tests/security/sast -p test_trial_workflow.py` and `python3 -m unittest discover -s tests/security/sast -p test_trusted_input.py` | PASS. Static workflow policy, 27/27 P2 workflow tests and 16/16 P1 runtime trust tests. |

## U1 consistency and adopted hashes

The original `u1_consistency.py` was recovered from the project transcript.
Its SHA-256 matched the historical U1C record,
`5670fb170d05333c5599946ac094a94390b24f738107a51bd7e65ccaad4883ba`.
The scratch inputs were reconstructed from hash-matched generator scripts,
official wheels and RPMs, and the committed U1B metadata. The tree-sitter
rebuild in the recorded AlmaLinux image matched the historical binary hash.
`python3 -I "$CHECKER" "$SCRATCH/u1-reconstruction"` returned
`{"checks": 237, "failures": []}`. Static rehashing also confirmed all 14
U1E entries, including both wheels and both core binaries, and all 14 P2
trial and review bindings. Semgrep was never installed or executed in this
verification. [U1C checker hash record](m4c-c5-u1c-lt-u1-execution.json)

## Owner review

The exact revision depends on continued availability in Alpine `v3.24/main`.
The all-severity frontend scan still reported six MEDIUM and four LOW
OpenSSL package findings across `libcrypto3` and `libssl3`. These remain
below the existing gate. Vulnerability intelligence can change between the
local scans and the next hosted run. **GO for manual commit after owner
review.** Hosted mandatory CI on the resulting commit and any release or
redistribution decision remain separate.
