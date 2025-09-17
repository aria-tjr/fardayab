#!/usr/bin/env python3
"""
Test script for the web server healthcheck
"""

import asyncio
import aiohttp
import sys
import os

# Add paths
sys.path.insert(0, os.getcwd())

async def test_healthcheck():
    """Test the healthcheck endpoint"""
    try:
        # Start the web server in background
        from railway_web_server import WebServer
        
        web_server = WebServer(port=8001)  # Use different port for testing
        await web_server.start()
        
        # Wait a moment for server to start
        await asyncio.sleep(2)
        
        # Test healthcheck endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8001/') as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Healthcheck test passed!")
                    print(f"Response: {data}")
                    return True
                else:
                    print(f"❌ Healthcheck test failed with status: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Healthcheck test error: {e}")
        return False
    finally:
        # Clean up
        try:
            await web_server.stop()
        except:
            pass

async def test_status_endpoint():
    """Test the status endpoint"""
    try:
        from railway_web_server import WebServer
        
        web_server = WebServer(port=8002)  # Use different port for testing
        await web_server.start()
        
        # Wait a moment for server to start
        await asyncio.sleep(2)
        
        # Test status endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8002/status') as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Status endpoint test passed!")
                    print(f"Response: {data}")
                    return True
                else:
                    print(f"❌ Status endpoint test failed with status: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Status endpoint test error: {e}")
        return False
    finally:
        # Clean up
        try:
            await web_server.stop()
        except:
            pass

async def main():
    """Run all tests"""
    print("🧪 Testing Railway Web Server...")
    print("=" * 50)
    
    # Test healthcheck
    print("\n1. Testing healthcheck endpoint...")
    healthcheck_ok = await test_healthcheck()
    
    # Test status
    print("\n2. Testing status endpoint...")
    status_ok = await test_status_endpoint()
    
    print("\n" + "=" * 50)
    if healthcheck_ok and status_ok:
        print("🎉 All tests passed! The web server is ready for Railway deployment.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return healthcheck_ok and status_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
