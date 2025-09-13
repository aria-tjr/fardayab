from __future__ import annotations

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

import httpx
from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class SignalStrength(Enum):
    """Signal strength levels"""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4
    EXTREME = 5


@dataclass
class TradingSignal:
    """Trading signal data structure"""
    symbol: str
    signal_type: SignalType
    strength: SignalStrength
    price: float
    target_price: Optional[float]
    stop_loss: Optional[float]
    confidence: float  # 0-100
    reasoning: str
    indicators: Dict[str, Any]
    timeframe: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class AlertRule:
    """Alert rule configuration"""
    symbol: str
    condition: str  # 'price_above', 'price_below', 'volume_spike', 'rsi_oversold', etc.
    threshold: float
    comparison: str  # '>', '<', '>=', '<=', '=='
    message_template: str
    is_active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class AdvancedTradingSignals:
    """Advanced trading signals and alerts system"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        self.signals: List[TradingSignal] = []
        self.alert_rules: List[AlertRule] = []
        self.price_alerts: Dict[str, List[float]] = {}
        
    async def generate_signals(self, symbol: str) -> List[TradingSignal]:
        """Generate trading signals for a symbol"""
        try:
            signals = []
            
            # Fetch current market data
            market_data = await self._fetch_market_data(symbol)
            if not market_data:
                return []
            
            # Technical analysis signals
            technical_signals = await self._analyze_technical_signals(symbol, market_data)
            signals.extend(technical_signals)
            
            # News sentiment signals
            sentiment_signals = await self._analyze_sentiment_signals(symbol)
            signals.extend(sentiment_signals)
            
            # Volume analysis signals
            volume_signals = await self._analyze_volume_signals(symbol, market_data)
            signals.extend(volume_signals)
            
            # Market structure signals
            structure_signals = await self._analyze_market_structure_signals(symbol, market_data)
            signals.extend(structure_signals)
            
            # Combine and rank signals
            combined_signals = self._combine_signals(symbol, signals)
            
            # Store signals
            self.signals.extend(combined_signals)
            
            return combined_signals
            
        except Exception as e:
            log.error(f"Signal generation failed for {symbol}: {e}")
            return []
    
    async def _fetch_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch comprehensive market data for a symbol"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if symbol.upper() in ['BTC', 'ETH', 'ADA', 'SOL', 'MATIC', 'DOT', 'LINK', 'UNI', 'AAVE', 'COMP']:
                    # Crypto data from CoinGecko
                    coin_id = self._get_coin_id(symbol)
                    response = await client.get(
                        f"https://api.coingecko.com/api/v3/coins/{coin_id}",
                        params={
                            "localization": "false",
                            "tickers": "false",
                            "market_data": "true",
                            "community_data": "false",
                            "developer_data": "false",
                            "sparkline": "true"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        market_data = data.get("market_data", {})
                        
                        return {
                            "symbol": symbol,
                            "current_price": market_data.get("current_price", {}).get("usd", 0),
                            "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                            "total_volume": market_data.get("total_volume", {}).get("usd", 0),
                            "price_change_24h": market_data.get("price_change_percentage_24h", 0),
                            "price_change_7d": market_data.get("price_change_percentage_7d", 0),
                            "price_change_30d": market_data.get("price_change_percentage_30d", 0),
                            "high_24h": market_data.get("high_24h", {}).get("usd", 0),
                            "low_24h": market_data.get("low_24h", {}).get("usd", 0),
                            "circulating_supply": market_data.get("circulating_supply", 0),
                            "total_supply": market_data.get("total_supply", 0),
                            "max_supply": market_data.get("max_supply", 0),
                            "ath": market_data.get("ath", {}).get("usd", 0),
                            "atl": market_data.get("atl", {}).get("usd", 0),
                            "sparkline": data.get("market_data", {}).get("sparkline_7d", {}).get("price", []),
                            "category": "crypto"
                        }
                else:
                    # Forex data from ExchangeRate.host
                    base = symbol[:3]
                    quote = symbol[3:]
                    response = await client.get(
                        "https://api.exchangerate.host/latest",
                        params={"base": base, "symbols": quote}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        rate = data.get("rates", {}).get(quote, 0)
                        
                        return {
                            "symbol": symbol,
                            "current_price": rate,
                            "category": "forex"
                        }
                        
        except Exception as e:
            log.warning(f"Failed to fetch market data for {symbol}: {e}")
        
        return None
    
    async def _analyze_technical_signals(self, symbol: str, market_data: Dict[str, Any]) -> List[TradingSignal]:
        """Analyze technical indicators for signals"""
        try:
            signals = []
            current_price = market_data.get("current_price", 0)
            
            if not current_price:
                return []
            
            # RSI analysis
            rsi_signal = self._analyze_rsi_signal(symbol, market_data)
            if rsi_signal:
                signals.append(rsi_signal)
            
            # MACD analysis
            macd_signal = self._analyze_macd_signal(symbol, market_data)
            if macd_signal:
                signals.append(macd_signal)
            
            # Bollinger Bands analysis
            bb_signal = self._analyze_bollinger_bands_signal(symbol, market_data)
            if bb_signal:
                signals.append(bb_signal)
            
            # Moving Average analysis
            ma_signal = self._analyze_moving_average_signal(symbol, market_data)
            if ma_signal:
                signals.append(ma_signal)
            
            # Support/Resistance analysis
            sr_signal = self._analyze_support_resistance_signal(symbol, market_data)
            if sr_signal:
                signals.append(sr_signal)
            
            return signals
            
        except Exception as e:
            log.error(f"Technical signal analysis failed for {symbol}: {e}")
            return []
    
    def _analyze_rsi_signal(self, symbol: str, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Analyze RSI for trading signals"""
        try:
            # Simplified RSI calculation (would need historical data for accurate RSI)
            price_change_24h = market_data.get("price_change_24h", 0)
            
            # Estimate RSI based on price change
            if price_change_24h > 10:
                rsi_estimate = 80  # Overbought
                signal_type = SignalType.SELL
                strength = SignalStrength.STRONG
                confidence = 75
                reasoning = f"RSI indicates overbought conditions (estimated RSI: {rsi_estimate})"
            elif price_change_24h < -10:
                rsi_estimate = 20  # Oversold
                signal_type = SignalType.BUY
                strength = SignalStrength.STRONG
                confidence = 75
                reasoning = f"RSI indicates oversold conditions (estimated RSI: {rsi_estimate})"
            elif price_change_24h > 5:
                rsi_estimate = 70  # Approaching overbought
                signal_type = SignalType.SELL
                strength = SignalStrength.MODERATE
                confidence = 60
                reasoning = f"RSI approaching overbought (estimated RSI: {rsi_estimate})"
            elif price_change_24h < -5:
                rsi_estimate = 30  # Approaching oversold
                signal_type = SignalType.BUY
                strength = SignalStrength.MODERATE
                confidence = 60
                reasoning = f"RSI approaching oversold (estimated RSI: {rsi_estimate})"
            else:
                return None
            
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                price=market_data.get("current_price", 0),
                target_price=None,
                stop_loss=None,
                confidence=confidence,
                reasoning=reasoning,
                indicators={"rsi": rsi_estimate, "price_change_24h": price_change_24h},
                timeframe="short",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=4)
            )
            
        except Exception as e:
            log.warning(f"RSI analysis failed for {symbol}: {e}")
            return None
    
    def _analyze_macd_signal(self, symbol: str, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Analyze MACD for trading signals"""
        try:
            price_change_7d = market_data.get("price_change_7d", 0)
            price_change_24h = market_data.get("price_change_24h", 0)
            
            # Simplified MACD analysis based on price momentum
            if price_change_7d > 20 and price_change_24h > 5:
                signal_type = SignalType.STRONG_BUY
                strength = SignalStrength.VERY_STRONG
                confidence = 80
                reasoning = f"Strong bullish momentum: 7d +{price_change_7d:.1f}%, 24h +{price_change_24h:.1f}%"
            elif price_change_7d < -20 and price_change_24h < -5:
                signal_type = SignalType.STRONG_SELL
                strength = SignalStrength.VERY_STRONG
                confidence = 80
                reasoning = f"Strong bearish momentum: 7d {price_change_7d:.1f}%, 24h {price_change_24h:.1f}%"
            elif price_change_7d > 10 and price_change_24h > 2:
                signal_type = SignalType.BUY
                strength = SignalStrength.STRONG
                confidence = 70
                reasoning = f"Bullish momentum: 7d +{price_change_7d:.1f}%, 24h +{price_change_24h:.1f}%"
            elif price_change_7d < -10 and price_change_24h < -2:
                signal_type = SignalType.SELL
                strength = SignalStrength.STRONG
                confidence = 70
                reasoning = f"Bearish momentum: 7d {price_change_7d:.1f}%, 24h {price_change_24h:.1f}%"
            else:
                return None
            
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                price=market_data.get("current_price", 0),
                target_price=None,
                stop_loss=None,
                confidence=confidence,
                reasoning=reasoning,
                indicators={"macd_momentum": price_change_7d, "short_momentum": price_change_24h},
                timeframe="medium",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=8)
            )
            
        except Exception as e:
            log.warning(f"MACD analysis failed for {symbol}: {e}")
            return None
    
    def _analyze_bollinger_bands_signal(self, symbol: str, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Analyze Bollinger Bands for trading signals"""
        try:
            current_price = market_data.get("current_price", 0)
            high_24h = market_data.get("high_24h", 0)
            low_24h = market_data.get("low_24h", 0)
            
            if not all([current_price, high_24h, low_24h]):
                return None
            
            # Calculate position relative to 24h range
            range_size = high_24h - low_24h
            if range_size == 0:
                return None
            
            position = (current_price - low_24h) / range_size
            
            if position > 0.9:  # Near upper band
                signal_type = SignalType.SELL
                strength = SignalStrength.STRONG
                confidence = 70
                reasoning = f"Price near 24h high ({position:.1%} of range) - potential resistance"
            elif position < 0.1:  # Near lower band
                signal_type = SignalType.BUY
                strength = SignalStrength.STRONG
                confidence = 70
                reasoning = f"Price near 24h low ({position:.1%} of range) - potential support"
            elif position > 0.8:  # Approaching upper band
                signal_type = SignalType.SELL
                strength = SignalStrength.MODERATE
                confidence = 60
                reasoning = f"Price approaching 24h high ({position:.1%} of range)"
            elif position < 0.2:  # Approaching lower band
                signal_type = SignalType.BUY
                strength = SignalStrength.MODERATE
                confidence = 60
                reasoning = f"Price approaching 24h low ({position:.1%} of range)"
            else:
                return None
            
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                price=current_price,
                target_price=None,
                stop_loss=None,
                confidence=confidence,
                reasoning=reasoning,
                indicators={"position_in_range": position, "high_24h": high_24h, "low_24h": low_24h},
                timeframe="short",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=6)
            )
            
        except Exception as e:
            log.warning(f"Bollinger Bands analysis failed for {symbol}: {e}")
            return None
    
    def _analyze_moving_average_signal(self, symbol: str, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Analyze Moving Averages for trading signals"""
        try:
            current_price = market_data.get("current_price", 0)
            price_change_7d = market_data.get("price_change_7d", 0)
            price_change_30d = market_data.get("price_change_30d", 0)
            
            if not current_price:
                return None
            
            # Simplified MA analysis based on price trends
            if price_change_7d > 0 and price_change_30d > 0:
                signal_type = SignalType.BUY
                strength = SignalStrength.STRONG
                confidence = 75
                reasoning = f"Price above both 7d and 30d averages: 7d +{price_change_7d:.1f}%, 30d +{price_change_30d:.1f}%"
            elif price_change_7d < 0 and price_change_30d < 0:
                signal_type = SignalType.SELL
                strength = SignalStrength.STRONG
                confidence = 75
                reasoning = f"Price below both 7d and 30d averages: 7d {price_change_7d:.1f}%, 30d {price_change_30d:.1f}%"
            elif price_change_7d > 5 and price_change_30d < 0:
                signal_type = SignalType.BUY
                strength = SignalStrength.MODERATE
                confidence = 60
                reasoning = f"Short-term bullish, long-term bearish: 7d +{price_change_7d:.1f}%, 30d {price_change_30d:.1f}%"
            elif price_change_7d < -5 and price_change_30d > 0:
                signal_type = SignalType.SELL
                strength = SignalStrength.MODERATE
                confidence = 60
                reasoning = f"Short-term bearish, long-term bullish: 7d {price_change_7d:.1f}%, 30d +{price_change_30d:.1f}%"
            else:
                return None
            
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                price=current_price,
                target_price=None,
                stop_loss=None,
                confidence=confidence,
                reasoning=reasoning,
                indicators={"ma_7d": price_change_7d, "ma_30d": price_change_30d},
                timeframe="medium",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=12)
            )
            
        except Exception as e:
            log.warning(f"Moving Average analysis failed for {symbol}: {e}")
            return None
    
    def _analyze_support_resistance_signal(self, symbol: str, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Analyze Support/Resistance levels for trading signals"""
        try:
            current_price = market_data.get("current_price", 0)
            high_24h = market_data.get("high_24h", 0)
            low_24h = market_data.get("low_24h", 0)
            ath = market_data.get("ath", 0)
            atl = market_data.get("atl", 0)
            
            if not all([current_price, high_24h, low_24h]):
                return None
            
            # Analyze position relative to key levels
            if ath > 0:
                ath_distance = (current_price - ath) / ath
                if ath_distance > -0.05:  # Within 5% of ATH
                    signal_type = SignalType.SELL
                    strength = SignalStrength.STRONG
                    confidence = 80
                    reasoning = f"Price near all-time high ({ath_distance:.1%} from ATH) - potential resistance"
                elif ath_distance < -0.5:  # More than 50% below ATH
                    signal_type = SignalType.BUY
                    strength = SignalStrength.MODERATE
                    confidence = 60
                    reasoning = f"Price significantly below ATH ({ath_distance:.1%} from ATH) - potential support"
                else:
                    return None
            else:
                return None
            
            return TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                price=current_price,
                target_price=None,
                stop_loss=None,
                confidence=confidence,
                reasoning=reasoning,
                indicators={"ath_distance": ath_distance, "ath": ath},
                timeframe="long",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24)
            )
            
        except Exception as e:
            log.warning(f"Support/Resistance analysis failed for {symbol}: {e}")
            return None
    
    async def _analyze_sentiment_signals(self, symbol: str) -> List[TradingSignal]:
        """Analyze news sentiment for trading signals"""
        try:
            # This would integrate with the advanced news module
            # For now, return empty list
            return []
            
        except Exception as e:
            log.warning(f"Sentiment signal analysis failed for {symbol}: {e}")
            return []
    
    async def _analyze_volume_signals(self, symbol: str, market_data: Dict[str, Any]) -> List[TradingSignal]:
        """Analyze volume for trading signals"""
        try:
            signals = []
            total_volume = market_data.get("total_volume", 0)
            market_cap = market_data.get("market_cap", 0)
            
            if not total_volume or not market_cap:
                return []
            
            # Calculate volume ratio
            volume_ratio = total_volume / market_cap if market_cap > 0 else 0
            
            if volume_ratio > 0.1:  # High volume
                signal_type = SignalType.BUY
                strength = SignalStrength.STRONG
                confidence = 70
                reasoning = f"High volume activity (ratio: {volume_ratio:.2%}) - potential breakout"
                
                signals.append(TradingSignal(
                    symbol=symbol,
                    signal_type=signal_type,
                    strength=strength,
                    price=market_data.get("current_price", 0),
                    target_price=None,
                    stop_loss=None,
                    confidence=confidence,
                    reasoning=reasoning,
                    indicators={"volume_ratio": volume_ratio, "total_volume": total_volume},
                    timeframe="short",
                    created_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=4)
                ))
            
            return signals
            
        except Exception as e:
            log.warning(f"Volume signal analysis failed for {symbol}: {e}")
            return []
    
    async def _analyze_market_structure_signals(self, symbol: str, market_data: Dict[str, Any]) -> List[TradingSignal]:
        """Analyze market structure for trading signals"""
        try:
            signals = []
            current_price = market_data.get("current_price", 0)
            high_24h = market_data.get("high_24h", 0)
            low_24h = market_data.get("low_24h", 0)
            
            if not all([current_price, high_24h, low_24h]):
                return []
            
            # Analyze breakout patterns
            range_size = high_24h - low_24h
            if range_size > 0:
                position_in_range = (current_price - low_24h) / range_size
                
                if position_in_range > 0.95:  # Near range high
                    signal_type = SignalType.BUY
                    strength = SignalStrength.STRONG
                    confidence = 75
                    reasoning = f"Price breaking above range high - potential continuation"
                    
                    signals.append(TradingSignal(
                        symbol=symbol,
                        signal_type=signal_type,
                        strength=strength,
                        price=current_price,
                        target_price=high_24h * 1.05,  # 5% above current high
                        stop_loss=low_24h,
                        confidence=confidence,
                        reasoning=reasoning,
                        indicators={"position_in_range": position_in_range, "range_size": range_size},
                        timeframe="short",
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(hours=6)
                    ))
                
                elif position_in_range < 0.05:  # Near range low
                    signal_type = SignalType.SELL
                    strength = SignalStrength.STRONG
                    confidence = 75
                    reasoning = f"Price breaking below range low - potential continuation"
                    
                    signals.append(TradingSignal(
                        symbol=symbol,
                        signal_type=signal_type,
                        strength=strength,
                        price=current_price,
                        target_price=low_24h * 0.95,  # 5% below current low
                        stop_loss=high_24h,
                        confidence=confidence,
                        reasoning=reasoning,
                        indicators={"position_in_range": position_in_range, "range_size": range_size},
                        timeframe="short",
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(hours=6)
                    ))
            
            return signals
            
        except Exception as e:
            log.warning(f"Market structure signal analysis failed for {symbol}: {e}")
            return []
    
    def _combine_signals(self, symbol: str, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Combine multiple signals into final recommendations"""
        try:
            if not signals:
                return []
            
            # Group signals by type
            buy_signals = [s for s in signals if s.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]]
            sell_signals = [s for s in signals if s.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]]
            
            # Calculate combined confidence
            buy_confidence = sum(s.confidence for s in buy_signals) / len(buy_signals) if buy_signals else 0
            sell_confidence = sum(s.confidence for s in sell_signals) / len(sell_signals) if sell_signals else 0
            
            # Determine final signal
            if buy_confidence > sell_confidence and buy_confidence > 60:
                final_signal_type = SignalType.STRONG_BUY if buy_confidence > 80 else SignalType.BUY
                final_confidence = buy_confidence
                final_reasoning = f"Combined analysis: {len(buy_signals)} buy signals, {len(sell_signals)} sell signals"
            elif sell_confidence > buy_confidence and sell_confidence > 60:
                final_signal_type = SignalType.STRONG_SELL if sell_confidence > 80 else SignalType.SELL
                final_confidence = sell_confidence
                final_reasoning = f"Combined analysis: {len(sell_signals)} sell signals, {len(buy_signals)} buy signals"
            else:
                final_signal_type = SignalType.HOLD
                final_confidence = max(buy_confidence, sell_confidence)
                final_reasoning = f"Mixed signals: {len(buy_signals)} buy, {len(sell_signals)} sell - holding recommended"
            
            # Create final combined signal
            combined_signal = TradingSignal(
                symbol=symbol,
                signal_type=final_signal_type,
                strength=SignalStrength.VERY_STRONG if final_confidence > 80 else SignalStrength.STRONG,
                price=signals[0].price,
                target_price=None,
                stop_loss=None,
                confidence=final_confidence,
                reasoning=final_reasoning,
                indicators={"total_signals": len(signals), "buy_signals": len(buy_signals), "sell_signals": len(sell_signals)},
                timeframe="mixed",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=12)
            )
            
            return [combined_signal]
            
        except Exception as e:
            log.error(f"Signal combination failed for {symbol}: {e}")
            return signals  # Return original signals if combination fails
    
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
    
    async def get_active_signals(self, symbol: Optional[str] = None) -> List[TradingSignal]:
        """Get active trading signals"""
        try:
            now = datetime.now()
            active_signals = []
            
            for signal in self.signals:
                if not signal.is_active:
                    continue
                
                if signal.expires_at and signal.expires_at < now:
                    signal.is_active = False
                    continue
                
                if symbol is None or signal.symbol == symbol:
                    active_signals.append(signal)
            
            return sorted(active_signals, key=lambda x: x.confidence, reverse=True)
            
        except Exception as e:
            log.error(f"Failed to get active signals: {e}")
            return []
    
    async def create_price_alert(self, symbol: str, price: float, condition: str = "above") -> bool:
        """Create a price alert"""
        try:
            if symbol not in self.price_alerts:
                self.price_alerts[symbol] = []
            
            self.price_alerts[symbol].append({
                "price": price,
                "condition": condition,
                "created_at": datetime.now(),
                "triggered": False
            })
            
            return True
            
        except Exception as e:
            log.error(f"Failed to create price alert: {e}")
            return False
    
    async def check_price_alerts(self, symbol: str, current_price: float) -> List[Dict[str, Any]]:
        """Check if any price alerts should be triggered"""
        try:
            triggered_alerts = []
            
            if symbol not in self.price_alerts:
                return triggered_alerts
            
            for alert in self.price_alerts[symbol]:
                if alert["triggered"]:
                    continue
                
                should_trigger = False
                if alert["condition"] == "above" and current_price >= alert["price"]:
                    should_trigger = True
                elif alert["condition"] == "below" and current_price <= alert["price"]:
                    should_trigger = True
                
                if should_trigger:
                    alert["triggered"] = True
                    triggered_alerts.append({
                        "symbol": symbol,
                        "price": alert["price"],
                        "current_price": current_price,
                        "condition": alert["condition"],
                        "created_at": alert["created_at"]
                    })
            
            return triggered_alerts
            
        except Exception as e:
            log.error(f"Failed to check price alerts: {e}")
            return []
