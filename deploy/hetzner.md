Hetzner deployment guide (IPv6-ready)

Prereqs
- Fresh Ubuntu 22.04/24.04 (or Debian 12) VPS on Hetzner
- SSH access as root (or a sudo user)
- Your repo copied to the server at `/opt/telegram-bot`
- Your environment file at `/opt/telegram-bot/config/.env`

1) SSH to the server

If you only have IPv6, use brackets:

ssh root@[2a01:4f8:1c1a:9cc1::1]

Replace `::1` with the actual assigned address from your /64. In most cases Hetzner also provides IPv4; use it if available.

2) Install Docker and Compose

apt update && apt -y install git
git clone <your-repo> /opt/telegram-bot
bash /opt/telegram-bot/deploy/install.sh

3) Provide configuration

Copy your local `.env` to the server:

scp config/.env root@[SERVER]:/opt/telegram-bot/config/.env

Verify it contains your tokens and keys and Persian settings.

4) Build and run with Docker Compose

cd /opt/telegram-bot/deploy
docker compose up -d --build

The container restarts automatically on reboot (`restart: unless-stopped`).

5) Logs and health

docker compose logs -f
tail -f /opt/telegram-bot/data/bot.log

6) Firewall (optional but recommended)

If you enable UFW, allow SSH and outbound by default; the bot does not need inbound ports:

ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw enable

7) IPv6 in Docker (optional)

The bot uses only outbound connections; IPv6 is not required for inbound. If you want IPv6 inside containers:

cat > /etc/docker/daemon.json <<'JSON'
{
  "ipv6": true,
  "fixed-cidr-v6": "2a01:4f8:1c1a:9cc1::/64"
}
JSON
systemctl restart docker

8) Updating

cd /opt/telegram-bot
git pull
docker compose -f deploy/docker-compose.yml up -d --build

Using GitHub Container Registry (recommended for auto-updates)
1. Enable GitHub Actions in your repo and merge to main — it will build and push to `ghcr.io/<owner>/<repo>:latest`.
2. On the server, log in to GHCR once (so Watchtower can pull):

docker login ghcr.io -u <your_github_username>
# paste a GitHub Personal Access Token (classic) with `read:packages`

3. Create `/opt/telegram-bot/deploy/.env` with:

IMAGE=ghcr.io/<owner>/<repo>:latest

4. Start via the GHCR compose + Watchtower:

cd /opt/telegram-bot/deploy
docker compose -f docker-compose.ghcr.yml --env-file ./.env up -d

Now Watchtower checks every 20 minutes and updates the container when a new image is published.

9) Service auto-start (Compose already restarts)

Docker starts on boot and your container restarts automatically. No extra systemd unit is required.

Troubleshooting
- Check env file path in compose: `/opt/telegram-bot/config/.env`
- Ensure the bot is admin of your channel with posting rights
- Watch `/opt/telegram-bot/data/bot.log` for errors
- Validate Telegram token and OpenAI key
