#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/deploy.sh user@server_ip [/remote/path]
# Copies project to remote, installs docker if missing, and starts compose

REMOTE=${1:-}
DEST=${2:-/opt/tg-bot}

if [[ -z "$REMOTE" ]]; then
  echo "Usage: $0 user@server_ip [/remote/path]"
  exit 1
fi

echo "==> Preparing remote directory $REMOTE:$DEST"
ssh -o StrictHostKeyChecking=no "$REMOTE" "sudo mkdir -p '$DEST' && sudo chown -R \$USER: '$DEST'"

echo "==> Syncing files"
rsync -az --delete --exclude '.git' --exclude '__pycache__' --exclude 'node_modules' \ 
  ./ "$REMOTE:$DEST/"

echo "==> Installing Docker if needed"
ssh "$REMOTE" "bash -s" < ./scripts/install_docker.sh

echo "==> Starting containers"
ssh "$REMOTE" "cd '$DEST' && docker compose pull || true && docker compose up -d --build"

echo "==> Deployment complete"
