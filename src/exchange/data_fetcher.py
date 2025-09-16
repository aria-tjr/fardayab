"""
Exchange data fetcher using CCXT
"""
import ccxt
import pandas as pd
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np

from ..config import Config

logger = logging.getLogger(__name__)

class ExchangeDataFetcher:
    """Handles fetching market data from exchanges"""
    
    def __init__(self):
        self.exchange = self._initialize_exchange()
        self.rate_limiter = asyncio.Semaphore(10)  # Limit concurrent requests
        
    def _initialize_exchange(self) -> ccxt.Exchange:
        """Initialize the exchange connection"""
        try:
            exchange_class = getattr(ccxt, Config.EXCHANGE_NAME)
            exchange = exchange_class({
                'apiKey': Config.EXCHANGE_API_KEY,
                'secret': Config.EXCHANGE_SECRET,
                'sandbox': False,
                'enableRateLimit': True,
                'timeout': 30000,
            })
            
            # Test connection
            exchange.load_markets()
            logger.info(f"Successfully connected to {Config.EXCHANGE_NAME}")
            return exchange
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise
    
    async def get_ohlcv_data(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        """Fetch OHLCV data for a symbol"""
        async with self.rate_limiter:
            try:
                ohlcv = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                )
                
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                return df
                
            except Exception as e:
                logger.error(f"Error fetching OHLCV data for {symbol} {timeframe}: {e}")
                raise
    
    async def get_ticker_data(self, symbol: str) -> Dict:
        """Fetch current ticker data for a symbol"""
        async with self.rate_limiter:
            try:
                ticker = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.exchange.fetch_ticker(symbol)
                )
                return ticker
                
            except Exception as e:
                logger.error(f"Error fetching ticker data for {symbol}: {e}")
                raise
    
    async def get_volume_filtered_pairs(self) -> List[str]:
        """Get pairs that meet minimum volume requirement"""
        valid_pairs = []
        
        for symbol in Config.TRADING_PAIRS:
            try:
                ticker = await self.get_ticker_data(symbol)
                volume_usd = ticker.get('quoteVolume', 0)
                
                if volume_usd >= Config.MIN_VOLUME_USD:
                    valid_pairs.append(symbol)
                    logger.info(f"{symbol} passed volume filter: ${volume_usd:,.0f}")
                else:
                    logger.debug(f"{symbol} failed volume filter: ${volume_usd:,.0f}")
                    
            except Exception as e:
                logger.warning(f"Could not fetch volume data for {symbol}: {e}")
                continue
        
        return valid_pairs
    
    async def get_market_data(self, symbols: List[str], timeframes: List[str]) -> Dict[str, Dict[str, pd.DataFrame]]:
        """Fetch market data for multiple symbols and timeframes"""
        market_data = {}
        
        tasks = []
        for symbol in symbols:
            market_data[symbol] = {}
            for timeframe in timeframes:
                task = self.get_ohlcv_data(symbol, timeframe)
                tasks.append((symbol, timeframe, task))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*[task for _, _, task in tasks], return_exceptions=True)
        
        for i, (symbol, timeframe, _) in enumerate(tasks):
            result = results[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {symbol} {timeframe}: {result}")
                continue
            
            market_data[symbol][timeframe] = result
        
        return market_data
    
    async def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for multiple symbols"""
        prices = {}
        
        tasks = [self.get_ticker_data(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to get price for {symbol}: {result}")
                continue
            
            prices[symbol] = result.get('last', 0)
        
        return prices
    
    def calculate_volume_24h(self, df: pd.DataFrame) -> float:
        """Calculate 24-hour volume from OHLCV data"""
        if len(df) < 24:  # If we don't have 24 hours of data
            return df['volume'].sum()
        
        # Get last 24 hours of data
        last_24h = df.tail(24)
        return last_24h['volume'].sum()
    
    async def get_market_summary(self) -> Dict:
        """Get overall market summary"""
        try:
            # Get current prices for all pairs
            prices = await self.get_current_prices(Config.TRADING_PAIRS)
            
            # Calculate market cap weighted average (simplified)
            total_market_value = sum(prices.values())
            avg_price = total_market_value / len(prices) if prices else 0
            
            # Get BTC dominance (simplified)
            btc_price = prices.get('BTC/USDT', 0)
            btc_dominance = (btc_price / avg_price) * 100 if avg_price > 0 else 0
            
            return {
                'timestamp': datetime.now(),
                'total_pairs': len(Config.TRADING_PAIRS),
                'active_pairs': len(prices),
                'average_price': avg_price,
                'btc_dominance': btc_dominance,
                'prices': prices
            }
            
        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return {}
    
    def close(self):
        """Close exchange connection"""
        if hasattr(self.exchange, 'close'):
            self.exchange.close()
