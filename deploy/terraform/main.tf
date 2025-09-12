# Hetzner Cloud Terraform Configuration
# This creates a server for the Telegram Bot deployment

terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.0"
    }
  }
}

# Configure the Hetzner Cloud Provider
provider "hcloud" {
  token = var.hcloud_token
}

# Variables
variable "hcloud_token" {
  description = "Hetzner Cloud API Token"
  type        = string
  sensitive   = true
}

variable "ssh_public_key" {
  description = "SSH Public Key"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

# Create SSH Key
resource "hcloud_ssh_key" "telegram_bot_key" {
  name       = "telegram-bot-key"
  public_key = file(var.ssh_public_key)
}

# Create Server
resource "hcloud_server" "telegram_bot_server" {
  name        = "telegram-bot-server"
  image       = "ubuntu-22.04"
  server_type = "cx22"
  location    = "nbg1"
  ssh_keys    = [hcloud_ssh_key.telegram_bot_key.id]
  
  user_data = <<-EOF
    #!/bin/bash
    # Update system
    apt-get update
    apt-get upgrade -y
    
    # Install required packages
    apt-get install -y curl wget git ufw fail2ban htop
    
    # Configure IPv6
    if [ -f /etc/netplan/50-cloud-init.yaml ]; then
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
    
    echo "Server setup completed successfully!"
  EOF
}

# Output server information
output "server_ipv4" {
  value = hcloud_server.telegram_bot_server.ipv4_address
}

output "server_ipv6" {
  value = hcloud_server.telegram_bot_server.ipv6_address
}

output "server_name" {
  value = hcloud_server.telegram_bot_server.name
}

output "ssh_connection" {
  value = "ssh root@${hcloud_server.telegram_bot_server.ipv4_address}"
}
