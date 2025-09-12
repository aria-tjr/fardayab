#!/usr/bin/env bash
set -euo pipefail

# Quick deployment script for existing Hetzner server
# This script assumes the server is already configured with IPv6

echo "[+] Quick deployment to Hetzner server"

# Configuration
PROJECT_DIR="/opt/telegram-bot"
DEPLOY_DIR="$PROJECT_DIR/deploy"
IPV6_ADDRESS="2a01:4f8:1c1a:9cc1::1"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Create directories
mkdir -p "$PROJECT_DIR"/{config,data,deploy,ssl}
mkdir -p "$DATA_DIR"/{logs,backups}

# Copy deployment files
echo "[+] Copying deployment files"
cp docker-compose.hetzner.yml "$DEPLOY_DIR/"
cp nginx.conf "$DEPLOY_DIR/"
cp hetzner-ipv6-setup.sh "$DEPLOY_DIR/"

# Set permissions
chmod +x "$DEPLOY_DIR"/*.sh
chown -R $SUDO_USER:$SUDO_USER "$PROJECT_DIR"

# Generate SSL certificate if not exists
if [ ! -f "$PROJECT_DIR/ssl/cert.pem" ]; then
    echo "[+] Generating SSL certificate"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$PROJECT_DIR/ssl/key.pem" \
        -out "$PROJECT_DIR/ssl/cert.pem" \
        -subj "/C=DE/ST=Hesse/L=Frankfurt/O=TelegramBot/CN=$IPV6_ADDRESS"
    
    chmod 600 "$PROJECT_DIR/ssl/key.pem"
    chmod 644 "$PROJECT_DIR/ssl/cert.pem"
fi

# Create .env template if not exists
if [ ! -f "$PROJECT_DIR/config/.env" ]; then
    echo "[+] Creating .env template"
    cat > "$PROJECT_DIR/config/.env.template" << EOF
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here

# Database Configuration
DATABASE_URL=sqlite:///app/data/bot.db

# Scheduler Configuration
TIMEZONE=Asia/Tehran
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
    
    echo "[!] Please copy your .env file to $PROJECT_DIR/config/.env"
    echo "    You can use the template: cp $PROJECT_DIR/config/.env.template $PROJECT_DIR/config/.env"
fi

# Deploy with Docker Compose
echo "[+] Deploying with Docker Compose"
cd "$PROJECT_DIR"
docker-compose -f "$DEPLOY_DIR/docker-compose.hetzner.yml" up -d --build

# Check deployment status
echo "[+] Checking deployment status"
sleep 10

if docker ps | grep -q telegram-bot; then
    echo "[+] Telegram bot deployed successfully!"
    echo ""
    echo "Access URLs:"
    echo "  HTTP:  http://[$IPV6_ADDRESS]"
    echo "  HTTPS: https://[$IPV6_ADDRESS]"
    echo ""
    echo "To view logs:"
    echo "  docker-compose -f $DEPLOY_DIR/docker-compose.hetzner.yml logs -f"
    echo ""
    echo "To stop:"
    echo "  docker-compose -f $DEPLOY_DIR/docker-compose.hetzner.yml down"
else
    echo "[!] Deployment failed. Check logs:"
    echo "  docker-compose -f $DEPLOY_DIR/docker-compose.hetzner.yml logs"
fi
