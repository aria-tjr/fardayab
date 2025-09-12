#!/bin/bash
# Download and deploy script for Contabo server
# Run this in your VNC console

echo "Downloading deployment script..."
curl -o /tmp/deploy.sh http://38.242.247.182:8080/contabo-complete-deployment.sh
chmod +x /tmp/deploy.sh
echo "Starting deployment..."
/tmp/deploy.sh
