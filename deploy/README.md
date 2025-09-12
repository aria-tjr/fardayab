# Hetzner Telegram Bot Deployment

This directory contains deployment scripts and configurations for deploying the Telegram bot on a Hetzner server with IPv6 support.

## IPv6 Configuration

The deployment uses the IPv6 subnet `2a01:4f8:1c1a:9cc1::/64` with the primary address `2a01:4f8:1c1a:9cc1::1`.

## Files

- `hetzner-deploy.sh` - Complete deployment script with system setup
- `quick-deploy.sh` - Quick deployment for pre-configured servers
- `hetzner-ipv6-setup.sh` - IPv6 networking configuration
- `docker-compose.hetzner.yml` - Docker Compose configuration for Hetzner
- `nginx.conf` - Nginx configuration with IPv6 support

## Quick Start

### 1. Complete Deployment (New Server)

```bash
# Upload files to server
scp -r deploy/ root@your-server-ip:/opt/telegram-bot/

# SSH to server
ssh root@your-server-ip

# Run complete deployment
cd /opt/telegram-bot/deploy
chmod +x *.sh
./hetzner-deploy.sh
```

### 2. Quick Deployment (Existing Server)

```bash
# Upload files to server
scp -r deploy/ root@your-server-ip:/opt/telegram-bot/

# SSH to server
ssh root@your-server-ip

# Run quick deployment
cd /opt/telegram-bot/deploy
chmod +x *.sh
./quick-deploy.sh
```

## Configuration

### Environment Variables

Create `/opt/telegram-bot/config/.env` with your configuration:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here
DATABASE_URL=sqlite:///app/data/bot.db
TIMEZONE=Asia/Tehran
DAILY_RUN_AT=09:00
NEWS_API_KEY=your_news_api_key
WEATHER_API_KEY=your_weather_api_key
CRYPTO_API_KEY=your_crypto_api_key
HOST=0.0.0.0
PORT=8080
DEBUG=false
```

### IPv6 Network Configuration

The deployment automatically configures IPv6 networking. If manual configuration is needed:

1. **Debian/Ubuntu**: Edit `/etc/network/interfaces`
2. **CentOS**: Edit `/etc/sysconfig/network-scripts/ifcfg-eth0`

## Services

### Docker Compose Services

- `telegram-bot` - Main bot application
- `nginx` - Reverse proxy with SSL termination
- `watchtower` - Automatic container updates

### System Services

- `telegram-bot.service` - Systemd service for the bot
- `fail2ban` - Intrusion prevention
- `ufw` - Firewall management

## Monitoring

### Logs

- Application logs: `/opt/telegram-bot/data/logs/`
- Docker logs: `docker-compose -f /opt/telegram-bot/deploy/docker-compose.hetzner.yml logs -f`
- System logs: `journalctl -u telegram-bot.service`

### Health Checks

- HTTP: `http://[2a01:4f8:1c1a:9cc1::1]/health`
- HTTPS: `https://[2a01:4f8:1c1a:9cc1::1]/health`

### Monitoring Script

The deployment includes a monitoring script that runs every 5 minutes:

```bash
/opt/telegram-bot/monitor.sh
```

## Backup

### Automatic Backup

Daily backups are created at 2 AM:

```bash
/opt/telegram-bot/backup.sh
```

### Manual Backup

```bash
cd /opt/telegram-bot
./backup.sh
```

## Security

### Firewall Rules

- SSH (port 22)
- HTTP (port 80)
- HTTPS (port 443)
- Bot API (port 8080)

### SSL/TLS

- Self-signed certificates are generated automatically
- For production, replace with valid certificates

### Fail2ban

- SSH protection
- Nginx HTTP auth protection
- Custom rules for bot endpoints

## Troubleshooting

### Check IPv6 Connectivity

```bash
ping6 2a01:4f8:1c1a:9cc1::1
```

### Check Docker Services

```bash
docker ps
docker-compose -f /opt/telegram-bot/deploy/docker-compose.hetzner.yml ps
```

### Check System Services

```bash
systemctl status telegram-bot.service
systemctl status nginx
systemctl status fail2ban
```

### View Logs

```bash
# Application logs
tail -f /opt/telegram-bot/data/logs/monitor.log

# Docker logs
docker-compose -f /opt/telegram-bot/deploy/docker-compose.hetzner.yml logs -f

# System logs
journalctl -u telegram-bot.service -f
```

## Maintenance

### Update Bot

```bash
cd /opt/telegram-bot
docker-compose -f deploy/docker-compose.hetzner.yml pull
docker-compose -f deploy/docker-compose.hetzner.yml up -d
```

### Restart Services

```bash
systemctl restart telegram-bot.service
```

### Clean Up

```bash
# Remove old Docker images
docker system prune -a

# Clean old backups
find /opt/telegram-bot/data/backups -mtime +30 -delete
```

## Access URLs

- **HTTP**: `http://[2a01:4f8:1c1a:9cc1::1]`
- **HTTPS**: `https://[2a01:4f8:1c1a:9cc1::1]`
- **Health Check**: `https://[2a01:4f8:1c1a:9cc1::1]/health`

## Support

For issues or questions:

1. Check the logs first
2. Verify IPv6 connectivity
3. Check Docker service status
4. Review firewall rules
5. Check system resources (CPU, memory, disk)
