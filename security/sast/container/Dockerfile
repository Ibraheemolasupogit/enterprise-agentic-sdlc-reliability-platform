# C5-F4R SAST runtime: Ubuntu 24.04 amd64 + distro CPython 3.12 only.
# Semgrep is NOT installed here; it is installed later, offline and hash-locked,
# into a mounted venv inside a --network none container. Build context is this
# directory only (no repository source enters the image).
#
# Base: docker.io/library/ubuntu:24.04, linux/amd64 platform manifest (index
# sha256:2198e4c65076e9cb0b3d695219df667c0e3b0072da64ca3c2648aca17dcecaf5,
# created 2026-11-10, source git.launchpad.net/cloud-images/+oci/ubuntu-base
# revision cb8ca376b19ad1ff943035430fbcb9d069789a5a).
FROM ubuntu@sha256:77eb101c607d6e3d4f5ad0c8a02c2136c689b98aba1f359e6502ba517e5c57ec

# APT authenticates every index via signed InRelease and the image's
# ubuntu-archive-keyring. ca-certificates comes from the live signed archive
# (needed for the HTTPS snapshot service); all Python packages come from a fixed
# snapshot. Any superseded or unavailable pin fails the build (fail closed).
ARG UBUNTU_SNAPSHOT=20261110T000000Z
RUN set -eu; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates=20260816ubuntu0.24.04.2; \
    apt-get update --snapshot "$UBUNTU_SNAPSHOT"; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends --snapshot "$UBUNTU_SNAPSHOT" \
        python3=3.12.3-0ubuntu2.1 python3-minimal=3.12.3-0ubuntu2.1 libpython3-stdlib=3.12.3-0ubuntu2.1 \
        python3-venv=3.12.3-0ubuntu2.1 python3.12=3.12.3-1ubuntu0.17 python3.12-minimal=3.12.3-1ubuntu0.17 \
        libpython3.12-minimal=3.12.3-1ubuntu0.17 libpython3.12-stdlib=3.12.3-1ubuntu0.17 \
        python3.12-venv=3.12.3-1ubuntu0.17 python3-pip-whl=24.0+dfsg-1ubuntu1.3 \
        python3-setuptools-whl=68.1.2-2ubuntu1.2; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*; \
    groupadd --gid 1001 sast; \
    useradd --uid 1001 --gid 1001 --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin sast

USER 1001:1001
WORKDIR /repo
