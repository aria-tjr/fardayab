# Telegram Content Factory Bot (aiogram + OpenAI)

بات تلگرام خودکار برای تولید و انتشار محتوا (فقط فارسی):
- جمع‌آوری داده از APIها (کریپتو/ارز، خبر، ترند، ورزش، آب‌وهوا)
- تولید متن‌های حرفه‌ای فارسی با OpenAI
- زمان‌بندی انتشار روزانه با APScheduler
- گزارش روزانه برای ادمین + پیشنهاد زمان انتشار
- معماری ماژولار، قابل توسعه، Docker-ready

## نصب و اجرا

### پیش‌نیازها
- Python 3.12+
- توکن Bot تلگرام
- کلیدهای API اختیاری/توصیه‌شده: OpenWeather, NewsAPI, TheSportsDB, API-Football

### تنظیمات
1. فایل نمونه را کپی و مقادیر را تنظیم کنید:
```
cp config/.env.example config/.env
```
2. مقادیر مهم:
- `TELEGRAM_BOT_TOKEN`: توکن ربات
- `TELEGRAM_CHANNEL_ID`: آیدی کانال (مثلاً `@your_channel` یا عددی)
- `ADMIN_USER_ID`: عدد آی‌دی ادمین برای گزارش
- `OPENAI_API_KEY`: کلید OpenAI
- `OPENAI_MODEL`: مدل مانند `gpt-4o-mini` (قابل تغییر)
- `TIMEZONE`: مانند `Asia/Tehran`
- `DAILY_RUN_AT`: زمان اجرای روزانه مانند `22:00`

### اجرای محلی
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m telegram_bot.main
```

### اجرای با Docker
```
docker build -t telegram-bot .
docker run --env-file=config/.env --name tg-bot --restart=unless-stopped telegram-bot
```

## فرمان‌های ادمین (PV)
- `/start` معرفی ربات
- `/run` اجرای فوری وظیفه روزانه
- `/status` وضعیت زمان‌بندی و آخرین اجرا
- `/settime HH:MM` تغییر زمان اجرای روزانه
- `/settz Area/City` تغییر منطقه زمانی (مثال: Asia/Tehran)

## نکات
- برای A/B تست، ربات دو نسخه متن می‌سازد و یکی را برای همان روز انتخاب می‌کند و لاگ می‌کند. (اندازه‌گیری بازدید در Bot API محدود است.)
- اگر APIها در دسترس نباشند، ربات با داده‌های موجود/جایگزین، متن ایمن می‌سازد.
- نام مدل OpenAI از طریق `OPENAI_MODEL` قابل تغییر است.

## ساختار پروژه
```
telegram_bot/
  config/
  data/
  modules/
  ai/
  scheduler/
  handlers/
  utils/
  main.py
  requirements.txt
  Dockerfile
  README.md
```
