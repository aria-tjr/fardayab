#!/usr/bin/env python3
"""
Railway startup script for Crypto Signal Bot
Handles module path issues in Railway deployment
"""

import sys
import os

# Add paths for Railway deployment
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

# Change to src directory to run as module
os.chdir('/app/src')

# Import and run the main application
if __name__ == "__main__":
    try:
        from main import main
        import asyncio
        asyncio.run(main())
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
