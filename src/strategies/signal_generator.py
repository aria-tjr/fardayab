"""
Signal generation strategies
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

from .indicators import TechnicalIndicators
from .ultra_high_winrate_generator import UltraHighWinRateGenerator
from ..config import Config

logger = logging.getLogger(__name__)

class SignalGenerator:
    """Generates trading signals based on technical analysis"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.ultra_high_winrate_generator = UltraHighWinRateGenerator()
    
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
        
        # Volume and ATR moving averages for filters
        indicators['volume_ma_20'] = df['volume'].rolling(20).mean()
        indicators['atr_ma_20'] = indicators['atr'].rolling(20).mean()
        
        # Advanced high win rate indicators for maximum win rate
        indicators['obv'] = self.indicators.obv(df['close'], df['volume'])
        indicators['mfi'] = self.indicators.mfi(df['high'], df['low'], df['close'], df['volume'])
        indicators['vwap'] = self.indicators.vwap(df['high'], df['low'], df['close'], df['volume'])
        indicators['vpt'] = self.indicators.volume_price_trend(df['close'], df['volume'])
        indicators['ad'] = self.indicators.accumulation_distribution(df['high'], df['low'], df['close'], df['volume'])
        indicators['cci'] = self.indicators.commodity_channel_index(df['high'], df['low'], df['close'])
        indicators['williams_r'] = self.indicators.williams_r(df['high'], df['low'], df['close'])
        indicators['uo'] = self.indicators.ultimate_oscillator(df['high'], df['low'], df['close'])
        indicators['po'] = self.indicators.price_oscillator(df['close'])
        indicators['mfi_index'] = self.indicators.market_facilitation_index(df['high'], df['low'], df['volume'])
        
        return indicators
    
    def apply_filters(self, df: pd.DataFrame, indicators: Dict) -> bool:
        """Apply ultra-strict filters for maximum win rate"""
        try:
            current_volume = df['volume'].iloc[-1]
            volume_ma = indicators['volume_ma_20'].iloc[-1]
            current_atr = indicators['atr'].iloc[-1]
            atr_ma = indicators['atr_ma_20'].iloc[-1]
            
            # Ultra-strict volume filter
            if current_volume < volume_ma * Config.MIN_VOLUME_RATIO:
                return False
            
            # Ultra-strict volatility filter
            if current_atr < atr_ma * Config.MIN_ATR_RATIO:
                return False
            
            # Time filter (only trade during active hours)
            current_hour = datetime.now().hour
            if not (Config.TRADING_HOURS_START <= current_hour <= Config.TRADING_HOURS_END):
                return False
            
            # Market condition adaptation
            if len(df) >= 50:
                # Check for strong trend
                adx = indicators['adx'].iloc[-1]
                if adx < Config.MIN_TREND_STRENGTH:
                    return False
                
                # Check for low volatility (avoid choppy markets)
                price_range = (df['high'].iloc[-20:].max() - df['low'].iloc[-20:].min()) / df['close'].iloc[-1]
                if price_range > 0.1:  # More than 10% range in 20 periods
                    return False
                
                # Check for consistent momentum
                rsi_values = indicators['rsi'].iloc[-5:].values
                if len(rsi_values) >= 5:
                    rsi_consistency = np.std(rsi_values)
                    if rsi_consistency > 15:  # Too much RSI variation
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return False
    
    def trend_following_signal(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Generate trend following signals according to spec:
        LONG: price > EMA200 + bullish EMA21/50 cross + RSI>53 + Donchian breakout (min 3 conditions)
        SHORT: price < EMA200 + bearish EMA21/50 cross + RSI<47 + Donchian breakdown (min 3 conditions)
        """
        current_price = df['close'].iloc[-1]
        ema_21 = indicators['ema_21'].iloc[-1]
        ema_50 = indicators['ema_50'].iloc[-1]
        ema_200 = indicators['ema_200'].iloc[-1]
        rsi = indicators['rsi'].iloc[-1]
        donchian_upper = indicators['donchian_upper'].iloc[-1]
        donchian_lower = indicators['donchian_lower'].iloc[-1]
        atr = indicators['atr'].iloc[-1]
        
        signal = {
            'type': 'trend_following',
            'direction': None,
            'confidence': 0.0,
            'entry_price': current_price,
            'stop_loss': None,
            'take_profit': None,
            'risk_reward': None,
            'rationale': [],
            'conditions_met': []
        }
        
        # Check for LONG signal (per spec: price>EMA200 + bullish EMA21/50 cross + RSI>53 + Donchian breakout)
        long_conditions = []
        
        # 1. Price above EMA200 (trend filter) - MANDATORY
        if current_price > ema_200:
            long_conditions.append('price_above_ema200')
            signal['conditions_met'].append('قیمت بالای EMA200')
        
        # 2. EMA21/EMA50 bullish cross or alignment - MANDATORY
        if ema_21 > ema_50:
            # Check if it's a fresh cross or continuation
            if len(df) >= 2:
                prev_ema21 = indicators['ema_21'].iloc[-2]
                prev_ema50 = indicators['ema_50'].iloc[-2]
                if prev_ema21 <= prev_ema50 or ema_21 > ema_50 * 1.002:  # Fresh cross or strong alignment
                    long_conditions.append('ema21_over_ema50')
                    signal['conditions_met'].append('کراس صعودی EMA21/50')
            else:
                long_conditions.append('ema21_over_ema50')
                signal['conditions_met'].append('کراس صعودی EMA21/50')
        
        # 3. RSI > 53 (per spec) - MANDATORY
        if rsi > 53:
            long_conditions.append('rsi_bullish')
            signal['conditions_met'].append(f'RSI بالای 53 ({rsi:.1f})')
        
        # 4. Donchian breakout - MANDATORY
        if current_price >= donchian_upper * 0.999:  # Allow small tolerance
            long_conditions.append('donchian_breakout')
            signal['conditions_met'].append('بریک‌اوت Donchian')
        
        # Optional additional confirmations (for higher confidence)
        # Volume confirmation
        volume_ma = indicators['volume_ma_20'].iloc[-1]
        current_volume = df['volume'].iloc[-1]
        if current_volume > volume_ma * 1.2:
            long_conditions.append('volume_confirmation')
            signal['conditions_met'].append('تأیید حجم معاملات')
        
        # Check for SHORT signal (per spec: price<EMA200 + bearish EMA21/50 cross + RSI<47 + Donchian breakdown)
        short_conditions = []
        
        # 1. Price below EMA200 (trend filter) - MANDATORY
        if current_price < ema_200:
            short_conditions.append('price_below_ema200')
            signal['conditions_met'].append('قیمت زیر EMA200')
        
        # 2. EMA21/EMA50 bearish cross or alignment - MANDATORY
        if ema_21 < ema_50:
            # Check if it's a fresh cross or continuation
            if len(df) >= 2:
                prev_ema21 = indicators['ema_21'].iloc[-2]
                prev_ema50 = indicators['ema_50'].iloc[-2]
                if prev_ema21 >= prev_ema50 or ema_21 < ema_50 * 0.998:  # Fresh cross or strong alignment
                    short_conditions.append('ema21_under_ema50')
                    signal['conditions_met'].append('کراس نزولی EMA21/50')
            else:
                short_conditions.append('ema21_under_ema50')
                signal['conditions_met'].append('کراس نزولی EMA21/50')
        
        # 3. RSI < 47 (per spec) - MANDATORY
        if rsi < 47:
            short_conditions.append('rsi_bearish')
            signal['conditions_met'].append(f'RSI زیر 47 ({rsi:.1f})')
        
        # 4. Donchian breakdown - MANDATORY
        if current_price <= donchian_lower * 1.001:  # Allow small tolerance
            short_conditions.append('donchian_breakdown')
            signal['conditions_met'].append('شکست Donchian')
        
        # Optional additional confirmations (for higher confidence)
        # Volume confirmation
        if current_volume > volume_ma * 1.2:
            short_conditions.append('volume_confirmation')
            signal['conditions_met'].append('تأیید حجم معاملات')
        
        # Determine signal direction and confidence - per spec: min 3 conditions
        if len(long_conditions) >= 3:
            signal['direction'] = 'LONG'
            signal['confidence'] = min(0.7 + 0.05 * (len(long_conditions) - 3), 0.95)
            
            # Use ATR for SL/TP only (per spec)
            stop_loss = current_price - (1.5 * atr)
            stop_loss = max(stop_loss, current_price * (1 - Config.MAX_DRAWDOWN_PCT / 100))
            take_profit = current_price + (1.5 * atr)
            
            signal['stop_loss'] = stop_loss
            signal['take_profit'] = take_profit
            signal['risk_reward'] = (take_profit - current_price) / (current_price - stop_loss)
            
            signal['rationale'] = [
                f"قیمت فعلی: ${current_price:.4f}",
                f"EMA21: ${ema_21:.4f}",
                f"EMA50: ${ema_50:.4f}",
                f"EMA200: ${ema_200:.4f}",
                f"RSI: {rsi:.1f}",
                f"Donchian Upper: ${donchian_upper:.4f}",
                f"ATR: ${atr:.4f}"
            ]
            
        elif len(short_conditions) >= 3:
            signal['direction'] = 'SHORT'
            signal['confidence'] = min(0.7 + 0.05 * (len(short_conditions) - 3), 0.95)
            
            # Use ATR for SL/TP only (per spec)
            stop_loss = current_price + (1.5 * atr)
            stop_loss = min(stop_loss, current_price * (1 + Config.MAX_DRAWDOWN_PCT / 100))
            take_profit = current_price - (1.5 * atr)
            
            signal['stop_loss'] = stop_loss
            signal['take_profit'] = take_profit
            signal['risk_reward'] = (current_price - take_profit) / (stop_loss - current_price)
            
            signal['rationale'] = [
                f"قیمت فعلی: ${current_price:.4f}",
                f"EMA21: ${ema_21:.4f}",
                f"EMA50: ${ema_50:.4f}",
                f"EMA200: ${ema_200:.4f}",
                f"RSI: {rsi:.1f}",
                f"Donchian Lower: ${donchian_lower:.4f}",
                f"ATR: ${atr:.4f}"
            ]
        
        return signal
    
    def mean_reversion_signal(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Generate mean reversion signals based on Bollinger Bands for increased signal count
        Strategy: Buy oversold bounces, sell overbought rejections
        """
        current_price = df['close'].iloc[-1]
        bb_upper = indicators['bb_upper'].iloc[-1]
        bb_middle = indicators['bb_middle'].iloc[-1]
        bb_lower = indicators['bb_lower'].iloc[-1]
        rsi = indicators['rsi'].iloc[-1]
        stoch_k = indicators['stoch_k'].iloc[-1]
        stoch_d = indicators['stoch_d'].iloc[-1]
        atr = indicators['atr'].iloc[-1]
        volume_ma = indicators['volume_ma_20'].iloc[-1]
        current_volume = df['volume'].iloc[-1]
        
        signal = {
            'type': 'mean_reversion',
            'direction': None,
            'confidence': 0.0,
            'entry_price': current_price,
            'stop_loss': None,
            'take_profit': None,
            'risk_reward': None,
            'rationale': [],
            'conditions_met': []
        }
        
        # Check for LONG signal (oversold bounce) - Relaxed conditions for more signals
        long_conditions = []
        
        # Price near lower Bollinger Band (relaxed from 20% to 30%)
        bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
        if bb_position < 0.3:  # Within 30% of lower band
            long_conditions.append('bb_oversold')
            signal['conditions_met'].append('قیمت نزدیک باند پایین Bollinger')
        
        # RSI oversold (relaxed from 30 to 35)
        if rsi < 35:
            long_conditions.append('rsi_oversold')
            signal['conditions_met'].append(f'RSI اشباع فروش ({rsi:.1f})')
        
        # Stochastic oversold (relaxed from 20 to 25)
        if stoch_k < 25 and stoch_d < 25:
            long_conditions.append('stoch_oversold')
            signal['conditions_met'].append(f'Stochastic اشباع فروش (K:{stoch_k:.1f}, D:{stoch_d:.1f})')
        
        # Volume confirmation (optional)
        if current_volume > volume_ma * 1.1:  # Lower threshold for more signals
            long_conditions.append('volume_confirmation')
            signal['conditions_met'].append('تأیید حجم')
        
        # Check for SHORT signal (overbought rejection) - Relaxed conditions for more signals
        short_conditions = []
        
        # Price near upper Bollinger Band (relaxed from 80% to 70%)
        if bb_position > 0.7:  # Within 30% of upper band
            short_conditions.append('bb_overbought')
            signal['conditions_met'].append('قیمت نزدیک باند بالای Bollinger')
        
        # RSI overbought (relaxed from 70 to 65)
        if rsi > 65:
            short_conditions.append('rsi_overbought')
            signal['conditions_met'].append(f'RSI اشباع خرید ({rsi:.1f})')
        
        # Stochastic overbought (relaxed from 80 to 75)
        if stoch_k > 75 and stoch_d > 75:
            short_conditions.append('stoch_overbought')
            signal['conditions_met'].append(f'Stochastic اشباع خرید (K:{stoch_k:.1f}, D:{stoch_d:.1f})')
        
        # Volume confirmation (optional)
        if current_volume > volume_ma * 1.1:  # Lower threshold for more signals
            short_conditions.append('volume_confirmation')
            signal['conditions_met'].append('تأیید حجم')
        
        # Determine signal direction and confidence
        if len(long_conditions) >= 2:
            signal['direction'] = 'LONG'
            signal['confidence'] = min(len(long_conditions) / 3.0, 1.0)
            
            # Calculate stop loss and take profit
            stop_loss = current_price - (1.5 * atr)
            take_profit = bb_middle  # Target middle band
            
            signal['stop_loss'] = stop_loss
            signal['take_profit'] = take_profit
            signal['risk_reward'] = (take_profit - current_price) / (current_price - stop_loss)
            
            signal['rationale'] = [
                f"قیمت فعلی: ${current_price:.4f}",
                f"BB Upper: ${bb_upper:.4f}",
                f"BB Middle: ${bb_middle:.4f}",
                f"BB Lower: ${bb_lower:.4f}",
                f"RSI: {rsi:.1f}",
                f"Stochastic K: {stoch_k:.1f}",
                f"Stochastic D: {stoch_d:.1f}"
            ]
            
        elif len(short_conditions) >= 2:
            signal['direction'] = 'SHORT'
            signal['confidence'] = min(len(short_conditions) / 3.0, 1.0)
            
            # Calculate stop loss and take profit
            stop_loss = current_price + (1.5 * atr)
            take_profit = bb_middle  # Target middle band
            
            signal['stop_loss'] = stop_loss
            signal['take_profit'] = take_profit
            signal['risk_reward'] = (current_price - take_profit) / (stop_loss - current_price)
            
            signal['rationale'] = [
                f"قیمت فعلی: ${current_price:.4f}",
                f"BB Upper: ${bb_upper:.4f}",
                f"BB Middle: ${bb_middle:.4f}",
                f"BB Lower: ${bb_lower:.4f}",
                f"RSI: {rsi:.1f}",
                f"Stochastic K: {stoch_k:.1f}",
                f"Stochastic D: {stoch_d:.1f}"
            ]
        
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
            
            # Optimized take-profit and stop-loss for better R:R ratio
            stop_loss = current_price - (Config.STOP_LOSS_ATR_MULTIPLIER * atr)
            take_profit = current_price + (Config.TAKE_PROFIT_ATR_MULTIPLIER * atr)
            
            signal['stop_loss'] = stop_loss
            signal['take_profit'] = take_profit
            signal['risk_reward'] = (take_profit - current_price) / (current_price - stop_loss)
            
        elif len(short_conditions) >= 3:
            signal['direction'] = 'SHORT'
            signal['confidence'] = min(len(short_conditions) / 3.0, 1.0)
            
            # Optimized take-profit and stop-loss for better R:R ratio
            stop_loss = current_price + (Config.STOP_LOSS_ATR_MULTIPLIER * atr)
            take_profit = current_price - (Config.TAKE_PROFIT_ATR_MULTIPLIER * atr)
            
            signal['stop_loss'] = stop_loss
            signal['take_profit'] = take_profit
            signal['risk_reward'] = (current_price - take_profit) / (stop_loss - current_price)
        
        return signal
    
    def generate_signal(self, symbol: str, df: pd.DataFrame, exchange_fetcher=None) -> Optional[Dict]:
        """Generate ultra high win rate trading signal for a symbol"""
        try:
            # Use ultra high win rate mode if enabled
            if Config.ULTRA_HIGH_WINRATE_MODE:
                return self.ultra_high_winrate_generator.generate_signal(symbol, df, exchange_fetcher)
            
            # Calculate indicators
            indicators = self.calculate_indicators(df)
            
            # Apply filters first
            if not self.apply_filters(df, indicators):
                return None
            
            # Generate signals from all strategies
            trend_signal = self.trend_following_signal(df, indicators)
            mean_reversion_signal = self.mean_reversion_signal(df, indicators)
            momentum_signal = self.momentum_signal(df, indicators)
            
            # Choose the signal with highest confidence
            best_signal = None
            signals = [trend_signal, mean_reversion_signal, momentum_signal]
            
            for signal in signals:
                if (signal['direction'] and 
                    signal['confidence'] >= Config.CONFIDENCE_THRESHOLD and
                    (best_signal is None or signal['confidence'] > best_signal['confidence'])):
                    best_signal = signal
            
            if best_signal:
                # MANDATORY: Ensure stop-loss is always present
                best_signal = self._ensure_stop_loss(best_signal, df, indicators)
                
                best_signal['symbol'] = symbol
                best_signal['timestamp'] = datetime.now()
                best_signal['timeframe'] = '5m'  # Default timeframe
                
                # Add additional context
                best_signal['volume_24h'] = df['volume'].tail(24).sum() if len(df) >= 24 else df['volume'].sum()
                best_signal['price_change_24h'] = ((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100) if len(df) >= 24 else 0
                
                logger.info(f"Generated {best_signal['direction']} signal for {symbol} with confidence {best_signal['confidence']:.2f}")
            
            return best_signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None

    def check_support_resistance(self, df: pd.DataFrame, direction: str) -> bool:
        """Check for support/resistance confirmation"""
        try:
            current_price = df['close'].iloc[-1]
            high_20 = df['high'].iloc[-20:].max()
            low_20 = df['low'].iloc[-20:].min()
            
            if direction == 'LONG':
                # Check if price is near support level (within 1% of recent low)
                return current_price <= low_20 * 1.01
            else:  # SHORT
                # Check if price is near resistance level (within 1% of recent high)
                return current_price >= high_20 * 0.99
        except:
            return False
    
    def check_multiple_timeframe_confirmation(self, df: pd.DataFrame, direction: str) -> bool:
        """Check for multiple timeframe confirmation"""
        try:
            # Check if price is consistently above/below key levels
            if len(df) >= 10:
                if direction == 'LONG':
                    # Check if last 5 candles are consistently above EMA21
                    ema_21 = df['close'].ewm(span=21).mean()
                    return all(df['close'].iloc[-5:] > ema_21.iloc[-5:])
                else:  # SHORT
                    # Check if last 5 candles are consistently below EMA21
                    ema_21 = df['close'].ewm(span=21).mean()
                    return all(df['close'].iloc[-5:] < ema_21.iloc[-5:])
            return False
        except:
            return False

    def _ensure_stop_loss(self, signal: Dict, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Ensure every signal has a proper stop-loss"""
        try:
            current_price = df['close'].iloc[-1]
            atr = indicators.get('atr', 0.01)
            
            # If signal doesn't have stop-loss, add one
            if not signal.get('stop_loss'):
                if signal['direction'] == 'LONG':
                    signal['stop_loss'] = current_price - (1.8 * atr)
                    signal['stop_loss'] = max(signal['stop_loss'], current_price * (1 - Config.MAX_DRAWDOWN_PCT / 100))
                else:  # SHORT
                    signal['stop_loss'] = current_price + (1.8 * atr)
                    signal['stop_loss'] = min(signal['stop_loss'], current_price * (1 + Config.MAX_DRAWDOWN_PCT / 100))
            
            # If signal doesn't have take-profit, add one
            if not signal.get('take_profit'):
                if signal['direction'] == 'LONG':
                    signal['take_profit'] = current_price + (1.8 * atr)
                else:  # SHORT
                    signal['take_profit'] = current_price - (1.8 * atr)
            
            # Recalculate risk-reward ratio
            if signal['direction'] == 'LONG':
                signal['risk_reward'] = (signal['take_profit'] - current_price) / (current_price - signal['stop_loss'])
            else:
                signal['risk_reward'] = (current_price - signal['take_profit']) / (signal['stop_loss'] - current_price)
            
            # Add ATR for trailing stop functionality
            signal['atr'] = atr
            
            logger.debug(f"Ensured stop-loss for {signal['direction']} signal: SL={signal['stop_loss']:.4f}, TP={signal['take_profit']:.4f}")
            return signal
            
        except Exception as e:
            logger.error(f"Error ensuring stop-loss: {e}")
            return signal
    
    def generate_signals_batch(self, market_data: Dict[str, Dict[str, pd.DataFrame]], exchange_fetcher=None) -> List[Dict]:
        """Generate signals for multiple symbols and timeframes"""
        signals = []
        
        for symbol, timeframes in market_data.items():
            for timeframe, df in timeframes.items():
                if len(df) < 200:  # Need enough data for indicators
                    continue
                
                signal = self.generate_signal(symbol, df, exchange_fetcher)
                if signal:
                    signal['timeframe'] = timeframe
                    signals.append(signal)
        
        # Sort by confidence (highest first)
        signals.sort(key=lambda x: x['confidence'], reverse=True)
        
        return signals
