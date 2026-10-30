#!/bin/sh
set -eu
case "$API_PORT" in ''|*[!0-9]*) echo 'API_PORT must be a local numeric port' >&2; exit 1;; esac
if [ "$API_PORT" -lt 1024 ] || [ "$API_PORT" -gt 65535 ]; then exit 1; fi
envsubst '${API_PORT}' < /app/default.conf.template > /tmp/default.conf
exec nginx -c /app/nginx.conf -g 'daemon off;'
