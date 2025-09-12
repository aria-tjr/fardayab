#!/usr/bin/env bash
set -euo pipefail

# Hetzner CLI Setup and Server Creation Script
# This script sets up hcloud CLI and creates a server for the Telegram Bot

echo "[+] Setting up Hetzner CLI and creating server for Telegram Bot"

# Configuration
SERVER_NAME="telegram-bot-server"
SERVER_TYPE="cx22"
IMAGE="ubuntu-22.04"
LOCATION="nbg1"
SSH_KEY_NAME="telegram-bot-key"

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

# Check if hcloud is installed
if ! command -v hcloud >/dev/null 2>&1; then
    log_error "hcloud CLI is not installed. Please install it first:"
    echo "brew install hcloud"
    exit 1
fi

log_info "hcloud CLI is installed"

# Check if user is already logged in
if hcloud context active >/dev/null 2>&1; then
    log_info "Already logged in to hcloud"
    CURRENT_CONTEXT=$(hcloud context active)
    echo "Current context: $CURRENT_CONTEXT"
else
    log_info "Setting up hcloud context"
    echo ""
    echo "You need to provide your Hetzner Cloud API token."
    echo "Get it from: https://console.hetzner.com/projects -> Access Tokens"
    echo ""
    read -p "Enter your Hetzner API token: " -s API_TOKEN
    echo ""
    
    if [ -z "$API_TOKEN" ]; then
        log_error "API token is required"
        exit 1
    fi
    
    # Create context
    echo "$API_TOKEN" | hcloud context create telegram-bot-context
    hcloud context use telegram-bot-context
    log_info "hcloud context created and activated"
fi

# Check if SSH key exists
if ! hcloud ssh-key describe "$SSH_KEY_NAME" >/dev/null 2>&1; then
    log_info "Creating SSH key: $SSH_KEY_NAME"
    
    # Use the existing ed25519 key
    SSH_KEY_PATH="$HOME/.ssh/id_ed25519.pub"
    
    if [ ! -f "$SSH_KEY_PATH" ]; then
        log_error "SSH public key not found at $SSH_KEY_PATH"
        exit 1
    fi
    
    hcloud ssh-key create --name "$SSH_KEY_NAME" --public-key-from-file "$SSH_KEY_PATH"
    log_info "SSH key created successfully"
else
    log_info "SSH key already exists: $SSH_KEY_NAME"
fi

# Check if server already exists
if hcloud server describe "$SERVER_NAME" >/dev/null 2>&1; then
    log_warn "Server $SERVER_NAME already exists"
    echo "Server details:"
    hcloud server describe "$SERVER_NAME"
    echo ""
    read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deleting existing server..."
        hcloud server delete "$SERVER_NAME"
        sleep 5
    else
        log_info "Using existing server"
        SERVER_INFO=$(hcloud server describe "$SERVER_NAME" -o json)
        SERVER_IPV4=$(echo "$SERVER_INFO" | jq -r '.public_net.ipv4.ip')
        SERVER_IPV6=$(echo "$SERVER_INFO" | jq -r '.public_net.ipv6.ip')
        
        echo ""
        echo "=========================================="
        echo "  EXISTING HETZNER SERVER FOUND"
        echo "=========================================="
        echo ""
        echo "Server Name: $SERVER_NAME"
        echo "IPv4 Address: $SERVER_IPV4"
        echo "IPv6 Address: $SERVER_IPV6"
        echo ""
        echo "SSH connection:"
        echo "  ssh root@$SERVER_IPV4"
        echo ""
        echo "To deploy the bot:"
        echo "  scp -r deploy/ root@$SERVER_IPV4:/opt/telegram-bot/"
        echo "  ssh root@$SERVER_IPV4"
        echo "  cd /opt/telegram-bot/deploy"
        echo "  sudo ./complete-deployment-package.sh"
        echo ""
        echo "=========================================="
        exit 0
    fi
fi

# Create server
log_info "Creating server: $SERVER_NAME"
echo "This may take a few minutes..."

SERVER_OUTPUT=$(hcloud server create \
    --name "$SERVER_NAME" \
    --type "$SERVER_TYPE" \
    --image "$IMAGE" \
    --location "$LOCATION" \
    --ssh-key "$SSH_KEY_NAME" \
    --user-data-from-file - << 'EOF'
#!/bin/bash
# Update system
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y curl wget git ufw fail2ban htop

# Configure IPv6
if [ -f /etc/netplan/50-cloud-init.yaml ]; then
    # Ubuntu with Netplan - ensure IPv6 is enabled
    cat > /etc/netplan/50-cloud-init.yaml << 'NETPLAN_EOF'
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp6: true
      accept-ra: true
NETPLAN_EOF
    netplan apply
fi

# Enable IPv6 forwarding
echo 'net.ipv6.conf.all.forwarding=1' >> /etc/sysctl.conf
sysctl -p

# Configure firewall
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp
ufw --force enable

# Create project directories
mkdir -p /opt/telegram-bot/{config,data,deploy,ssl}

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configure Docker for IPv6
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'DOCKER_EOF'
{
    "ipv6": true,
    "fixed-cidr-v6": "2a01:4f8:1c1a:9cc1::/64"
}
DOCKER_EOF

systemctl restart docker

echo "Server setup completed successfully!"
echo "Ready for Telegram Bot deployment"
EOF
)

# Extract server information
SERVER_IPV4=$(echo "$SERVER_OUTPUT" | grep "IPv4" | awk '{print $2}')
SERVER_IPV6=$(echo "$SERVER_OUTPUT" | grep "IPv6" | awk '{print $2}')

log_info "Server created successfully!"

# Wait a moment for server to be ready
log_info "Waiting for server to be ready..."
sleep 30

# Test SSH connection
log_info "Testing SSH connection..."
if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@$SERVER_IPV4 "echo 'SSH connection successful'" >/dev/null 2>&1; then
    log_info "✓ SSH connection successful"
else
    log_warn "⚠ SSH connection test failed, server may still be starting up"
fi

# Display server information
echo ""
echo "=========================================="
echo "  HETZNER SERVER CREATED SUCCESSFULLY"
echo "=========================================="
echo ""
echo "Server Name: $SERVER_NAME"
echo "IPv4 Address: $SERVER_IPV4"
echo "IPv6 Address: $SERVER_IPV6"
echo ""
echo "SSH connection:"
echo "  ssh root@$SERVER_IPV4"
echo ""
echo "Next steps:"
echo "1. Upload deployment files:"
echo "   scp -r deploy/ root@$SERVER_IPV4:/opt/telegram-bot/"
echo ""
echo "2. SSH to server and deploy:"
echo "   ssh root@$SERVER_IPV4"
echo "   cd /opt/telegram-bot/deploy"
echo "   sudo ./complete-deployment-package.sh"
echo ""
echo "3. Configure your bot:"
echo "   nano /opt/telegram-bot/config/.env"
echo "   # Add your bot token and API keys"
echo ""
echo "4. Restart the bot:"
echo "   cd /opt/telegram-bot"
echo "   sudo docker-compose -f deploy/docker-compose.hetzner.yml restart"
echo ""
echo "=========================================="

# Ask if user wants to proceed with deployment
echo ""
read -p "Do you want to proceed with uploading files and deploying the bot now? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Proceeding with deployment..."
    
    # Upload files
    log_info "Uploading deployment files..."
    scp -r deploy/ root@$SERVER_IPV4:/opt/telegram-bot/
    
    # Deploy bot
    log_info "Deploying bot on server..."
    ssh root@$SERVER_IPV4 "cd /opt/telegram-bot/deploy && chmod +x *.sh && sudo ./complete-deployment-package.sh"
    
    log_info "Deployment completed!"
    echo ""
    echo "Your bot should now be accessible at:"
    echo "  HTTP:  http://[$SERVER_IPV6]"
    echo "  HTTPS: https://[$SERVER_IPV6]"
    echo ""
    echo "To check status:"
    echo "  ssh root@$SERVER_IPV4"
    echo "  cd /opt/telegram-bot"
    echo "  sudo docker-compose -f deploy/docker-compose.hetzner.yml ps"
else
    log_info "Deployment skipped. You can run it manually later using the commands above."
fi
