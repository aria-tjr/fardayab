#!/usr/bin/env bash
set -euo pipefail

# Hetzner Telegram Bot Deployment Script
# This script deploys the telegram bot on Hetzner server with IPv6 support

echo "[+] Starting Hetzner deployment for Telegram Bot"

# Configuration
PROJECT_DIR="/opt/telegram-bot"
DEPLOY_DIR="$PROJECT_DIR/deploy"
CONFIG_DIR="$PROJECT_DIR/config"
DATA_DIR="$PROJECT_DIR/data"
IPV6_ADDRESS="2a01:4f8:1c1a:9cc1::1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root (use sudo)"
    exit 1
fi

# Update system packages
log_info "Updating system packages"
apt-get update
apt-get upgrade -y

# Install required packages
log_info "Installing required packages"
apt-get install -y curl wget git ufw fail2ban htop

# Install Docker if not present
if ! command -v docker >/dev/null 2>&1; then
    log_info "Installing Docker"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Add current user to docker group
    usermod -aG docker $SUDO_USER
fi

# Install Docker Compose if not present
if ! command -v docker-compose >/dev/null 2>&1; then
    log_info "Installing Docker Compose"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Create project directories
log_info "Creating project directories"
mkdir -p "$PROJECT_DIR"/{config,data,deploy,ssl}
mkdir -p "$DATA_DIR"/{logs,backups}

# Set proper permissions
chown -R $SUDO_USER:$SUDO_USER "$PROJECT_DIR"
chmod 755 "$PROJECT_DIR"

# Configure IPv6 networking
log_info "Configuring IPv6 networking"
if [ -f "$DEPLOY_DIR/hetzner-ipv6-setup.sh" ]; then
    chmod +x "$DEPLOY_DIR/hetzner-ipv6-setup.sh"
    "$DEPLOY_DIR/hetzner-ipv6-setup.sh"
else
    log_warn "IPv6 setup script not found, configuring manually"
    
    # Detect network interface
    INTERFACE=$(ip link show | grep -E "^2:" | head -1 | cut -d: -f2 | tr -d ' ')
    if [ -z "$INTERFACE" ]; then
        INTERFACE="eth0"
    fi
    
    # Add IPv6 configuration
    cat >> /etc/network/interfaces << EOF

# IPv6 configuration for Hetzner
iface $INTERFACE inet6 static
    address $IPV6_ADDRESS
    netmask 64
    gateway fe80::1
EOF
    
    # Restart networking
    systemctl restart networking
fi

# Configure firewall
log_info "Configuring firewall rules"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# IPv4 rules
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp

# IPv6 rules
ufw allow from 2a01:4f8:1c1a:9cc1::/64 to any port 80
ufw allow from 2a01:4f8:1c1a:9cc1::/64 to any port 443
ufw allow from 2a01:4f8:1c1a:9cc1::/64 to any port 8080

ufw --force enable

# Configure fail2ban
log_info "Configuring fail2ban"
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
EOF

systemctl enable fail2ban
systemctl restart fail2ban

# Generate self-signed SSL certificate
log_info "Generating SSL certificate"
if [ ! -f "$PROJECT_DIR/ssl/cert.pem" ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$PROJECT_DIR/ssl/key.pem" \
        -out "$PROJECT_DIR/ssl/cert.pem" \
        -subj "/C=DE/ST=Hesse/L=Frankfurt/O=TelegramBot/CN=$IPV6_ADDRESS"
    
    chmod 600 "$PROJECT_DIR/ssl/key.pem"
    chmod 644 "$PROJECT_DIR/ssl/cert.pem"
fi

# Create environment file template
log_info "Creating environment file template"
cat > "$CONFIG_DIR/.env.template" << EOF
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here

# Database Configuration
DATABASE_URL=sqlite:///app/data/bot.db

# Scheduler Configuration
TIMEZONE=Asia/Tehran
DAILY_RUN_AT=09:00

# API Keys (add your keys here)
NEWS_API_KEY=your_news_api_key
WEATHER_API_KEY=your_weather_api_key
CRYPTO_API_KEY=your_crypto_api_key

# Server Configuration
HOST=0.0.0.0
PORT=8080
DEBUG=false
EOF

# Create systemd service for the bot
log_info "Creating systemd service"
cat > /etc/systemd/system/telegram-bot.service << EOF
[Unit]
Description=Telegram Bot Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker-compose -f $DEPLOY_DIR/docker-compose.hetzner.yml up -d
ExecStop=/usr/local/bin/docker-compose -f $DEPLOY_DIR/docker-compose.hetzner.yml down
TimeoutStartSec=0
User=$SUDO_USER
Group=$SUDO_USER

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl daemon-reload
systemctl enable telegram-bot.service

# Create monitoring script
log_info "Creating monitoring script"
cat > "$PROJECT_DIR/monitor.sh" << 'EOF'
#!/bin/bash
# Telegram Bot Monitoring Script

PROJECT_DIR="/opt/telegram-bot"
LOG_FILE="$PROJECT_DIR/data/logs/monitor.log"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Check if bot container is running
if ! docker ps | grep -q telegram-bot; then
    log_message "ERROR: Telegram bot container is not running"
    cd "$PROJECT_DIR"
    docker-compose -f deploy/docker-compose.hetzner.yml up -d
    log_message "INFO: Attempted to restart telegram bot"
else
    log_message "INFO: Telegram bot is running normally"
fi

# Check IPv6 connectivity
if ! ping6 -c 1 2a01:4f8:1c1a:9cc1::1 >/dev/null 2>&1; then
    log_message "WARNING: IPv6 connectivity issue detected"
fi

# Check disk space
DISK_USAGE=$(df /opt | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    log_message "WARNING: Disk usage is at ${DISK_USAGE}%"
fi
EOF

chmod +x "$PROJECT_DIR/monitor.sh"

# Add monitoring to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * $PROJECT_DIR/monitor.sh") | crontab -

# Create backup script
log_info "Creating backup script"
cat > "$PROJECT_DIR/backup.sh" << 'EOF'
#!/bin/bash
# Telegram Bot Backup Script

PROJECT_DIR="/opt/telegram-bot"
BACKUP_DIR="$PROJECT_DIR/data/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup database
if [ -f "$PROJECT_DIR/data/bot.db" ]; then
    cp "$PROJECT_DIR/data/bot.db" "$BACKUP_DIR/bot_$DATE.db"
    echo "Database backed up to bot_$DATE.db"
fi

# Backup logs
if [ -d "$PROJECT_DIR/data/logs" ]; then
    tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" -C "$PROJECT_DIR/data" logs/
    echo "Logs backed up to logs_$DATE.tar.gz"
fi

# Clean old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.db" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed at $(date)"
EOF

chmod +x "$PROJECT_DIR/backup.sh"

# Add backup to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * $PROJECT_DIR/backup.sh") | crontab -

# Display deployment information
log_info "Deployment completed successfully!"
echo ""
echo "=========================================="
echo "  HETZNER TELEGRAM BOT DEPLOYMENT"
echo "=========================================="
echo ""
echo "IPv6 Address: $IPV6_ADDRESS"
echo "Project Directory: $PROJECT_DIR"
echo "Configuration: $CONFIG_DIR/.env"
echo ""
echo "Next steps:"
echo "1. Copy your .env file to $CONFIG_DIR/.env"
echo "2. Update the .env file with your bot token and API keys"
echo "3. Start the bot: systemctl start telegram-bot"
echo "4. Check status: systemctl status telegram-bot"
echo "5. View logs: docker-compose -f $DEPLOY_DIR/docker-compose.hetzner.yml logs -f"
echo ""
echo "Access URLs:"
echo "  HTTP:  http://[$IPV6_ADDRESS]"
echo "  HTTPS: https://[$IPV6_ADDRESS]"
echo ""
echo "Monitoring:"
echo "  Logs: $PROJECT_DIR/data/logs/"
echo "  Monitor: $PROJECT_DIR/monitor.sh"
echo "  Backup: $PROJECT_DIR/backup.sh"
echo ""
echo "=========================================="
