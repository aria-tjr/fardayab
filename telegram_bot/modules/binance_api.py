from __future__ import annotations

import asyncio
import logging
import hmac
import hashlib
import time
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from telegram_bot.config.settings import Settings

# Optional WebSocket import
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None

log = logging.getLogger(__name__)


@dataclass
class BinanceTicker:
    """Binance ticker data structure"""
    symbol: str
    price: float
    price_change: float
    price_change_percent: float
    weighted_avg_price: float
    prev_close_price: float
    last_price: float
    bid_price: float
    ask_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float
    open_time: datetime
    close_time: datetime
    count: int


@dataclass
class BinanceKline:
    """Binance kline/candlestick data structure"""
    open_time: datetime
    close_time: datetime
    symbol: str
    interval: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: datetime
    quote_asset_volume: float
    number_of_trades: int
    taker_buy_base_asset_volume: float
    taker_buy_quote_asset_volume: float


@dataclass
class BinanceOrderBook:
    """Binance order book data structure"""
    symbol: str
    bids: List[Tuple[float, float]]  # (price, quantity)
    asks: List[Tuple[float, float]]  # (price, quantity)
    last_update_id: int


class BinanceAPI:
    """Advanced Binance API integration for real-time market data"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        self.api_key = "UPchixR6CyXXthOG3vSpAaZOXJikWDxD4q7Uu8kkW0qbs1LKCPdXhRIiEg4SBwHv"
        self.secret_key = "EIxLfnfANrnin3r8EyDQ6eWmwbWxFbQiDzl3TbXKqG7nWCarBXyXE9EQLlnyr3k7"
        self.base_url = "https://api.binance.com"
        self.ws_url = "wss://stream.binance.com:9443/ws"
        
        # WebSocket connections
        self.ws_connections = {}
        self.ws_callbacks = {}
        
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature for authenticated requests"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_headers(self, signature: str = None) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
        if signature:
            headers['X-MBX-SIGNATURE'] = signature
        return headers
    
    async def get_server_time(self) -> Dict[str, Any]:
        """Get Binance server time"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v3/time")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            log.error(f"Failed to get server time: {e}")
        return {}
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange trading rules and symbol information"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v3/exchangeInfo")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            log.error(f"Failed to get exchange info: {e}")
        return {}
    
    async def get_24hr_ticker(self, symbol: str = None) -> List[BinanceTicker]:
        """Get 24hr ticker price change statistics"""
        try:
            url = f"{self.base_url}/api/v3/ticker/24hr"
            if symbol:
                url += f"?symbol={symbol}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        data = [data]
                    
                    tickers = []
                    for ticker_data in data:
                        ticker = BinanceTicker(
                            symbol=ticker_data['symbol'],
                            price=float(ticker_data['lastPrice']),
                            price_change=float(ticker_data['priceChange']),
                            price_change_percent=float(ticker_data['priceChangePercent']),
                            weighted_avg_price=float(ticker_data['weightedAvgPrice']),
                            prev_close_price=float(ticker_data['prevClosePrice']),
                            last_price=float(ticker_data['lastPrice']),
                            bid_price=float(ticker_data['bidPrice']),
                            ask_price=float(ticker_data['askPrice']),
                            open_price=float(ticker_data['openPrice']),
                            high_price=float(ticker_data['highPrice']),
                            low_price=float(ticker_data['lowPrice']),
                            volume=float(ticker_data['volume']),
                            quote_volume=float(ticker_data['quoteVolume']),
                            open_time=datetime.fromtimestamp(ticker_data['openTime'] / 1000),
                            close_time=datetime.fromtimestamp(ticker_data['closeTime'] / 1000),
                            count=ticker_data['count']
                        )
                        tickers.append(ticker)
                    
                    return tickers
        except Exception as e:
            log.error(f"Failed to get 24hr ticker: {e}")
        return []
    
    async def get_klines(self, symbol: str, interval: str = "1d", 
                        limit: int = 500, start_time: int = None, end_time: int = None) -> List[BinanceKline]:
        """Get kline/candlestick data"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': min(limit, 1000)
            }
            
            if start_time:
                params['startTime'] = start_time
            if end_time:
                params['endTime'] = end_time
            
            query_string = urlencode(params)
            url = f"{self.base_url}/api/v3/klines?{query_string}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    
                    klines = []
                    for kline_data in data:
                        kline = BinanceKline(
                            open_time=datetime.fromtimestamp(kline_data[0] / 1000),
                            close_time=datetime.fromtimestamp(kline_data[6] / 1000),
                            symbol=symbol,
                            interval=interval,
                            open=float(kline_data[1]),
                            high=float(kline_data[2]),
                            low=float(kline_data[3]),
                            close=float(kline_data[4]),
                            volume=float(kline_data[5]),
                            quote_asset_volume=float(kline_data[7]),
                            number_of_trades=int(kline_data[8]),
                            taker_buy_base_asset_volume=float(kline_data[9]),
                            taker_buy_quote_asset_volume=float(kline_data[10])
                        )
                        klines.append(kline)
                    
                    return klines
        except Exception as e:
            log.error(f"Failed to get klines for {symbol}: {e}")
        return []
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> BinanceOrderBook:
        """Get order book depth"""
        try:
            params = {'symbol': symbol, 'limit': limit}
            query_string = urlencode(params)
            url = f"{self.base_url}/api/v3/depth?{query_string}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    
                    bids = [(float(bid[0]), float(bid[1])) for bid in data['bids']]
                    asks = [(float(ask[0]), float(ask[1])) for ask in data['asks']]
                    
                    return BinanceOrderBook(
                        symbol=symbol,
                        bids=bids,
                        asks=asks,
                        last_update_id=data['lastUpdateId']
                    )
        except Exception as e:
            log.error(f"Failed to get order book for {symbol}: {e}")
        return None
    
    async def get_recent_trades(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Get recent trades"""
        try:
            params = {'symbol': symbol, 'limit': limit}
            query_string = urlencode(params)
            url = f"{self.base_url}/api/v3/trades?{query_string}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            log.error(f"Failed to get recent trades for {symbol}: {e}")
        return []
    
    async def get_aggregate_trades(self, symbol: str, limit: int = 500, 
                                 start_time: int = None, end_time: int = None) -> List[Dict[str, Any]]:
        """Get aggregate trades"""
        try:
            params = {'symbol': symbol, 'limit': limit}
            if start_time:
                params['startTime'] = start_time
            if end_time:
                params['endTime'] = end_time
            
            query_string = urlencode(params)
            url = f"{self.base_url}/api/v3/aggTrades?{query_string}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            log.error(f"Failed to get aggregate trades for {symbol}: {e}")
        return []
    
    async def get_market_data(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Get comprehensive market data for multiple symbols"""
        try:
            if not symbols:
                symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'MATICUSDT', 
                          'DOTUSDT', 'LINKUSDT', 'UNIUSDT', 'AAVEUSDT', 'COMPUSDT']
            
            # Get 24hr tickers for all symbols
            tickers = await self.get_24hr_ticker()
            ticker_dict = {ticker.symbol: ticker for ticker in tickers}
            
            # Get klines for each symbol
            klines_data = {}
            for symbol in symbols:
                if symbol in ticker_dict:
                    klines = await self.get_klines(symbol, "1d", 30)
                    klines_data[symbol] = klines
            
            # Get order books for major symbols
            order_books = {}
            for symbol in symbols[:5]:  # Limit to first 5 symbols
                if symbol in ticker_dict:
                    order_book = await self.get_order_book(symbol, 50)
                    if order_book:
                        order_books[symbol] = order_book
            
            return {
                "tickers": ticker_dict,
                "klines": klines_data,
                "order_books": order_books,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log.error(f"Failed to get market data: {e}")
            return {}
    
    async def start_websocket_stream(self, symbol: str, stream_type: str = "ticker", 
                                   callback=None) -> bool:
        """Start WebSocket stream for real-time data"""
        if not WEBSOCKETS_AVAILABLE:
            log.warning("WebSockets not available, skipping WebSocket stream")
            return False
            
        try:
            stream_name = f"{symbol.lower()}@ticker" if stream_type == "ticker" else f"{symbol.lower()}@kline_1m"
            ws_url = f"{self.ws_url}/{stream_name}"
            
            async def websocket_handler():
                try:
                    async with websockets.connect(ws_url) as websocket:
                        self.ws_connections[symbol] = websocket
                        log.info(f"WebSocket connected for {symbol}")
                        
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                if callback:
                                    await callback(symbol, data)
                            except Exception as e:
                                log.warning(f"Error processing WebSocket message: {e}")
                                
                except Exception as e:
                    log.error(f"WebSocket error for {symbol}: {e}")
                    if symbol in self.ws_connections:
                        del self.ws_connections[symbol]
            
            # Store callback
            if callback:
                self.ws_callbacks[symbol] = callback
            
            # Start WebSocket in background
            asyncio.create_task(websocket_handler())
            return True
            
        except Exception as e:
            log.error(f"Failed to start WebSocket for {symbol}: {e}")
            return False
    
    async def stop_websocket_stream(self, symbol: str) -> bool:
        """Stop WebSocket stream"""
        try:
            if symbol in self.ws_connections:
                await self.ws_connections[symbol].close()
                del self.ws_connections[symbol]
                if symbol in self.ws_callbacks:
                    del self.ws_callbacks[symbol]
                log.info(f"WebSocket stopped for {symbol}")
                return True
        except Exception as e:
            log.error(f"Failed to stop WebSocket for {symbol}: {e}")
        return False
    
    async def get_crypto_prices(self) -> Dict[str, Any]:
        """Get comprehensive crypto prices from Binance"""
        try:
            # Major crypto symbols
            symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'MATICUSDT', 
                      'DOTUSDT', 'LINKUSDT', 'UNIUSDT', 'AAVEUSDT', 'COMPUSDT']
            
            # Get 24hr tickers
            tickers = await self.get_24hr_ticker()
            ticker_dict = {ticker.symbol: ticker for ticker in tickers}
            
            # Format data for the bot
            crypto_data = {}
            for symbol in symbols:
                if symbol in ticker_dict:
                    ticker = ticker_dict[symbol]
                    base_symbol = symbol.replace('USDT', '')
                    
                    crypto_data[base_symbol] = {
                        'symbol': base_symbol,
                        'price': ticker.price,
                        'price_change_24h': ticker.price_change_percent,
                        'volume_24h': ticker.volume,
                        'high_24h': ticker.high_price,
                        'low_24h': ticker.low_price,
                        'bid_price': ticker.bid_price,
                        'ask_price': ticker.ask_price,
                        'weighted_avg_price': ticker.weighted_avg_price,
                        'count': ticker.count,
                        'source': 'Binance'
                    }
            
            return {
                'crypto_prices': crypto_data,
                'total_symbols': len(crypto_data),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            log.error(f"Failed to get crypto prices: {e}")
            return {}
    
    async def get_forex_rates(self) -> Dict[str, Any]:
        """Get forex rates (using crypto pairs as proxy)"""
        try:
            # Forex proxy pairs (using USDT as base)
            forex_pairs = {
                'EURUSDT': 'EUR/USD',
                'GBPUSDT': 'GBP/USD', 
                'JPYUSDT': 'USD/JPY',
                'CHFUSDT': 'USD/CHF',
                'CADUSDT': 'USD/CAD',
                'AUDUSDT': 'AUD/USD',
                'NZDUSDT': 'NZD/USD'
            }
            
            # Get tickers for forex pairs
            tickers = await self.get_24hr_ticker()
            ticker_dict = {ticker.symbol: ticker for ticker in tickers}
            
            forex_data = {}
            for symbol, pair_name in forex_pairs.items():
                if symbol in ticker_dict:
                    ticker = ticker_dict[symbol]
                    forex_data[pair_name] = {
                        'pair': pair_name,
                        'rate': ticker.price,
                        'change_24h': ticker.price_change_percent,
                        'volume_24h': ticker.volume,
                        'high_24h': ticker.high_price,
                        'low_24h': ticker.low_price,
                        'source': 'Binance'
                    }
            
            return {
                'forex_rates': forex_data,
                'total_pairs': len(forex_data),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            log.error(f"Failed to get forex rates: {e}")
            return {}
    
    async def get_market_summary(self) -> Dict[str, Any]:
        """Get comprehensive market summary"""
        try:
            # Get crypto prices
            crypto_data = await self.get_crypto_prices()
            
            # Get forex rates
            forex_data = await self.get_forex_rates()
            
            # Calculate market metrics
            crypto_prices = crypto_data.get('crypto_prices', {})
            total_crypto_volume = sum(price.get('volume_24h', 0) for price in crypto_prices.values())
            
            # Find top gainers and losers
            price_changes = [(symbol, price.get('price_change_24h', 0)) 
                           for symbol, price in crypto_prices.items()]
            price_changes.sort(key=lambda x: x[1], reverse=True)
            
            top_gainers = price_changes[:3]
            top_losers = price_changes[-3:]
            
            return {
                'crypto_data': crypto_data,
                'forex_data': forex_data,
                'market_metrics': {
                    'total_crypto_volume': total_crypto_volume,
                    'total_symbols': len(crypto_prices),
                    'top_gainers': top_gainers,
                    'top_losers': top_losers
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            log.error(f"Failed to get market summary: {e}")
            return {}


class BinanceWebSocketManager:
    """Manager for Binance WebSocket connections"""
    
    def __init__(self, binance_api: BinanceAPI):
        self.binance_api = binance_api
        self.active_streams = {}
        self.data_callbacks = {}
    
    async def start_price_stream(self, symbols: List[str], callback=None) -> bool:
        """Start real-time price streaming for multiple symbols"""
        try:
            for symbol in symbols:
                success = await self.binance_api.start_websocket_stream(
                    symbol, "ticker", callback
                )
                if success:
                    self.active_streams[symbol] = "ticker"
                    if callback:
                        self.data_callbacks[symbol] = callback
            
            return len(self.active_streams) > 0
            
        except Exception as e:
            log.error(f"Failed to start price streams: {e}")
            return False
    
    async def start_kline_stream(self, symbols: List[str], callback=None) -> bool:
        """Start real-time kline streaming for multiple symbols"""
        try:
            for symbol in symbols:
                success = await self.binance_api.start_websocket_stream(
                    symbol, "kline", callback
                )
                if success:
                    self.active_streams[symbol] = "kline"
                    if callback:
                        self.data_callbacks[symbol] = callback
            
            return len(self.active_streams) > 0
            
        except Exception as e:
            log.error(f"Failed to start kline streams: {e}")
            return False
    
    async def stop_all_streams(self) -> bool:
        """Stop all active WebSocket streams"""
        try:
            for symbol in list(self.active_streams.keys()):
                await self.binance_api.stop_websocket_stream(symbol)
                if symbol in self.data_callbacks:
                    del self.data_callbacks[symbol]
            
            self.active_streams.clear()
            return True
            
        except Exception as e:
            log.error(f"Failed to stop streams: {e}")
            return False
    
    def get_active_streams(self) -> Dict[str, str]:
        """Get list of active streams"""
        return self.active_streams.copy()
