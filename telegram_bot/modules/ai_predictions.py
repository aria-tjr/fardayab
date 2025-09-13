from __future__ import annotations

import asyncio
import logging
import json
import math
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np

import httpx
from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


@dataclass
class Prediction:
    """Market prediction data structure"""
    symbol: str
    prediction_type: str  # 'price', 'trend', 'volatility', 'sentiment'
    timeframe: str  # '1h', '4h', '1d', '1w', '1m'
    current_value: float
    predicted_value: float
    confidence: float  # 0-100
    probability: float  # 0-1
    reasoning: str
    factors: List[str]
    created_at: datetime
    expires_at: datetime


@dataclass
class MarketSentiment:
    """Market sentiment analysis"""
    symbol: str
    overall_sentiment: str  # 'bullish', 'bearish', 'neutral'
    sentiment_score: float  # -1 to 1
    fear_greed_index: int  # 0-100
    social_sentiment: float  # -1 to 1
    news_sentiment: float  # -1 to 1
    technical_sentiment: float  # -1 to 1
    institutional_sentiment: float  # -1 to 1
    confidence: float  # 0-100
    analysis_timestamp: datetime


class AIPredictor:
    """AI-powered market prediction and analysis"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
        # Prediction models (simplified for demo)
        self.models = {
            'price_prediction': self._price_prediction_model,
            'trend_prediction': self._trend_prediction_model,
            'volatility_prediction': self._volatility_prediction_model,
            'sentiment_analysis': self._sentiment_analysis_model
        }
    
    async def predict_price_movement(self, symbol: str, timeframe: str = "1d") -> Prediction:
        """Predict price movement for a symbol"""
        try:
            # Fetch market data
            market_data = await self._fetch_comprehensive_data(symbol)
            if not market_data:
                return None
            
            # Get current price
            current_price = market_data.get("current_price", 0)
            if not current_price:
                return None
            
            # Run prediction model
            prediction_result = await self._price_prediction_model(symbol, market_data, timeframe)
            
            if not prediction_result:
                return None
            
            return Prediction(
                symbol=symbol,
                prediction_type="price",
                timeframe=timeframe,
                current_value=current_price,
                predicted_value=prediction_result["predicted_price"],
                confidence=prediction_result["confidence"],
                probability=prediction_result["probability"],
                reasoning=prediction_result["reasoning"],
                factors=prediction_result["factors"],
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=self._get_timeframe_hours(timeframe))
            )
            
        except Exception as e:
            log.error(f"Price prediction failed for {symbol}: {e}")
            return None
    
    async def predict_trend(self, symbol: str, timeframe: str = "1d") -> Prediction:
        """Predict market trend for a symbol"""
        try:
            # Fetch market data
            market_data = await self._fetch_comprehensive_data(symbol)
            if not market_data:
                return None
            
            # Run trend prediction model
            prediction_result = await self._trend_prediction_model(symbol, market_data, timeframe)
            
            if not prediction_result:
                return None
            
            return Prediction(
                symbol=symbol,
                prediction_type="trend",
                timeframe=timeframe,
                current_value=0,  # Trend doesn't have a current value
                predicted_value=prediction_result["trend_direction"],
                confidence=prediction_result["confidence"],
                probability=prediction_result["probability"],
                reasoning=prediction_result["reasoning"],
                factors=prediction_result["factors"],
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=self._get_timeframe_hours(timeframe))
            )
            
        except Exception as e:
            log.error(f"Trend prediction failed for {symbol}: {e}")
            return None
    
    async def predict_volatility(self, symbol: str, timeframe: str = "1d") -> Prediction:
        """Predict market volatility for a symbol"""
        try:
            # Fetch market data
            market_data = await self._fetch_comprehensive_data(symbol)
            if not market_data:
                return None
            
            # Run volatility prediction model
            prediction_result = await self._volatility_prediction_model(symbol, market_data, timeframe)
            
            if not prediction_result:
                return None
            
            return Prediction(
                symbol=symbol,
                prediction_type="volatility",
                timeframe=timeframe,
                current_value=market_data.get("volatility", 0),
                predicted_value=prediction_result["predicted_volatility"],
                confidence=prediction_result["confidence"],
                probability=prediction_result["probability"],
                reasoning=prediction_result["reasoning"],
                factors=prediction_result["factors"],
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=self._get_timeframe_hours(timeframe))
            )
            
        except Exception as e:
            log.error(f"Volatility prediction failed for {symbol}: {e}")
            return None
    
    async def analyze_market_sentiment(self, symbol: str) -> MarketSentiment:
        """Analyze comprehensive market sentiment"""
        try:
            # Fetch sentiment data from multiple sources
            fear_greed_data = await self._fetch_fear_greed_index()
            social_sentiment = await self._analyze_social_sentiment(symbol)
            news_sentiment = await self._analyze_news_sentiment(symbol)
            technical_sentiment = await self._analyze_technical_sentiment(symbol)
            institutional_sentiment = await self._analyze_institutional_sentiment(symbol)
            
            # Calculate overall sentiment
            sentiment_scores = [
                social_sentiment.get("score", 0),
                news_sentiment.get("score", 0),
                technical_sentiment.get("score", 0),
                institutional_sentiment.get("score", 0)
            ]
            
            # Remove None values
            sentiment_scores = [s for s in sentiment_scores if s is not None]
            
            if not sentiment_scores:
                overall_sentiment_score = 0
            else:
                overall_sentiment_score = sum(sentiment_scores) / len(sentiment_scores)
            
            # Determine sentiment label
            if overall_sentiment_score > 0.3:
                overall_sentiment = "bullish"
            elif overall_sentiment_score < -0.3:
                overall_sentiment = "bearish"
            else:
                overall_sentiment = "neutral"
            
            # Calculate confidence
            confidence = min(abs(overall_sentiment_score) * 100, 100)
            
            return MarketSentiment(
                symbol=symbol,
                overall_sentiment=overall_sentiment,
                sentiment_score=overall_sentiment_score,
                fear_greed_index=fear_greed_data.get("value", 50),
                social_sentiment=social_sentiment.get("score", 0),
                news_sentiment=news_sentiment.get("score", 0),
                technical_sentiment=technical_sentiment.get("score", 0),
                institutional_sentiment=institutional_sentiment.get("score", 0),
                confidence=confidence,
                analysis_timestamp=datetime.now()
            )
            
        except Exception as e:
            log.error(f"Sentiment analysis failed for {symbol}: {e}")
            return None
    
    async def get_comprehensive_predictions(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive predictions for a symbol"""
        try:
            # Run all prediction models concurrently
            price_task = asyncio.create_task(self.predict_price_movement(symbol, "1d"))
            trend_task = asyncio.create_task(self.predict_trend(symbol, "1d"))
            volatility_task = asyncio.create_task(self.predict_volatility(symbol, "1d"))
            sentiment_task = asyncio.create_task(self.analyze_market_sentiment(symbol))
            
            price_prediction = await price_task
            trend_prediction = await trend_task
            volatility_prediction = await volatility_task
            sentiment_analysis = await sentiment_task
            
            # Calculate overall market outlook
            outlook = self._calculate_market_outlook(price_prediction, trend_prediction, 
                                                   volatility_prediction, sentiment_analysis)
            
            return {
                "symbol": symbol,
                "predictions": {
                    "price": price_prediction,
                    "trend": trend_prediction,
                    "volatility": volatility_prediction,
                    "sentiment": sentiment_analysis
                },
                "overall_outlook": outlook,
                "analysis_timestamp": datetime.now().isoformat(),
                "recommendation": self._generate_trading_recommendation(outlook)
            }
            
        except Exception as e:
            log.error(f"Comprehensive predictions failed for {symbol}: {e}")
            return {"error": str(e)}
    
    async def _fetch_comprehensive_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch comprehensive market data for analysis"""
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
                            "community_data": "true",
                            "developer_data": "true",
                            "sparkline": "true"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        market_data = data.get("market_data", {})
                        community_data = data.get("community_data", {})
                        developer_data = data.get("developer_data", {})
                        
                        # Calculate volatility (simplified)
                        price_change_24h = market_data.get("price_change_percentage_24h", 0)
                        price_change_7d = market_data.get("price_change_percentage_7d", 0)
                        volatility = abs(price_change_24h) + abs(price_change_7d) / 7
                        
                        return {
                            "symbol": symbol,
                            "current_price": market_data.get("current_price", {}).get("usd", 0),
                            "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                            "total_volume": market_data.get("total_volume", {}).get("usd", 0),
                            "price_change_24h": price_change_24h,
                            "price_change_7d": price_change_7d,
                            "price_change_30d": market_data.get("price_change_percentage_30d", 0),
                            "high_24h": market_data.get("high_24h", {}).get("usd", 0),
                            "low_24h": market_data.get("low_24h", {}).get("usd", 0),
                            "volatility": volatility,
                            "circulating_supply": market_data.get("circulating_supply", 0),
                            "total_supply": market_data.get("total_supply", 0),
                            "max_supply": market_data.get("max_supply", 0),
                            "ath": market_data.get("ath", {}).get("usd", 0),
                            "atl": market_data.get("atl", {}).get("usd", 0),
                            "sparkline": market_data.get("sparkline_7d", {}).get("price", []),
                            "social_mentions": community_data.get("twitter_followers", 0),
                            "github_activity": developer_data.get("forks", 0),
                            "category": "crypto"
                        }
                        
        except Exception as e:
            log.warning(f"Failed to fetch comprehensive data for {symbol}: {e}")
        
        return None
    
    async def _price_prediction_model(self, symbol: str, market_data: Dict[str, Any], timeframe: str) -> Optional[Dict[str, Any]]:
        """AI model for price prediction"""
        try:
            current_price = market_data.get("current_price", 0)
            price_change_24h = market_data.get("price_change_24h", 0)
            price_change_7d = market_data.get("price_change_7d", 0)
            volatility = market_data.get("volatility", 0)
            volume = market_data.get("total_volume", 0)
            market_cap = market_data.get("market_cap", 0)
            
            # Simplified AI prediction based on multiple factors
            factors = []
            confidence = 0
            probability = 0.5
            
            # Price momentum factor
            momentum_score = (price_change_24h + price_change_7d) / 2
            if momentum_score > 5:
                factors.append("Strong bullish momentum")
                confidence += 20
                probability += 0.2
            elif momentum_score < -5:
                factors.append("Strong bearish momentum")
                confidence += 20
                probability -= 0.2
            
            # Volatility factor
            if volatility > 20:
                factors.append("High volatility - increased uncertainty")
                confidence -= 10
            elif volatility < 5:
                factors.append("Low volatility - stable conditions")
                confidence += 10
            
            # Volume factor
            if volume > 0 and market_cap > 0:
                volume_ratio = volume / market_cap
                if volume_ratio > 0.1:
                    factors.append("High volume activity")
                    confidence += 15
                elif volume_ratio < 0.01:
                    factors.append("Low volume - weak participation")
                    confidence -= 10
            
            # Technical levels factor
            high_24h = market_data.get("high_24h", 0)
            low_24h = market_data.get("low_24h", 0)
            if high_24h > 0 and low_24h > 0:
                position_in_range = (current_price - low_24h) / (high_24h - low_24h)
                if position_in_range > 0.8:
                    factors.append("Near resistance level")
                    confidence -= 5
                elif position_in_range < 0.2:
                    factors.append("Near support level")
                    confidence += 5
            
            # Calculate predicted price
            price_change_factor = momentum_score / 100
            volatility_factor = (volatility / 100) * 0.5  # Volatility adds uncertainty
            
            predicted_change = price_change_factor + (np.random.normal(0, volatility_factor))
            predicted_price = current_price * (1 + predicted_change)
            
            # Ensure confidence is within bounds
            confidence = max(0, min(100, confidence))
            probability = max(0, min(1, probability))
            
            reasoning = f"Price prediction based on momentum ({momentum_score:.1f}%), volatility ({volatility:.1f}%), and volume analysis"
            
            return {
                "predicted_price": predicted_price,
                "confidence": confidence,
                "probability": probability,
                "reasoning": reasoning,
                "factors": factors
            }
            
        except Exception as e:
            log.error(f"Price prediction model failed: {e}")
            return None
    
    async def _trend_prediction_model(self, symbol: str, market_data: Dict[str, Any], timeframe: str) -> Optional[Dict[str, Any]]:
        """AI model for trend prediction"""
        try:
            price_change_24h = market_data.get("price_change_24h", 0)
            price_change_7d = market_data.get("price_change_7d", 0)
            price_change_30d = market_data.get("price_change_30d", 0)
            volatility = market_data.get("volatility", 0)
            
            factors = []
            confidence = 0
            
            # Multi-timeframe trend analysis
            trend_score = (price_change_24h * 0.4 + price_change_7d * 0.4 + price_change_30d * 0.2)
            
            if trend_score > 10:
                trend_direction = 1  # Strong uptrend
                factors.append("Strong multi-timeframe uptrend")
                confidence = 80
            elif trend_score > 5:
                trend_direction = 0.5  # Moderate uptrend
                factors.append("Moderate uptrend across timeframes")
                confidence = 65
            elif trend_score < -10:
                trend_direction = -1  # Strong downtrend
                factors.append("Strong multi-timeframe downtrend")
                confidence = 80
            elif trend_score < -5:
                trend_direction = -0.5  # Moderate downtrend
                factors.append("Moderate downtrend across timeframes")
                confidence = 65
            else:
                trend_direction = 0  # Sideways
                factors.append("Sideways trend - consolidation")
                confidence = 50
            
            # Volatility adjustment
            if volatility > 30:
                factors.append("High volatility - trend may be unstable")
                confidence -= 15
            elif volatility < 10:
                factors.append("Low volatility - trend likely to continue")
                confidence += 10
            
            # Volume confirmation
            volume = market_data.get("total_volume", 0)
            market_cap = market_data.get("market_cap", 0)
            if volume > 0 and market_cap > 0:
                volume_ratio = volume / market_cap
                if volume_ratio > 0.05:
                    factors.append("Volume confirms trend")
                    confidence += 10
                elif volume_ratio < 0.01:
                    factors.append("Low volume - trend may not be sustainable")
                    confidence -= 10
            
            confidence = max(0, min(100, confidence))
            probability = abs(trend_direction)
            
            trend_labels = {1: "Strong Uptrend", 0.5: "Moderate Uptrend", 0: "Sideways", 
                          -0.5: "Moderate Downtrend", -1: "Strong Downtrend"}
            
            reasoning = f"Trend analysis based on multi-timeframe price action and volume confirmation"
            
            return {
                "trend_direction": trend_direction,
                "trend_label": trend_labels.get(trend_direction, "Unknown"),
                "confidence": confidence,
                "probability": probability,
                "reasoning": reasoning,
                "factors": factors
            }
            
        except Exception as e:
            log.error(f"Trend prediction model failed: {e}")
            return None
    
    async def _volatility_prediction_model(self, symbol: str, market_data: Dict[str, Any], timeframe: str) -> Optional[Dict[str, Any]]:
        """AI model for volatility prediction"""
        try:
            current_volatility = market_data.get("volatility", 0)
            price_change_24h = market_data.get("price_change_24h", 0)
            volume = market_data.get("total_volume", 0)
            market_cap = market_data.get("market_cap", 0)
            
            factors = []
            confidence = 0
            
            # Base volatility prediction
            predicted_volatility = current_volatility
            
            # Recent price action impact
            if abs(price_change_24h) > 10:
                predicted_volatility += 5
                factors.append("High recent price movement increases volatility")
                confidence += 20
            elif abs(price_change_24h) < 2:
                predicted_volatility -= 3
                factors.append("Low recent price movement decreases volatility")
                confidence += 15
            
            # Volume impact
            if volume > 0 and market_cap > 0:
                volume_ratio = volume / market_cap
                if volume_ratio > 0.1:
                    predicted_volatility += 8
                    factors.append("High volume activity increases volatility")
                    confidence += 15
                elif volume_ratio < 0.01:
                    predicted_volatility -= 5
                    factors.append("Low volume activity decreases volatility")
                    confidence += 10
            
            # Market cap impact (smaller caps are more volatile)
            if market_cap > 0:
                if market_cap < 1e9:  # Less than 1B
                    predicted_volatility += 10
                    factors.append("Small market cap increases volatility")
                elif market_cap > 1e11:  # More than 100B
                    predicted_volatility -= 5
                    factors.append("Large market cap decreases volatility")
            
            # Ensure volatility is positive
            predicted_volatility = max(1, predicted_volatility)
            
            # Calculate probability based on confidence
            probability = min(confidence / 100, 1.0)
            
            reasoning = f"Volatility prediction based on recent price action, volume, and market characteristics"
            
            return {
                "predicted_volatility": predicted_volatility,
                "confidence": confidence,
                "probability": probability,
                "reasoning": reasoning,
                "factors": factors
            }
            
        except Exception as e:
            log.error(f"Volatility prediction model failed: {e}")
            return None
    
    async def _sentiment_analysis_model(self, symbol: str) -> Dict[str, Any]:
        """AI model for sentiment analysis"""
        try:
            # This would integrate with the advanced news module
            # For now, return a simplified analysis
            return {
                "score": 0.1,  # Slightly positive
                "confidence": 60,
                "factors": ["News sentiment analysis", "Social media sentiment", "Technical sentiment"]
            }
            
        except Exception as e:
            log.error(f"Sentiment analysis model failed: {e}")
            return {"score": 0, "confidence": 0, "factors": []}
    
    async def _fetch_fear_greed_index(self) -> Dict[str, Any]:
        """Fetch Fear & Greed Index"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get("https://api.alternative.me/fng/")
                
                if response.status_code == 200:
                    data = response.json()
                    fng_data = data.get("data", [{}])[0]
                    return {
                        "value": int(fng_data.get("value", 50)),
                        "classification": fng_data.get("value_classification", "Neutral")
                    }
        except Exception as e:
            log.warning(f"Failed to fetch Fear & Greed Index: {e}")
        
        return {"value": 50, "classification": "Neutral"}
    
    async def _analyze_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze social media sentiment"""
        try:
            # This would integrate with social media APIs
            # For now, return mock data
            return {
                "score": 0.2,  # Slightly positive
                "confidence": 50,
                "source": "Social Media Analysis"
            }
        except Exception as e:
            log.warning(f"Social sentiment analysis failed: {e}")
            return {"score": 0, "confidence": 0}
    
    async def _analyze_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze news sentiment"""
        try:
            # This would integrate with the advanced news module
            # For now, return mock data
            return {
                "score": 0.1,  # Slightly positive
                "confidence": 60,
                "source": "News Analysis"
            }
        except Exception as e:
            log.warning(f"News sentiment analysis failed: {e}")
            return {"score": 0, "confidence": 0}
    
    async def _analyze_technical_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze technical sentiment"""
        try:
            # This would integrate with technical analysis
            # For now, return mock data
            return {
                "score": 0.3,  # Moderately positive
                "confidence": 70,
                "source": "Technical Analysis"
            }
        except Exception as e:
            log.warning(f"Technical sentiment analysis failed: {e}")
            return {"score": 0, "confidence": 0}
    
    async def _analyze_institutional_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze institutional sentiment"""
        try:
            # This would integrate with institutional data
            # For now, return mock data
            return {
                "score": 0.0,  # Neutral
                "confidence": 40,
                "source": "Institutional Analysis"
            }
        except Exception as e:
            log.warning(f"Institutional sentiment analysis failed: {e}")
            return {"score": 0, "confidence": 0}
    
    def _calculate_market_outlook(self, price_prediction, trend_prediction, 
                                volatility_prediction, sentiment_analysis) -> Dict[str, Any]:
        """Calculate overall market outlook"""
        try:
            outlook_score = 0
            confidence_scores = []
            factors = []
            
            # Price prediction factor
            if price_prediction:
                price_confidence = price_prediction.confidence
                price_change = (price_prediction.predicted_value - price_prediction.current_value) / price_prediction.current_value
                outlook_score += price_change * (price_confidence / 100)
                confidence_scores.append(price_confidence)
                factors.append(f"Price prediction: {price_change:.1%}")
            
            # Trend prediction factor
            if trend_prediction:
                trend_confidence = trend_prediction.confidence
                trend_direction = trend_prediction.predicted_value
                outlook_score += trend_direction * (trend_confidence / 100)
                confidence_scores.append(trend_confidence)
                factors.append(f"Trend: {trend_prediction.reasoning}")
            
            # Sentiment factor
            if sentiment_analysis:
                sentiment_score = sentiment_analysis.sentiment_score
                sentiment_confidence = sentiment_analysis.confidence
                outlook_score += sentiment_score * (sentiment_confidence / 100)
                confidence_scores.append(sentiment_confidence)
                factors.append(f"Sentiment: {sentiment_analysis.overall_sentiment}")
            
            # Calculate overall confidence
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            # Determine outlook
            if outlook_score > 0.3:
                outlook = "Very Bullish"
            elif outlook_score > 0.1:
                outlook = "Bullish"
            elif outlook_score < -0.3:
                outlook = "Very Bearish"
            elif outlook_score < -0.1:
                outlook = "Bearish"
            else:
                outlook = "Neutral"
            
            return {
                "outlook": outlook,
                "outlook_score": outlook_score,
                "confidence": overall_confidence,
                "factors": factors
            }
            
        except Exception as e:
            log.error(f"Market outlook calculation failed: {e}")
            return {"outlook": "Unknown", "outlook_score": 0, "confidence": 0, "factors": []}
    
    def _generate_trading_recommendation(self, outlook: Dict[str, Any]) -> str:
        """Generate trading recommendation based on outlook"""
        try:
            outlook_type = outlook.get("outlook", "Neutral")
            confidence = outlook.get("confidence", 0)
            
            if confidence < 50:
                return "Low confidence - wait for clearer signals"
            
            if outlook_type in ["Very Bullish", "Bullish"]:
                return "Consider long positions with appropriate risk management"
            elif outlook_type in ["Very Bearish", "Bearish"]:
                return "Consider short positions or reduce exposure"
            else:
                return "Market neutral - focus on range trading or wait for breakout"
                
        except Exception as e:
            log.error(f"Trading recommendation generation failed: {e}")
            return "Unable to generate recommendation"
    
    def _get_timeframe_hours(self, timeframe: str) -> int:
        """Convert timeframe string to hours"""
        timeframe_map = {
            "1h": 1,
            "4h": 4,
            "1d": 24,
            "1w": 168,
            "1m": 720
        }
        return timeframe_map.get(timeframe, 24)
    
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
