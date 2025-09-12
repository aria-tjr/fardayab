FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY telegram_bot/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the entire project
COPY . /app

# Create data directory
RUN mkdir -p /app/data

# Set working directory to telegram_bot
WORKDIR /app/telegram_bot

# Set Python path
ENV PYTHONPATH="/app/telegram_bot:$PYTHONPATH"

# Run the bot
CMD ["python3", "main.py"]
