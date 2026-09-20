#!/usr/bin/env bash
set -euo pipefail
: "${DEPLOY_HOST:?Set DEPLOY_HOST}"; : "${DEPLOY_USER:?Set DEPLOY_USER}"; : "${DEPLOY_HOST_PROJECT_PATH:?Set DEPLOY_HOST_PROJECT_PATH}"; : "${RELEASE_ID:?Set RELEASE_ID}"; : "${SITE_IMAGE:?Set SITE_IMAGE}"; : "${DOCKER_USERNAME:?Set DOCKER_USERNAME}"; : "${DOCKER_TOKEN:?Set DOCKER_TOKEN}"
DEPLOY_PORT="${DEPLOY_PORT:-22}"
remote="$DEPLOY_USER@$DEPLOY_HOST"; release="$DEPLOY_HOST_PROJECT_PATH/releases/$RELEASE_ID"; opts=(-o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=15 -o Port="$DEPLOY_PORT")
cleanup(){ ssh "${opts[@]}" "$remote" "rm -f '$release/.docker/config.json'; rmdir '$release/.docker' 2>/dev/null || true" || true; }; trap cleanup EXIT
ssh "${opts[@]}" "$remote" "umask 077; mkdir -p '$DEPLOY_HOST_PROJECT_PATH/releases'; mkdir '$release'; mkdir '$release/.docker'"
scp "${opts[@]}" compose.yaml scripts/deploy-remote.sh "$remote:$release/"
printf 'SITE_IMAGE=%s\n' "$SITE_IMAGE" | ssh "${opts[@]}" "$remote" "cat > '$release/.env'"
printf '%s' "$DOCKER_TOKEN" | ssh "${opts[@]}" "$remote" "DOCKER_CONFIG='$release/.docker' docker login --username '$DOCKER_USERNAME' --password-stdin"
ssh "${opts[@]}" "$remote" "bash '$release/deploy-remote.sh' '$DEPLOY_HOST_PROJECT_PATH' '$RELEASE_ID'"

