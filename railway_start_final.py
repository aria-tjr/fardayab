#!/usr/bin/env python3
"""
Final Railway startup script - uses single-file bot
"""

import sys
import os

# Set working directory to /app
os.chdir('/app')

# Add Python path
sys.path.insert(0, '/app')

# Import and run the single-file bot
if __name__ == "__main__":
    try:
        from railway_bot import main
        import asyncio
        asyncio.run(main())
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
