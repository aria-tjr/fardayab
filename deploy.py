#!/usr/bin/env python3
"""
Deployment helper script
"""

import os
import sys

def check_files():
    """Check if all required files exist"""
    required_files = [
        'railway_bot.py',
        'Dockerfile.railway',
        'railway.toml',
        'requirements.txt',
        '.env.example'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files present")
    return True

def check_env_vars():
    """Check if environment variables are set"""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHANNEL_ID',
        'OPENAI_API_KEY',
        'BINANCE_API_KEY',
        'BINANCE_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Set these in Railway dashboard > Variables tab")
        return False
    
    print("✅ All environment variables set")
    return True

def main():
    print("🚀 CRYPTO SIGNAL BOT DEPLOYMENT CHECKER")
    print("=" * 50)
    
    # Check files
    files_ok = check_files()
    
    # Check environment variables
    env_ok = check_env_vars()
    
    print("\n" + "=" * 50)
    
    if files_ok and env_ok:
        print("🎉 READY FOR DEPLOYMENT!")
        print("\nNext steps:")
        print("1. Push code to GitHub")
        print("2. Deploy to Railway")
        print("3. Check logs for success")
    else:
        print("❌ NOT READY - Fix issues above first")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
