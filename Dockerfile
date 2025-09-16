# بات سیگنال‌دهنده کریپتو - Docker Image
FROM python:3.11-slim

# نصب وابستگی‌های سیستمی
RUN apt-get update && apt-get install -y \
    build-essential \
    libta-lib-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# تنظیم دایرکتری کاری
WORKDIR /app

# کپی فایل‌های requirements
COPY requirements.txt .

# نصب وابستگی‌های Python
RUN pip install --no-cache-dir -r requirements.txt

# کپی کد برنامه
COPY src/ ./src/
COPY run_bot.py .

# ایجاد کاربر غیر root برای امنیت
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app
USER botuser

# تنظیم متغیرهای محیطی
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# پورت پیش‌فرض (در صورت نیاز)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.config import Config; Config.validate()" || exit 1

# دستور اجرا
CMD ["python", "-m", "src.main"]
