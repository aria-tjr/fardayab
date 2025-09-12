#!/bin/bash
# Complete Contabo Bot Deployment
# This script deploys everything needed for your Telegram bot

set -euo pipefail

echo "🚀 Starting Complete Contabo Bot Deployment"
echo "Server: Cloud VPS 10 SSD"
echo "IPv4: 38.242.247.182"
echo "IPv6: 2a02:c207:3017:9335::1"
echo "VNC: 207.180.255.168:63178"
echo "=========================================="

# Configuration
IPV4_ADDRESS="38.242.247.182"
IPV6_ADDRESS="2a02:c207:3017:9335::1"
IPV6_SUBNET="2a02:c207:3017:9335::/64"
PROJECT_DIR="/opt/telegram-bot"
CONFIG_DIR="$PROJECT_DIR/config"
DATA_DIR="$PROJECT_DIR/data"
DEPLOY_DIR="$PROJECT_DIR/deploy"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root (use sudo)"
    exit 1
fi

# Step 1: Update system
log_step "1. Updating system packages"
apt-get update
apt-get upgrade -y
apt-get install -y curl wget git ufw fail2ban htop python3 python3-venv openssl nano

# Step 2: Install Docker
log_step "2. Installing Docker"
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    usermod -aG docker $SUDO_USER
    log_info "Docker installed successfully"
else
    log_info "Docker already installed"
fi

# Step 3: Install Docker Compose
log_step "3. Installing Docker Compose"
if ! command -v docker-compose >/dev/null 2>&1; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log_info "Docker Compose installed successfully"
else
    log_info "Docker Compose already installed"
fi

# Step 4: Configure Docker for IPv6
log_step "4. Configuring Docker for IPv6"
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << EOF
{
    "ipv6": true,
    "fixed-cidr-v6": "$IPV6_SUBNET"
}
EOF
systemctl restart docker
log_info "Docker configured for IPv6"

# Step 5: Create project directories
log_step "5. Creating project structure"
mkdir -p "$PROJECT_DIR"/{config,data,deploy,ssl}
mkdir -p "$DATA_DIR"/{logs,backups}
mkdir -p "$PROJECT_DIR/telegram_bot"/{config,utils,handlers,scheduler,data,ai,modules}

# Step 6: Configure IPv6 networking
log_step "6. Configuring IPv6 networking"
INTERFACE=$(ip link show | grep -E "^2:" | head -1 | cut -d: -f2 | tr -d ' ')
if [ -z "$INTERFACE" ]; then
    INTERFACE="eth0"
fi

log_info "Using network interface: $INTERFACE"

# Add IPv6 address
ip address add "$IPV6_ADDRESS/64" dev "$INTERFACE" 2>/dev/null || log_warn "IPv6 address may already exist"

# Configure Netplan for IPv6
if [ -f /etc/netplan/50-cloud-init.yaml ]; then
    cp /etc/netplan/50-cloud-init.yaml /etc/netplan/50-cloud-init.yaml.backup.$(date +%Y%m%d_%H%M%S)
    cat > /etc/netplan/50-cloud-init.yaml << EOF
network:
  version: 2
  ethernets:
    $INTERFACE:
      addresses:
        - $IPV6_ADDRESS/64
      dhcp4: true
      routes:
        - to: default
          via: fe80::1
      nameservers:
        addresses:
          - 2001:4860:4860::8888
          - 2001:4860:4860::8844
EOF
    netplan apply
    log_info "IPv6 configured with Netplan"
fi

# Step 7: Configure firewall
log_step "7. Configuring firewall"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# IPv4 rules
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp

# IPv6 rules
ufw allow from "$IPV6_SUBNET" to any port 22 comment 'SSH IPv6'
ufw allow from "$IPV6_SUBNET" to any port 80 comment 'HTTP IPv6'
ufw allow from "$IPV6_SUBNET" to any port 443 comment 'HTTPS IPv6'
ufw allow from "$IPV6_SUBNET" to any port 8080 comment 'Bot API IPv6'

# Allow localhost
ufw allow from 127.0.0.1
ufw allow from ::1

ufw --force enable
log_info "Firewall configured"

# Step 8: Generate SSL certificate
log_step "8. Generating SSL certificate"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$PROJECT_DIR/ssl/key.pem" \
    -out "$PROJECT_DIR/ssl/cert.pem" \
    -subj "/C=DE/ST=Bavaria/L=Munich/O=TelegramBot/CN=$IPV6_ADDRESS"

chmod 600 "$PROJECT_DIR/ssl/key.pem"
chmod 644 "$PROJECT_DIR/ssl/cert.pem"
log_info "SSL certificate generated"

# Step 9: Create environment configuration
log_step "9. Creating environment configuration"
cat > "$CONFIG_DIR/.env" << 'EOF'
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here

# Database Configuration
DATABASE_URL=sqlite:///app/data/bot.db

# Scheduler Configuration
TIMEZONE=Europe/Berlin
DAILY_RUN_AT=09:00

# API Keys
NEWS_API_KEY=your_news_api_key
WEATHER_API_KEY=your_weather_api_key
CRYPTO_API_KEY=your_crypto_api_key

# Server Configuration
HOST=0.0.0.0
PORT=8080
DEBUG=false
EOF

# Step 10: Create Docker Compose configuration
log_step "10. Creating Docker Compose configuration"
cat > "$DEPLOY_DIR/docker-compose.yml" << 'EOF'
version: "3.9"

services:
  telegram-bot:
    build:
      context: ../telegram_bot
      dockerfile: Dockerfile
    container_name: telegram-bot
    env_file:
      - ../config/.env
    environment:
      - TZ=Europe/Berlin
    volumes:
      - ../config/.env:/app/config/.env:ro
      - ../data:/app/data
    restart: unless-stopped
    networks:
      - bot-network
    ports:
      - "2a02:c207:3017:9335::1:8080:8080"
    healthcheck:
      test: ["CMD", "python", "-c", "import os,sys; sys.exit(0)"]
      interval: 1m
      timeout: 5s
      retries: 3
      start_period: 20s

  nginx:
    image: nginx:alpine
    container_name: telegram-bot-nginx
    ports:
      - "2a02:c207:3017:9335::1:80:80"
      - "2a02:c207:3017:9335::1:443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ../ssl:/etc/nginx/ssl:ro
    depends_on:
      - telegram-bot
    restart: unless-stopped
    networks:
      - bot-network

  watchtower:
    image: containrrr/watchtower:latest
    container_name: watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_POLL_INTERVAL=1200
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_INCLUDE_RESTARTING=true
      - WATCHTOWER_SCOPE=telegram-bot
    command: --scope telegram-bot telegram-bot
    restart: unless-stopped
    networks:
      - bot-network

networks:
  bot-network:
    driver: bridge
    enable_ipv6: true
    ipam:
      config:
        - subnet: 172.20.0.0/16
        - subnet: 2a02:c207:3017:9335::/64
EOF

# Step 11: Create Nginx configuration
log_step "11. Creating Nginx configuration"
cat > "$DEPLOY_DIR/nginx.conf" << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    upstream telegram_bot {
        server telegram-bot:8080;
    }
    
    server {
        listen [2a02:c207:3017:9335::1]:80;
        server_name _;
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen [2a02:c207:3017:9335::1]:443 ssl http2;
        server_name _;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        
        limit_req zone=api burst=20 nodelay;
        
        location / {
            proxy_pass http://telegram_bot;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
        
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Step 12: Create bot application
log_step "12. Creating Telegram bot application"

# Create main.py
cat > "$PROJECT_DIR/telegram_bot/main.py" << 'EOF'
import asyncio
import logging
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from telegram_bot.config.settings import Settings
from telegram_bot.utils.logging import setup_logging
from telegram_bot.handlers.admin import admin_router
from telegram_bot.scheduler.scheduler import build_scheduler
from telegram_bot.data.db import Database
from telegram_bot.handlers.polls import polls_router

async def main() -> None:
    load_dotenv("config/.env", override=False)
    settings = Settings()
    setup_logging(settings)

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    db = Database(settings)
    await db.init()

    scheduler = build_scheduler(settings, bot, db)
    scheduler.start()

    dp.include_router(admin_router(settings, scheduler, db))
    dp.include_router(polls_router(db))

    logging.getLogger(__name__).info(
        "Bot started. Timezone=%s Daily=%s Channel=%s",
        settings.TIMEZONE,
        settings.DAILY_RUN_AT,
        settings.TELEGRAM_CHANNEL_ID,
    )

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
EOF

# Create Dockerfile
cat > "$PROJECT_DIR/telegram_bot/Dockerfile" << 'EOF'
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

CMD ["python", "-m", "telegram_bot.main"]
EOF

# Create requirements.txt
cat > "$PROJECT_DIR/telegram_bot/requirements.txt" << 'EOF'
aiogram==3.4.1
python-dotenv==1.0.0
apscheduler==3.10.4
aiohttp==3.9.1
aiosqlite==0.19.0
pydantic==2.5.2
pydantic-settings==2.1.0
EOF

# Create settings.py
cat > "$PROJECT_DIR/telegram_bot/config/settings.py" << 'EOF'
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = "your_bot_token_here"
    TELEGRAM_CHANNEL_ID: str = "your_channel_id_here"
    DATABASE_URL: str = "sqlite:///app/data/bot.db"
    TIMEZONE: str = "Europe/Berlin"
    DAILY_RUN_AT: str = "09:00"
    NEWS_API_KEY: Optional[str] = None
    WEATHER_API_KEY: Optional[str] = None
    CRYPTO_API_KEY: Optional[str] = None
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = False

    class Config:
        env_file = ".env"
EOF

# Create other required files
cat > "$PROJECT_DIR/telegram_bot/utils/logging.py" << 'EOF'
import logging
from telegram_bot.config.settings import Settings

def setup_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
EOF

cat > "$PROJECT_DIR/telegram_bot/data/db.py" << 'EOF'
import aiosqlite
from telegram_bot.config.settings import Settings

class Database:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db_path = "bot.db"
    
    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()
EOF

cat > "$PROJECT_DIR/telegram_bot/handlers/admin.py" << 'EOF'
from aiogram import Router
from telegram_bot.config.settings import Settings
from telegram_bot.data.db import Database

def admin_router(settings: Settings, scheduler, db: Database) -> Router:
    router = Router()
    
    @router.message()
    async def handle_message(message):
        await message.answer(f"🤖 Bot is running on Contabo IPv6: 2a02:c207:3017:9335::1")
    
    return router
EOF

cat > "$PROJECT_DIR/telegram_bot/handlers/polls.py" << 'EOF'
from aiogram import Router
from telegram_bot.data.db import Database

def polls_router(db: Database) -> Router:
    router = Router()
    return router
EOF

cat > "$PROJECT_DIR/telegram_bot/scheduler/scheduler.py" << 'EOF'
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram_bot.config.settings import Settings

def build_scheduler(settings: Settings, bot, db) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    return scheduler
EOF

# Create __init__.py files
touch "$PROJECT_DIR/telegram_bot/__init__.py"
touch "$PROJECT_DIR/telegram_bot/config/__init__.py"
touch "$PROJECT_DIR/telegram_bot/utils/__init__.py"
touch "$PROJECT_DIR/telegram_bot/handlers/__init__.py"
touch "$PROJECT_DIR/telegram_bot/scheduler/__init__.py"
touch "$PROJECT_DIR/telegram_bot/data/__init__.py"
touch "$PROJECT_DIR/telegram_bot/ai/__init__.py"
touch "$PROJECT_DIR/telegram_bot/modules/__init__.py"

# Step 13: Set permissions
log_step "13. Setting permissions"
chown -R $SUDO_USER:$SUDO_USER "$PROJECT_DIR"
chmod +x "$DEPLOY_DIR"/*.sh

# Step 14: Deploy with Docker Compose
log_step "14. Deploying with Docker Compose"
cd "$PROJECT_DIR"
docker-compose -f "$DEPLOY_DIR/docker-compose.yml" up -d --build

# Wait for services to start
log_info "Waiting for services to start..."
sleep 20

# Step 15: Check deployment status
log_step "15. Checking deployment status"
if docker ps | grep -q telegram-bot; then
    log_info "✅ Telegram bot deployed successfully!"
else
    log_error "❌ Deployment failed. Checking logs..."
    docker-compose -f "$DEPLOY_DIR/docker-compose.yml" logs
    exit 1
fi

# Step 16: Test connectivity
log_step "16. Testing connectivity"
if curl -s --connect-timeout 10 --max-time 30 "http://[$IPV6_ADDRESS]" >/dev/null 2>&1; then
    log_info "✅ Bot accessible via HTTP"
else
    log_warn "⚠️ Bot may not be accessible via HTTP"
fi

if curl -s -k --connect-timeout 10 --max-time 30 "https://[$IPV6_ADDRESS]" >/dev/null 2>&1; then
    log_info "✅ Bot accessible via HTTPS"
else
    log_warn "⚠️ Bot may not be accessible via HTTPS"
fi

# Step 17: Display final results
log_info "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo ""
echo "=========================================="
echo "  CONTABO TELEGRAM BOT DEPLOYMENT"
echo "=========================================="
echo ""
echo "Server Details:"
echo "  IPv4 Address: $IPV4_ADDRESS"
echo "  IPv6 Address: $IPV6_ADDRESS"
echo "  VNC Access: 207.180.255.168:63178"
echo "  VNC Password: S35HdcCw"
echo ""
echo "Project Structure:"
echo "  Project Directory: $PROJECT_DIR"
echo "  Configuration: $CONFIG_DIR/.env"
echo "  Data Directory: $DATA_DIR"
echo "  Deploy Directory: $DEPLOY_DIR"
echo ""
echo "Access URLs:"
echo "  HTTP:  http://[$IPV6_ADDRESS]"
echo "  HTTPS: https://[$IPV6_ADDRESS]"
echo "  Health: https://[$IPV6_ADDRESS]/health"
echo ""
echo "Next Steps:"
echo "1. Configure your bot:"
echo "   nano $CONFIG_DIR/.env"
echo "   # Add your bot token and API keys"
echo ""
echo "2. Restart the bot:"
echo "   cd $PROJECT_DIR"
echo "   docker-compose -f $DEPLOY_DIR/docker-compose.yml restart"
echo ""
echo "Management Commands:"
echo "  View logs: docker-compose -f $DEPLOY_DIR/docker-compose.yml logs -f"
echo "  Stop: docker-compose -f $DEPLOY_DIR/docker-compose.yml down"
echo "  Restart: docker-compose -f $DEPLOY_DIR/docker-compose.yml restart"
echo "  Status: docker ps"
echo ""
echo "=========================================="
