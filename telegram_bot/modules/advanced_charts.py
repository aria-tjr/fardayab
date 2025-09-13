from __future__ import annotations

import asyncio
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import base64
import io

import httpx
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import matplotlib.patches as patches

from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)

# Set matplotlib to use a non-interactive backend
plt.switch_backend('Agg')

@dataclass
class ChartConfig:
    """Chart configuration parameters"""
    width: int = 12
    height: int = 8
    dpi: int = 100
    style: str = "seaborn-v0_8"
    color_scheme: str = "crypto"  # 'crypto', 'forex', 'classic'
    show_volume: bool = True
    show_indicators: bool = True
    show_grid: bool = True
    show_legend: bool = True


class AdvancedChartGenerator:
    """Advanced chart generation for crypto and forex markets"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
        # Color schemes
        self.color_schemes = {
            "crypto": {
                "bullish": "#00ff88",
                "bearish": "#ff4444",
                "neutral": "#888888",
                "volume": "#4a90e2",
                "background": "#1a1a1a",
                "grid": "#333333",
                "text": "#ffffff"
            },
            "forex": {
                "bullish": "#2ecc71",
                "bearish": "#e74c3c",
                "neutral": "#95a5a6",
                "volume": "#3498db",
                "background": "#ffffff",
                "grid": "#ecf0f1",
                "text": "#2c3e50"
            },
            "classic": {
                "bullish": "#26a69a",
                "bearish": "#ef5350",
                "neutral": "#78909c",
                "volume": "#42a5f5",
                "background": "#fafafa",
                "grid": "#e0e0e0",
                "text": "#212121"
            }
        }
    
    async def generate_candlestick_chart(self, symbol: str, timeframe: str = "1d", 
                                       days: int = 30, config: ChartConfig = None) -> str:
        """Generate candlestick chart for a symbol"""
        try:
            if config is None:
                config = ChartConfig()
            
            # Fetch historical data
            historical_data = await self._fetch_historical_data(symbol, timeframe, days)
            if not historical_data:
                return None
            
            # Set up the plot
            plt.style.use(config.style)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(config.width, config.height), 
                                         dpi=config.dpi, gridspec_kw={'height_ratios': [3, 1]})
            
            colors = self.color_schemes.get(config.color_scheme, self.color_schemes["crypto"])
            
            # Prepare data
            dates = [datetime.fromtimestamp(candle['timestamp']) for candle in historical_data]
            opens = [candle['open'] for candle in historical_data]
            highs = [candle['high'] for candle in historical_data]
            lows = [candle['low'] for candle in historical_data]
            closes = [candle['close'] for candle in historical_data]
            volumes = [candle.get('volume', 0) for candle in historical_data]
            
            # Plot candlesticks
            self._plot_candlesticks(ax1, dates, opens, highs, lows, closes, colors)
            
            # Add technical indicators
            if config.show_indicators:
                self._add_technical_indicators(ax1, dates, closes, colors)
            
            # Plot volume
            if config.show_volume and any(volumes):
                self._plot_volume(ax2, dates, volumes, colors)
            
            # Customize chart
            self._customize_chart(ax1, ax2, symbol, colors, config)
            
            # Convert to base64
            chart_base64 = self._chart_to_base64(fig)
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            log.error(f"Failed to generate candlestick chart for {symbol}: {e}")
            return None
    
    async def generate_line_chart(self, symbol: str, timeframe: str = "1d", 
                                days: int = 30, config: ChartConfig = None) -> str:
        """Generate line chart for a symbol"""
        try:
            if config is None:
                config = ChartConfig()
            
            # Fetch historical data
            historical_data = await self._fetch_historical_data(symbol, timeframe, days)
            if not historical_data:
                return None
            
            # Set up the plot
            plt.style.use(config.style)
            fig, ax = plt.subplots(figsize=(config.width, config.height), dpi=config.dpi)
            
            colors = self.color_schemes.get(config.color_scheme, self.color_schemes["crypto"])
            
            # Prepare data
            dates = [datetime.fromtimestamp(candle['timestamp']) for candle in historical_data]
            closes = [candle['close'] for candle in historical_data]
            
            # Plot line
            ax.plot(dates, closes, color=colors["bullish"], linewidth=2, label=f"{symbol} Price")
            
            # Add moving averages
            if config.show_indicators:
                self._add_moving_averages(ax, dates, closes, colors)
            
            # Customize chart
            self._customize_line_chart(ax, symbol, colors, config)
            
            # Convert to base64
            chart_base64 = self._chart_to_base64(fig)
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            log.error(f"Failed to generate line chart for {symbol}: {e}")
            return None
    
    async def generate_technical_analysis_chart(self, symbol: str, timeframe: str = "1d", 
                                              days: int = 30, config: ChartConfig = None) -> str:
        """Generate comprehensive technical analysis chart"""
        try:
            if config is None:
                config = ChartConfig()
            
            # Fetch historical data
            historical_data = await self._fetch_historical_data(symbol, timeframe, days)
            if not historical_data:
                return None
            
            # Set up the plot with subplots
            plt.style.use(config.style)
            fig = plt.figure(figsize=(config.width, config.height + 2), dpi=config.dpi)
            gs = fig.add_gridspec(4, 1, height_ratios=[3, 1, 1, 1], hspace=0.3)
            
            ax1 = fig.add_subplot(gs[0])  # Price chart
            ax2 = fig.add_subplot(gs[1])  # Volume
            ax3 = fig.add_subplot(gs[2])  # RSI
            ax4 = fig.add_subplot(gs[3])  # MACD
            
            colors = self.color_schemes.get(config.color_scheme, self.color_schemes["crypto"])
            
            # Prepare data
            dates = [datetime.fromtimestamp(candle['timestamp']) for candle in historical_data]
            opens = [candle['open'] for candle in historical_data]
            highs = [candle['high'] for candle in historical_data]
            lows = [candle['low'] for candle in historical_data]
            closes = [candle['close'] for candle in historical_data]
            volumes = [candle.get('volume', 0) for candle in historical_data]
            
            # Plot candlesticks
            self._plot_candlesticks(ax1, dates, opens, highs, lows, closes, colors)
            
            # Add technical indicators to price chart
            self._add_bollinger_bands(ax1, dates, closes, colors)
            self._add_support_resistance(ax1, dates, highs, lows, closes, colors)
            
            # Plot volume
            if any(volumes):
                self._plot_volume(ax2, dates, volumes, colors)
            
            # Plot RSI
            self._plot_rsi(ax3, dates, closes, colors)
            
            # Plot MACD
            self._plot_macd(ax4, dates, closes, colors)
            
            # Customize all subplots
            self._customize_technical_chart(ax1, ax2, ax3, ax4, symbol, colors, config)
            
            # Convert to base64
            chart_base64 = self._chart_to_base64(fig)
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            log.error(f"Failed to generate technical analysis chart for {symbol}: {e}")
            return None
    
    async def generate_market_overview_chart(self, symbols: List[str], config: ChartConfig = None) -> str:
        """Generate market overview chart for multiple symbols"""
        try:
            if config is None:
                config = ChartConfig()
            
            # Fetch data for all symbols
            all_data = {}
            for symbol in symbols:
                data = await self._fetch_historical_data(symbol, "1d", 30)
                if data:
                    all_data[symbol] = data
            
            if not all_data:
                return None
            
            # Set up the plot
            plt.style.use(config.style)
            fig, axes = plt.subplots(2, 2, figsize=(config.width, config.height), dpi=config.dpi)
            axes = axes.flatten()
            
            colors = self.color_schemes.get(config.color_scheme, self.color_schemes["crypto"])
            
            # Plot each symbol
            for i, (symbol, data) in enumerate(all_data.items()):
                if i >= 4:  # Limit to 4 symbols
                    break
                
                ax = axes[i]
                dates = [datetime.fromtimestamp(candle['timestamp']) for candle in data]
                closes = [candle['close'] for candle in data]
                
                # Normalize prices to percentage change
                if closes:
                    first_price = closes[0]
                    normalized_closes = [(price / first_price - 1) * 100 for price in closes]
                    
                    ax.plot(dates, normalized_closes, color=colors["bullish"], linewidth=2)
                    ax.set_title(f"{symbol} (30d % change)", color=colors["text"])
                    ax.grid(True, alpha=0.3, color=colors["grid"])
                    ax.set_facecolor(colors["background"])
            
            # Hide unused subplots
            for i in range(len(all_data), 4):
                axes[i].set_visible(False)
            
            # Set overall title
            fig.suptitle("Market Overview - 30 Day Performance", fontsize=16, color=colors["text"])
            fig.patch.set_facecolor(colors["background"])
            
            # Convert to base64
            chart_base64 = self._chart_to_base64(fig)
            plt.close(fig)
            
            return chart_base64
            
        except Exception as e:
            log.error(f"Failed to generate market overview chart: {e}")
            return None
    
    def _plot_candlesticks(self, ax, dates, opens, highs, lows, closes, colors):
        """Plot candlestick chart"""
        try:
            for i, (date, open_price, high, low, close) in enumerate(zip(dates, opens, highs, lows, closes)):
                # Determine color
                color = colors["bullish"] if close >= open_price else colors["bearish"]
                
                # Draw the wick
                ax.plot([date, date], [low, high], color=color, linewidth=1)
                
                # Draw the body
                body_height = abs(close - open_price)
                body_bottom = min(open_price, close)
                
                if body_height > 0:
                    rect = Rectangle((date - timedelta(hours=6), body_bottom), 
                                   timedelta(hours=12), body_height, 
                                   facecolor=color, edgecolor=color, alpha=0.8)
                    ax.add_patch(rect)
                else:
                    # Doji
                    ax.plot([date - timedelta(hours=6), date + timedelta(hours=6)], 
                           [close, close], color=color, linewidth=2)
            
        except Exception as e:
            log.warning(f"Failed to plot candlesticks: {e}")
    
    def _plot_volume(self, ax, dates, volumes, colors):
        """Plot volume bars"""
        try:
            if not any(volumes):
                return
            
            # Normalize volume for better visualization
            max_volume = max(volumes)
            if max_volume > 0:
                normalized_volumes = [vol / max_volume for vol in volumes]
            else:
                normalized_volumes = volumes
            
            ax.bar(dates, normalized_volumes, color=colors["volume"], alpha=0.7, width=0.8)
            ax.set_ylabel("Volume", color=colors["text"])
            ax.set_facecolor(colors["background"])
            
        except Exception as e:
            log.warning(f"Failed to plot volume: {e}")
    
    def _add_technical_indicators(self, ax, dates, closes, colors):
        """Add technical indicators to the chart"""
        try:
            if len(closes) < 20:
                return
            
            # Simple Moving Averages
            sma_20 = self._calculate_sma(closes, 20)
            sma_50 = self._calculate_sma(closes, 50)
            
            if len(sma_20) > 0:
                ax.plot(dates[-len(sma_20):], sma_20, color=colors["neutral"], 
                       linewidth=1, alpha=0.8, label="SMA 20")
            
            if len(sma_50) > 0:
                ax.plot(dates[-len(sma_50):], sma_50, color=colors["text"], 
                       linewidth=1, alpha=0.8, label="SMA 50")
            
        except Exception as e:
            log.warning(f"Failed to add technical indicators: {e}")
    
    def _add_moving_averages(self, ax, dates, closes, colors):
        """Add moving averages to line chart"""
        try:
            if len(closes) < 20:
                return
            
            # Simple Moving Averages
            sma_20 = self._calculate_sma(closes, 20)
            sma_50 = self._calculate_sma(closes, 50)
            
            if len(sma_20) > 0:
                ax.plot(dates[-len(sma_20):], sma_20, color=colors["neutral"], 
                       linewidth=1, alpha=0.8, label="SMA 20")
            
            if len(sma_50) > 0:
                ax.plot(dates[-len(sma_50):], sma_50, color=colors["text"], 
                       linewidth=1, alpha=0.8, label="SMA 50")
            
        except Exception as e:
            log.warning(f"Failed to add moving averages: {e}")
    
    def _add_bollinger_bands(self, ax, dates, closes, colors):
        """Add Bollinger Bands to the chart"""
        try:
            if len(closes) < 20:
                return
            
            sma_20 = self._calculate_sma(closes, 20)
            if len(sma_20) == 0:
                return
            
            # Calculate standard deviation
            std_dev = []
            for i in range(len(sma_20)):
                start_idx = max(0, i - 19)
                period_closes = closes[start_idx:i + 1]
                if len(period_closes) > 1:
                    std = np.std(period_closes)
                    std_dev.append(std)
                else:
                    std_dev.append(0)
            
            # Calculate bands
            upper_band = [sma_20[i] + 2 * std_dev[i] for i in range(len(sma_20))]
            lower_band = [sma_20[i] - 2 * std_dev[i] for i in range(len(sma_20))]
            
            # Plot bands
            band_dates = dates[-len(sma_20):]
            ax.fill_between(band_dates, upper_band, lower_band, 
                          color=colors["neutral"], alpha=0.1, label="Bollinger Bands")
            ax.plot(band_dates, upper_band, color=colors["neutral"], linewidth=1, alpha=0.7)
            ax.plot(band_dates, lower_band, color=colors["neutral"], linewidth=1, alpha=0.7)
            
        except Exception as e:
            log.warning(f"Failed to add Bollinger Bands: {e}")
    
    def _add_support_resistance(self, ax, dates, highs, lows, closes, colors):
        """Add support and resistance levels"""
        try:
            if len(closes) < 10:
                return
            
            # Find significant levels
            recent_highs = highs[-10:]
            recent_lows = lows[-10:]
            
            resistance_level = max(recent_highs)
            support_level = min(recent_lows)
            
            # Plot levels
            ax.axhline(y=resistance_level, color=colors["bearish"], 
                      linestyle='--', alpha=0.7, label="Resistance")
            ax.axhline(y=support_level, color=colors["bullish"], 
                      linestyle='--', alpha=0.7, label="Support")
            
        except Exception as e:
            log.warning(f"Failed to add support/resistance: {e}")
    
    def _plot_rsi(self, ax, dates, closes, colors):
        """Plot RSI indicator"""
        try:
            if len(closes) < 14:
                return
            
            rsi = self._calculate_rsi(closes, 14)
            if len(rsi) == 0:
                return
            
            rsi_dates = dates[-len(rsi):]
            ax.plot(rsi_dates, rsi, color=colors["bullish"], linewidth=2)
            ax.axhline(y=70, color=colors["bearish"], linestyle='--', alpha=0.7)
            ax.axhline(y=30, color=colors["bullish"], linestyle='--', alpha=0.7)
            ax.axhline(y=50, color=colors["neutral"], linestyle='-', alpha=0.5)
            ax.set_ylabel("RSI", color=colors["text"])
            ax.set_ylim(0, 100)
            ax.set_facecolor(colors["background"])
            
        except Exception as e:
            log.warning(f"Failed to plot RSI: {e}")
    
    def _plot_macd(self, ax, dates, closes, colors):
        """Plot MACD indicator"""
        try:
            if len(closes) < 26:
                return
            
            macd_line, signal_line, histogram = self._calculate_macd(closes)
            if len(macd_line) == 0:
                return
            
            macd_dates = dates[-len(macd_line):]
            ax.plot(macd_dates, macd_line, color=colors["bullish"], linewidth=2, label="MACD")
            ax.plot(macd_dates, signal_line, color=colors["bearish"], linewidth=2, label="Signal")
            ax.bar(macd_dates, histogram, color=colors["volume"], alpha=0.7, width=0.8)
            ax.axhline(y=0, color=colors["neutral"], linestyle='-', alpha=0.5)
            ax.set_ylabel("MACD", color=colors["text"])
            ax.set_facecolor(colors["background"])
            
        except Exception as e:
            log.warning(f"Failed to plot MACD: {e}")
    
    def _calculate_sma(self, prices, period):
        """Calculate Simple Moving Average"""
        try:
            if len(prices) < period:
                return []
            
            sma = []
            for i in range(period - 1, len(prices)):
                sma.append(sum(prices[i - period + 1:i + 1]) / period)
            
            return sma
        except Exception as e:
            log.warning(f"Failed to calculate SMA: {e}")
            return []
    
    def _calculate_rsi(self, prices, period):
        """Calculate RSI"""
        try:
            if len(prices) < period + 1:
                return []
            
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            
            rsi = []
            for i in range(period, len(prices)):
                avg_gain = sum(gains[i-period:i]) / period
                avg_loss = sum(losses[i-period:i]) / period
                
                if avg_loss == 0:
                    rsi.append(100)
                else:
                    rs = avg_gain / avg_loss
                    rsi.append(100 - (100 / (1 + rs)))
            
            return rsi
        except Exception as e:
            log.warning(f"Failed to calculate RSI: {e}")
            return []
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        try:
            if len(prices) < slow + signal:
                return [], [], []
            
            # Calculate EMAs
            ema_fast = self._calculate_ema(prices, fast)
            ema_slow = self._calculate_ema(prices, slow)
            
            # MACD line
            macd_line = [ema_fast[i] - ema_slow[i] for i in range(len(ema_fast))]
            
            # Signal line
            signal_line = self._calculate_ema(macd_line, signal)
            
            # Histogram
            histogram = [macd_line[i] - signal_line[i] for i in range(len(signal_line))]
            
            return macd_line, signal_line, histogram
        except Exception as e:
            log.warning(f"Failed to calculate MACD: {e}")
            return [], [], []
    
    def _calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        try:
            if len(prices) < period:
                return []
            
            multiplier = 2 / (period + 1)
            ema = [prices[0]]
            
            for i in range(1, len(prices)):
                ema.append((prices[i] * multiplier) + (ema[-1] * (1 - multiplier)))
            
            return ema
        except Exception as e:
            log.warning(f"Failed to calculate EMA: {e}")
            return []
    
    def _customize_chart(self, ax1, ax2, symbol, colors, config):
        """Customize the main chart"""
        try:
            # Price chart
            ax1.set_title(f"{symbol} Price Chart", fontsize=14, color=colors["text"])
            ax1.set_ylabel("Price (USD)", color=colors["text"])
            ax1.set_facecolor(colors["background"])
            ax1.grid(config.show_grid, alpha=0.3, color=colors["grid"])
            
            if config.show_legend:
                ax1.legend(loc='upper left')
            
            # Volume chart
            ax2.set_ylabel("Volume", color=colors["text"])
            ax2.set_facecolor(colors["background"])
            ax2.grid(config.show_grid, alpha=0.3, color=colors["grid"])
            
            # Format x-axis
            for ax in [ax1, ax2]:
                ax.tick_params(colors=colors["text"])
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
        except Exception as e:
            log.warning(f"Failed to customize chart: {e}")
    
    def _customize_line_chart(self, ax, symbol, colors, config):
        """Customize line chart"""
        try:
            ax.set_title(f"{symbol} Price Chart", fontsize=14, color=colors["text"])
            ax.set_ylabel("Price (USD)", color=colors["text"])
            ax.set_facecolor(colors["background"])
            ax.grid(config.show_grid, alpha=0.3, color=colors["grid"])
            
            if config.show_legend:
                ax.legend(loc='upper left')
            
            ax.tick_params(colors=colors["text"])
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
        except Exception as e:
            log.warning(f"Failed to customize line chart: {e}")
    
    def _customize_technical_chart(self, ax1, ax2, ax3, ax4, symbol, colors, config):
        """Customize technical analysis chart"""
        try:
            # Price chart
            ax1.set_title(f"{symbol} Technical Analysis", fontsize=14, color=colors["text"])
            ax1.set_ylabel("Price (USD)", color=colors["text"])
            ax1.set_facecolor(colors["background"])
            ax1.grid(config.show_grid, alpha=0.3, color=colors["grid"])
            
            # Volume chart
            ax2.set_ylabel("Volume", color=colors["text"])
            ax2.set_facecolor(colors["background"])
            ax2.grid(config.show_grid, alpha=0.3, color=colors["grid"])
            
            # RSI chart
            ax3.set_ylabel("RSI", color=colors["text"])
            ax3.set_facecolor(colors["background"])
            ax3.grid(config.show_grid, alpha=0.3, color=colors["grid"])
            
            # MACD chart
            ax4.set_ylabel("MACD", color=colors["text"])
            ax4.set_facecolor(colors["background"])
            ax4.grid(config.show_grid, alpha=0.3, color=colors["grid"])
            
            # Format all axes
            for ax in [ax1, ax2, ax3, ax4]:
                ax.tick_params(colors=colors["text"])
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
        except Exception as e:
            log.warning(f"Failed to customize technical chart: {e}")
    
    def _chart_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        try:
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                       facecolor=fig.get_facecolor(), edgecolor='none')
            buffer.seek(0)
            chart_base64 = base64.b64encode(buffer.getvalue()).decode()
            buffer.close()
            return chart_base64
        except Exception as e:
            log.error(f"Failed to convert chart to base64: {e}")
            return None
    
    async def _fetch_historical_data(self, symbol: str, timeframe: str, days: int) -> List[Dict[str, Any]]:
        """Fetch historical data for charting"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if symbol.upper() in ['BTC', 'ETH', 'ADA', 'SOL', 'MATIC', 'DOT', 'LINK', 'UNI', 'AAVE', 'COMP']:
                    # Crypto data from CoinGecko
                    coin_id = self._get_coin_id(symbol)
                    response = await client.get(
                        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
                        params={
                            "vs_currency": "usd",
                            "days": days,
                            "interval": "daily" if timeframe == "1d" else "hourly"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        prices = data.get("prices", [])
                        volumes = data.get("total_volumes", [])
                        
                        historical_data = []
                        for i, (price_data, volume_data) in enumerate(zip(prices, volumes)):
                            # Create OHLC data (simplified)
                            price = price_data[1]
                            historical_data.append({
                                'timestamp': int(price_data[0] / 1000),  # Convert to seconds
                                'open': price,
                                'high': price * 1.02,  # Approximate
                                'low': price * 0.98,   # Approximate
                                'close': price,
                                'volume': volume_data[1] if volume_data else 0
                            })
                        
                        return historical_data
                        
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
