"""
Multi-timeframe confirmation system for maximum win rate
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from .indicators import TechnicalIndicators
from ..config import Config

logger = logging.getLogger(__name__)

class MultiTimeframeConfirmation:
    """Multi-timeframe confirmation for ultra high win rate"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.timeframes = ['5m', '15m', '1h', '4h']  # Multiple timeframes for confirmation
        
    def get_timeframe_data(self, exchange_fetcher, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Get data for specific timeframe"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            df = loop.run_until_complete(
                exchange_fetcher.get_ohlcv_data(symbol, timeframe, limit=200)
            )
            return df
        except Exception as e:
            logger.error(f"Error getting {timeframe} data for {symbol}: {e}")
            return None
    
    def check_trend_alignment(self, df_5m: pd.DataFrame, df_15m: pd.DataFrame, 
                            df_1h: pd.DataFrame, df_4h: pd.DataFrame, direction: str) -> bool:
        """Check if all timeframes align in the same direction"""
        try:
            # Calculate EMAs for each timeframe
            ema_21_5m = self.indicators.ema(df_5m['close'], 21).iloc[-1]
            ema_50_5m = self.indicators.ema(df_5m['close'], 50).iloc[-1]
            
            ema_21_15m = self.indicators.ema(df_15m['close'], 21).iloc[-1]
            ema_50_15m = self.indicators.ema(df_15m['close'], 50).iloc[-1]
            
            ema_21_1h = self.indicators.ema(df_1h['close'], 21).iloc[-1]
            ema_50_1h = self.indicators.ema(df_1h['close'], 50).iloc[-1]
            
            ema_21_4h = self.indicators.ema(df_4h['close'], 21).iloc[-1]
            ema_50_4h = self.indicators.ema(df_4h['close'], 50).iloc[-1]
            
            if direction == 'LONG':
                # All timeframes must show bullish alignment
                return (ema_21_5m > ema_50_5m and 
                        ema_21_15m > ema_50_15m and 
                        ema_21_1h > ema_50_1h and 
                        ema_21_4h > ema_50_4h)
            else:  # SHORT
                # All timeframes must show bearish alignment
                return (ema_21_5m < ema_50_5m and 
                        ema_21_15m < ema_50_15m and 
                        ema_21_1h < ema_50_1h and 
                        ema_21_4h < ema_50_4h)
                
        except Exception as e:
            logger.error(f"Error checking trend alignment: {e}")
            return False
    
    def check_momentum_confirmation(self, df_5m: pd.DataFrame, df_15m: pd.DataFrame, 
                                  df_1h: pd.DataFrame, direction: str) -> bool:
        """Check momentum confirmation across timeframes"""
        try:
            # RSI for each timeframe
            rsi_5m = self.indicators.rsi(df_5m['close'], 14).iloc[-1]
            rsi_15m = self.indicators.rsi(df_15m['close'], 14).iloc[-1]
            rsi_1h = self.indicators.rsi(df_1h['close'], 14).iloc[-1]
            
            if direction == 'LONG':
                # All RSI must be above 50
                return (rsi_5m > 50 and rsi_15m > 50 and rsi_1h > 50)
            else:  # SHORT
                # All RSI must be below 50
                return (rsi_5m < 50 and rsi_15m < 50 and rsi_1h < 50)
                
        except Exception as e:
            logger.error(f"Error checking momentum confirmation: {e}")
            return False
    
    def check_volume_confirmation(self, df_5m: pd.DataFrame, df_15m: pd.DataFrame) -> bool:
        """Check volume confirmation across timeframes"""
        try:
            # Volume ratios
            volume_5m = df_5m['volume'].iloc[-1]
            volume_ma_5m = df_5m['volume'].rolling(20).mean().iloc[-1]
            volume_ratio_5m = volume_5m / volume_ma_5m
            
            volume_15m = df_15m['volume'].iloc[-1]
            volume_ma_15m = df_15m['volume'].rolling(20).mean().iloc[-1]
            volume_ratio_15m = volume_15m / volume_ma_15m
            
            # Both timeframes must have high volume
            return (volume_ratio_5m > 1.5 and volume_ratio_15m > 1.2)
            
        except Exception as e:
            logger.error(f"Error checking volume confirmation: {e}")
            return False
    
    def check_support_resistance_levels(self, df_1h: pd.DataFrame, df_4h: pd.DataFrame, 
                                      current_price: float, direction: str) -> bool:
        """Check if price is near key support/resistance levels"""
        try:
            # Bollinger Bands for higher timeframes
            bb_upper_1h, bb_middle_1h, bb_lower_1h = self.indicators.bollinger_bands(df_1h['close'], 20, 2)
            bb_upper_4h, bb_middle_4h, bb_lower_4h = self.indicators.bollinger_bands(df_4h['close'], 20, 2)
            
            if direction == 'LONG':
                # Price should be near support levels
                return (current_price <= bb_middle_1h * 1.02 and 
                        current_price <= bb_middle_4h * 1.05)
            else:  # SHORT
                # Price should be near resistance levels
                return (current_price >= bb_middle_1h * 0.98 and 
                        current_price >= bb_middle_4h * 0.95)
                
        except Exception as e:
            logger.error(f"Error checking support/resistance levels: {e}")
            return False
    
    def check_market_structure(self, df_4h: pd.DataFrame, direction: str) -> bool:
        """Check market structure on higher timeframe"""
        try:
            # Check if we're in a clear trend on 4H
            ema_21 = self.indicators.ema(df_4h['close'], 21).iloc[-1]
            ema_50 = self.indicators.ema(df_4h['close'], 50).iloc[-1]
            ema_100 = self.indicators.ema(df_4h['close'], 100).iloc[-1]
            
            if direction == 'LONG':
                # Clear uptrend structure
                return (ema_21 > ema_50 > ema_100)
            else:  # SHORT
                # Clear downtrend structure
                return (ema_21 < ema_50 < ema_100)
                
        except Exception as e:
            logger.error(f"Error checking market structure: {e}")
            return False
    
    def confirm_signal(self, symbol: str, exchange_fetcher, direction: str) -> Tuple[bool, List[str]]:
        """Confirm signal across multiple timeframes"""
        try:
            confirmation_conditions = []
            
            # Get data for all timeframes
            df_5m = self.get_timeframe_data(exchange_fetcher, symbol, '5m')
            df_15m = self.get_timeframe_data(exchange_fetcher, symbol, '15m')
            df_1h = self.get_timeframe_data(exchange_fetcher, symbol, '1h')
            df_4h = self.get_timeframe_data(exchange_fetcher, symbol, '4h')
            
            if not all([df_5m is not None, df_15m is not None, df_1h is not None, df_4h is not None]):
                return False, ["Missing timeframe data"]
            
            # Check trend alignment
            if self.check_trend_alignment(df_5m, df_15m, df_1h, df_4h, direction):
                confirmation_conditions.append("Trend alignment across all timeframes")
            else:
                return False, ["Trend not aligned across timeframes"]
            
            # Check momentum confirmation
            if self.check_momentum_confirmation(df_5m, df_15m, df_1h, direction):
                confirmation_conditions.append("Momentum confirmation across timeframes")
            else:
                return False, ["Momentum not confirmed across timeframes"]
            
            # Check volume confirmation
            if self.check_volume_confirmation(df_5m, df_15m):
                confirmation_conditions.append("Volume confirmation across timeframes")
            else:
                return False, ["Volume not confirmed across timeframes"]
            
            # Check support/resistance levels
            current_price = df_5m['close'].iloc[-1]
            if self.check_support_resistance_levels(df_1h, df_4h, current_price, direction):
                confirmation_conditions.append("Support/resistance levels confirmed")
            else:
                return False, ["Support/resistance levels not confirmed"]
            
            # Check market structure
            if self.check_market_structure(df_4h, direction):
                confirmation_conditions.append("Market structure confirmed")
            else:
                return False, ["Market structure not confirmed"]
            
            return True, confirmation_conditions
            
        except Exception as e:
            logger.error(f"Error confirming signal for {symbol}: {e}")
            return False, [f"Confirmation error: {e}"]
