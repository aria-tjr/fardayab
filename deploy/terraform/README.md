# Hetzner Server Creation with Terraform

This directory contains Terraform configuration to create a Hetzner server for the Telegram Bot deployment.

## Prerequisites

1. **Hetzner Cloud Account**: Sign up at https://console.hetzner.com
2. **API Token**: Create an API token in your Hetzner Cloud Console
3. **Terraform**: Install Terraform on your local machine
4. **SSH Key**: Have an SSH key pair ready

## Setup

1. **Copy the configuration file**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit terraform.tfvars** with your values:
   ```hcl
   hcloud_token = "your_actual_api_token_here"
   ssh_public_key = "~/.ssh/id_rsa.pub"
   ```

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

4. **Plan the deployment**:
   ```bash
   terraform plan
   ```

5. **Create the server**:
   ```bash
   terraform apply
   ```

## After Creation

Once the server is created, you'll see output with:
- IPv4 address
- IPv6 address
- SSH connection command

Then follow these steps:

1. **SSH to your server**:
   ```bash
   ssh root@YOUR_SERVER_IP
   ```

2. **Upload deployment files**:
   ```bash
   scp -r ../deploy/ root@YOUR_SERVER_IP:/opt/telegram-bot/
   ```

3. **Run deployment script**:
   ```bash
   cd /opt/telegram-bot/deploy
   sudo ./complete-deployment-package.sh
   ```

## Cleanup

To destroy the server when you're done:
```bash
terraform destroy
```

## Server Specifications

- **Image**: Ubuntu 22.04 LTS
- **Type**: CX22 (2 vCPU, 4GB RAM, 40GB SSD)
- **Location**: Nuremberg (nbg1)
- **Networking**: IPv4 + IPv6 enabled
- **Firewall**: Pre-configured for bot deployment
