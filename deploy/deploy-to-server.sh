#!/usr/bin/env bash
set -euo pipefail

# Manual deployment script for the created Hetzner server
# Run this script to deploy the bot to your server

echo "[+] Manual deployment script for Hetzner server"
echo ""
echo "Server Details:"
echo "  Name: telegram-bot-server"
echo "  IPv4: 188.245.154.239"
echo "  IPv6: 2a01:4f8:1c1a:9cc1::1"
echo "  Type: cpx11 (2 vCPU, 2GB RAM, 40GB SSD)"
echo ""

# Test connectivity
echo "[+] Testing server connectivity..."

# Try IPv4 first
if ping -c 3 188.245.154.239 >/dev/null 2>&1; then
    echo "✓ IPv4 ping successful"
    SERVER_IP="188.245.154.239"
elif ping6 -c 3 2a01:4f8:1c1a:9cc1::1 >/dev/null 2>&1; then
    echo "✓ IPv6 ping successful"
    SERVER_IP="2a01:4f8:1c1a:9cc1::1"
else
    echo "✗ Server is not reachable. Please check:"
    echo "  1. Server is fully started (may take 2-3 minutes)"
    echo "  2. Your network supports the IP version"
    echo "  3. Firewall settings"
    exit 1
fi

echo ""
echo "Using server IP: $SERVER_IP"
echo ""

# Upload files
echo "[+] Uploading deployment files..."
if scp -r . root@$SERVER_IP:/opt/telegram-bot/deploy/; then
    echo "✓ Files uploaded successfully"
else
    echo "✗ Failed to upload files. Please check SSH connectivity."
    echo ""
    echo "Manual steps:"
    echo "1. SSH to server: ssh root@$SERVER_IP"
    echo "2. Create directories: mkdir -p /opt/telegram-bot/deploy"
    echo "3. Upload files manually or copy the complete-deployment-package.sh"
    exit 1
fi

# Deploy bot
echo "[+] Deploying bot on server..."
if ssh root@$SERVER_IP "cd /opt/telegram-bot/deploy && chmod +x *.sh && sudo ./complete-deployment-package.sh"; then
    echo "✓ Bot deployed successfully!"
else
    echo "✗ Deployment failed. Please check the logs."
    echo ""
    echo "Manual deployment steps:"
    echo "1. SSH to server: ssh root@$SERVER_IP"
    echo "2. Run: cd /opt/telegram-bot/deploy"
    echo "3. Run: sudo ./complete-deployment-package.sh"
    exit 1
fi

echo ""
echo "=========================================="
echo "  DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "=========================================="
echo ""
echo "Your bot is now accessible at:"
echo "  HTTP:  http://[2a01:4f8:1c1a:9cc1::1]"
echo "  HTTPS: https://[2a01:4f8:1c1a:9cc1::1]"
echo ""
echo "Next steps:"
echo "1. Configure your bot:"
echo "   ssh root@$SERVER_IP"
echo "   nano /opt/telegram-bot/config/.env"
echo "   # Add your bot token and API keys"
echo ""
echo "2. Restart the bot:"
echo "   cd /opt/telegram-bot"
echo "   sudo docker-compose -f deploy/docker-compose.hetzner.yml restart"
echo ""
echo "3. Check status:"
echo "   sudo docker-compose -f deploy/docker-compose.hetzner.yml ps"
echo ""
echo "=========================================="
