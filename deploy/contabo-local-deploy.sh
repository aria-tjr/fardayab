#!/bin/bash
# Local deployment script for Contabo server
# This script will try different methods to connect and deploy

set -euo pipefail

echo "🚀 Contabo Bot Deployment - Local Script"
echo "Server: 38.242.247.182"
echo "IPv6: 2a02:c207:3017:9335::1"
echo "=========================================="

# Try different connection methods
echo "Trying different connection methods..."

# Method 1: Direct IP
echo "Method 1: Direct IP connection"
if sshpass -p 'asTonvilla13' ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@38.242.247.182 "echo 'Connected via direct IP'" 2>/dev/null; then
    echo "✅ Connected via direct IP"
    CONNECTION_METHOD="38.242.247.182"
elif sshpass -p 'asTonvilla13' ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@vmd179335.contaboserver.net "echo 'Connected via hostname'" 2>/dev/null; then
    echo "✅ Connected via hostname"
    CONNECTION_METHOD="vmd179335.contaboserver.net"
elif sshpass -p 'asTonvilla13' ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@207.180.255.168 "echo 'Connected via VNC IP'" 2>/dev/null; then
    echo "✅ Connected via VNC IP"
    CONNECTION_METHOD="207.180.255.168"
else
    echo "❌ All connection methods failed"
    echo "The DNS resolution issue is preventing SSH connections."
    echo "Please use the VNC console method instead."
    exit 1
fi

echo "Using connection method: $CONNECTION_METHOD"

# Upload deployment script
echo "Uploading deployment script..."
scp -o ConnectTimeout=30 -o StrictHostKeyChecking=no /Users/ariatajeri/fardayab/deploy/contabo-complete-deployment.sh root@$CONNECTION_METHOD:/tmp/

# Execute deployment
echo "Executing deployment..."
sshpass -p 'asTonvilla13' ssh -o ConnectTimeout=30 -o StrictHostKeyChecking=no root@$CONNECTION_METHOD "chmod +x /tmp/contabo-complete-deployment.sh && /tmp/contabo-complete-deployment.sh"

echo "🎉 Deployment completed successfully!"
echo "Your bot is now running on:"
echo "  HTTP: http://[2a02:c207:3017:9335::1]"
echo "  HTTPS: https://[2a02:c207:3017:9335::1]"
echo "  Health: https://[2a02:c207:3017:9335::1]/health"
