#!/bin/sh
set -eu
fail() { echo 'Invalid proxy/auth configuration; refusing startup.' >&2; exit 1; }
AUTH_MODE=${AUTH_MODE:-anonymous}
PROXY_MODE=${PROXY_MODE:-local}
DNS_RESOLVER=${DNS_RESOLVER:-127.0.0.11}
case "$DNS_RESOLVER" in ''|*[!0-9.]* ) fail;; esac
printf '%s\n' "$DNS_RESOLVER" | awk -F. 'NF!=4{exit 1}{for(i=1;i<=4;i++)if($i=="" || $i>255)exit 1}' || fail
case "$PROXY_MODE" in
  local)
    [ "$AUTH_MODE" = anonymous ] || fail
    API_PORT=${API_PORT:-3000}
    case "$API_PORT" in ''|*[!0-9]*) fail;; esac
    [ "$API_PORT" -ge 1024 ] && [ "$API_PORT" -le 65535 ] || fail
    API_UPSTREAM="http://api:$API_PORT"
    API_HOST=api
    AUTH_HEADER='""'
    FORWARDED_PROTO=http
    ;;
  https)
    [ "$AUTH_MODE" = oidc ] || fail
    case "${API_ORIGIN:-}" in *[!a-zA-Z0-9:/.\-]*) fail;; esac
    printf '%s\n' "${API_ORIGIN:-}" | grep -Eq '^https://[a-zA-Z0-9][a-zA-Z0-9.-]*$' || fail
    API_HOST=${API_ORIGIN#https://}
    [ "${TRUSTED_API_HOST:-}" = "$API_HOST" ] || fail
    API_UPSTREAM="$API_ORIGIN:443"
    AUTH_HEADER='$http_authorization'
    FORWARDED_PROTO=https
    ;;
  *) fail;;
esac
case "$AUTH_MODE" in
  anonymous)
    OIDC_CONNECT_ORIGIN=''
    printf '%s\n' '{"mode":"anonymous"}' > /tmp/auth-config.json;;
  oidc)
    for value in "${OIDC_ISSUER:-}" "${PUBLIC_ORIGIN:-}"; do
      case "$value" in ''|*[!a-zA-Z0-9:/._\-]*) fail;; esac
    done
    printf '%s\n' "$OIDC_ISSUER" | grep -Eq '^https://[a-zA-Z0-9][a-zA-Z0-9.-]*(/[a-zA-Z0-9._/-]*)?$' || fail
    printf '%s\n' "$PUBLIC_ORIGIN" | grep -Eq '^https://[a-zA-Z0-9][a-zA-Z0-9.-]*(:[0-9]+)?$' || fail
    case "${OIDC_CLIENT_ID:-}" in ''|*[!a-zA-Z0-9._\-]*) fail;; esac
    case "${OIDC_SCOPES:-}" in ''|*[!a-zA-Z0-9:/._\ -]*) fail;; esac
    case " $OIDC_SCOPES " in *' openid '*) :;; *) fail;; esac
    issuer_host=${OIDC_ISSUER#https://}
    OIDC_CONNECT_ORIGIN=${OIDC_CONNECT_ORIGIN:-https://${issuer_host%%/*}}
    case "$OIDC_CONNECT_ORIGIN" in ''|*[!a-zA-Z0-9:/._\-]*) fail;; esac
    printf '%s\n' "$OIDC_CONNECT_ORIGIN" | grep -Eq '^https://[a-zA-Z0-9][a-zA-Z0-9.-]*$' || fail
    printf '{"mode":"oidc","authority":"%s","clientId":"%s","scope":"%s","publicOrigin":"%s"}\n' \
      "$OIDC_ISSUER" "$OIDC_CLIENT_ID" "$OIDC_SCOPES" "$PUBLIC_ORIGIN" > /tmp/auth-config.json
    ;;
  *) fail;;
esac
export API_UPSTREAM DNS_RESOLVER OIDC_CONNECT_ORIGIN
envsubst '${API_UPSTREAM} ${DNS_RESOLVER} ${OIDC_CONNECT_ORIGIN}' < /app/default.conf.template > /tmp/default.conf
cat > /tmp/upstream.conf <<EOF
proxy_pass \$api\$request_uri;
proxy_set_header Host $API_HOST;
proxy_set_header Authorization $AUTH_HEADER;
proxy_set_header X-Forwarded-Proto $FORWARDED_PROTO;
proxy_set_header X-Forwarded-Host "";
proxy_set_header X-Forwarded-For "";
proxy_set_header X-MS-CLIENT-PRINCIPAL "";
proxy_set_header X-Authenticated-User "";
EOF
if [ "$PROXY_MODE" = https ]; then
  PROXY_CA_FILE=${PROXY_CA_FILE:-/etc/ssl/certs/ca-certificates.crt}
  case "$PROXY_CA_FILE" in /*) :;; *) fail;; esac
  case "$PROXY_CA_FILE" in *[!a-zA-Z0-9/._\-]*) fail;; esac
  [ -f "$PROXY_CA_FILE" ] || fail
  cat >> /tmp/upstream.conf <<EOF
proxy_ssl_server_name on;
proxy_ssl_name $API_HOST;
proxy_ssl_verify on;
proxy_ssl_verify_depth 3;
proxy_ssl_trusted_certificate $PROXY_CA_FILE;
EOF
fi
exec nginx -c /app/nginx.conf -g 'daemon off;'
