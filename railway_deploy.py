#!/usr/bin/env python3
"""
Railway Deployment Script
"""

import os
import subprocess
import sys

def check_git_status():
    """Check if git is initialized and files are committed"""
    try:
        # Check if git is initialized
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Git not initialized. Run: git init")
            return False
        
        # Check if there are uncommitted changes
        if "nothing to commit" not in result.stdout:
            print("⚠️  You have uncommitted changes. Consider committing them first.")
            print("   Run: git add . && git commit -m 'Ready for Railway deployment'")
        
        print("✅ Git repository ready")
        return True
    except FileNotFoundError:
        print("❌ Git not installed. Please install Git first.")
        return False

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        'railway_bot.py',
        'Dockerfile.railway',
        'railway.toml',
        'requirements.txt',
        'Procfile',
        'runtime.txt',
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

def show_deployment_steps():
    """Show step-by-step deployment instructions"""
    print("\n🚀 RAILWAY DEPLOYMENT STEPS:")
    print("=" * 50)
    
    print("\n1️⃣  PUSH TO GITHUB:")
    print("   git add .")
    print("   git commit -m 'Ready for Railway deployment'")
    print("   git push origin main")
    
    print("\n2️⃣  DEPLOY TO RAILWAY:")
    print("   • Go to https://railway.app")
    print("   • Sign in with GitHub")
    print("   • Click 'New Project'")
    print("   • Select 'Deploy from GitHub repo'")
    print("   • Choose your repository")
    
    print("\n3️⃣  CONFIGURE ENVIRONMENT:")
    print("   • Go to 'Variables' tab in Railway dashboard")
    print("   • Add these environment variables:")
    print("     - TELEGRAM_BOT_TOKEN=your_bot_token")
    print("     - TELEGRAM_CHANNEL_ID=your_channel_id")
    print("     - OPENAI_API_KEY=your_openai_key")
    print("     - BINANCE_API_KEY=your_binance_key")
    print("     - BINANCE_SECRET_KEY=your_binance_secret")
    
    print("\n4️⃣  DEPLOY:")
    print("   • Railway will auto-detect your configuration")
    print("   • Bot will start with 'python railway_bot.py'")
    print("   • Check logs for successful startup")
    
    print("\n5️⃣  VERIFY:")
    print("   • Check Railway logs for 'Bot started successfully'")
    print("   • Check your Telegram channel for messages")
    print("   • Monitor signal generation every 5 minutes")

def main():
    print("🚀 RAILWAY DEPLOYMENT PREPARATION")
    print("=" * 50)
    
    # Check files
    files_ok = check_required_files()
    
    # Check git status
    git_ok = check_git_status()
    
    print("\n" + "=" * 50)
    
    if files_ok and git_ok:
        print("🎉 READY FOR RAILWAY DEPLOYMENT!")
        show_deployment_steps()
    else:
        print("❌ NOT READY - Fix issues above first")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
