#!/usr/bin/env bash
set -euo pipefail

: "${DEPLOY_HOST:?Set DEPLOY_HOST}"
: "${DEPLOY_USER:?Set DEPLOY_USER}"
: "${DEPLOY_HOST_PROJECT_PATH:?Set DEPLOY_HOST_PROJECT_PATH}"
: "${SITE_IMAGE:?Set SITE_IMAGE}"
DEPLOY_PORT="${DEPLOY_PORT:-22}"

[[ "$DEPLOY_HOST_PROJECT_PATH" =~ ^/home/[a-zA-Z0-9_/-]+$ && "$DEPLOY_HOST_PROJECT_PATH" != *..* ]]
remote="$DEPLOY_USER@$DEPLOY_HOST"
opts=(-o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=15 -o Port="$DEPLOY_PORT")

ssh "${opts[@]}" "$remote" "mkdir -p '$DEPLOY_HOST_PROJECT_PATH'; rm -f '$DEPLOY_HOST_PROJECT_PATH/compose.yaml.next' '$DEPLOY_HOST_PROJECT_PATH/.env.next'"
scp "${opts[@]}" compose.yaml "$remote:$DEPLOY_HOST_PROJECT_PATH/compose.yaml.next"
printf 'SITE_IMAGE=%s\n' "$SITE_IMAGE" | ssh "${opts[@]}" "$remote" "umask 077; cat > '$DEPLOY_HOST_PROJECT_PATH/.env.next'"

ssh "${opts[@]}" "$remote" "set -eu
  cd '$DEPLOY_HOST_PROJECT_PATH'
  rm -f compose.yaml .env
  mv compose.yaml.next compose.yaml
  mv .env.next .env
  docker compose config --quiet
  docker compose pull
  docker compose up -d --wait --wait-timeout 120
  rm -f routing.env .deploy.lock current previous
  rm -rf releases
"
