from __future__ import annotations

import asyncio
import logging
from typing import Any

from telegram_bot.config.settings import Settings
from telegram_bot.modules.collector import collect_all
from telegram_bot.utils.connectivity import RealTimeDataManager

log = logging.getLogger(__name__)


class RealTimeScheduler:
    """Handle real-time data updates and scheduling"""
    
    def __init__(self, settings: Settings, data_manager: RealTimeDataManager):
        self.settings = settings
        self.data_manager = data_manager
        self.is_running = False
        self.update_task = None
        
    async def start(self):
        """Start the real-time data update system"""
        if self.is_running:
            return
            
        self.is_running = True
        log.info("Starting real-time data update system...")
        
        # Start the update loop
        self.update_task = asyncio.create_task(self._update_loop())
        
    async def stop(self):
        """Stop the real-time data update system"""
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        log.info("Real-time data update system stopped")
    
    async def _update_loop(self):
        """Main update loop for real-time data"""
        while self.is_running:
            try:
                # Check if we should update data
                if await self.data_manager.should_update():
                    log.info("Updating real-time data...")
                    
                    # Collect fresh data
                    fresh_data = await collect_all(self.settings)
                    
                    # Update the data manager
                    await self.data_manager.update_data(fresh_data)
                    
                    log.info("Real-time data updated successfully")
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                log.error(f"Error in real-time update loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def force_update(self) -> dict[str, Any]:
        """Force an immediate data update"""
        log.info("Forcing immediate data update...")
        fresh_data = await collect_all(self.settings)
        await self.data_manager.update_data(fresh_data)
        return fresh_data
    
    async def get_latest_data(self) -> dict[str, Any]:
        """Get the latest available data"""
        # Try to get cached data first
        cached_data = await self.data_manager.get_cached_data()
        if cached_data:
            return cached_data
        
        # If no cached data or it's too old, force update
        return await self.force_update()


class HealthChecker:
    """Monitor bot health and connectivity"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.health_status = {
            "internet": False,
            "openai": False,
            "apis": False,
            "last_check": 0
        }
        
    async def check_health(self) -> dict[str, Any]:
        """Perform comprehensive health check"""
        import time
        current_time = time.time()
        
        # Check internet connectivity
        internet_ok = await self._check_internet()
        
        # Check OpenAI API
        openai_ok = await self._check_openai()
        
        # Check other APIs
        apis_ok = await self._check_apis()
        
        self.health_status = {
            "internet": internet_ok,
            "openai": openai_ok,
            "apis": apis_ok,
            "last_check": current_time,
            "overall": internet_ok and openai_ok and apis_ok
        }
        
        return self.health_status
    
    async def _check_internet(self) -> bool:
        """Check basic internet connectivity"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("https://httpbin.org/status/200")
                return response.status_code == 200
        except Exception:
            return False
    
    async def _check_openai(self) -> bool:
        """Check OpenAI API connectivity"""
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self.settings.OPENAI_API_KEY}"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://api.openai.com/v1/models", headers=headers)
                return response.status_code in [200, 401, 403]
        except Exception:
            return False
    
    async def _check_apis(self) -> bool:
        """Check other API connectivity"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test a few key APIs
                tests = [
                    client.get("https://api.coingecko.com/api/v3/ping"),
                    client.get("https://newsapi.org/v2/sources?apiKey=test")  # This will fail but we can reach the server
                ]
                
                results = await asyncio.gather(*tests, return_exceptions=True)
                # If at least one API is reachable, consider it OK
                return any(not isinstance(result, Exception) for result in results)
        except Exception:
            return False
    
    def get_status_summary(self) -> str:
        """Get a human-readable status summary"""
        status = self.health_status
        if status["overall"]:
            return "✅ All systems operational"
        else:
            issues = []
            if not status["internet"]:
                issues.append("Internet")
            if not status["openai"]:
                issues.append("OpenAI")
            if not status["apis"]:
                issues.append("APIs")
            return f"⚠️ Issues with: {', '.join(issues)}"
