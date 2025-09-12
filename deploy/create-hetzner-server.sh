#!/usr/bin/env bash
set -euo pipefail

# Hetzner Server Creation Script
# This script creates a Hetzner server using the hcloud CLI

echo "[+] Creating Hetzner server for Telegram Bot deployment"

# Configuration
SERVER_NAME="telegram-bot-server"
SERVER_TYPE="cx22"
IMAGE="ubuntu-22.04"
LOCATION="nbg1"
SSH_KEY_NAME="telegram-bot-key"

# Check if hcloud CLI is installed
if ! command -v hcloud >/dev/null 2>&1; then
    echo "Error: hcloud CLI is not installed"
    echo "Please install it first: https://github.com/hetznercloud/cli"
    exit 1
fi

# Check if user is logged in
if ! hcloud context active >/dev/null 2>&1; then
    echo "Error: Not logged in to hcloud"
    echo "Please run: hcloud context create"
    exit 1
fi

# Create SSH key if it doesn't exist
if ! hcloud ssh-key describe "$SSH_KEY_NAME" >/dev/null 2>&1; then
    echo "[+] Creating SSH key: $SSH_KEY_NAME"
    hcloud ssh-key create --name "$SSH_KEY_NAME" --public-key-from-file ~/.ssh/id_rsa.pub
else
    echo "[+] SSH key already exists: $SSH_KEY_NAME"
fi

# Create server
echo "[+] Creating server: $SERVER_NAME"
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

# Configure IPv6 (if available)
if [ -f /etc/netplan/50-cloud-init.yaml ]; then
    # Ubuntu with Netplan - add IPv6 configuration
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

echo "Server setup completed successfully!"
EOF
)

# Extract server IP addresses
SERVER_IPV4=$(echo "$SERVER_OUTPUT" | grep "IPv4" | awk '{print $2}')
SERVER_IPV6=$(echo "$SERVER_OUTPUT" | grep "IPv6" | awk '{print $2}')

echo ""
echo "=========================================="
echo "  HETZNER SERVER CREATED SUCCESSFULLY"
echo "=========================================="
echo ""
echo "Server Name: $SERVER_NAME"
echo "IPv4 Address: $SERVER_IPV4"
echo "IPv6 Address: $SERVER_IPV6"
echo ""
echo "Next steps:"
echo "1. SSH to your server:"
echo "   ssh root@$SERVER_IPV4"
echo "   # or with IPv6:"
echo "   ssh root@$SERVER_IPV6"
echo ""
echo "2. Upload deployment files:"
echo "   scp -r deploy/ root@$SERVER_IPV4:/opt/telegram-bot/"
echo ""
echo "3. Run deployment script:"
echo "   cd /opt/telegram-bot/deploy"
echo "   sudo ./complete-deployment-package.sh"
echo ""
echo "=========================================="
