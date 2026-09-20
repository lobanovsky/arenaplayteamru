#!/usr/bin/env bash
set -euo pipefail
project="${1:?Project directory required}"; release_id="${2:?Release id required}"; release="$project/releases/$release_id"; export DOCKER_CONFIG="$release/.docker"
exec 9>"$project/.deploy.lock"; flock -w 300 9
if [[ ! -f "$project/routing.env" ]]; then (umask 077; printf 'TRAEFIK_ENABLED=true\n' > "$project/routing.env"); fi
previous="$(readlink -f "$project/current" 2>/dev/null || true)"
compose(){ local dir="$1"; shift; docker compose --project-name arenaplayteam --project-directory "$project" --env-file "$dir/.env" --env-file "$project/routing.env" -f "$dir/compose.yaml" "$@"; }
cleanup(){ rm -f "$DOCKER_CONFIG/config.json"; rmdir "$DOCKER_CONFIG" 2>/dev/null || true; }; trap cleanup EXIT
compose "$release" config --quiet; docker network inspect housekpr-network >/dev/null; compose "$release" pull
if ! compose "$release" up -d --wait --wait-timeout 120; then
  compose "$release" logs --tail=50 >&2 || true
  if [[ -n "$previous" && -f "$previous/compose.yaml" ]]; then compose "$previous" up -d --wait --wait-timeout 120; else compose "$release" down; fi
  exit 1
fi
[[ -n "$previous" && -f "$previous/compose.yaml" ]] && ln -sfn "$previous" "$project/previous"
ln -s "$release" "$project/current-$release_id"; mv -Tf "$project/current-$release_id" "$project/current"; echo "Deployed $release_id"
ln -sfn current/compose.yaml "$project/compose.yaml"
ln -sfn current/.env "$project/.env"
