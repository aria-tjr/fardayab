from __future__ import annotations

import asyncio
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx
import numpy as np
from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


@dataclass
class TechnicalIndicator:
    """Technical indicator data structure"""
    name: str
    value: float
    signal: str  # 'bullish', 'bearish', 'neutral'
    strength: float  # 0-100
    description: str


@dataclass
class MarketStructure:
    """Market structure analysis"""
    trend: str  # 'uptrend', 'downtrend', 'sideways'
    support_levels: List[float]
    resistance_levels: List[float]
    key_levels: List[float]
    volatility: float
    volume_profile: Dict[str, float]


class AdvancedTechnicalAnalysis:
    """Advanced technical analysis for crypto and forex markets"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
    async def fetch_historical_data(self, symbol: str, timeframe: str = "1d", limit: int = 200) -> List[Dict[str, Any]]:
        """Fetch historical price data for technical analysis"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if symbol.upper() in ['BTC', 'ETH', 'ADA', 'SOL', 'MATIC']:
                    # Use CoinGecko for crypto
                    coin_id = self._get_coin_id(symbol)
                    response = await client.get(
                        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
                        params={
                            "vs_currency": "usd",
                            "days": min(limit // 24, 365),  # Convert to days
                            "interval": "daily" if timeframe == "1d" else "hourly"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        prices = data.get("prices", [])
                        volumes = data.get("total_volumes", [])
                        
                        return [
                            {
                                'timestamp': int(price[0]),
                                'open': price[1],
                                'high': price[1] * 1.02,  # Approximate
                                'low': price[1] * 0.98,   # Approximate
                                'close': price[1],
                                'volume': vol[1] if vol else 0
                            }
                            for price, vol in zip(prices, volumes)
                        ]
                else:
                    # Use Alpha Vantage for forex
                    response = await client.get(
                        "https://www.alphavantage.co/query",
                        params={
                            "function": "FX_DAILY",
                            "from_symbol": symbol[:3],
                            "to_symbol": symbol[3:],
                            "apikey": getattr(self.settings, 'ALPHA_VANTAGE_KEY', 'demo'),
                            "outputsize": "compact"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        time_series = data.get("Time Series (FX)", {})
                        
                        return [
                            {
                                'timestamp': int(datetime.strptime(date, "%Y-%m-%d").timestamp()),
                                'open': float(day_data["1. open"]),
                                'high': float(day_data["2. high"]),
                                'low': float(day_data["3. low"]),
                                'close': float(day_data["4. close"]),
                                'volume': 0  # Forex doesn't have volume
                            }
                            for date, day_data in sorted(time_series.items())[-limit:]
                        ]
        except Exception as e:
            log.warning(f"Failed to fetch historical data for {symbol}: {e}")
            return []
    
    def _get_coin_id(self, symbol: str) -> str:
        """Convert symbol to CoinGecko coin ID"""
        symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'ADA': 'cardano',
            'SOL': 'solana',
            'MATIC': 'matic-network',
            'DOT': 'polkadot',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'AAVE': 'aave',
            'COMP': 'compound-governance-token'
        }
        return symbol_map.get(symbol.upper(), 'bitcoin')
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> TechnicalIndicator:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return TechnicalIndicator("RSI", 50, "neutral", 0, "Insufficient data")
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        if rsi > 70:
            signal = "bearish"
            strength = min((rsi - 70) * 3.33, 100)
        elif rsi < 30:
            signal = "bullish"
            strength = min((30 - rsi) * 3.33, 100)
        else:
            signal = "neutral"
            strength = 0
        
        description = f"RSI: {rsi:.2f} - {'Overbought' if rsi > 70 else 'Oversold' if rsi < 30 else 'Neutral'}"
        
        return TechnicalIndicator("RSI", rsi, signal, strength, description)
    
    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, TechnicalIndicator]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow + signal:
            return {
                "MACD": TechnicalIndicator("MACD", 0, "neutral", 0, "Insufficient data"),
                "Signal": TechnicalIndicator("Signal", 0, "neutral", 0, "Insufficient data"),
                "Histogram": TechnicalIndicator("Histogram", 0, "neutral", 0, "Insufficient data")
            }
        
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(ema_fast))]
        signal_line = self._calculate_ema(macd_line, signal)
        histogram = [macd_line[i] - signal_line[i] for i in range(len(macd_line))]
        
        current_macd = macd_line[-1]
        current_signal = signal_line[-1]
        current_histogram = histogram[-1]
        
        # MACD signal
        if current_macd > current_signal:
            macd_signal = "bullish"
            macd_strength = min(abs(current_histogram) * 100, 100)
        else:
            macd_signal = "bearish"
            macd_strength = min(abs(current_histogram) * 100, 100)
        
        # Signal line
        if current_signal > 0:
            signal_signal = "bullish"
            signal_strength = min(current_signal * 10, 100)
        else:
            signal_signal = "bearish"
            signal_strength = min(abs(current_signal) * 10, 100)
        
        # Histogram
        if current_histogram > 0:
            hist_signal = "bullish"
            hist_strength = min(current_histogram * 100, 100)
        else:
            hist_signal = "bearish"
            hist_strength = min(abs(current_histogram) * 100, 100)
        
        return {
            "MACD": TechnicalIndicator("MACD", current_macd, macd_signal, macd_strength, 
                                    f"MACD: {current_macd:.4f}"),
            "Signal": TechnicalIndicator("Signal", current_signal, signal_signal, signal_strength,
                                      f"Signal: {current_signal:.4f}"),
            "Histogram": TechnicalIndicator("Histogram", current_histogram, hist_signal, hist_strength,
                                         f"Histogram: {current_histogram:.4f}")
        }
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2) -> Dict[str, TechnicalIndicator]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return {
                "Upper": TechnicalIndicator("Upper Band", 0, "neutral", 0, "Insufficient data"),
                "Middle": TechnicalIndicator("Middle Band", 0, "neutral", 0, "Insufficient data"),
                "Lower": TechnicalIndicator("Lower Band", 0, "neutral", 0, "Insufficient data"),
                "Position": TechnicalIndicator("Position", 0, "neutral", 0, "Insufficient data")
            }
        
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / period
        variance = sum((price - sma) ** 2 for price in recent_prices) / period
        std = math.sqrt(variance)
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        current_price = prices[-1]
        
        # Position relative to bands
        if current_price > upper_band:
            position_signal = "overbought"
            position_strength = min(((current_price - upper_band) / upper_band) * 100, 100)
        elif current_price < lower_band:
            position_signal = "oversold"
            position_strength = min(((lower_band - current_price) / lower_band) * 100, 100)
        else:
            position_signal = "neutral"
            position_strength = 0
        
        return {
            "Upper": TechnicalIndicator("Upper Band", upper_band, "resistance", 100, 
                                     f"Upper: {upper_band:.2f}"),
            "Middle": TechnicalIndicator("Middle Band", sma, "neutral", 50, 
                                      f"SMA: {sma:.2f}"),
            "Lower": TechnicalIndicator("Lower Band", lower_band, "support", 100,
                                     f"Lower: {lower_band:.2f}"),
            "Position": TechnicalIndicator("Position", current_price, position_signal, position_strength,
                                        f"Price: {current_price:.2f} - {position_signal.title()}")
        }
    
    def calculate_support_resistance(self, prices: List[float], window: int = 20) -> MarketStructure:
        """Calculate support and resistance levels"""
        if len(prices) < window:
            return MarketStructure("sideways", [], [], [], 0, {})
        
        # Find local peaks and troughs
        highs = []
        lows = []
        
        for i in range(window, len(prices) - window):
            if all(prices[i] >= prices[j] for j in range(i - window, i + window + 1)):
                highs.append(prices[i])
            if all(prices[i] <= prices[j] for j in range(i - window, i + window + 1)):
                lows.append(prices[i])
        
        # Calculate trend
        recent_prices = prices[-20:]
        trend_slope = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
        
        if trend_slope > 0.01:
            trend = "uptrend"
        elif trend_slope < -0.01:
            trend = "downtrend"
        else:
            trend = "sideways"
        
        # Calculate volatility
        returns = [prices[i] / prices[i-1] - 1 for i in range(1, len(prices))]
        volatility = math.sqrt(sum(r**2 for r in returns) / len(returns)) * 100
        
        # Volume profile (simplified)
        volume_profile = {
            "high_volume": max(prices) * 0.8,
            "medium_volume": max(prices) * 0.5,
            "low_volume": max(prices) * 0.2
        }
        
        return MarketStructure(
            trend=trend,
            support_levels=sorted(lows, reverse=True)[:5],
            resistance_levels=sorted(highs)[-5:],
            key_levels=sorted(highs + lows)[-10:],
            volatility=volatility,
            volume_profile=volume_profile
        )
    
    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        if not prices:
            return []
        
        multiplier = 2 / (period + 1)
        ema = [prices[0]]
        
        for i in range(1, len(prices)):
            ema.append((prices[i] * multiplier) + (ema[-1] * (1 - multiplier)))
        
        return ema
    
    async def get_comprehensive_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive technical analysis for a symbol"""
        try:
            # Fetch historical data
            historical_data = await self.fetch_historical_data(symbol, "1d", 200)
            
            if not historical_data:
                return {"error": f"No data available for {symbol}"}
            
            # Extract prices
            prices = [candle['close'] for candle in historical_data]
            
            # Calculate indicators
            rsi = self.calculate_rsi(prices)
            macd = self.calculate_macd(prices)
            bollinger = self.calculate_bollinger_bands(prices)
            market_structure = self.calculate_support_resistance(prices)
            
            # Overall signal strength
            bullish_signals = sum(1 for indicator in [rsi] + list(macd.values()) + list(bollinger.values()) 
                                if indicator.signal == "bullish")
            bearish_signals = sum(1 for indicator in [rsi] + list(macd.values()) + list(bollinger.values()) 
                                if indicator.signal == "bearish")
            
            overall_signal = "bullish" if bullish_signals > bearish_signals else "bearish" if bearish_signals > bullish_signals else "neutral"
            signal_strength = abs(bullish_signals - bearish_signals) * 20
            
            return {
                "symbol": symbol,
                "current_price": prices[-1],
                "rsi": rsi,
                "macd": macd,
                "bollinger_bands": bollinger,
                "market_structure": market_structure,
                "overall_signal": overall_signal,
                "signal_strength": min(signal_strength, 100),
                "analysis_timestamp": datetime.now().isoformat(),
                "data_points": len(historical_data)
            }
            
        except Exception as e:
            log.error(f"Technical analysis failed for {symbol}: {e}")
            return {"error": f"Analysis failed: {str(e)}"}


class AdvancedMarketScanner:
    """Advanced market scanner for multiple assets"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.technical_analysis = AdvancedTechnicalAnalysis(settings)
        
    async def scan_crypto_markets(self) -> Dict[str, Any]:
        """Scan all major crypto markets for opportunities"""
        try:
            # Major cryptocurrencies to scan
            symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'MATIC', 'DOT', 'LINK', 'UNI', 'AAVE', 'COMP']
            
            # Scan all symbols concurrently
            tasks = [self.technical_analysis.get_comprehensive_analysis(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            opportunities = []
            strong_signals = []
            
            for i, result in enumerate(results):
                if isinstance(result, dict) and "error" not in result:
                    symbol = symbols[i]
                    
                    # Identify opportunities
                    if result["overall_signal"] == "bullish" and result["signal_strength"] > 70:
                        opportunities.append({
                            "symbol": symbol,
                            "signal": "BUY",
                            "strength": result["signal_strength"],
                            "price": result["current_price"],
                            "rsi": result["rsi"].value,
                            "reason": f"Strong bullish signals - RSI: {result['rsi'].value:.1f}"
                        })
                    elif result["overall_signal"] == "bearish" and result["signal_strength"] > 70:
                        opportunities.append({
                            "symbol": symbol,
                            "signal": "SELL",
                            "strength": result["signal_strength"],
                            "price": result["current_price"],
                            "rsi": result["rsi"].value,
                            "reason": f"Strong bearish signals - RSI: {result['rsi'].value:.1f}"
                        })
                    
                    # Track strong signals
                    if result["signal_strength"] > 60:
                        strong_signals.append({
                            "symbol": symbol,
                            "signal": result["overall_signal"],
                            "strength": result["signal_strength"]
                        })
            
            return {
                "scan_timestamp": datetime.now().isoformat(),
                "total_scanned": len(symbols),
                "opportunities": opportunities,
                "strong_signals": strong_signals,
                "market_summary": {
                    "bullish_count": len([s for s in strong_signals if s["signal"] == "bullish"]),
                    "bearish_count": len([s for s in strong_signals if s["signal"] == "bearish"]),
                    "opportunity_count": len(opportunities)
                }
            }
            
        except Exception as e:
            log.error(f"Market scanning failed: {e}")
            return {"error": f"Scanning failed: {str(e)}"}
    
    async def scan_forex_markets(self) -> Dict[str, Any]:
        """Scan major forex pairs for opportunities"""
        try:
            # Major forex pairs
            pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
            
            # Scan all pairs concurrently
            tasks = [self.technical_analysis.get_comprehensive_analysis(pair) for pair in pairs]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            opportunities = []
            
            for i, result in enumerate(results):
                if isinstance(result, dict) and "error" not in result:
                    pair = pairs[i]
                    
                    if result["overall_signal"] == "bullish" and result["signal_strength"] > 60:
                        opportunities.append({
                            "pair": pair,
                            "signal": "BUY",
                            "strength": result["signal_strength"],
                            "price": result["current_price"],
                            "reason": f"Bullish trend - RSI: {result['rsi'].value:.1f}"
                        })
                    elif result["overall_signal"] == "bearish" and result["signal_strength"] > 60:
                        opportunities.append({
                            "pair": pair,
                            "signal": "SELL",
                            "strength": result["signal_strength"],
                            "price": result["current_price"],
                            "reason": f"Bearish trend - RSI: {result['rsi'].value:.1f}"
                        })
            
            return {
                "scan_timestamp": datetime.now().isoformat(),
                "total_scanned": len(pairs),
                "opportunities": opportunities,
                "market_summary": {
                    "opportunity_count": len(opportunities),
                    "strong_trends": len([o for o in opportunities if o["strength"] > 80])
                }
            }
            
        except Exception as e:
            log.error(f"Forex scanning failed: {e}")
            return {"error": f"Forex scanning failed: {str(e)}"}
