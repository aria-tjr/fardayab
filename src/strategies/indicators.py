"""
Technical analysis indicators
"""
import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Collection of technical analysis indicators"""
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def donchian_channels(high: pd.Series, low: pd.Series, period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Donchian Channels"""
        upper = high.rolling(window=period).max()
        lower = low.rolling(window=period).min()
        middle = (upper + lower) / 2
        return upper, middle, lower
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return upper, sma, lower
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD"""
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Calculate Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return k_percent, d_percent
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Williams %R"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        wr = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return wr
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index"""
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate Directional Movement
        dm_plus = high.diff()
        dm_minus = -low.diff()
        
        dm_plus = dm_plus.where((dm_plus > dm_minus) & (dm_plus > 0), 0)
        dm_minus = dm_minus.where((dm_minus > dm_plus) & (dm_minus > 0), 0)
        
        # Calculate smoothed values
        atr = tr.rolling(window=period).mean()
        di_plus = 100 * (dm_plus.rolling(window=period).mean() / atr)
        di_minus = 100 * (dm_minus.rolling(window=period).mean() / atr)
        
        # Calculate ADX
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        adx = dx.rolling(window=period).mean()
        
        return adx
    
    @staticmethod
    def volume_profile(volume: pd.Series, price: pd.Series, bins: int = 20) -> Dict:
        """Calculate volume profile"""
        # Create price bins
        price_min = price.min()
        price_max = price.max()
        bin_size = (price_max - price_min) / bins
        
        # Assign prices to bins
        price_bins = ((price - price_min) / bin_size).astype(int)
        price_bins = price_bins.clip(0, bins - 1)
        
        # Calculate volume for each bin
        volume_profile = {}
        for i in range(bins):
            bin_price = price_min + (i * bin_size)
            bin_volume = volume[price_bins == i].sum()
            volume_profile[bin_price] = bin_volume
        
        return volume_profile
    
    @staticmethod
    def support_resistance(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 20) -> Tuple[List[float], List[float]]:
        """Identify support and resistance levels"""
        # Find local maxima and minima
        highs = high.rolling(window=window, center=True).max()
        lows = low.rolling(window=window, center=True).min()
        
        resistance_levels = []
        support_levels = []
        
        for i in range(window, len(high) - window):
            if high.iloc[i] == highs.iloc[i]:
                resistance_levels.append(high.iloc[i])
            if low.iloc[i] == lows.iloc[i]:
                support_levels.append(low.iloc[i])
        
        return support_levels, resistance_levels
    
    def obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate On-Balance Volume (OBV)"""
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    def mfi(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Money Flow Index (MFI)"""
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume
        
        positive_flow = pd.Series(index=close.index, dtype=float)
        negative_flow = pd.Series(index=close.index, dtype=float)
        
        for i in range(1, len(typical_price)):
            if typical_price.iloc[i] > typical_price.iloc[i-1]:
                positive_flow.iloc[i] = money_flow.iloc[i]
                negative_flow.iloc[i] = 0
            elif typical_price.iloc[i] < typical_price.iloc[i-1]:
                positive_flow.iloc[i] = 0
                negative_flow.iloc[i] = money_flow.iloc[i]
            else:
                positive_flow.iloc[i] = 0
                negative_flow.iloc[i] = 0
        
        positive_flow_ma = positive_flow.rolling(period).sum()
        negative_flow_ma = negative_flow.rolling(period).sum()
        
        mfi = 100 - (100 / (1 + positive_flow_ma / negative_flow_ma))
        return mfi
    
    def vwap(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate Volume Weighted Average Price (VWAP)"""
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap

    def tma(self, close: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Triangular Moving Average (TMA) - High win rate indicator"""
        sma1 = close.rolling(period).mean()
        sma2 = sma1.rolling(period).mean()
        return sma2

    def pb_forex_signal(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate PB Forex Signal - High accuracy entry signal"""
        # Price action based signal
        price_change = close.pct_change()
        volume_change = volume.pct_change()
        
        # Combine price and volume momentum
        signal = (price_change * 0.7 + volume_change * 0.3).rolling(5).mean()
        return signal

    def haos_visual_alert(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate Haos Visual Alert - Multi-confirmation signal"""
        # RSI divergence
        rsi = self.rsi(close, 14)
        rsi_divergence = (rsi - rsi.shift(1)).rolling(5).mean()
        
        # Volume confirmation
        volume_ma = volume.rolling(20).mean()
        volume_ratio = volume / volume_ma
        
        # Price momentum
        price_momentum = close.pct_change().rolling(5).mean()
        
        # Combined signal strength
        signal_strength = (rsi_divergence * 0.4 + volume_ratio * 0.3 + price_momentum * 0.3)
        
        return signal_strength

    def fibonacci_retracement(self, high: pd.Series, low: pd.Series, period: int = 20) -> Dict:
        """Calculate Fibonacci retracement levels"""
        recent_high = high.rolling(period).max()
        recent_low = low.rolling(period).min()
        
        diff = recent_high - recent_low
        
        return {
            'level_0': recent_high,
            'level_236': recent_high - (0.236 * diff),
            'level_382': recent_high - (0.382 * diff),
            'level_500': recent_high - (0.500 * diff),
            'level_618': recent_high - (0.618 * diff),
            'level_786': recent_high - (0.786 * diff),
            'level_100': recent_low
        }

    def pivot_points(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        """Calculate Pivot Points for support/resistance"""
        pivot = (high + low + close) / 3
        
        return {
            'pivot': pivot,
            'r1': 2 * pivot - low,
            'r2': pivot + (high - low),
            'r3': high + 2 * (pivot - low),
            's1': 2 * pivot - high,
            's2': pivot - (high - low),
            's3': low - 2 * (high - pivot)
        }

    def volume_price_trend(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate Volume Price Trend (VPT) - High win rate indicator"""
        vpt = pd.Series(index=close.index, dtype=float)
        vpt.iloc[0] = 0
        
        for i in range(1, len(close)):
            price_change = (close.iloc[i] - close.iloc[i-1]) / close.iloc[i-1]
            vpt.iloc[i] = vpt.iloc[i-1] + (price_change * volume.iloc[i])
        
        return vpt

    def accumulation_distribution(self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate Accumulation/Distribution Line - High win rate indicator"""
        clv = ((close - low) - (high - close)) / (high - low)
        clv = clv.fillna(0)  # Handle division by zero
        ad = (clv * volume).cumsum()
        return ad

    def commodity_channel_index(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index (CCI) - High win rate indicator"""
        typical_price = (high + low + close) / 3
        sma = typical_price.rolling(period).mean()
        mad = typical_price.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())))
        cci = (typical_price - sma) / (0.015 * mad)
        return cci

    def williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Williams %R - High win rate indicator"""
        highest_high = high.rolling(period).max()
        lowest_low = low.rolling(period).min()
        wr = -100 * (highest_high - close) / (highest_high - lowest_low)
        return wr

    def ultimate_oscillator(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Calculate Ultimate Oscillator - High win rate indicator"""
        tr = np.maximum(high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))
        bp = close - np.minimum(low, close.shift(1))
        
        avg7 = bp.rolling(7).sum() / tr.rolling(7).sum()
        avg14 = bp.rolling(14).sum() / tr.rolling(14).sum()
        avg28 = bp.rolling(28).sum() / tr.rolling(28).sum()
        
        uo = 100 * (4 * avg7 + 2 * avg14 + avg28) / 7
        return uo

    def price_oscillator(self, close: pd.Series, fast: int = 12, slow: int = 26) -> pd.Series:
        """Calculate Price Oscillator - High win rate indicator"""
        fast_ma = close.rolling(fast).mean()
        slow_ma = close.rolling(slow).mean()
        po = ((fast_ma - slow_ma) / slow_ma) * 100
        return po

    def market_facilitation_index(self, high: pd.Series, low: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate Market Facilitation Index (MFI) - High win rate indicator"""
        mfi = (high - low) / volume
        return mfi
