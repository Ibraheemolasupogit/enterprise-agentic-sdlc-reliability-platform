FROM node:24.22.2-bookworm-slim@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c AS build
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY frontend ./frontend
RUN npm run build:web

FROM nginxinc/nginx-unprivileged:stable-alpine@sha256:f5116ed4606f3eb015dd4a8e28cb9b351476dc0ad4bc6e9f93b19cec130cdf03
USER root
# Exact security patch versions; no blanket scanner ignores or ignore-unfixed gate.
RUN apk add --no-cache brotli-libs=1.2.1-r0 curl=8.23.0-r0 libcurl=8.23.0-r0 \
    libexpat=2.10.0-r0 libxslt=1.1.43-r4 musl=1.2.6-r3 musl-utils=1.2.6-r3 zlib=1.4-r0
# nginx 1.30.7 security release (CVE-2026-113425/-118899/-121810/-123007/-123633/-123634; also -125283).
# All five installed nginx.org packages move together, from nginx.org's signed Alpine 3.24 repository. apk verifies
# them with the nginx signing key already shipped in the pinned base and refuses untrusted signatures. Remove these
# pins once the pinned nginx-unprivileged base digest itself ships nginx >= 1.30.7.
RUN apk add --no-cache --repository https://nginx.org/packages/alpine/v3.24/main \
    nginx=1.30.7-r1 nginx-module-geoip=1.30.7-r1 nginx-module-image-filter=1.30.7-r1 \
    nginx-module-njs=1.30.7.1.0.2-r1 nginx-module-xslt=1.30.7-r1
USER 101
COPY --from=build /app/frontend/dist /usr/share/nginx/html
COPY LICENSE /usr/share/nginx/html/LICENSE
COPY frontend/nginx.conf frontend/default.conf.template frontend/start.sh /app/
ENV API_PORT=3000
EXPOSE 8080
ENTRYPOINT ["/bin/sh", "/app/start.sh"]
