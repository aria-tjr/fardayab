#!/usr/bin/env python3
"""
Simple runner script for Crypto Signal Bot
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from src.main import main
    import asyncio
    asyncio.run(main())
