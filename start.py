#!/usr/bin/env python3
"""
Simple startup script for Railway deployment
"""

import sys
import os

# Add paths for Railway deployment
if '/app' in os.getcwd() or 'railway' in os.getcwd().lower():
    sys.path.insert(0, '/app')
    sys.path.insert(0, '/app/src')
    # Change to src directory only in Railway
    if os.path.exists('/app/src'):
        os.chdir('/app/src')
else:
    # Local development - run from project root
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

# Import and run the main application
if __name__ == "__main__":
    try:
        if '/app' in os.getcwd() or 'railway' in os.getcwd().lower():
            # Railway deployment - run from src directory
            from main import main
        else:
            # Local development - run as module
            from src.main import main
        import asyncio
        asyncio.run(main())
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
