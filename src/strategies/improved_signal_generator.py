"""
Improved signal generator with backtest recommendations
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

from .indicators import TechnicalIndicators
from ..config import Config

logger = logging.getLogger(__name__)

class ImprovedSignalGenerator:
    """Improved signal generator based on backtest analysis"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        
        # Improved parameters based on backtest analysis
        self.rsi_oversold = 35  # Reduced from 47
        self.rsi_overbought = 65  # Increased from 53
        self.position_size = 0.05  # Reduced from 0.1
        self.max_drawdown_pct = 3.0  # Maximum 3% loss per trade
        self.min_confidence = 0.8  # Increased from 0.6
        self.volume_threshold = 1.2  # Volume must be 20% above average
        self.atr_threshold = 0.8  # ATR must be 80% of average
        
    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate all technical indicators for a dataframe"""
        indicators = {}
        
        # EMAs with additional EMA 12
        indicators['ema_12'] = self.indicators.ema(df['close'], 12)
        indicators['ema_21'] = self.indicators.ema(df['close'], 21)
        indicators['ema_50'] = self.indicators.ema(df['close'], 50)
        indicators['ema_200'] = self.indicators.ema(df['close'], 200)
        
        # RSI
        indicators['rsi'] = self.indicators.rsi(df['close'], 14)
        
        # ATR
        indicators['atr'] = self.indicators.atr(df['high'], df['low'], df['close'], 14)
        
        # Donchian Channels with reduced period
        indicators['donchian_upper'], indicators['donchian_middle'], indicators['donchian_lower'] = \
            self.indicators.donchian_channels(df['high'], df['low'], 14)  # Reduced from 20
        
        # Bollinger Bands
        indicators['bb_upper'], indicators['bb_middle'], indicators['bb_lower'] = \
            self.indicators.bollinger_bands(df['close'], 20, 2)
        
        # MACD
        indicators['macd'], indicators['macd_signal'], indicators['macd_histogram'] = \
            self.indicators.macd(df['close'])
        
        # Stochastic
        indicators['stoch_k'], indicators['stoch_d'] = \
            self.indicators.stochastic(df['high'], df['low'], df['close'])
        
        # Williams %R
        indicators['williams_r'] = self.indicators.williams_r(df['high'], df['low'], df['close'])
        
        # ADX
        indicators['adx'] = self.indicators.adx(df['high'], df['low'], df['close'])
        
        # Volume indicators
        indicators['volume_ma_20'] = df['volume'].rolling(20).mean()
        indicators['atr_ma_20'] = indicators['atr'].rolling(20).mean()
        
        return indicators
    
    def apply_filters(self, df: pd.DataFrame, indicators: Dict) -> bool:
        """Apply additional filters to improve signal quality"""
        try:
            current_volume = df['volume'].iloc[-1]
            volume_ma = indicators['volume_ma_20'].iloc[-1]
            current_atr = indicators['atr'].iloc[-1]
            atr_ma = indicators['atr_ma_20'].iloc[-1]
            
            # Volume filter
            if current_volume < volume_ma * self.volume_threshold:
                return False
            
            # Volatility filter
            if current_atr < atr_ma * self.atr_threshold:
                return False
            
            # Time filter (only trade during high volume hours UTC 12-16)
            current_hour = datetime.now().hour
            if not (12 <= current_hour <= 16):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return False
    
    def improved_trend_following_signal(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Improved trend following signals"""
        current_price = df['close'].iloc[-1]
        ema_12 = indicators['ema_12'].iloc[-1]
        ema_21 = indicators['ema_21'].iloc[-1]
        ema_50 = indicators['ema_50'].iloc[-1]
        ema_200 = indicators['ema_200'].iloc[-1]
        rsi = indicators['rsi'].iloc[-1]
        donchian_upper = indicators['donchian_upper'].iloc[-1]
        donchian_lower = indicators['donchian_lower'].iloc[-1]
        atr = indicators['atr'].iloc[-1]
        adx = indicators['adx'].iloc[-1]
        
        signal = {
            'type': 'improved_trend_following',
            'direction': None,
            'confidence': 0.0,
            'entry_price': current_price,
            'stop_loss': None,
            'take_profit': None,
            'risk_reward': None,
            'rationale': [],
            'conditions_met': []
        }
        
        # Check for LONG signal
        long_conditions = []
        
        # Price above EMA200 (trend filter)
        if current_price > ema_200:
            long_conditions.append('price_above_ema200')
            signal['conditions_met'].append('قیمت بالای EMA200')
        
        # EMA alignment (12 > 21 > 50)
        if ema_12 > ema_21 > ema_50:
            long_conditions.append('ema_alignment')
            signal['conditions_met'].append('تراز EMA12/21/50')
        
        # RSI in bullish range
        if self.rsi_oversold < rsi < self.rsi_overbought:
            long_conditions.append('rsi_bullish')
            signal['conditions_met'].append(f'RSI صعودی ({rsi:.1f})')
        
        # Donchian breakout
        if current_price > donchian_upper:
            long_conditions.append('donchian_breakout')
            signal['conditions_met'].append('بریک‌اوت Donchian')
        
        # ADX for trend strength
        if adx > 25:  # Strong trend
            long_conditions.append('strong_trend')
            signal['conditions_met'].append(f'روند قوی (ADX: {adx:.1f})')
        
        # Check for SHORT signal
        short_conditions = []
        
        # Price below EMA200 (trend filter)
        if current_price < ema_200:
            short_conditions.append('price_below_ema200')
            signal['conditions_met'].append('قیمت زیر EMA200')
        
        # EMA alignment (12 < 21 < 50)
        if ema_12 < ema_21 < ema_50:
            short_conditions.append('ema_alignment')
            signal['conditions_met'].append('تراز نزولی EMA12/21/50')
        
        # RSI in bearish range
        if self.rsi_oversold < rsi < self.rsi_overbought:
            short_conditions.append('rsi_bearish')
            signal['conditions_met'].append(f'RSI نزولی ({rsi:.1f})')
        
        # Donchian breakdown
        if current_price < donchian_lower:
            short_conditions.append('donchian_breakdown')
            signal['conditions_met'].append('شکست Donchian')
        
        # ADX for trend strength
        if adx > 25:  # Strong trend
            short_conditions.append('strong_trend')
            signal['conditions_met'].append(f'روند قوی (ADX: {adx:.1f})')
        
        # Determine signal direction and confidence
        if len(long_conditions) >= 4:  # Increased from 3
            signal['direction'] = 'LONG'
            signal['confidence'] = min(len(long_conditions) / 5.0, 1.0)
            
            # Improved stop loss and take profit
            stop_loss = current_price - (1.5 * atr)  # Reduced from 2
            stop_loss = max(stop_loss, current_price * (1 - self.max_drawdown_pct / 100))
            take_profit = current_price + (2.5 * atr)  # Improved R:R ratio
            
            signal['stop_loss'] = stop_loss
            signal['take_profit'] = take_profit
            signal['risk_reward'] = (take_profit - current_price) / (current_price - stop_loss)
            
        elif len(short_conditions) >= 4:  # Increased from 3
            signal['direction'] = 'SHORT'
            signal['confidence'] = min(len(short_conditions) / 5.0, 1.0)
            
            # Improved stop loss and take profit
            stop_loss = current_price + (1.5 * atr)  # Reduced from 2
            stop_loss = min(stop_loss, current_price * (1 + self.max_drawdown_pct / 100))
            take_profit = current_price - (2.5 * atr)  # Improved R:R ratio
            
            signal['stop_loss'] = stop_loss
            signal['take_profit'] = take_profit
            signal['risk_reward'] = (current_price - take_profit) / (stop_loss - current_price)
        
        return signal
    
    def momentum_signal(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """New momentum-based signal strategy"""
        current_price = df['close'].iloc[-1]
        rsi = indicators['rsi'].iloc[-1]
        macd = indicators['macd'].iloc[-1]
        macd_signal = indicators['macd_signal'].iloc[-1]
        macd_histogram = indicators['macd_histogram'].iloc[-1]
        volume_ratio = df['volume'].iloc[-1] / indicators['volume_ma_20'].iloc[-1]
        atr = indicators['atr'].iloc[-1]
        
        signal = {
            'type': 'momentum',
            'direction': None,
            'confidence': 0.0,
            'entry_price': current_price,
            'stop_loss': None,
            'take_profit': None,
            'risk_reward': None,
            'rationale': [],
            'conditions_met': []
        }
        
        # Check for LONG signal
        long_conditions = []
        
        # RSI momentum
        if rsi > 50:
            long_conditions.append('rsi_momentum')
            signal['conditions_met'].append(f'RSI مومنتوم ({rsi:.1f})')
        
        # MACD bullish
        if macd > macd_signal and macd_histogram > 0:
            long_conditions.append('macd_bullish')
            signal['conditions_met'].append('MACD صعودی')
        
        # Volume confirmation
        if volume_ratio > 1.5:
            long_conditions.append('volume_confirmation')
            signal['conditions_met'].append(f'تأیید حجم ({volume_ratio:.1f}x)')
        
        # Check for SHORT signal
        short_conditions = []
        
        # RSI momentum
        if rsi < 50:
            short_conditions.append('rsi_momentum')
            signal['conditions_met'].append(f'RSI مومنتوم ({rsi:.1f})')
        
        # MACD bearish
        if macd < macd_signal and macd_histogram < 0:
            short_conditions.append('macd_bearish')
            signal['conditions_met'].append('MACD نزولی')
        
        # Volume confirmation
        if volume_ratio > 1.5:
            short_conditions.append('volume_confirmation')
            signal['conditions_met'].append(f'تأیید حجم ({volume_ratio:.1f}x)')
        
        # Determine signal direction
        if len(long_conditions) >= 3:
            signal['direction'] = 'LONG'
            signal['confidence'] = min(len(long_conditions) / 3.0, 1.0)
            
            stop_loss = current_price - (1.5 * atr)
            take_profit = current_price + (2.0 * atr)
            
            signal['stop_loss'] = stop_loss
            signal['take_profit'] = take_profit
            signal['risk_reward'] = (take_profit - current_price) / (current_price - stop_loss)
            
        elif len(short_conditions) >= 3:
            signal['direction'] = 'SHORT'
            signal['confidence'] = min(len(short_conditions) / 3.0, 1.0)
            
            stop_loss = current_price + (1.5 * atr)
            take_profit = current_price - (2.0 * atr)
            
            signal['stop_loss'] = stop_loss
            signal['take_profit'] = take_profit
            signal['risk_reward'] = (current_price - take_profit) / (stop_loss - current_price)
        
        return signal
    
    def generate_signal(self, symbol: str, df: pd.DataFrame) -> Optional[Dict]:
        """Generate improved trading signal for a symbol"""
        try:
            # Calculate indicators
            indicators = self.calculate_indicators(df)
            
            # Apply filters
            if not self.apply_filters(df, indicators):
                return None
            
            # Generate signals from both strategies
            trend_signal = self.improved_trend_following_signal(df, indicators)
            momentum_signal = self.momentum_signal(df, indicators)
            
            # Choose the signal with higher confidence
            best_signal = None
            if trend_signal['direction'] and trend_signal['confidence'] >= self.min_confidence:
                best_signal = trend_signal
            elif momentum_signal['direction'] and momentum_signal['confidence'] >= self.min_confidence:
                best_signal = momentum_signal
            
            if best_signal:
                best_signal['symbol'] = symbol
                best_signal['timestamp'] = datetime.now()
                best_signal['timeframe'] = '5m'
                
                # Add additional context
                best_signal['volume_24h'] = df['volume'].tail(24).sum() if len(df) >= 24 else df['volume'].sum()
                best_signal['price_change_24h'] = ((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100) if len(df) >= 24 else 0
                
                logger.info(f"Generated {best_signal['direction']} signal for {symbol} with confidence {best_signal['confidence']:.2f}")
            
            return best_signal
            
        except Exception as e:
            logger.error(f"Error generating improved signal for {symbol}: {e}")
            return None
