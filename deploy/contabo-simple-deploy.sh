#!/bin/bash
# Simple Contabo Deployment Script
# Copy and paste this entire script into your VNC console

echo "Starting Contabo Bot Deployment..."

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create directories
mkdir -p /opt/telegram-bot/{config,data,deploy,ssl}

# Configure IPv6
ip address add 2a02:c207:3017:9335::1/64 dev eth0 2>/dev/null || echo "IPv6 already configured"

# Configure Docker for IPv6
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << EOF
{
    "ipv6": true,
    "fixed-cidr-v6": "2a02:c207:3017:9335::/64"
}
EOF
systemctl restart docker

# Generate SSL certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /opt/telegram-bot/ssl/key.pem \
    -out /opt/telegram-bot/ssl/cert.pem \
    -subj "/C=DE/ST=Bavaria/L=Munich/O=TelegramBot/CN=2a02:c207:3017:9335::1"

# Create environment file
cat > /opt/telegram-bot/config/.env << EOF
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here
DATABASE_URL=sqlite:///app/data/bot.db
TIMEZONE=Europe/Berlin
DAILY_RUN_AT=09:00
HOST=0.0.0.0
PORT=8080
DEBUG=false
EOF

# Create Docker Compose file
cat > /opt/telegram-bot/deploy/docker-compose.yml << 'EOF'
version: "3.9"
services:
  telegram-bot:
    image: python:3.12-slim
    container_name: telegram-bot
    working_dir: /app
    command: >
      bash -c "
        pip install aiogram python-dotenv apscheduler aiohttp aiosqlite pydantic pydantic-settings &&
        echo 'import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import os

async def main():
    bot = Bot(token=os.getenv(\"TELEGRAM_BOT_TOKEN\", \"your_bot_token_here\"), 
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    @dp.message()
    async def handle_message(message):
        await message.answer(f\"🤖 Bot is running on Contabo IPv6: 2a02:c207:3017:9335::1\")
    
    await dp.start_polling(bot)

if __name__ == \"__main__\":
    asyncio.run(main())' > bot.py &&
        python bot.py"
    env_file:
      - ../config/.env
    restart: unless-stopped
    networks:
      - bot-network
    ports:
      - "2a02:c207:3017:9335::1:8080:8080"

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

networks:
  bot-network:
    driver: bridge
    enable_ipv6: true
    ipam:
      config:
        - subnet: 172.20.0.0/16
        - subnet: 2a02:c207:3017:9335::/64
EOF

# Create Nginx configuration
cat > /opt/telegram-bot/deploy/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
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
        
        location / {
            proxy_pass http://telegram-bot:8080;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location /health {
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Configure firewall
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp
ufw allow from 2a02:c207:3017:9335::/64
ufw allow from 127.0.0.1
ufw allow from ::1
ufw --force enable

# Deploy
cd /opt/telegram-bot
docker-compose -f deploy/docker-compose.yml up -d

echo "=========================================="
echo "  CONTABO BOT DEPLOYMENT COMPLETE"
echo "=========================================="
echo "IPv4: 38.242.247.182"
echo "IPv6: 2a02:c207:3017:9335::1"
echo ""
echo "Access URLs:"
echo "  HTTP:  http://[2a02:c207:3017:9335::1]"
echo "  HTTPS: https://[2a02:c207:3017:9335::1]"
echo "  Health: https://[2a02:c207:3017:9335::1]/health"
echo ""
echo "Configure your bot:"
echo "  nano /opt/telegram-bot/config/.env"
echo ""
echo "View logs:"
echo "  docker-compose -f /opt/telegram-bot/deploy/docker-compose.yml logs -f"
echo "=========================================="
