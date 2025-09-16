# 🤖 بات سیگنال‌دهنده کریپتو - کاملاً خودکار

یک بات تلگرام کاملاً خودکار برای تولید سیگنال‌های معاملاتی کریپتوکارنسی و محتوای آموزشی با تمرکز بر **Win Rate** و **تعداد سیگنال‌ها**.

## 🎯 ویژگی‌های کلیدی

### ⚡ سیستم سیگنال‌دهی
- **روزانه 2-5 سیگنال باکیفیت** با تمرکز بر Win Rate
- **دو استراتژی ترکیبی**: Trend Following + Mean Reversion
- **تحلیل موازی** تایم‌فریم‌های 5m و 15m
- **10 ارز لیکویید برتر**: BTC, ETH, SOL, BNB, XRP, ADA, MATIC, LTC, AVAX, OP
- **اندیکاتورهای حرفه‌ای**: EMA(21/50/200), RSI, Donchian Channel, Bollinger Bands, ATR

### 🤖 اتوماسیون کامل
- **هر 5 دقیقه**: اسکن بازار و تولید سیگنال
- **09:00 روزانه**: خلاصه بازار کریپتو
- **13:00 روزانه**: تحلیل آلتکوین منتخب
- **19:00 روزانه**: نکات آموزشی
- **جمعه عصر**: گزارش هفتگی + پست تبلیغی

### 📊 تولید محتوای هوشمند
- استفاده از **OpenAI GPT-4** برای تولید محتوا
- **7 نوع محتوای متنوع**: سیگنال، تحلیل بازار، آموزش، گزارش عملکرد و...
- **لحن حرفه‌ای** با ایموجی‌ها و هشتگ‌های مناسب
- **گزارش‌دهی شفاف** Win Rate و آمار عملکرد

### 📈 نمودارهای تعاملی
- چارت‌های زنده با **mplfinance**
- نمایش اندیکاتورها و سطوح SL/TP
- چارت‌های عملکرد و تحلیل بازار

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها
```bash
# Python 3.11 یا بالاتر
python --version

# Git برای کلون پروژه
git --version
```

### 1. دانلود پروژه
```bash
git clone <repository-url>
cd "fardayab copy"
```

### 2. نصب وابستگی‌ها
```bash
# نصب پکیج‌های Python
pip install -r requirements.txt

# در صورت خطا با TA-Lib:
# Windows: دانلود wheel file از https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# macOS: brew install ta-lib
# Linux: sudo apt-get install libta-lib-dev
```

### 3. تنظیم متغیرهای محیطی
```bash
# کپی فایل نمونه
cp env.example .env

# ویرایش فایل .env با اطلاعات خود
nano .env
```

### 4. تنظیمات ضروری در .env

#### الزامی:
```env
# توکن بات تلگرام (از @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789

# شناسه کانال تلگرام (از @userinfobot)
TELEGRAM_CHANNEL_ID=-1001234567890

# کلید API OpenAI (از platform.openai.com)
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

#### اختیاری (مقادیر پیش‌فرض موجود):
```env
# تنظیمات سیگنال‌دهی
CONFIDENCE_THRESHOLD=0.65
MIN_VOLUME_USD=5000000
TREND_RSI_LONG_MIN=53
TREND_RSI_SHORT_MAX=47

# زمان‌بندی انتشار محتوا
MARKET_SUMMARY_TIME=09:00
EDUCATION_TIME=19:00
ALTCOIN_SPOTLIGHT_TIME=13:00
```

### 5. راه‌اندازی بات تلگرام

#### ایجاد بات:
1. به [@BotFather](https://t.me/botfather) در تلگرام مراجعه کنید
2. دستور `/newbot` را ارسال کنید
3. نام و username برای بات انتخاب کنید
4. توکن دریافتی را در `TELEGRAM_BOT_TOKEN` قرار دهید

#### ایجاد کانال:
1. کانال جدید در تلگرام ایجاد کنید
2. بات را به عنوان ادمین به کانال اضافه کنید
3. شناسه کانال را در `TELEGRAM_CHANNEL_ID` قرار دهید

### 6. اجرای بات
```bash
# اجرای معمولی
python -m src.main

# تست عملکرد قبل از اجرا
python -m src.main --test

# اجرای در پس‌زمینه (Linux/macOS)
nohup python -m src.main &

# اجرای با Docker (اختیاری)
docker build -t crypto-signal-bot .
docker run -d --env-file .env crypto-signal-bot
```

## 📋 ساختار پروژه

```
fardayab copy/
├── src/
│   ├── main.py              # نقطه ورود اصلی
│   ├── config.py            # تنظیمات و پیکربندی
│   ├── strategies/          # استراتژی‌های سیگنال‌دهی
│   │   ├── signal_generator.py
│   │   ├── indicators.py
│   │   └── ultra_high_winrate_generator.py
│   ├── content/             # تولید محتوا
│   │   └── content_generator.py
│   ├── telegram/            # بات تلگرام
│   │   └── bot.py
│   ├── scheduler/           # زمان‌بندی وظایف
│   │   └── scheduler.py
│   ├── charts/              # تولید نمودار
│   │   └── chart_generator.py
│   ├── exchange/            # دریافت داده بازار
│   │   └── data_fetcher.py
│   └── storage/             # دیتابیس
│       └── models.py
├── requirements.txt         # وابستگی‌های Python
├── env.example             # نمونه تنظیمات محیطی
├── README.md               # مستندات (این فایل)
└── crypto_bot.log          # فایل لاگ
```

## ⚙️ تنظیمات پیشرفته

### استراتژی‌های سیگنال‌دهی

#### Trend Following:
- **LONG**: قیمت > EMA200 + کراس صعودی EMA21/50 + RSI>53 + بریک‌اوت Donchian
- **SHORT**: قیمت < EMA200 + کراس نزولی EMA21/50 + RSI<47 + شکست Donchian
- **حداقل 3 شرط** برای تولید سیگنال

#### Mean Reversion:
- **LONG**: قیمت نزدیک باند پایین Bollinger + RSI<35 + Stochastic<25
- **SHORT**: قیمت نزدیک باند بالای Bollinger + RSI>65 + Stochastic>75

### مدیریت ریسک
```env
# اندازه پوزیشن (5% پیش‌فرض)
POSITION_SIZE=0.05

# حداکثر ضرر (3% پیش‌فرض)
MAX_DRAWDOWN_PCT=3.0

# حداکثر معاملات همزمان
MAX_CONCURRENT_TRADES=2

# ضرایب ATR برای SL/TP
STOP_LOSS_ATR_MULTIPLIER=1.2
TAKE_PROFIT_ATR_MULTIPLIER=2.4
```

### زمان‌بندی محتوا
```env
# بررسی سیگنال (ثانیه)
SIGNAL_CHECK_INTERVAL=300

# زمان انتشار محتوا (فرمت 24 ساعته)
MARKET_SUMMARY_TIME=09:00
ALTCOIN_SPOTLIGHT_TIME=13:00
EDUCATION_TIME=19:00

# گزارش هفتگی (4=جمعه)
WEEKLY_REPORT_DAY=4
WEEKLY_REPORT_TIME=17:00
```

## 📊 نمونه خروجی‌ها

### سیگنال معاملاتی:
```
🟢 سیگنال خرید | BTC/USDT | 5m

📊 نوع: trend_following

💵 قیمت ورود: $43,250.00
🛑 حد ضرر: $42,800.00
🎯 حد سود: $44,100.00
🎯 اعتماد: 78.5%

🏆 Win Rate هفته اخیر: 72.3% (34/47)
📈 تعداد سیگنال‌های هفته: 47

📋 شرایط برآورده شده:
• قیمت بالای EMA200
• کراس صعودی EMA21/50
• RSI بالای 53 (58.2)
• بریک‌اوت Donchian
• تأیید حجم معاملات

⚠️ هشدار ریسک: این سیگنال‌ها صرفاً برای اهداف آموزشی...
```

### گزارش هفتگی:
```
📊 گزارش هفتگی عملکرد - هفته 2024/03/15

📈 آمار کلی:
• کل سیگنال‌ها: 47
• سیگنال‌های برنده: 34
• سیگنال‌های بازنده: 13
• نرخ برد: 72.3%

💰 آمار مالی:
• سود/زیان کل: +8.4%
• میانگین سود: +2.1%
• میانگین زیان: -1.2%

#گزارش_هفتگی #عملکرد #کریپتو #سیگنال
```

## 🔧 عیب‌یابی

### مشکلات رایج:

#### خطای توکن تلگرام:
```bash
# بررسی صحت توکن
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
```

#### خطای OpenAI API:
```bash
# بررسی اعتبار کلید
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer <YOUR_API_KEY>"
```

#### خطای نصب TA-Lib:
```bash
# Windows
pip install --find-links https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib TA-Lib

# macOS
brew install ta-lib
pip install TA-Lib

# Ubuntu/Debian
sudo apt-get install libta-lib-dev
pip install TA-Lib
```

### بررسی لاگ‌ها:
```bash
# مشاهده لاگ‌های زنده
tail -f crypto_bot.log

# جستجو در لاگ‌ها
grep "ERROR" crypto_bot.log
grep "Signal" crypto_bot.log
```

## 📈 بهینه‌سازی عملکرد

### افزایش Win Rate:
```env
# حالت محافظه‌کارانه
ULTRA_HIGH_WINRATE_MODE=true
ULTRA_MIN_CONFIDENCE=0.90
CONFIDENCE_THRESHOLD=0.75
```

### افزایش تعداد سیگنال‌ها:
```env
# کاهش محدودیت‌ها
CONFIDENCE_THRESHOLD=0.60
MIN_VOLUME_USD=3000000
TRADING_HOURS_START=0
TRADING_HOURS_END=23
```

## 🔐 امنیت

### محافظت از کلیدها:
- **هرگز** فایل `.env` را commit نکنید
- از **environment variables** در production استفاده کنید
- کلیدهای API را به صورت دوره‌ای تغییر دهید

### دسترسی‌های بات:
- فقط دسترسی **ارسال پیام** به بات بدهید
- از **webhook** به جای polling در production استفاده کنید
- **لاگ‌ها** را به صورت منظم بررسی کنید

## 🆘 پشتیبانی

### راه‌های ارتباطی:
- **Issues**: برای گزارش باگ یا درخواست ویژگی
- **Discussions**: برای سوالات و بحث
- **Wiki**: برای مستندات تکمیلی

### قبل از گزارش مشکل:
1. فایل `crypto_bot.log` را بررسی کنید
2. تست `python -m src.main --test` را اجرا کنید
3. تنظیمات `.env` را دوباره بررسی کنید

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است. برای اطلاعات بیشتر فایل LICENSE را مطالعه کنید.

## ⚠️ هشدار مهم

**این بات صرفاً برای اهداف آموزشی و تحقیقاتی طراحی شده است.**

- معاملات کریپتوکارنسی دارای ریسک بالایی است
- همیشه مدیریت ریسک را رعایت کنید
- بیش از توان مالی خود سرمایه‌گذاری نکنید
- این بات مسئولیتی در قبال ضررهای احتمالی ندارد

---

**ساخته شده با ❤️ برای جامعه کریپتو**