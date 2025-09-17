#!/usr/bin/env python3
"""
Test script to verify Docker module imports work correctly
"""

def test_imports():
    """Test all critical imports"""
    print("🧪 Testing Docker Module Imports")
    print("=" * 40)
    
    # Test 1: Basic src module
    try:
        import src
        print("✅ src module: OK")
    except Exception as e:
        print(f"❌ src module: {e}")
        return False
    
    # Test 2: Charts module
    try:
        from src.charts.chart_generator import ChartGenerator
        print("✅ src.charts.chart_generator: OK")
    except Exception as e:
        print(f"❌ src.charts.chart_generator: {e}")
        return False
    
    # Test 3: Scheduler module
    try:
        from src.scheduler.scheduler import SchedulerManager
        print("✅ src.scheduler.scheduler: OK")
    except Exception as e:
        print(f"❌ src.scheduler.scheduler: {e}")
        return False
    
    # Test 4: All other modules
    modules = [
        'src.config',
        'src.exchange.data_fetcher',
        'src.strategies.signal_generator',
        'src.content.content_generator',
        'src.telegram.bot',
        'src.storage.models'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}: OK")
        except Exception as e:
            print(f"❌ {module}: {e}")
            return False
    
    print("\n🎯 All imports successful!")
    return True

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)
