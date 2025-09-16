#!/usr/bin/env python3
"""
راه‌اندازی آسان بات سیگنال کریپتو
Simple launcher for Crypto Signal Bot

استفاده:
python run_bot.py          # اجرای عادی
python run_bot.py --test   # تست سیستم
python run_bot.py --help   # راهنما
"""

import sys
import os
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(
        description='🤖 بات سیگنال‌دهنده کریپتو - کاملاً خودکار',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
نمونه‌های استفاده:
  python run_bot.py              اجرای عادی بات
  python run_bot.py --test       تست عملکرد سیستم
  python run_bot.py --validate   بررسی تنظیمات
  python run_bot.py --status     نمایش وضعیت

برای کسب اطلاعات بیشتر README.md را مطالعه کنید.
        """
    )
    
    parser.add_argument(
        '--test', 
        action='store_true',
        help='اجرای تست کامل سیستم'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true', 
        help='بررسی تنظیمات و پیکربندی'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='نمایش وضعیت سیستم'
    )
    
    args = parser.parse_args()
    
    # بررسی وجود فایل‌های ضروری
    required_files = ['.env', 'requirements.txt', 'src/main.py']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("❌ فایل‌های ضروری یافت نشدند:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n💡 لطفاً از دایرکتری اصلی پروژه اجرا کنید.")
        return 1
    
    # بررسی Python version
    if sys.version_info < (3, 11):
        print(f"❌ Python 3.11+ مورد نیاز است. نسخه فعلی: {sys.version}")
        return 1
    
    print("🤖 بات سیگنال‌دهنده کریپتو")
    print("=" * 50)
    
    try:
        if args.validate:
            print("🔍 بررسی تنظیمات...")
            result = subprocess.run([
                sys.executable, '-c',
                'from src.config import Config; Config.validate(); print("✅ تنظیمات معتبر است")'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(result.stdout)
            else:
                print("❌ خطا در تنظیمات:")
                print(result.stderr)
                return 1
                
        elif args.status:
            print("📊 بررسی وضعیت سیستم...")
            result = subprocess.run([
                sys.executable, '-c',
                '''
import asyncio
from src.exchange.data_fetcher import ExchangeDataFetcher
from src.storage.models import DatabaseManager

async def check_status():
    try:
        # بررسی دیتابیس
        db = DatabaseManager()
        recent_signals = db.get_recent_signals(5)
        print(f"📈 آخرین سیگنال‌ها: {len(recent_signals)}")
        
        # بررسی اتصال صرافی
        fetcher = ExchangeDataFetcher()
        pairs = await fetcher.get_volume_filtered_pairs()
        print(f"💱 جفت ارزهای معتبر: {len(pairs)}")
        await fetcher.close()
        
        print("✅ سیستم آماده است")
        
    except Exception as e:
        print(f"❌ خطا: {e}")

asyncio.run(check_status())
                '''
            ], capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print("خطاها:", result.stderr)
                
        elif args.test:
            print("🧪 اجرای تست کامل...")
            result = subprocess.run([
                sys.executable, '-m', 'src.main', '--test'
            ])
            return result.returncode
            
        else:
            print("🚀 شروع بات...")
            print("برای توقف: Ctrl+C")
            print("-" * 50)
            
            result = subprocess.run([
                sys.executable, '-m', 'src.main'
            ])
            return result.returncode
            
    except KeyboardInterrupt:
        print("\n👋 بات متوقف شد.")
        return 0
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
