from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

import httpx
from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """News article data structure"""
    title: str
    content: str
    url: str
    source: str
    published_at: datetime
    sentiment_score: float  # -1 to 1
    sentiment_label: str  # 'positive', 'negative', 'neutral'
    impact_score: float  # 0 to 100
    keywords: List[str]
    category: str
    language: str = "en"


@dataclass
class MarketImpact:
    """Market impact analysis"""
    symbol: str
    impact_score: float
    impact_type: str  # 'positive', 'negative', 'neutral'
    confidence: float
    expected_movement: str  # 'up', 'down', 'sideways'
    timeframe: str  # 'short', 'medium', 'long'
    reasoning: str


class AdvancedNewsAggregator:
    """Advanced news aggregation and sentiment analysis"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
        # Crypto and forex keywords for impact analysis
        self.crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'cryptocurrency', 'crypto', 'blockchain',
            'defi', 'nft', 'altcoin', 'trading', 'exchange', 'wallet', 'mining',
            'regulation', 'sec', 'cftc', 'cbdc', 'digital currency', 'stablecoin'
        ]
        
        self.forex_keywords = [
            'dollar', 'euro', 'pound', 'yen', 'forex', 'fx', 'currency', 'exchange rate',
            'fed', 'federal reserve', 'ecb', 'boe', 'boj', 'interest rate', 'inflation',
            'gdp', 'unemployment', 'monetary policy', 'quantitative easing'
        ]
        
        # Sentiment analysis keywords
        self.positive_keywords = [
            'bullish', 'surge', 'rally', 'gain', 'rise', 'increase', 'growth', 'positive',
            'optimistic', 'strong', 'breakthrough', 'milestone', 'adoption', 'institutional',
            'approval', 'launch', 'upgrade', 'partnership', 'investment'
        ]
        
        self.negative_keywords = [
            'bearish', 'crash', 'drop', 'fall', 'decline', 'decrease', 'negative',
            'pessimistic', 'weak', 'concern', 'risk', 'volatility', 'uncertainty',
            'regulation', 'ban', 'hack', 'security', 'loss', 'correction'
        ]
    
    async def fetch_crypto_news(self) -> List[NewsArticle]:
        """Fetch cryptocurrency news from multiple sources"""
        try:
            articles = []
            
            # NewsAPI
            if self.settings.NEWSAPI_KEY:
                articles.extend(await self._fetch_newsapi_articles("cryptocurrency"))
            
            # NewsData
            if self.settings.NEWSDATA_KEY:
                articles.extend(await self._fetch_newsdata_articles("cryptocurrency"))
            
            # MediaStack
            if self.settings.MEDIASTACK_KEY:
                articles.extend(await self._fetch_mediastack_articles("cryptocurrency"))
            
            # CoinDesk API
            articles.extend(await self._fetch_coindesk_articles())
            
            # CryptoPanic API
            articles.extend(await self._fetch_cryptopanic_articles())
            
            # Remove duplicates and analyze sentiment
            unique_articles = self._remove_duplicates(articles)
            analyzed_articles = []
            
            for article in unique_articles:
                sentiment = self._analyze_sentiment(article.title + " " + article.content)
                impact = self._calculate_impact(article, "crypto")
                
                article.sentiment_score = sentiment["score"]
                article.sentiment_label = sentiment["label"]
                article.impact_score = impact["score"]
                article.keywords = impact["keywords"]
                article.category = "cryptocurrency"
                
                analyzed_articles.append(article)
            
            return sorted(analyzed_articles, key=lambda x: x.impact_score, reverse=True)
            
        except Exception as e:
            log.error(f"Failed to fetch crypto news: {e}")
            return []
    
    async def fetch_forex_news(self) -> List[NewsArticle]:
        """Fetch forex news from multiple sources"""
        try:
            articles = []
            
            # NewsAPI
            if self.settings.NEWSAPI_KEY:
                articles.extend(await self._fetch_newsapi_articles("forex"))
            
            # NewsData
            if self.settings.NEWSDATA_KEY:
                articles.extend(await self._fetch_newsdata_articles("forex"))
            
            # MediaStack
            if self.settings.MEDIASTACK_KEY:
                articles.extend(await self._fetch_mediastack_articles("forex"))
            
            # Economic calendar data
            articles.extend(await self._fetch_economic_calendar())
            
            # Remove duplicates and analyze sentiment
            unique_articles = self._remove_duplicates(articles)
            analyzed_articles = []
            
            for article in unique_articles:
                sentiment = self._analyze_sentiment(article.title + " " + article.content)
                impact = self._calculate_impact(article, "forex")
                
                article.sentiment_score = sentiment["score"]
                article.sentiment_label = sentiment["label"]
                article.impact_score = impact["score"]
                article.keywords = impact["keywords"]
                article.category = "forex"
                
                analyzed_articles.append(article)
            
            return sorted(analyzed_articles, key=lambda x: x.impact_score, reverse=True)
            
        except Exception as e:
            log.error(f"Failed to fetch forex news: {e}")
            return []
    
    async def _fetch_newsapi_articles(self, category: str) -> List[NewsArticle]:
        """Fetch articles from NewsAPI"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "apiKey": self.settings.NEWSAPI_KEY,
                        "q": category,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "pageSize": 50,
                        "from": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles = []
                    
                    for article_data in data.get("articles", []):
                        if article_data.get("title") and article_data.get("content"):
                            article = NewsArticle(
                                title=article_data["title"],
                                content=article_data["content"] or "",
                                url=article_data["url"],
                                source=article_data["source"]["name"],
                                published_at=datetime.fromisoformat(
                                    article_data["publishedAt"].replace("Z", "+00:00")
                                ),
                                sentiment_score=0,
                                sentiment_label="neutral",
                                impact_score=0,
                                keywords=[],
                                category=category
                            )
                            articles.append(article)
                    
                    return articles
                    
        except Exception as e:
            log.warning(f"NewsAPI fetch failed: {e}")
        
        return []
    
    async def _fetch_newsdata_articles(self, category: str) -> List[NewsArticle]:
        """Fetch articles from NewsData"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://newsdata.io/api/1/news",
                    params={
                        "apikey": self.settings.NEWSDATA_KEY,
                        "q": category,
                        "language": "en",
                        "category": "business,technology",
                        "country": "us,gb,ca,au",
                        "timeframe": "24h"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles = []
                    
                    for article_data in data.get("results", []):
                        if article_data.get("title"):
                            article = NewsArticle(
                                title=article_data["title"],
                                content=article_data.get("content", ""),
                                url=article_data["link"],
                                source=article_data.get("source_id", "NewsData"),
                                published_at=datetime.fromisoformat(
                                    article_data["pubDate"].replace("Z", "+00:00")
                                ),
                                sentiment_score=0,
                                sentiment_label="neutral",
                                impact_score=0,
                                keywords=[],
                                category=category
                            )
                            articles.append(article)
                    
                    return articles
                    
        except Exception as e:
            log.warning(f"NewsData fetch failed: {e}")
        
        return []
    
    async def _fetch_mediastack_articles(self, category: str) -> List[NewsArticle]:
        """Fetch articles from MediaStack"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "http://api.mediastack.com/v1/news",
                    params={
                        "access_key": self.settings.MEDIASTACK_KEY,
                        "keywords": category,
                        "languages": "en",
                        "sort": "published_desc",
                        "limit": 50
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles = []
                    
                    for article_data in data.get("data", []):
                        if article_data.get("title"):
                            article = NewsArticle(
                                title=article_data["title"],
                                content=article_data.get("description", ""),
                                url=article_data["url"],
                                source=article_data["source"],
                                published_at=datetime.fromisoformat(
                                    article_data["published_at"].replace("Z", "+00:00")
                                ),
                                sentiment_score=0,
                                sentiment_label="neutral",
                                impact_score=0,
                                keywords=[],
                                category=category
                            )
                            articles.append(article)
                    
                    return articles
                    
        except Exception as e:
            log.warning(f"MediaStack fetch failed: {e}")
        
        return []
    
    async def _fetch_coindesk_articles(self) -> List[NewsArticle]:
        """Fetch articles from CoinDesk"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=json"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles = []
                    
                    for item in data.get("items", [])[:20]:  # Limit to 20 articles
                        if item.get("title"):
                            article = NewsArticle(
                                title=item["title"],
                                content=item.get("content_html", ""),
                                url=item["url"],
                                source="CoinDesk",
                                published_at=datetime.fromisoformat(
                                    item["date_published"].replace("Z", "+00:00")
                                ),
                                sentiment_score=0,
                                sentiment_label="neutral",
                                impact_score=0,
                                keywords=[],
                                category="cryptocurrency"
                            )
                            articles.append(article)
                    
                    return articles
                    
        except Exception as e:
            log.warning(f"CoinDesk fetch failed: {e}")
        
        return []
    
    async def _fetch_cryptopanic_articles(self) -> List[NewsArticle]:
        """Fetch articles from CryptoPanic"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://cryptopanic.com/api/v1/posts/",
                    params={
                        "auth_token": "free",  # Free tier
                        "public": "true",
                        "filter": "hot",
                        "currencies": "BTC,ETH,ADA,SOL,MATIC"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles = []
                    
                    for post in data.get("results", [])[:20]:
                        if post.get("title"):
                            article = NewsArticle(
                                title=post["title"],
                                content=post.get("metadata", {}).get("description", ""),
                                url=post["url"],
                                source="CryptoPanic",
                                published_at=datetime.fromisoformat(
                                    post["created_at"].replace("Z", "+00:00")
                                ),
                                sentiment_score=0,
                                sentiment_label="neutral",
                                impact_score=0,
                                keywords=[],
                                category="cryptocurrency"
                            )
                            articles.append(article)
                    
                    return articles
                    
        except Exception as e:
            log.warning(f"CryptoPanic fetch failed: {e}")
        
        return []
    
    async def _fetch_economic_calendar(self) -> List[NewsArticle]:
        """Fetch economic calendar events"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://api.fxempire.com/v1/en/markets/currencies/economic-calendar",
                    params={
                        "from": datetime.now().strftime("%Y-%m-%d"),
                        "to": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles = []
                    
                    for event in data.get("economicEvents", [])[:20]:
                        if event.get("title"):
                            article = NewsArticle(
                                title=f"Economic Event: {event['title']}",
                                content=f"Impact: {event.get('impact', 'Medium')} - {event.get('description', '')}",
                                url="",
                                source="FX Empire",
                                published_at=datetime.fromisoformat(
                                    event["date"].replace("Z", "+00:00")
                                ),
                                sentiment_score=0,
                                sentiment_label="neutral",
                                impact_score=0,
                                keywords=[],
                                category="forex"
                            )
                            articles.append(article)
                    
                    return articles
                    
        except Exception as e:
            log.warning(f"Economic calendar fetch failed: {e}")
        
        return []
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        try:
            text_lower = text.lower()
            
            # Count positive and negative keywords
            positive_count = sum(1 for keyword in self.positive_keywords if keyword in text_lower)
            negative_count = sum(1 for keyword in self.negative_keywords if keyword in text_lower)
            
            # Calculate sentiment score
            total_keywords = positive_count + negative_count
            if total_keywords == 0:
                return {"score": 0, "label": "neutral"}
            
            sentiment_score = (positive_count - negative_count) / total_keywords
            
            # Determine label
            if sentiment_score > 0.2:
                label = "positive"
            elif sentiment_score < -0.2:
                label = "negative"
            else:
                label = "neutral"
            
            return {"score": sentiment_score, "label": label}
            
        except Exception as e:
            log.warning(f"Sentiment analysis failed: {e}")
            return {"score": 0, "label": "neutral"}
    
    def _calculate_impact(self, article: NewsArticle, category: str) -> Dict[str, Any]:
        """Calculate market impact of an article"""
        try:
            text = (article.title + " " + article.content).lower()
            impact_score = 0
            keywords = []
            
            # Check for high-impact keywords
            high_impact_keywords = [
                'regulation', 'sec', 'cftc', 'ban', 'approval', 'adoption',
                'institutional', 'partnership', 'hack', 'security', 'crash',
                'rally', 'breakthrough', 'milestone'
            ]
            
            for keyword in high_impact_keywords:
                if keyword in text:
                    impact_score += 20
                    keywords.append(keyword)
            
            # Check for category-specific keywords
            if category == "crypto":
                for keyword in self.crypto_keywords:
                    if keyword in text:
                        impact_score += 5
                        if keyword not in keywords:
                            keywords.append(keyword)
            elif category == "forex":
                for keyword in self.forex_keywords:
                    if keyword in text:
                        impact_score += 5
                        if keyword not in keywords:
                            keywords.append(keyword)
            
            # Check for sentiment impact
            if article.sentiment_score > 0.5:
                impact_score += 15
            elif article.sentiment_score < -0.5:
                impact_score += 15
            
            # Source credibility
            credible_sources = ['coindesk', 'reuters', 'bloomberg', 'wsj', 'ft', 'cnbc']
            if any(source in article.source.lower() for source in credible_sources):
                impact_score += 10
            
            # Recency bonus
            hours_old = (datetime.now() - article.published_at).total_seconds() / 3600
            if hours_old < 1:
                impact_score += 20
            elif hours_old < 6:
                impact_score += 10
            elif hours_old < 24:
                impact_score += 5
            
            return {
                "score": min(impact_score, 100),
                "keywords": keywords[:10]  # Limit to top 10 keywords
            }
            
        except Exception as e:
            log.warning(f"Impact calculation failed: {e}")
            return {"score": 0, "keywords": []}
    
    def _remove_duplicates(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on title similarity"""
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            # Simple title normalization
            normalized_title = re.sub(r'[^\w\s]', '', article.title.lower()).strip()
            
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_articles.append(article)
        
        return unique_articles
    
    async def analyze_market_impact(self, articles: List[NewsArticle]) -> List[MarketImpact]:
        """Analyze market impact of news articles"""
        try:
            impacts = []
            
            # Group articles by symbol/currency
            symbol_articles = {}
            for article in articles:
                # Extract symbols from keywords
                symbols = self._extract_symbols(article.keywords)
                for symbol in symbols:
                    if symbol not in symbol_articles:
                        symbol_articles[symbol] = []
                    symbol_articles[symbol].append(article)
            
            # Analyze impact for each symbol
            for symbol, symbol_articles_list in symbol_articles.items():
                impact = self._calculate_symbol_impact(symbol, symbol_articles_list)
                if impact:
                    impacts.append(impact)
            
            return sorted(impacts, key=lambda x: x.impact_score, reverse=True)
            
        except Exception as e:
            log.error(f"Market impact analysis failed: {e}")
            return []
    
    def _extract_symbols(self, keywords: List[str]) -> List[str]:
        """Extract trading symbols from keywords"""
        symbols = []
        
        # Crypto symbols
        crypto_symbols = {
            'bitcoin': 'BTC', 'btc': 'BTC', 'ethereum': 'ETH', 'eth': 'ETH',
            'cardano': 'ADA', 'ada': 'ADA', 'solana': 'SOL', 'sol': 'SOL',
            'matic': 'MATIC', 'polkadot': 'DOT', 'dot': 'DOT',
            'chainlink': 'LINK', 'link': 'LINK', 'uniswap': 'UNI', 'uni': 'UNI'
        }
        
        for keyword in keywords:
            if keyword in crypto_symbols:
                symbols.append(crypto_symbols[keyword])
        
        # Forex symbols
        forex_symbols = {
            'dollar': 'USD', 'euro': 'EUR', 'pound': 'GBP', 'yen': 'JPY',
            'usd': 'USD', 'eur': 'EUR', 'gbp': 'GBP', 'jpy': 'JPY'
        }
        
        for keyword in keywords:
            if keyword in forex_symbols:
                symbols.append(forex_symbols[keyword])
        
        return list(set(symbols))
    
    def _calculate_symbol_impact(self, symbol: str, articles: List[NewsArticle]) -> Optional[MarketImpact]:
        """Calculate market impact for a specific symbol"""
        try:
            if not articles:
                return None
            
            # Calculate weighted impact score
            total_impact = 0
            total_weight = 0
            positive_articles = 0
            negative_articles = 0
            
            for article in articles:
                weight = 1.0
                
                # Weight by recency
                hours_old = (datetime.now() - article.published_at).total_seconds() / 3600
                if hours_old < 1:
                    weight *= 2.0
                elif hours_old < 6:
                    weight *= 1.5
                elif hours_old < 24:
                    weight *= 1.2
                
                # Weight by source credibility
                credible_sources = ['coindesk', 'reuters', 'bloomberg', 'wsj', 'ft', 'cnbc']
                if any(source in article.source.lower() for source in credible_sources):
                    weight *= 1.5
                
                total_impact += article.impact_score * weight
                total_weight += weight
                
                if article.sentiment_score > 0.2:
                    positive_articles += 1
                elif article.sentiment_score < -0.2:
                    negative_articles += 1
            
            if total_weight == 0:
                return None
            
            avg_impact = total_impact / total_weight
            
            # Determine impact type
            if positive_articles > negative_articles:
                impact_type = "positive"
                expected_movement = "up"
            elif negative_articles > positive_articles:
                impact_type = "negative"
                expected_movement = "down"
            else:
                impact_type = "neutral"
                expected_movement = "sideways"
            
            # Determine timeframe
            if avg_impact > 70:
                timeframe = "short"
            elif avg_impact > 40:
                timeframe = "medium"
            else:
                timeframe = "long"
            
            # Calculate confidence
            confidence = min(avg_impact / 100, 1.0)
            
            # Generate reasoning
            reasoning = f"Based on {len(articles)} articles: {positive_articles} positive, {negative_articles} negative sentiment"
            
            return MarketImpact(
                symbol=symbol,
                impact_score=avg_impact,
                impact_type=impact_type,
                confidence=confidence,
                expected_movement=expected_movement,
                timeframe=timeframe,
                reasoning=reasoning
            )
            
        except Exception as e:
            log.warning(f"Symbol impact calculation failed for {symbol}: {e}")
            return None
