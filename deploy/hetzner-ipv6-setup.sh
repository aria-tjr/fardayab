#!/usr/bin/env bash
set -euo pipefail

# Hetzner IPv6 Configuration Script
# This script configures IPv6 networking for the Hetzner server

echo "[+] Configuring IPv6 networking for Hetzner server"

# Detect network interface
INTERFACE=$(ip link show | grep -E "^2:" | head -1 | cut -d: -f2 | tr -d ' ')
if [ -z "$INTERFACE" ]; then
    INTERFACE="eth0"
    echo "[!] Could not detect network interface, using default: $INTERFACE"
else
    echo "[+] Detected network interface: $INTERFACE"
fi

# IPv6 configuration
IPV6_SUBNET="2a01:4f8:1c1a:9cc1::/64"
IPV6_ADDRESS="2a01:4f8:1c1a:9cc1::1"
IPV6_GATEWAY="fe80::1"

echo "[+] Configuring IPv6 address: $IPV6_ADDRESS"

# Detect OS and configure accordingly
if [ -f /etc/debian_version ]; then
    echo "[+] Detected Debian/Ubuntu system"
    
    # Backup original interfaces file
    cp /etc/network/interfaces /etc/network/interfaces.backup.$(date +%Y%m%d_%H%M%S)
    
    # Add IPv6 configuration to interfaces file
    cat >> /etc/network/interfaces << EOF

# IPv6 configuration for Hetzner
iface $INTERFACE inet6 static
    address $IPV6_ADDRESS
    netmask 64
    gateway $IPV6_GATEWAY
EOF

    echo "[+] IPv6 configuration added to /etc/network/interfaces"
    
elif [ -f /etc/redhat-release ]; then
    echo "[+] Detected CentOS/RHEL system"
    
    # Configure IPv6 for CentOS
    cat > /etc/sysconfig/network-scripts/ifcfg-$INTERFACE << EOF
# IPv6 configuration for Hetzner
IPV6INIT=yes
IPV6ADDR=$IPV6_ADDRESS/64
IPV6_DEFAULTGW=$IPV6_GATEWAY
EOF

    echo "[+] IPv6 configuration added to /etc/sysconfig/network-scripts/ifcfg-$INTERFACE"
    
else
    echo "[!] Unsupported OS detected. Please configure IPv6 manually:"
    echo "    Address: $IPV6_ADDRESS/64"
    echo "    Gateway: $IPV6_GATEWAY"
    exit 1
fi

# Enable IPv6 forwarding
echo 'net.ipv6.conf.all.forwarding=1' >> /etc/sysctl.conf
sysctl -p

# Configure firewall for IPv6
echo "[+] Configuring IPv6 firewall rules"

# Install iptables-persistent if not present
if ! dpkg -l | grep -q iptables-persistent; then
    apt-get update
    apt-get install -y iptables-persistent
fi

# Add IPv6 firewall rules
ip6tables -A INPUT -p tcp --dport 80 -j ACCEPT
ip6tables -A INPUT -p tcp --dport 443 -j ACCEPT
ip6tables -A INPUT -p tcp --dport 8080 -j ACCEPT
ip6tables -A INPUT -p tcp --dport 8443 -j ACCEPT

# Save IPv6 rules
ip6tables-save > /etc/iptables/rules.v6

echo "[+] IPv6 firewall rules configured"

# Restart networking
echo "[+] Restarting networking service"
if [ -f /etc/debian_version ]; then
    systemctl restart networking
else
    systemctl restart network
fi

# Wait for network to come up
sleep 5

# Test IPv6 connectivity
echo "[+] Testing IPv6 connectivity"
if ping6 -c 3 $IPV6_GATEWAY >/dev/null 2>&1; then
    echo "[+] IPv6 connectivity test successful"
else
    echo "[!] IPv6 connectivity test failed. Please check configuration."
fi

# Display current IPv6 configuration
echo "[+] Current IPv6 configuration:"
ip -6 addr show $INTERFACE

echo "[+] IPv6 configuration completed successfully!"
echo "[!] Please verify the configuration and restart the server if needed."
