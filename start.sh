#!/bin/bash

# Start script for Telegram Bot
echo "Starting Telegram Bot..."

# Debug environment
echo "=== Environment Debug ==="
echo "Current directory: $(pwd)"
echo "Python version: $(python3 --version 2>/dev/null || echo 'Python3 not found')"
echo "Available in /usr/bin:"
ls -la /usr/bin/ | grep -E "(python|pip)" || echo "No Python found"
echo "Available in /bin:"
ls -la /bin/ | grep -E "(python|pip)" || echo "No Python found in /bin"
echo "========================="

# Try to install Python if not available
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found, attempting to install..."
    
    # Update package lists
    if command -v apt-get &> /dev/null; then
        echo "Using apt-get to install Python..."
        apt-get update
        apt-get install -y python3 python3-pip python3-venv
    elif command -v yum &> /dev/null; then
        echo "Using yum to install Python..."
        yum update -y
        yum install -y python3 python3-pip
    elif command -v apk &> /dev/null; then
        echo "Using apk to install Python..."
        apk update
        apk add python3 py3-pip
    else
        echo "No package manager found, trying to use existing Python..."
        # Try to find any Python executable
        PYTHON_CMD=$(find /usr -name "python*" -type f -executable 2>/dev/null | head -1)
        if [ -n "$PYTHON_CMD" ]; then
            echo "Found Python at: $PYTHON_CMD"
            ln -s "$PYTHON_CMD" /usr/bin/python3
        else
            echo "Error: Cannot install Python and no Python found"
            exit 1
        fi
    fi
fi

# Verify Python is now available
if command -v python3 &> /dev/null; then
    echo "Python3 is now available: $(python3 --version)"
else
    echo "Error: Python3 still not available after installation attempt"
    exit 1
fi

# Set Python path
export PYTHONPATH="/app/telegram_bot:$PYTHONPATH"

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Create data directory
mkdir -p data

# Run the bot using the root main.py
echo "Starting bot..."
python3 main.py
