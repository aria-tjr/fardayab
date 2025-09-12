#!/usr/bin/env python3
"""
Main entry point for the Telegram Bot application.
This file redirects to the actual bot implementation.
"""

import sys
import os

# Add the telegram_bot directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'telegram_bot'))

# Import and run the actual bot
if __name__ == "__main__":
    from telegram_bot.main import main
    import asyncio
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
