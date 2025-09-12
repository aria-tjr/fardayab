#!/usr/bin/env bash
set -euo pipefail

# Deployment script for existing Hetzner server
# This script deploys the telegram bot to an existing server with IPv6 support

echo "[+] Deploying Telegram Bot to existing Hetzner server"

# Configuration
PROJECT_DIR="/opt/telegram-bot"
DEPLOY_DIR="$PROJECT_DIR/deploy"
IPV6_ADDRESS="2a01:4f8:1c1a:9cc1::1"
IPV6_SUBNET="2a01:4f8:1c1a:9cc1::/64"

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

# Configure Docker for IPv6
log_info "Configuring Docker for IPv6"
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << EOF
{
    "ipv6": true,
    "fixed-cidr-v6": "$IPV6_SUBNET"
}
EOF

systemctl restart docker

# Create project directories
log_info "Creating project directories"
mkdir -p "$PROJECT_DIR"/{config,data,deploy,ssl}
mkdir -p "$DATA_DIR"/{logs,backups}

# Set proper permissions
chown -R $SUDO_USER:$SUDO_USER "$PROJECT_DIR"
chmod 755 "$PROJECT_DIR"

# Configure IPv6 networking (Ubuntu/Debian with Netplan)
log_info "Configuring IPv6 networking"
if [ -f /etc/netplan/50-cloud-init.yaml ]; then
    log_info "Using Netplan configuration"
    
    # Backup original file
    cp /etc/netplan/50-cloud-init.yaml /etc/netplan/50-cloud-init.yaml.backup.$(date +%Y%m%d_%H%M%S)
    
    # Create new Netplan configuration
    cat > /etc/netplan/50-cloud-init.yaml << EOF
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - $IPV6_ADDRESS/64
      dhcp4: true
      routes:
        - to: default
          via: fe80::1
      nameservers:
        addresses:
          - 2a01:4ff:ff00::add:2
          - 2a01:4ff:ff00::add:1
EOF
    
    # Apply Netplan configuration
    netplan apply
    
elif [ -f /etc/network/interfaces ]; then
    log_info "Using interfaces configuration"
    
    # Backup original file
    cp /etc/network/interfaces /etc/network/interfaces.backup.$(date +%Y%m%d_%H%M%S)
    
    # Add IPv6 configuration
    cat >> /etc/network/interfaces << EOF

# IPv6 configuration for Hetzner
iface eth0 inet6 static
    address $IPV6_ADDRESS
    netmask 64
    gateway fe80::1
EOF
    
    # Restart networking
    systemctl restart networking
fi

# Wait for network to come up
sleep 5

# Configure firewall
log_info "Configuring firewall"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# IPv4 rules
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp

# IPv6 rules
ufw allow from $IPV6_SUBNET to any port 22
ufw allow from $IPV6_SUBNET to any port 80
ufw allow from $IPV6_SUBNET to any port 443
ufw allow from $IPV6_SUBNET to any port 8080

ufw --force enable

# Configure fail2ban
log_info "Configuring fail2ban"
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 ::1 $IPV6_SUBNET

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

# Generate SSL certificate
log_info "Generating SSL certificate"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$PROJECT_DIR/ssl/key.pem" \
    -out "$PROJECT_DIR/ssl/cert.pem" \
    -subj "/C=DE/ST=Hesse/L=Frankfurt/O=TelegramBot/CN=$IPV6_ADDRESS"

chmod 600 "$PROJECT_DIR/ssl/key.pem"
chmod 644 "$PROJECT_DIR/ssl/cert.pem"

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

# API Keys
NEWS_API_KEY=your_news_api_key
WEATHER_API_KEY=your_weather_api_key
CRYPTO_API_KEY=your_crypto_api_key

# Server Configuration
HOST=0.0.0.0
PORT=8080
DEBUG=false
EOF

# Copy deployment files
log_info "Copying deployment files"
cp docker-compose.hetzner.yml "$DEPLOY_DIR/"
cp nginx.conf "$DEPLOY_DIR/"

# Set permissions
chmod +x "$DEPLOY_DIR"/*.sh
chown -R $SUDO_USER:$SUDO_USER "$PROJECT_DIR"

# Test IPv6 connectivity
log_info "Testing IPv6 connectivity"
if ping6 -c 3 $IPV6_ADDRESS >/dev/null 2>&1; then
    log_info "✓ IPv6 connectivity test successful"
else
    log_warn "⚠ IPv6 connectivity test failed"
fi

# Deploy with Docker Compose
log_info "Deploying with Docker Compose"
cd "$PROJECT_DIR"
docker-compose -f "$DEPLOY_DIR/docker-compose.hetzner.yml" up -d --build

# Wait for services to start
sleep 15

# Check deployment status
log_info "Checking deployment status"
if docker ps | grep -q telegram-bot; then
    log_info "✓ Telegram bot deployed successfully!"
else
    log_error "✗ Deployment failed. Check logs:"
    docker-compose -f "$DEPLOY_DIR/docker-compose.hetzner.yml" logs
    exit 1
fi

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
echo "3. Restart the bot: docker-compose -f $DEPLOY_DIR/docker-compose.hetzner.yml restart"
echo ""
echo "Access URLs:"
echo "  HTTP:  http://[$IPV6_ADDRESS]"
echo "  HTTPS: https://[$IPV6_ADDRESS]"
echo "  Health: https://[$IPV6_ADDRESS]/health"
echo ""
echo "Management commands:"
echo "  View logs: docker-compose -f $DEPLOY_DIR/docker-compose.hetzner.yml logs -f"
echo "  Stop: docker-compose -f $DEPLOY_DIR/docker-compose.hetzner.yml down"
echo "  Restart: docker-compose -f $DEPLOY_DIR/docker-compose.hetzner.yml restart"
echo ""
echo "=========================================="
