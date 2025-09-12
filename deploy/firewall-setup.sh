#!/usr/bin/env bash
set -euo pipefail

# Firewall Configuration Script for Hetzner IPv6 Deployment
# This script configures UFW and iptables for IPv6 access

echo "[+] Configuring firewall for Hetzner IPv6 deployment"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# IPv6 configuration
IPV6_SUBNET="2a01:4f8:1c1a:9cc1::/64"
IPV6_ADDRESS="2a01:4f8:1c1a:9cc1::1"

# Install required packages
echo "[+] Installing required packages"
apt-get update
apt-get install -y ufw iptables-persistent

# Reset UFW to defaults
echo "[+] Resetting UFW configuration"
ufw --force reset

# Set default policies
echo "[+] Setting default policies"
ufw default deny incoming
ufw default allow outgoing

# IPv4 rules
echo "[+] Configuring IPv4 rules"
ufw allow ssh
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 8080/tcp comment 'Bot API'

# IPv6 rules
echo "[+] Configuring IPv6 rules"
ufw allow from 2a01:4f8:1c1a:9cc1::/64 to any port 22 comment 'SSH IPv6'
ufw allow from 2a01:4f8:1c1a:9cc1::/64 to any port 80 comment 'HTTP IPv6'
ufw allow from 2a01:4f8:1c1a:9cc1::/64 to any port 443 comment 'HTTPS IPv6'
ufw allow from 2a01:4f8:1c1a:9cc1::/64 to any port 8080 comment 'Bot API IPv6'

# Allow localhost
ufw allow from 127.0.0.1
ufw allow from ::1

# Rate limiting rules
echo "[+] Configuring rate limiting"
ufw limit ssh/tcp comment 'SSH rate limit'

# Enable UFW
echo "[+] Enabling UFW firewall"
ufw --force enable

# Configure iptables for IPv6
echo "[+] Configuring iptables for IPv6"

# IPv6 rules
ip6tables -A INPUT -i lo -j ACCEPT
ip6tables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
ip6tables -A INPUT -p icmpv6 -j ACCEPT

# Allow SSH
ip6tables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
ip6tables -A INPUT -p tcp --dport 80 -j ACCEPT
ip6tables -A INPUT -p tcp --dport 443 -j ACCEPT
ip6tables -A INPUT -p tcp --dport 8080 -j ACCEPT

# Allow from Hetzner subnet
ip6tables -A INPUT -s 2a01:4f8:1c1a:9cc1::/64 -j ACCEPT

# Drop all other traffic
ip6tables -A INPUT -j DROP

# Save iptables rules
echo "[+] Saving iptables rules"
ip6tables-save > /etc/iptables/rules.v6

# Create iptables service
echo "[+] Creating iptables service"
cat > /etc/systemd/system/iptables-restore.service << 'EOF'
[Unit]
Description=Restore iptables rules
Before=network-pre.target

[Service]
Type=oneshot
ExecStart=/sbin/iptables-restore /etc/iptables/rules.v4
ExecStart=/sbin/ip6tables-restore /etc/iptables/rules.v6
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable iptables service
systemctl enable iptables-restore.service

# Configure fail2ban for additional security
echo "[+] Configuring fail2ban"
apt-get install -y fail2ban

# Create fail2ban configuration
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 ::1 2a01:4f8:1c1a:9cc1::/64

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

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
EOF

# Create nginx fail2ban filters
cat > /etc/fail2ban/filter.d/nginx-limit-req.conf << 'EOF'
[Definition]
failregex = limiting requests, excess: .* by zone .*, client: <HOST>
ignoreregex =
EOF

# Start and enable fail2ban
systemctl enable fail2ban
systemctl restart fail2ban

# Display firewall status
echo "[+] Firewall configuration completed"
echo ""
echo "UFW Status:"
ufw status verbose

echo ""
echo "IPv6 iptables rules:"
ip6tables -L -n

echo ""
echo "Fail2ban status:"
fail2ban-client status

echo ""
echo "Firewall configuration completed successfully!"
echo "IPv6 address: $IPV6_ADDRESS"
echo "Allowed ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 8080 (Bot API)"
