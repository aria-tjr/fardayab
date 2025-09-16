"""
Ultra High Win Rate Signal Generator
Optimized for maximum win rate with strict filtering
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from .indicators import TechnicalIndicators
from .multi_timeframe_confirmation import MultiTimeframeConfirmation
from ..config import Config

logger = logging.getLogger(__name__)

class UltraHighWinRateGenerator:
    """Ultra high win rate signal generator with maximum filtering"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.multi_timeframe_confirmation = MultiTimeframeConfirmation()
        
        # Ultra-strict parameters for maximum win rate (configurable)
        self.min_confidence = getattr(Config, 'ULTRA_MIN_CONFIDENCE', 0.95)
        self.min_volume_ratio = getattr(Config, 'MIN_VOLUME_RATIO', 2.0)
        self.min_atr_ratio = getattr(Config, 'MIN_ATR_RATIO', 1.5)
        self.min_trend_strength = getattr(Config, 'MIN_TREND_STRENGTH', 40)
        self.min_rsi_divergence = getattr(Config, 'MIN_RSI_DIVERGENCE', 10)
        self.max_volatility = getattr(Config, 'MAX_VOLATILITY', 0.05)
        self.min_momentum_consistency = getattr(Config, 'MIN_MOMENTUM_CONSISTENCY', 3)
        
    def calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive indicators for ultra filtering"""
        indicators = {}
        
        # Price data
        indicators['close'] = df['close']
        indicators['high'] = df['high']
        indicators['low'] = df['low']
        indicators['volume'] = df['volume']
        
        # EMAs (multiple timeframes)
        indicators['ema_8'] = self.indicators.ema(df['close'], 8)
        indicators['ema_12'] = self.indicators.ema(df['close'], 12)
        indicators['ema_21'] = self.indicators.ema(df['close'], 21)
        indicators['ema_50'] = self.indicators.ema(df['close'], 50)
        indicators['ema_100'] = self.indicators.ema(df['close'], 100)
        indicators['ema_200'] = self.indicators.ema(df['close'], 200)
        
        # RSI with multiple periods
        indicators['rsi_14'] = self.indicators.rsi(df['close'], 14)
        indicators['rsi_21'] = self.indicators.rsi(df['close'], 21)
        
        # MACD
        indicators['macd'], indicators['macd_signal'], indicators['macd_histogram'] = \
            self.indicators.macd(df['close'])
        
        # ATR
        indicators['atr'] = self.indicators.atr(df['high'], df['low'], df['close'], 14)
        
        # ADX for trend strength
        indicators['adx'] = self.indicators.adx(df['high'], df['low'], df['close'])
        
        # Bollinger Bands
        indicators['bb_upper'], indicators['bb_middle'], indicators['bb_lower'] = \
            self.indicators.bollinger_bands(df['close'], 20, 2)
        
        # Stochastic
        indicators['stoch_k'], indicators['stoch_d'] = \
            self.indicators.stochastic(df['high'], df['low'], df['close'])
        
        # Williams %R
        indicators['williams_r'] = self.indicators.williams_r(df['high'], df['low'], df['close'])
        
        # Volume indicators
        indicators['volume_ma_20'] = df['volume'].rolling(20).mean()
        indicators['volume_ma_50'] = df['volume'].rolling(50).mean()
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
        
        # ATR moving averages
        indicators['atr_ma_20'] = indicators['atr'].rolling(20).mean()
        indicators['atr_ma_50'] = indicators['atr'].rolling(50).mean()
        
        # Price volatility
        indicators['price_volatility'] = df['close'].pct_change().rolling(20).std()
        
        # Momentum indicators
        indicators['momentum_5'] = df['close'].pct_change(5)
        indicators['momentum_10'] = df['close'].pct_change(10)
        
        return indicators
    
    def ultra_strict_filters(self, df: pd.DataFrame, indicators: Dict) -> bool:
        """Apply ultra-strict filters for maximum win rate"""
        try:
            current_price = df['close'].iloc[-1]
            current_volume = df['volume'].iloc[-1]
            current_atr = indicators['atr'].iloc[-1]
            
            # Volume filters
            volume_ma_20 = indicators['volume_ma_20'].iloc[-1]
            volume_ma_50 = indicators['volume_ma_50'].iloc[-1]
            
            if current_volume < volume_ma_20 * self.min_volume_ratio:
                return False
            
            if current_volume < volume_ma_50 * 1.5:
                return False
            
            # ATR filters
            atr_ma_20 = indicators['atr_ma_20'].iloc[-1]
            atr_ma_50 = indicators['atr_ma_50'].iloc[-1]
            
            if current_atr < atr_ma_20 * self.min_atr_ratio:
                return False
            
            if current_atr < atr_ma_50 * 1.2:
                return False
            
            # Trend strength filter
            adx = indicators['adx'].iloc[-1]
            if adx < self.min_trend_strength:
                return False
            
            # Volatility filter
            price_volatility = indicators['price_volatility'].iloc[-1]
            if price_volatility > self.max_volatility:
                return False
            
            # Time filter (only trade during high volume hours)
            # Use candle timestamp hour (UTC) instead of current wall-clock
            try:
                current_hour = df.index[-1].hour
            except Exception:
                from datetime import datetime as _dt
                current_hour = _dt.utcnow().hour
            start_hour = getattr(Config, 'TRADING_HOURS_START', 12)
            end_hour = getattr(Config, 'TRADING_HOURS_END', 16)
            if not (start_hour <= current_hour <= end_hour):  # UTC window from config
                return False
            
            # (Redundant exclusion removed; range above already enforces window)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in ultra strict filters: {e}")
            return False
    
    def check_momentum_consistency(self, df: pd.DataFrame, direction: str) -> bool:
        """Check if momentum is consistent for multiple candles"""
        try:
            if len(df) < self.min_momentum_consistency:
                return False
            
            recent_closes = df['close'].tail(self.min_momentum_consistency)
            
            if direction == 'LONG':
                # Check if last 3 candles are consistently higher
                for i in range(1, len(recent_closes)):
                    if recent_closes.iloc[i] <= recent_closes.iloc[i-1]:
                        return False
            else:  # SHORT
                # Check if last 3 candles are consistently lower
                for i in range(1, len(recent_closes)):
                    if recent_closes.iloc[i] >= recent_closes.iloc[i-1]:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking momentum consistency: {e}")
            return False
    
    def check_ema_alignment(self, indicators: Dict, direction: str) -> bool:
        """Check perfect EMA alignment for trend confirmation"""
        try:
            ema_8 = indicators['ema_8'].iloc[-1]
            ema_12 = indicators['ema_12'].iloc[-1]
            ema_21 = indicators['ema_21'].iloc[-1]
            ema_50 = indicators['ema_50'].iloc[-1]
            ema_100 = indicators['ema_100'].iloc[-1]
            ema_200 = indicators['ema_200'].iloc[-1]
            
            if direction == 'LONG':
                # Perfect bullish alignment: 8 > 12 > 21 > 50 > 100 > 200
                return (ema_8 > ema_12 > ema_21 > ema_50 > ema_100 > ema_200)
            else:  # SHORT
                # Perfect bearish alignment: 8 < 12 < 21 < 50 < 100 < 200
                return (ema_8 < ema_12 < ema_21 < ema_50 < ema_100 < ema_200)
                
        except Exception as e:
            logger.error(f"Error checking EMA alignment: {e}")
            return False
    
    def check_rsi_divergence(self, indicators: Dict, direction: str) -> bool:
        """Check RSI divergence for momentum confirmation"""
        try:
            rsi_14 = indicators['rsi_14'].iloc[-1]
            rsi_21 = indicators['rsi_21'].iloc[-1]
            
            if direction == 'LONG':
                # Both RSI must be significantly above 50
                return (rsi_14 > 50 + self.min_rsi_divergence and 
                        rsi_21 > 50 + self.min_rsi_divergence)
            else:  # SHORT
                # Both RSI must be significantly below 50
                return (rsi_14 < 50 - self.min_rsi_divergence and 
                        rsi_21 < 50 - self.min_rsi_divergence)
                
        except Exception as e:
            logger.error(f"Error checking RSI divergence: {e}")
            return False
    
    def check_macd_confirmation(self, indicators: Dict, direction: str) -> bool:
        """Check MACD confirmation for momentum"""
        try:
            macd = indicators['macd'].iloc[-1]
            macd_signal = indicators['macd_signal'].iloc[-1]
            macd_histogram = indicators['macd_histogram'].iloc[-1]
            
            if direction == 'LONG':
                # MACD above signal and histogram positive
                return (macd > macd_signal and macd_histogram > 0)
            else:  # SHORT
                # MACD below signal and histogram negative
                return (macd < macd_signal and macd_histogram < 0)
                
        except Exception as e:
            logger.error(f"Error checking MACD confirmation: {e}")
            return False
    
    def check_volume_confirmation(self, indicators: Dict) -> bool:
        """Check volume confirmation for strength"""
        try:
            obv = indicators['obv'].iloc[-1]
            obv_ma = indicators['obv'].rolling(20).mean().iloc[-1]
            
            # OBV must be above its moving average
            return obv > obv_ma
            
        except Exception as e:
            logger.error(f"Error checking volume confirmation: {e}")
            return False
    
    def check_support_resistance(self, df: pd.DataFrame, direction: str) -> bool:
        """Check if price is near key support/resistance levels"""
        try:
            current_price = df['close'].iloc[-1]
            bb_upper, bb_middle, bb_lower = self.indicators.bollinger_bands(df['close'], 20, 2)
            bb_upper = bb_upper.iloc[-1]
            bb_middle = bb_middle.iloc[-1]
            bb_lower = bb_lower.iloc[-1]
            
            if direction == 'LONG':
                # Price should be near support (lower BB or middle)
                return (current_price <= bb_middle * 1.02)
            else:  # SHORT
                # Price should be near resistance (upper BB or middle)
                return (current_price >= bb_middle * 0.98)
                
        except Exception as e:
            logger.error(f"Error checking support/resistance: {e}")
            return False
    
    def ultra_high_winrate_signal(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Generate ultra high win rate signal with maximum filtering"""
        current_price = df['close'].iloc[-1]
        atr = indicators['atr'].iloc[-1]
        
        signal = {
            'type': 'ultra_high_winrate',
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
        
        # Perfect EMA alignment
        if self.check_ema_alignment(indicators, 'LONG'):
            long_conditions.append('perfect_ema_alignment')
            signal['conditions_met'].append('تراز کامل EMA8/12/21/50/100/200')
        
        # RSI divergence
        if self.check_rsi_divergence(indicators, 'LONG'):
            long_conditions.append('rsi_divergence')
            signal['conditions_met'].append('RSI divergence صعودی')
        
        # MACD confirmation
        if self.check_macd_confirmation(indicators, 'LONG'):
            long_conditions.append('macd_confirmation')
            signal['conditions_met'].append('تأیید MACD صعودی')
        
        # Volume confirmation
        if self.check_volume_confirmation(indicators):
            long_conditions.append('volume_confirmation')
            signal['conditions_met'].append('تأیید حجم')
        
        # Additional high win rate confirmation indicators
        try:
            vpt = indicators['vpt'].iloc[-1]
            vpt_prev = indicators['vpt'].iloc[-2]
            if vpt > vpt_prev:
                long_conditions.append('vpt_increasing')
                signal['conditions_met'].append('VPT در حال افزایش')
        except:
            pass
        
        try:
            ad = indicators['ad'].iloc[-1]
            ad_prev = indicators['ad'].iloc[-2]
            if ad > ad_prev:
                long_conditions.append('ad_increasing')
                signal['conditions_met'].append('AD در حال افزایش')
        except:
            pass
        
        try:
            cci = indicators['cci'].iloc[-1]
            if cci > 100:  # Strong bullish momentum
                long_conditions.append('cci_bullish')
                signal['conditions_met'].append('CCI صعودی قوی')
        except:
            pass
        
        try:
            williams_r = indicators['williams_r'].iloc[-1]
            if williams_r > -20:  # Not oversold
                long_conditions.append('williams_r_bullish')
                signal['conditions_met'].append('Williams %R صعودی')
        except:
            pass
        
        try:
            uo = indicators['uo'].iloc[-1]
            if uo > 50:  # Above neutral
                long_conditions.append('uo_bullish')
                signal['conditions_met'].append('Ultimate Oscillator صعودی')
        except:
            pass
        
        try:
            po = indicators['po'].iloc[-1]
            po_prev = indicators['po'].iloc[-2]
            if po > po_prev and po > 0:  # Positive and increasing
                long_conditions.append('po_bullish')
                signal['conditions_met'].append('Price Oscillator صعودی')
        except:
            pass
        
        # Momentum consistency
        if self.check_momentum_consistency(df, 'LONG'):
            long_conditions.append('momentum_consistency')
            signal['conditions_met'].append('ثبات مومنتوم صعودی')
        
        # Support/resistance
        if self.check_support_resistance(df, 'LONG'):
            long_conditions.append('support_level')
            signal['conditions_met'].append('نزدیک سطح حمایت')
        
        # Check for SHORT signal
        short_conditions = []
        
        # Perfect EMA alignment
        if self.check_ema_alignment(indicators, 'SHORT'):
            short_conditions.append('perfect_ema_alignment')
            signal['conditions_met'].append('تراز کامل نزولی EMA8/12/21/50/100/200')
        
        # RSI divergence
        if self.check_rsi_divergence(indicators, 'SHORT'):
            short_conditions.append('rsi_divergence')
            signal['conditions_met'].append('RSI divergence نزولی')
        
        # MACD confirmation
        if self.check_macd_confirmation(indicators, 'SHORT'):
            short_conditions.append('macd_confirmation')
            signal['conditions_met'].append('تأیید MACD نزولی')
        
        # Volume confirmation
        if self.check_volume_confirmation(indicators):
            short_conditions.append('volume_confirmation')
            signal['conditions_met'].append('تأیید حجم')
        
        # Additional high win rate confirmation indicators for SHORT
        try:
            vpt = indicators['vpt'].iloc[-1]
            vpt_prev = indicators['vpt'].iloc[-2]
            if vpt < vpt_prev:
                short_conditions.append('vpt_decreasing')
                signal['conditions_met'].append('VPT در حال کاهش')
        except:
            pass
        
        try:
            ad = indicators['ad'].iloc[-1]
            ad_prev = indicators['ad'].iloc[-2]
            if ad < ad_prev:
                short_conditions.append('ad_decreasing')
                signal['conditions_met'].append('AD در حال کاهش')
        except:
            pass
        
        try:
            cci = indicators['cci'].iloc[-1]
            if cci < -100:  # Strong bearish momentum
                short_conditions.append('cci_bearish')
                signal['conditions_met'].append('CCI نزولی قوی')
        except:
            pass
        
        try:
            williams_r = indicators['williams_r'].iloc[-1]
            if williams_r < -80:  # Oversold
                short_conditions.append('williams_r_bearish')
                signal['conditions_met'].append('Williams %R نزولی')
        except:
            pass
        
        try:
            uo = indicators['uo'].iloc[-1]
            if uo < 50:  # Below neutral
                short_conditions.append('uo_bearish')
                signal['conditions_met'].append('Ultimate Oscillator نزولی')
        except:
            pass
        
        try:
            po = indicators['po'].iloc[-1]
            po_prev = indicators['po'].iloc[-2]
            if po < po_prev and po < 0:  # Negative and decreasing
                short_conditions.append('po_bearish')
                signal['conditions_met'].append('Price Oscillator نزولی')
        except:
            pass
        
        # Momentum consistency
        if self.check_momentum_consistency(df, 'SHORT'):
            short_conditions.append('momentum_consistency')
            signal['conditions_met'].append('ثبات مومنتوم نزولی')
        
        # Support/resistance
        if self.check_support_resistance(df, 'SHORT'):
            short_conditions.append('resistance_level')
            signal['conditions_met'].append('نزدیک سطح مقاومت')
        
        # Determine signal direction (require ALL conditions)
        if len(long_conditions) >= 9:  # Tightened for higher win rate
            signal['direction'] = 'LONG'
            signal['confidence'] = min(len(long_conditions) / 12.0, 1.0)
            
            # Tighter take-profit and wider stop-loss for easier targets
            stop_loss = current_price - (2.0 * atr)  # Wider stop-loss
            take_profit = current_price + (1.2 * atr)  # Tighter take-profit
            
            signal['stop_loss'] = stop_loss
            signal['take_profit'] = take_profit
            signal['risk_reward'] = (take_profit - current_price) / (current_price - stop_loss)
            
        elif len(short_conditions) >= 9:  # Tightened for higher win rate
            signal['direction'] = 'SHORT'
            signal['confidence'] = min(len(short_conditions) / 12.0, 1.0)
            
            # Tighter take-profit and wider stop-loss for easier targets
            stop_loss = current_price + (2.0 * atr)  # Wider stop-loss
            take_profit = current_price - (1.2 * atr)  # Tighter take-profit
            
            signal['stop_loss'] = stop_loss
            signal['take_profit'] = take_profit
            signal['risk_reward'] = (current_price - take_profit) / (stop_loss - current_price)
        
        return signal
    
    def generate_signal(self, symbol: str, df: pd.DataFrame, exchange_fetcher=None) -> Optional[Dict]:
        """Generate ultra high win rate signal with multi-timeframe confirmation"""
        try:
            # Calculate indicators
            indicators = self.calculate_indicators(df)
            
            # Apply ultra-strict filters first
            if not self.ultra_strict_filters(df, indicators):
                return None
            
            # Generate ultra high win rate signal
            signal = self.ultra_high_winrate_signal(df, indicators)
            
            if signal['direction'] and signal['confidence'] >= self.min_confidence:
                # Multi-timeframe confirmation
                if exchange_fetcher:
                    confirmed, confirmation_conditions = self.multi_timeframe_confirmation.confirm_signal(
                        symbol, exchange_fetcher, signal['direction']
                    )
                    
                    if not confirmed:
                        logger.debug(f"Signal not confirmed for {symbol}: {confirmation_conditions}")
                        return None
                    
                    # Add confirmation conditions to signal
                    signal['confirmation_conditions'] = confirmation_conditions
                    signal['multi_timeframe_confirmed'] = True
                
                # MANDATORY: Ensure stop-loss is always present
                signal = self._ensure_stop_loss(signal, df, indicators)
                
                signal['symbol'] = symbol
                signal['timestamp'] = datetime.now()
                signal['timeframe'] = '5m'

                # Add additional context
                signal['volume_24h'] = df['volume'].tail(24).sum() if len(df) >= 24 else df['volume'].sum()
                signal['price_change_24h'] = ((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100) if len(df) >= 24 else 0

                logger.info(f"Ultra high win rate signal: {signal['direction']} for {symbol} with confidence {signal['confidence']:.2f}")
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating ultra high win rate signal for {symbol}: {e}")
            return None

    def generate_signal_from_precomputed(self, symbol: str, df: pd.DataFrame, indicators: Dict, exchange_fetcher=None) -> Optional[Dict]:
        """Same as generate_signal, but uses precomputed indicators for performance."""
        try:
            # Apply ultra-strict filters first
            if not self.ultra_strict_filters(df, indicators):
                return None

            # Generate ultra high win rate signal
            signal = self.ultra_high_winrate_signal(df, indicators)

            if signal['direction'] and signal['confidence'] >= self.min_confidence:
                # Multi-timeframe confirmation (optional during backtest)
                if exchange_fetcher:
                    confirmed, confirmation_conditions = self.multi_timeframe_confirmation.confirm_signal(
                        symbol, exchange_fetcher, signal['direction']
                    )
                    if not confirmed:
                        return None
                    signal['confirmation_conditions'] = confirmation_conditions
                    signal['multi_timeframe_confirmed'] = True

                # Ensure risk params
                signal = self._ensure_stop_loss(signal, df, indicators)
                signal['symbol'] = symbol
                signal['timestamp'] = datetime.now()
                signal['timeframe'] = '5m'
                signal['volume_24h'] = df['volume'].tail(24).sum() if len(df) >= 24 else df['volume'].sum()
                signal['price_change_24h'] = ((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100) if len(df) >= 24 else 0
                return signal

            return None
        
        except Exception as e:
            logger.error(f"Error (precomputed) generating ultra high win rate signal for {symbol}: {e}")
            return None

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
            
            logger.debug(f"Ensured stop-loss for ultra high win rate {signal['direction']} signal: SL={signal['stop_loss']:.4f}, TP={signal['take_profit']:.4f}")
            return signal
            
        except Exception as e:
            logger.error(f"Error ensuring stop-loss: {e}")
            return signal
