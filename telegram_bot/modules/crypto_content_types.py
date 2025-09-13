from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class CryptocurrencyContent:
    """Cryptocurrency market content and analysis"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
    async def fetch_major_cryptocurrencies(self) -> List[Dict[str, Any]]:
        """Fetch major cryptocurrency data from CoinGecko API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "order": "market_cap_desc",
                        "per_page": "20",
                        "page": "1",
                        "sparkline": "true",
                        "price_change_percentage": "24h,7d,30d"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            'id': coin.get('id', ''),
                            'name': coin.get('name', ''),
                            'symbol': coin.get('symbol', '').upper(),
                            'current_price': coin.get('current_price', 0),
                            'market_cap': coin.get('market_cap', 0),
                            'total_volume': coin.get('total_volume', 0),
                            'price_change_24h': coin.get('price_change_percentage_24h', 0),
                            'price_change_7d': coin.get('price_change_percentage_7d_in_currency', 0),
                            'price_change_30d': coin.get('price_change_percentage_30d_in_currency', 0),
                            'market_cap_rank': coin.get('market_cap_rank', 0),
                            'sparkline': coin.get('sparkline_in_7d', {}).get('price', []),
                            'source': 'CoinGecko'
                        }
                        for coin in data[:10]  # Top 10 cryptocurrencies
                    ]
        except Exception as e:
            log.warning(f"Major cryptocurrencies data failed: {e}")
            return []
    
    async def fetch_defi_protocols(self) -> List[Dict[str, Any]]:
        """Fetch DeFi protocol data"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "category": "decentralized-finance-defi",
                        "order": "market_cap_desc",
                        "per_page": "10",
                        "page": "1"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            'name': coin.get('name', ''),
                            'symbol': coin.get('symbol', '').upper(),
                            'current_price': coin.get('current_price', 0),
                            'market_cap': coin.get('market_cap', 0),
                            'price_change_24h': coin.get('price_change_percentage_24h', 0),
                            'category': 'DeFi',
                            'source': 'CoinGecko'
                        }
                        for coin in data[:5]  # Top 5 DeFi protocols
                    ]
        except Exception as e:
            log.warning(f"DeFi protocols data failed: {e}")
            return []
    
    async def get_crypto_insights(self) -> Dict[str, Any]:
        """Get comprehensive cryptocurrency insights"""
        return {
            'major_cryptocurrencies': await self.fetch_major_cryptocurrencies(),
            'defi_protocols': await self.fetch_defi_protocols(),
            'market_analysis': 'تحلیل بازار کریپتو',
            'technical_indicators': 'شاخص‌های تکنیکال',
            'trading_volume': 'حجم معاملات'
        }


class ForexContent:
    """Forex market content and analysis"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
    async def fetch_major_currency_pairs(self) -> List[Dict[str, Any]]:
        """Fetch major currency pairs data"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://api.exchangerate.host/latest",
                    params={
                        "base": "USD",
                        "symbols": "IRR,EUR,GBP,JPY,CHF,CAD,AUD,NZD"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    rates = data.get('rates', {})
                    return [
                        {
                            'pair': 'USD/IRR',
                            'rate': rates.get('IRR', 0),
                            'change': 0,  # Would need historical data for change calculation
                            'source': 'ExchangeRate.host'
                        },
                        {
                            'pair': 'EUR/USD',
                            'rate': 1 / rates.get('EUR', 1),
                            'change': 0,
                            'source': 'ExchangeRate.host'
                        },
                        {
                            'pair': 'GBP/USD',
                            'rate': 1 / rates.get('GBP', 1),
                            'change': 0,
                            'source': 'ExchangeRate.host'
                        },
                        {
                            'pair': 'USD/JPY',
                            'rate': 1 / rates.get('JPY', 1),
                            'change': 0,
                            'source': 'ExchangeRate.host'
                        }
                    ]
        except Exception as e:
            log.warning(f"Major currency pairs data failed: {e}")
            return []
    
    async def fetch_economic_indicators(self) -> List[Dict[str, Any]]:
        """Fetch economic indicators that affect forex markets"""
        try:
            # This would typically come from a financial data API
            # For now, return sample data
            return [
                {
                    'indicator': 'نرخ تورم آمریکا',
                    'value': '3.2%',
                    'impact': 'high',
                    'trend': 'stable',
                    'source': 'Federal Reserve'
                },
                {
                    'indicator': 'نرخ بهره فدرال رزرو',
                    'value': '5.25%',
                    'impact': 'high',
                    'trend': 'stable',
                    'source': 'Federal Reserve'
                },
                {
                    'indicator': 'تولید ناخالص داخلی آمریکا',
                    'value': '2.1%',
                    'impact': 'medium',
                    'trend': 'growing',
                    'source': 'Bureau of Economic Analysis'
                }
            ]
        except Exception as e:
            log.warning(f"Economic indicators data failed: {e}")
            return []
    
    async def get_forex_insights(self) -> Dict[str, Any]:
        """Get comprehensive forex insights"""
        return {
            'major_pairs': await self.fetch_major_currency_pairs(),
            'economic_indicators': await self.fetch_economic_indicators(),
            'central_bank_policies': 'سیاست‌های بانک‌های مرکزی',
            'market_sentiment': 'احساسات بازار فارکس',
            'technical_analysis': 'تحلیل تکنیکال'
        }


class TradingContent:
    """Trading insights and technical analysis content"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
    async def fetch_fear_greed_index(self) -> Dict[str, Any]:
        """Fetch Fear & Greed Index data"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get("https://api.alternative.me/fng/")
                
                if response.status_code == 200:
                    data = response.json()
                    fng_data = data.get('data', [{}])[0]
                    return {
                        'value': int(fng_data.get('value', 0)),
                        'classification': fng_data.get('value_classification', ''),
                        'timestamp': fng_data.get('timestamp', ''),
                        'source': 'Alternative.me'
                    }
        except Exception as e:
            log.warning(f"Fear & Greed Index data failed: {e}")
            return {'value': 50, 'classification': 'Neutral', 'source': 'Alternative.me'}
    
    async def fetch_market_sentiment(self) -> List[Dict[str, Any]]:
        """Fetch market sentiment indicators"""
        try:
            # This would typically come from social media sentiment APIs
            # For now, return sample data
            return [
                {
                    'indicator': 'احساسات توییتر',
                    'value': 'مثبت',
                    'confidence': '75%',
                    'trend': 'بهبود',
                    'source': 'Social Media'
                },
                {
                    'indicator': 'فعالیت نهنگ‌ها',
                    'value': 'بالا',
                    'confidence': '80%',
                    'trend': 'افزایش',
                    'source': 'Blockchain Analysis'
                }
            ]
        except Exception as e:
            log.warning(f"Market sentiment data failed: {e}")
            return []
    
    async def get_trading_insights(self) -> Dict[str, Any]:
        """Get comprehensive trading insights"""
        return {
            'fear_greed_index': await self.fetch_fear_greed_index(),
            'market_sentiment': await self.fetch_market_sentiment(),
            'technical_patterns': 'الگوهای تکنیکال',
            'support_resistance': 'سطوح حمایت و مقاومت',
            'volume_analysis': 'تحلیل حجم'
        }


class RegulatoryContent:
    """Regulatory and compliance content"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
    async def fetch_regulatory_news(self) -> List[Dict[str, Any]]:
        """Fetch regulatory news and updates"""
        try:
            # This would typically come from news APIs filtered for regulatory content
            # For now, return sample data
            return [
                {
                    'title': 'به‌روزرسانی قوانین کریپتو در اروپا',
                    'impact': 'high',
                    'region': 'Europe',
                    'category': 'regulation',
                    'source': 'Regulatory News'
                },
                {
                    'title': 'سیاست‌های جدید بانک مرکزی آمریکا',
                    'impact': 'medium',
                    'region': 'USA',
                    'category': 'monetary_policy',
                    'source': 'Federal Reserve'
                }
            ]
        except Exception as e:
            log.warning(f"Regulatory news data failed: {e}")
            return []
    
    async def get_regulatory_insights(self) -> Dict[str, Any]:
        """Get comprehensive regulatory insights"""
        return {
            'regulatory_news': await self.fetch_regulatory_news(),
            'compliance_updates': 'به‌روزرسانی‌های انطباق',
            'policy_analysis': 'تحلیل سیاست‌ها',
            'legal_developments': 'توسعه‌های حقوقی'
        }


class CryptoForexContentManager:
    """Main class to manage all crypto and forex content types"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.crypto = CryptocurrencyContent(settings)
        self.forex = ForexContent(settings)
        self.trading = TradingContent(settings)
        self.regulatory = RegulatoryContent(settings)
        
    async def get_all_crypto_forex_content(self) -> Dict[str, Any]:
        """Get comprehensive crypto and forex content for فردایاب"""
        try:
            # Fetch all content types concurrently
            crypto_task = asyncio.create_task(self.crypto.get_crypto_insights())
            forex_task = asyncio.create_task(self.forex.get_forex_insights())
            trading_task = asyncio.create_task(self.trading.get_trading_insights())
            regulatory_task = asyncio.create_task(self.regulatory.get_regulatory_insights())
            
            crypto_data = await crypto_task
            forex_data = await forex_task
            trading_data = await trading_task
            regulatory_data = await regulatory_task
            
            return {
                'cryptocurrency': crypto_data,
                'forex': forex_data,
                'trading': trading_data,
                'regulatory': regulatory_data,
                'crypto_forex_content_active': True,
                'total_content_types': 4
            }
            
        except Exception as e:
            log.error(f"Crypto/Forex content collection failed: {e}")
            return {
                'cryptocurrency': {},
                'forex': {},
                'trading': {},
                'regulatory': {},
                'crypto_forex_content_active': False,
                'total_content_types': 0
            }
    
    async def get_content_type_insights(self, content_type: str) -> Dict[str, Any]:
        """Get insights for specific content type"""
        content_type = content_type.lower()
        
        if content_type in ['crypto', 'cryptocurrency', 'کریپتو', 'ارز_دیجیتال']:
            return await self.crypto.get_crypto_insights()
        elif content_type in ['forex', 'fx', 'فارکس', 'ارز']:
            return await self.forex.get_forex_insights()
        elif content_type in ['trading', 'معامله', 'ترید']:
            return await self.trading.get_trading_insights()
        elif content_type in ['regulatory', 'regulation', 'قانون', 'مقررات']:
            return await self.regulatory.get_regulatory_insights()
        else:
            return {'error': f'Unknown content type: {content_type}'}
