from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable

import httpx
from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class ConnectivityMonitor:
    """Monitor and maintain internet connectivity for the bot"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.is_connected = False
        self.last_check = 0
        self.check_interval = 60  # Check every minute
        self.retry_count = 0
        self.max_retries = 5
        
    async def check_connectivity(self) -> bool:
        """Check if the bot has internet connectivity"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test multiple endpoints for reliability
                test_urls = [
                    "https://api.openai.com/v1/models",
                    "https://api.coingecko.com/api/v3/ping",
                    "https://httpbin.org/status/200"
                ]
                
                for url in test_urls:
                    try:
                        response = await client.get(url)
                        if response.status_code in [200, 401, 403]:  # 401/403 means we reached the server
                            self.is_connected = True
                            self.retry_count = 0
                            return True
                    except Exception:
                        continue
                        
                self.is_connected = False
                self.retry_count += 1
                return False
                
        except Exception as e:
            log.warning(f"Connectivity check failed: {e}")
            self.is_connected = False
            self.retry_count += 1
            return False
    
    async def start_monitoring(self, callback: Callable[[bool], None] = None):
        """Start continuous connectivity monitoring"""
        log.info("Starting connectivity monitoring...")
        
        while True:
            try:
                current_time = time.time()
                
                # Check connectivity if enough time has passed
                if current_time - self.last_check >= self.check_interval:
                    was_connected = self.is_connected
                    is_connected = await self.check_connectivity()
                    
                    if is_connected != was_connected:
                        status = "connected" if is_connected else "disconnected"
                        log.info(f"Internet connectivity status changed: {status}")
                        
                        if callback:
                            await callback(is_connected)
                    
                    self.last_check = current_time
                
                # If disconnected, check more frequently
                if not self.is_connected:
                    await asyncio.sleep(10)  # Check every 10 seconds when disconnected
                else:
                    await asyncio.sleep(self.check_interval)
                    
            except Exception as e:
                log.error(f"Error in connectivity monitoring: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds on error


class RealTimeDataManager:
    """Manage real-time data updates for the bot"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.last_update = 0
        self.update_interval = settings.DATA_REFRESH_INTERVAL
        self.cached_data = None
        self.update_callbacks = []
        
    def add_update_callback(self, callback: Callable[[dict[str, Any]], None]):
        """Add a callback to be called when data is updated"""
        self.update_callbacks.append(callback)
    
    async def should_update(self) -> bool:
        """Check if data should be updated"""
        current_time = time.time()
        return (current_time - self.last_update) >= self.update_interval
    
    async def update_data(self, data: dict[str, Any]):
        """Update cached data and notify callbacks"""
        self.cached_data = data
        self.last_update = time.time()
        
        # Notify all callbacks
        for callback in self.update_callbacks:
            try:
                await callback(data)
            except Exception as e:
                log.error(f"Error in update callback: {e}")
    
    async def get_cached_data(self) -> dict[str, Any] | None:
        """Get cached data if available and not too old"""
        if self.cached_data and (time.time() - self.last_update) < self.update_interval * 2:
            return self.cached_data
        return None


class ModelUpdater:
    """Handle automatic model updates and version checking"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.current_model = settings.OPENAI_MODEL
        self.last_check = 0
        self.check_interval = 3600  # Check every hour
        
    async def check_for_updates(self) -> bool:
        """Check if there are newer models available"""
        try:
            current_time = time.time()
            if current_time - self.last_check < self.check_interval:
                return False
                
            async with httpx.AsyncClient(timeout=15.0) as client:
                headers = {"Authorization": f"Bearer {self.settings.OPENAI_API_KEY}"}
                response = await client.get("https://api.openai.com/v1/models", headers=headers)
                
                if response.status_code == 200:
                    models = response.json()
                    available_models = [model["id"] for model in models.get("data", [])]
                    
                    # Check for newer GPT-5 models
                    gpt5_models = [m for m in available_models if m.startswith("gpt-5")]
                    if gpt5_models:
                        latest_model = max(gpt5_models)
                        if latest_model != self.current_model:
                            log.info(f"New model available: {latest_model} (current: {self.current_model})")
                            self.last_check = current_time
                            return True
                
                self.last_check = current_time
                return False
                
        except Exception as e:
            log.warning(f"Failed to check for model updates: {e}")
            return False
    
    async def update_model(self, new_model: str):
        """Update to a new model"""
        log.info(f"Updating model from {self.current_model} to {new_model}")
        self.current_model = new_model
        # Note: In a real implementation, you'd update the settings here


async def create_connectivity_system(settings: Settings) -> tuple[ConnectivityMonitor, RealTimeDataManager, ModelUpdater]:
    """Create and initialize the connectivity system"""
    monitor = ConnectivityMonitor(settings)
    data_manager = RealTimeDataManager(settings)
    model_updater = ModelUpdater(settings)
    
    return monitor, data_manager, model_updater
