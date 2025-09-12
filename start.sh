#!/bin/bash

# Start script for Telegram Bot
echo "Starting Telegram Bot..."

# Set Python path
export PYTHONPATH="/app/telegram_bot:$PYTHONPATH"

# Install dependencies
echo "Installing dependencies..."
pip install -r telegram_bot/requirements.txt

# Create data directory if it doesn't exist
mkdir -p data

# Set working directory
cd telegram_bot

# Run the bot
echo "Starting bot..."
python main.py
