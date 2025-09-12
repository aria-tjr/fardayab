#!/bin/bash
# Simple Contabo deployment solution
# This creates a minimal bot that you can deploy manually

echo "🚀 Creating Simple Contabo Bot Deployment"
echo "=========================================="

# Create a simple bot application
mkdir -p /tmp/contabo-bot
cd /tmp/contabo-bot

# Create main.py
cat > main.py << 'EOF'
import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

async def main():
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN", "your_bot_token_here"), 
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    @dp.message()
    async def handle_message(message):
        await message.answer(f"🤖 Bot is running on Contabo IPv6: 2a02:c207:3017:9335::1")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
aiogram==3.4.1
python-dotenv==1.0.0
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
EOF

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: "3.9"
services:
  telegram-bot:
    build: .
    container_name: telegram-bot
    environment:
      - TELEGRAM_BOT_TOKEN=your_bot_token_here
    restart: unless-stopped
    networks:
      - bot-network
    ports:
      - "2a02:c207:3017:9335::1:8080:8080"

networks:
  bot-network:
    driver: bridge
    enable_ipv6: true
    ipam:
      config:
        - subnet: 172.20.0.0/16
        - subnet: 2a02:c207:3017:9335::/64
EOF

# Create deployment script
cat > deploy.sh << 'EOF'
#!/bin/bash
echo "🚀 Deploying Contabo Bot..."

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configure IPv6
ip address add 2a02:c207:3017:9335::1/64 dev eth0

# Configure Docker for IPv6
mkdir -p /etc/docker
echo '{"ipv6": true, "fixed-cidr-v6": "2a02:c207:3017:9335::/64"}' > /etc/docker/daemon.json
systemctl restart docker

# Create project directory
mkdir -p /opt/telegram-bot
cp -r /tmp/contabo-bot/* /opt/telegram-bot/

# Deploy
cd /opt/telegram-bot
docker-compose up -d

echo "✅ Bot deployed successfully!"
echo "Access: http://[2a02:c207:3017:9335::1]:8080"
EOF

chmod +x deploy.sh

echo "✅ Simple bot deployment package created!"
echo "Location: /tmp/contabo-bot"
echo ""
echo "To deploy:"
echo "1. Copy the files to your Contabo server"
echo "2. Run: ./deploy.sh"
echo ""
echo "Files created:"
echo "- main.py (bot application)"
echo "- requirements.txt (dependencies)"
echo "- Dockerfile (container config)"
echo "- docker-compose.yml (orchestration)"
echo "- deploy.sh (deployment script)"
