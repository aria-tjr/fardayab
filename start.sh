#!/bin/bash

# Start script for Telegram Bot
echo "Starting Telegram Bot..."

# Set Python path
export PYTHONPATH="/app/telegram_bot:$PYTHONPATH"

# Check which Python command is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found!"
    exit 1
fi

echo "Using Python command: $PYTHON_CMD"

# Install dependencies
echo "Installing dependencies..."
pip install -r telegram_bot/requirements.txt

# Create data directory if it doesn't exist
mkdir -p data

# Set working directory
cd telegram_bot

# Run the bot
echo "Starting bot..."
$PYTHON_CMD main.py
