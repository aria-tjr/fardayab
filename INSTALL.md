# 🚀 راهنمای نصب کامل - بات سیگنال کریپتو

این راهنما شما را قدم به قدم از طریق فرآیند نصب و راه‌اندازی بات سیگنال کریپتو راهنمایی می‌کند.

## 📋 پیش‌نیازهای سیستم

### سیستم‌عامل پشتیبانی‌شده:
- ✅ Windows 10/11
- ✅ macOS 10.15+
- ✅ Ubuntu 18.04+
- ✅ Debian 10+
- ✅ CentOS 7+

### نرم‌افزارهای مورد نیاز:
```bash
# Python 3.11 یا بالاتر
python --version
# باید نمایش دهد: Python 3.11.x یا بالاتر

# Git
git --version

# pip (معمولاً با Python نصب می‌شود)
pip --version
```

## 🔧 نصب Python

### Windows:
1. از [python.org](https://python.org/downloads/) دانلود کنید
2. در حین نصب "Add Python to PATH" را فعال کنید
3. Command Prompt را باز کرده و تست کنید:
```cmd
python --version
pip --version
```

### macOS:
```bash
# با Homebrew (توصیه می‌شود)
brew install python@3.11

# یا از python.org دانلود کنید
```

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv
```

### CentOS/RHEL:
```bash
sudo yum install python3.11 python3.11-pip
```

## 📦 دانلود و آماده‌سازی پروژه

### 1. دانلود پروژه
```bash
# کلون از Git (اگر در دسترس باشد)
git clone <repository-url>
cd "fardayab copy"

# یا دانلود ZIP و استخراج
```

### 2. ایجاد محیط مجازی (Virtual Environment)
```bash
# ایجاد محیط مجازی
python -m venv crypto_bot_env

# فعال‌سازی محیط مجازی
# Windows:
crypto_bot_env\Scripts\activate

# macOS/Linux:
source crypto_bot_env/bin/activate

# تأیید فعال‌سازی (باید (crypto_bot_env) در ابتدای خط ظاهر شود)
```

### 3. بروزرسانی pip
```bash
python -m pip install --upgrade pip
```

## 🔨 نصب وابستگی‌ها

### 1. نصب پکیج‌های اصلی
```bash
pip install -r requirements.txt
```

### 2. رفع مشکلات احتمالی

#### مشکل TA-Lib:

**Windows:**
```bash
# دانلود wheel file مناسب از:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

# مثال برای Python 3.11, 64-bit:
pip install TA_Lib-0.4.25-cp311-cp311-win_amd64.whl
```

**macOS:**
```bash
# نصب با Homebrew
brew install ta-lib

# سپس نصب پکیج Python
pip install TA-Lib
```

**Ubuntu/Debian:**
```bash
# نصب کتابخانه‌های سیستمی
sudo apt-get install libta-lib-dev

# نصب پکیج Python
pip install TA-Lib
```

**CentOS/RHEL:**
```bash
# نصب کتابخانه‌های سیستمی
sudo yum install ta-lib-devel

# نصب پکیج Python
pip install TA-Lib
```

#### مشکل matplotlib (در صورت خطا):
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install tkinter
```

### 3. تست نصب وابستگی‌ها
```bash
python -c "import ccxt, mplfinance, openai, aiogram; print('همه پکیج‌ها با موفقیت نصب شدند')"
```

## ⚙️ تنظیم متغیرهای محیطی

### 1. کپی فایل نمونه
```bash
# Windows
copy env.example .env

# macOS/Linux
cp env.example .env
```

### 2. ویرایش فایل .env
```bash
# با notepad در Windows
notepad .env

# با nano در macOS/Linux
nano .env

# یا با هر ویرایشگر متنی دیگر
```

### 3. تکمیل اطلاعات ضروری

#### الزامی - توکن بات تلگرام:
1. به [@BotFather](https://t.me/botfather) مراجعه کنید
2. دستور `/newbot` را ارسال کنید
3. نام بات را وارد کنید (مثال: "My Crypto Signal Bot")
4. نام کاربری بات را وارد کنید (باید به _bot ختم شود)
5. توکن دریافتی را در `TELEGRAM_BOT_TOKEN` قرار دهید

#### الزامی - شناسه کانال تلگرام:
1. کانال جدید ایجاد کنید
2. بات را به عنوان ادمین اضافه کنید
3. برای دریافت شناسه کانال:
   - پیام `/start` را در کانال ارسال کنید
   - یا از [@userinfobot](https://t.me/userinfobot) استفاده کنید
4. شناسه را در `TELEGRAM_CHANNEL_ID` قرار دهید

#### الزامی - کلید OpenAI:
1. به [platform.openai.com](https://platform.openai.com) مراجعه کنید
2. ثبت‌نام/ورود کنید
3. به بخش API Keys بروید
4. کلید جدید ایجاد کنید
5. کلید را در `OPENAI_API_KEY` قرار دهید

#### نمونه فایل .env تکمیل شده:
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789
TELEGRAM_CHANNEL_ID=-1001234567890
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# سایر تنظیمات اختیاری...
CONFIDENCE_THRESHOLD=0.65
MIN_VOLUME_USD=5000000
DEFAULT_LANGUAGE=fa
```

## 🧪 تست اولیه سیستم

### 1. تست پیکربندی
```bash
python -c "from src.config import Config; Config.validate(); print('پیکربندی معتبر است')"
```

### 2. تست کامل سیستم
```bash
python -m src.main --test
```

خروجی موفق باید شامل موارد زیر باشد:
- ✅ Exchange test: Found X valid pairs
- ✅ Signal generation test: LONG/SHORT signal generated
- ✅ Content generation test: education_tip generated
- ✅ Chart generation test: Chart generated successfully

### 3. تست اتصال تلگرام
```bash
# تست ارسال پیام به کانال
python -c "
import asyncio
from src.telegram.bot import TelegramBot
async def test():
    bot = TelegramBot()
    await bot.bot.send_message(bot.channel_id, '🧪 تست اتصال موفق')
asyncio.run(test())
"
```

## 🚀 اجرای بات

### 1. اجرای معمولی (Foreground)
```bash
python -m src.main
```

### 2. اجرای در پس‌زمینه

#### Windows (با PowerShell):
```powershell
Start-Process python -ArgumentList "-m src.main" -WindowStyle Hidden
```

#### macOS/Linux:
```bash
# با nohup
nohup python -m src.main > bot.log 2>&1 &

# یا با screen
screen -S crypto_bot
python -m src.main
# Ctrl+A, D برای detach
```

### 3. اجرای به عنوان سرویس

#### Ubuntu/Debian (systemd):
```bash
# ایجاد فایل سرویس
sudo nano /etc/systemd/system/crypto-bot.service
```

محتوای فایل:
```ini
[Unit]
Description=Crypto Signal Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/fardayab copy
Environment=PATH=/path/to/crypto_bot_env/bin
ExecStart=/path/to/crypto_bot_env/bin/python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

فعال‌سازی سرویس:
```bash
sudo systemctl daemon-reload
sudo systemctl enable crypto-bot
sudo systemctl start crypto-bot
sudo systemctl status crypto-bot
```

## 📊 نظارت و مدیریت

### 1. مشاهده لاگ‌ها
```bash
# لاگ‌های زنده
tail -f crypto_bot.log

# جستجوی خطاها
grep "ERROR" crypto_bot.log

# آخرین 100 خط
tail -100 crypto_bot.log
```

### 2. بررسی وضعیت
```bash
# تست سریع اتصال
python -c "
import asyncio
from src.exchange.data_fetcher import ExchangeDataFetcher
async def test():
    fetcher = ExchangeDataFetcher()
    pairs = await fetcher.get_volume_filtered_pairs()
    print(f'تعداد جفت ارز معتبر: {len(pairs)}')
    await fetcher.close()
asyncio.run(test())
"
```

### 3. راه‌اندازی مجدد
```bash
# متوقف کردن (اگر در foreground اجرا می‌شود)
Ctrl+C

# یا کشتن پروسه
pkill -f "python -m src.main"

# اجرای مجدد
python -m src.main
```

## 🔧 عیب‌یابی مشکلات رایج

### خطای "ModuleNotFoundError"
```bash
# بررسی محیط مجازی
which python
pip list

# نصب مجدد وابستگی‌ها
pip install -r requirements.txt --force-reinstall
```

### خطای "Permission Denied"
```bash
# Linux/macOS
chmod +x crypto_bot_env/bin/python

# Windows: اجرا به عنوان Administrator
```

### خطای اتصال به اینترنت
```bash
# تست اتصال
ping google.com
curl -I https://api.telegram.org

# بررسی proxy/firewall
```

### خطای حافظه کم
```bash
# بررسی استفاده از حافظه
free -h  # Linux
vm_stat  # macOS

# کاهش تعداد نمودارها
export MPLBACKEND=Agg
```

## 🔄 بروزرسانی

### 1. بروزرسانی کد
```bash
git pull origin main
# یا دانلود نسخه جدید
```

### 2. بروزرسانی وابستگی‌ها
```bash
pip install -r requirements.txt --upgrade
```

### 3. بروزرسانی دیتابیس
```bash
# backup قبل از بروزرسانی
cp crypto_signals.db crypto_signals.db.backup

# اجرای migration (در صورت وجود)
python -m src.storage.migrate
```

## 🆘 دریافت کمک

### مشکلات فنی:
1. **لاگ‌ها را بررسی کنید**: `tail -100 crypto_bot.log`
2. **تست کامل اجرا کنید**: `python -m src.main --test`
3. **تنظیمات را دوباره بررسی کنید**: فایل `.env`

### اطلاعات مفید برای گزارش مشکل:
```bash
# اطلاعات سیستم
python --version
pip --version
uname -a  # Linux/macOS
systeminfo  # Windows

# وضعیت پکیج‌ها
pip list | grep -E "(ccxt|aiogram|openai|mplfinance)"

# آخرین خطاها
tail -50 crypto_bot.log | grep ERROR
```

---

## ✅ چک‌لیست نصب

- [ ] Python 3.11+ نصب شده
- [ ] محیط مجازی ایجاد و فعال شده
- [ ] تمام وابستگی‌ها نصب شده
- [ ] فایل .env ایجاد و تکمیل شده
- [ ] توکن بات تلگرام معتبر
- [ ] شناسه کانال تلگرام صحیح
- [ ] کلید OpenAI فعال
- [ ] تست `--test` موفق
- [ ] اولین اجرای بات موفق
- [ ] پیام خوش‌آمدگویی در کانال ارسال شده

**🎉 تبریک! بات شما آماده فعالیت است.**