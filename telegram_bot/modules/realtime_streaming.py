from __future__ import annotations

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from telegram_bot.config.settings import Settings
from telegram_bot.modules.binance_api import BinanceAPI, BinanceWebSocketManager

# Optional WebSocket import
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None

log = logging.getLogger(__name__)


@dataclass
class StreamData:
    """Real-time stream data structure"""
    symbol: str
    data_type: str  # 'price', 'kline', 'depth', 'trade'
    data: Dict[str, Any]
    timestamp: datetime
    source: str = "binance"


class RealTimeStreamingManager:
    """Advanced real-time data streaming manager"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.binance_api = BinanceAPI(settings)
        self.binance_ws_manager = BinanceWebSocketManager(self.binance_api)
        
        # Active streams
        self.active_streams = {}
        self.data_callbacks = {}
        self.is_running = False
        
        # Stream data cache
        self.price_cache = {}
        self.kline_cache = {}
        self.depth_cache = {}
        
    async def start_price_streaming(self, symbols: List[str], callback: Callable = None) -> bool:
        """Start real-time price streaming for multiple symbols"""
        if not WEBSOCKETS_AVAILABLE:
            log.warning("WebSockets not available, skipping price streaming")
            return False
            
        try:
            log.info(f"Starting price streaming for symbols: {symbols}")
            
            # Define price callback
            async def price_callback(symbol: str, data: Dict[str, Any]):
                try:
                    stream_data = StreamData(
                        symbol=symbol,
                        data_type="price",
                        data=data,
                        timestamp=datetime.now(),
                        source="binance"
                    )
                    
                    # Cache the data
                    self.price_cache[symbol] = stream_data
                    
                    # Call user callback if provided
                    if callback:
                        await callback(stream_data)
                    
                    # Log price updates
                    if 'c' in data:  # Current price
                        log.debug(f"Price update for {symbol}: ${data['c']}")
                        
                except Exception as e:
                    log.error(f"Error processing price data for {symbol}: {e}")
            
            # Start Binance WebSocket streams
            success = await self.binance_ws_manager.start_price_stream(symbols, price_callback)
            
            if success:
                self.active_streams.update({symbol: "price" for symbol in symbols})
                self.data_callbacks.update({symbol: price_callback for symbol in symbols})
                self.is_running = True
                log.info(f"Successfully started price streaming for {len(symbols)} symbols")
                return True
            else:
                log.error("Failed to start price streaming")
                return False
                
        except Exception as e:
            log.error(f"Failed to start price streaming: {e}")
            return False
    
    async def start_kline_streaming(self, symbols: List[str], interval: str = "1m", 
                                  callback: Callable = None) -> bool:
        """Start real-time kline/candlestick streaming"""
        if not WEBSOCKETS_AVAILABLE:
            log.warning("WebSockets not available, skipping kline streaming")
            return False
            
        try:
            log.info(f"Starting kline streaming for symbols: {symbols} with interval: {interval}")
            
            # Define kline callback
            async def kline_callback(symbol: str, data: Dict[str, Any]):
                try:
                    kline_data = data.get('k', {})
                    stream_data = StreamData(
                        symbol=symbol,
                        data_type="kline",
                        data=kline_data,
                        timestamp=datetime.now(),
                        source="binance"
                    )
                    
                    # Cache the data
                    cache_key = f"{symbol}_{interval}"
                    self.kline_cache[cache_key] = stream_data
                    
                    # Call user callback if provided
                    if callback:
                        await callback(stream_data)
                    
                    # Log kline updates
                    if kline_data.get('c'):  # Close price
                        log.debug(f"Kline update for {symbol}: O:{kline_data['o']} H:{kline_data['h']} L:{kline_data['l']} C:{kline_data['c']}")
                        
                except Exception as e:
                    log.error(f"Error processing kline data for {symbol}: {e}")
            
            # Start Binance WebSocket streams
            success = await self.binance_ws_manager.start_kline_stream(symbols, kline_callback)
            
            if success:
                self.active_streams.update({symbol: "kline" for symbol in symbols})
                self.data_callbacks.update({symbol: kline_callback for symbol in symbols})
                self.is_running = True
                log.info(f"Successfully started kline streaming for {len(symbols)} symbols")
                return True
            else:
                log.error("Failed to start kline streaming")
                return False
                
        except Exception as e:
            log.error(f"Failed to start kline streaming: {e}")
            return False
    
    async def start_depth_streaming(self, symbols: List[str], callback: Callable = None) -> bool:
        """Start real-time order book depth streaming"""
        if not WEBSOCKETS_AVAILABLE:
            log.warning("WebSockets not available, skipping depth streaming")
            return False
            
        try:
            log.info(f"Starting depth streaming for symbols: {symbols}")
            
            # Define depth callback
            async def depth_callback(symbol: str, data: Dict[str, Any]):
                try:
                    stream_data = StreamData(
                        symbol=symbol,
                        data_type="depth",
                        data=data,
                        timestamp=datetime.now(),
                        source="binance"
                    )
                    
                    # Cache the data
                    self.depth_cache[symbol] = stream_data
                    
                    # Call user callback if provided
                    if callback:
                        await callback(stream_data)
                    
                    # Log depth updates
                    bids = data.get('b', [])
                    asks = data.get('a', [])
                    if bids and asks:
                        log.debug(f"Depth update for {symbol}: Best bid: {bids[0]} Best ask: {asks[0]}")
                        
                except Exception as e:
                    log.error(f"Error processing depth data for {symbol}: {e}")
            
            # Start individual WebSocket streams for depth
            for symbol in symbols:
                success = await self.binance_api.start_websocket_stream(
                    symbol, "depth", depth_callback
                )
                if success:
                    self.active_streams[symbol] = "depth"
                    self.data_callbacks[symbol] = depth_callback
            
            if self.active_streams:
                self.is_running = True
                log.info(f"Successfully started depth streaming for {len(self.active_streams)} symbols")
                return True
            else:
                log.error("Failed to start depth streaming")
                return False
                
        except Exception as e:
            log.error(f"Failed to start depth streaming: {e}")
            return False
    
    async def stop_all_streams(self) -> bool:
        """Stop all active streams"""
        try:
            log.info("Stopping all active streams")
            
            # Stop Binance WebSocket streams
            success = await self.binance_ws_manager.stop_all_streams()
            
            # Clear local data
            self.active_streams.clear()
            self.data_callbacks.clear()
            self.price_cache.clear()
            self.kline_cache.clear()
            self.depth_cache.clear()
            self.is_running = False
            
            log.info("Successfully stopped all streams")
            return success
            
        except Exception as e:
            log.error(f"Failed to stop streams: {e}")
            return False
    
    async def stop_symbol_stream(self, symbol: str) -> bool:
        """Stop streaming for a specific symbol"""
        try:
            if symbol in self.active_streams:
                success = await self.binance_api.stop_websocket_stream(symbol)
                if success:
                    del self.active_streams[symbol]
                    if symbol in self.data_callbacks:
                        del self.data_callbacks[symbol]
                    log.info(f"Stopped streaming for {symbol}")
                    return True
        except Exception as e:
            log.error(f"Failed to stop stream for {symbol}: {e}")
        return False
    
    def get_latest_price(self, symbol: str) -> Optional[StreamData]:
        """Get latest price data for a symbol"""
        return self.price_cache.get(symbol)
    
    def get_latest_kline(self, symbol: str, interval: str = "1m") -> Optional[StreamData]:
        """Get latest kline data for a symbol"""
        cache_key = f"{symbol}_{interval}"
        return self.kline_cache.get(cache_key)
    
    def get_latest_depth(self, symbol: str) -> Optional[StreamData]:
        """Get latest depth data for a symbol"""
        return self.depth_cache.get(symbol)
    
    def get_active_streams(self) -> Dict[str, str]:
        """Get list of active streams"""
        return self.active_streams.copy()
    
    def is_streaming(self) -> bool:
        """Check if any streams are active"""
        return self.is_running and len(self.active_streams) > 0
    
    async def get_streaming_summary(self) -> Dict[str, Any]:
        """Get comprehensive streaming summary"""
        try:
            summary = {
                "is_running": self.is_running,
                "active_streams": len(self.active_streams),
                "streams": self.active_streams.copy(),
                "cached_data": {
                    "price_symbols": list(self.price_cache.keys()),
                    "kline_symbols": list(self.kline_cache.keys()),
                    "depth_symbols": list(self.depth_cache.keys())
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Add sample data for each stream type
            if self.price_cache:
                sample_symbol = list(self.price_cache.keys())[0]
                sample_data = self.price_cache[sample_symbol]
                summary["sample_price_data"] = {
                    "symbol": sample_data.symbol,
                    "price": sample_data.data.get('c'),
                    "change_24h": sample_data.data.get('P'),
                    "volume": sample_data.data.get('v'),
                    "timestamp": sample_data.timestamp.isoformat()
                }
            
            return summary
            
        except Exception as e:
            log.error(f"Failed to get streaming summary: {e}")
            return {"error": str(e)}


class MarketDataProcessor:
    """Process and analyze real-time market data"""
    
    def __init__(self, streaming_manager: RealTimeStreamingManager):
        self.streaming_manager = streaming_manager
        self.price_alerts = {}
        self.volume_alerts = {}
        self.price_thresholds = {}
        
    async def setup_price_alerts(self, symbol: str, price: float, 
                               condition: str = "above", callback: Callable = None):
        """Setup price alerts for a symbol"""
        try:
            alert_key = f"{symbol}_{condition}_{price}"
            self.price_alerts[alert_key] = {
                "symbol": symbol,
                "price": price,
                "condition": condition,
                "callback": callback,
                "created_at": datetime.now()
            }
            log.info(f"Price alert set for {symbol}: {condition} {price}")
            return True
        except Exception as e:
            log.error(f"Failed to setup price alert: {e}")
            return False
    
    async def setup_volume_alerts(self, symbol: str, volume_threshold: float, 
                                callback: Callable = None):
        """Setup volume alerts for a symbol"""
        try:
            alert_key = f"{symbol}_volume_{volume_threshold}"
            self.volume_alerts[alert_key] = {
                "symbol": symbol,
                "volume_threshold": volume_threshold,
                "callback": callback,
                "created_at": datetime.now()
            }
            log.info(f"Volume alert set for {symbol}: {volume_threshold}")
            return True
        except Exception as e:
            log.error(f"Failed to setup volume alert: {e}")
            return False
    
    async def process_price_data(self, stream_data: StreamData):
        """Process incoming price data and check alerts"""
        try:
            symbol = stream_data.symbol
            data = stream_data.data
            
            # Check price alerts
            for alert_key, alert in self.price_alerts.items():
                if alert["symbol"] == symbol:
                    current_price = float(data.get('c', 0))
                    target_price = alert["price"]
                    condition = alert["condition"]
                    
                    should_trigger = False
                    if condition == "above" and current_price >= target_price:
                        should_trigger = True
                    elif condition == "below" and current_price <= target_price:
                        should_trigger = True
                    elif condition == "equals" and abs(current_price - target_price) < 0.01:
                        should_trigger = True
                    
                    if should_trigger and alert["callback"]:
                        await alert["callback"](stream_data, alert)
                        # Remove triggered alert
                        del self.price_alerts[alert_key]
            
            # Check volume alerts
            for alert_key, alert in self.volume_alerts.items():
                if alert["symbol"] == symbol:
                    current_volume = float(data.get('v', 0))
                    volume_threshold = alert["volume_threshold"]
                    
                    if current_volume >= volume_threshold and alert["callback"]:
                        await alert["callback"](stream_data, alert)
                        # Remove triggered alert
                        del self.volume_alerts[alert_key]
                        
        except Exception as e:
            log.error(f"Error processing price data: {e}")
    
    async def calculate_price_momentum(self, symbol: str, period: int = 5) -> Dict[str, Any]:
        """Calculate price momentum from cached data"""
        try:
            # Get recent kline data
            kline_data = self.streaming_manager.get_latest_kline(symbol)
            if not kline_data:
                return {"error": "No kline data available"}
            
            # This would need historical data for proper momentum calculation
            # For now, return basic momentum indicators
            current_price = float(kline_data.data.get('c', 0))
            open_price = float(kline_data.data.get('o', 0))
            
            price_change = current_price - open_price
            price_change_percent = (price_change / open_price) * 100 if open_price > 0 else 0
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "open_price": open_price,
                "price_change": price_change,
                "price_change_percent": price_change_percent,
                "momentum": "bullish" if price_change > 0 else "bearish",
                "strength": abs(price_change_percent)
            }
            
        except Exception as e:
            log.error(f"Error calculating price momentum: {e}")
            return {"error": str(e)}
    
    async def detect_volume_spikes(self, symbol: str, threshold: float = 2.0) -> Dict[str, Any]:
        """Detect volume spikes"""
        try:
            price_data = self.streaming_manager.get_latest_price(symbol)
            if not price_data:
                return {"error": "No price data available"}
            
            current_volume = float(price_data.data.get('v', 0))
            avg_volume = float(price_data.data.get('q', 0))  # Quote volume
            
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                is_spike = volume_ratio >= threshold
                
                return {
                    "symbol": symbol,
                    "current_volume": current_volume,
                    "avg_volume": avg_volume,
                    "volume_ratio": volume_ratio,
                    "is_spike": is_spike,
                    "spike_strength": volume_ratio if is_spike else 0
                }
            else:
                return {"error": "Insufficient volume data"}
                
        except Exception as e:
            log.error(f"Error detecting volume spikes: {e}")
            return {"error": str(e)}
    
    def get_active_alerts(self) -> Dict[str, Any]:
        """Get all active alerts"""
        return {
            "price_alerts": self.price_alerts,
            "volume_alerts": self.volume_alerts,
            "total_alerts": len(self.price_alerts) + len(self.volume_alerts)
        }
    
    async def clear_all_alerts(self) -> bool:
        """Clear all active alerts"""
        try:
            self.price_alerts.clear()
            self.volume_alerts.clear()
            log.info("Cleared all alerts")
            return True
        except Exception as e:
            log.error(f"Failed to clear alerts: {e}")
            return False
