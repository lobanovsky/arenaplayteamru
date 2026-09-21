#!/usr/bin/env bash
set -euo pipefail
image="${1:?Image required}"
container="$(docker run -d -p 127.0.0.1::8080 "$image")"
trap 'docker rm -f "$container" >/dev/null' EXIT
port="$(docker port "$container" 8080/tcp | cut -d: -f2)"
url="http://127.0.0.1:$port"
for attempt in {1..30}; do curl -fsS "$url/" >/dev/null 2>&1 && break; sleep 1; done
[[ "$(curl -s -o /dev/null -w '%{http_code}' "$url/")" == 200 ]]
[[ "$(curl -s -o /dev/null -w '%{http_code}' "$url/not-a-page")" == 404 ]]
curl -fsS "$url/scripts/main.js" | grep -q 'Arena Play'
curl -fsS "$url/assets/logo.svg" >/dev/null
curl -s "$url/404.html" | grep -q noindex
echo 'HTTP smoke tests passed.'
