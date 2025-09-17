#!/usr/bin/env python3
"""
Ultra-simple Railway startup script
"""

import sys
import os

# Add paths
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

# Change to src directory
os.chdir('/app/src')

# Run the main module
if __name__ == "__main__":
    try:
        import subprocess
        result = subprocess.run([sys.executable, '-m', 'main'], cwd='/app/src')
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
