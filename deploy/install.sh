#!/usr/bin/env bash
set -euo pipefail

# Quick installer for Docker + Compose on Ubuntu/Debian

if ! command -v docker >/dev/null 2>&1; then
  echo "[+] Installing Docker engine"
  apt-get update
  apt-get install -y ca-certificates curl gnupg lsb-release
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

echo "[+] Enabling Docker to start on boot"
systemctl enable --now docker

echo "[+] Ensuring project folders exist"
mkdir -p /opt/telegram-bot/config /opt/telegram-bot/data

echo "[!] Copy your .env to /opt/telegram-bot/config/.env"
echo "    and run: docker compose -f /opt/telegram-bot/deploy/docker-compose.yml up -d --build"

exit 0

