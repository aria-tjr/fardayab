#!/bin/bash

# Start script for Telegram Bot
echo "Starting Telegram Bot..."

# Debug environment
echo "=== Environment Debug ==="
echo "Current directory: $(pwd)"
echo "Python version: $(python3 --version 2>/dev/null || echo 'Python3 not found')"
echo "Available in /usr/bin:"
ls -la /usr/bin/ | grep -E "(python|pip)" || echo "No Python found"
echo "========================="

# Check if we're in a Python environment
if command -v python3 &> /dev/null; then
    echo "Python3 found, proceeding..."
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
elif command -v python &> /dev/null; then
    echo "Python found, proceeding..."
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo "No Python found, trying to install..."
    # Try to install Python (this might not work in all environments)
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y python3 python3-pip
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    else
        echo "Error: Cannot install Python in this environment"
        exit 1
    fi
fi

# Set Python path
export PYTHONPATH="/app/telegram_bot:$PYTHONPATH"

# Install dependencies
echo "Installing dependencies..."
$PIP_CMD install -r telegram_bot/requirements.txt

# Create data directory
mkdir -p data

# Change to telegram_bot directory
cd telegram_bot

# Run the bot
echo "Starting bot with $PYTHON_CMD..."
$PYTHON_CMD main.py
