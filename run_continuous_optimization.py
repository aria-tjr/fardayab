#!/usr/bin/env python3
"""
Simplified launcher for continuous optimization
"""
import asyncio
import sys
import os
from continuous_optimizer import ContinuousOptimizer

async def main():
    """Run continuous optimization with simplified interface"""
    print("🚀 Starting Continuous Parameter Optimization")
    print("🎯 Target: 80%+ Win Rate with Good Trading Frequency")
    print("⚙️  Using Genetic Algorithm + Machine Learning")
    print("=" * 60)
    
    optimizer = ContinuousOptimizer()
    
    try:
        await optimizer.start_continuous_optimization()
    except KeyboardInterrupt:
        print("\n⏹️  Optimization stopped by user")
        optimizer.stop_continuous_optimization()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
