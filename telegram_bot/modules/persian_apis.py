from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class PersianNewsAPI:
    """Enhanced Persian news collection from multiple sources"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
    async def fetch_persian_news(self) -> List[Dict[str, Any]]:
        """Fetch news from multiple Persian sources"""
        news_sources = []
        
        # World News API for Persian content
        if hasattr(self.settings, 'WORLD_NEWS_API_KEY') and self.settings.WORLD_NEWS_API_KEY:
            news_sources.append(self._fetch_world_news_persian())
        
        # Iranian news sources
        news_sources.extend([
            self._fetch_tasnim_news(),
            self._fetch_isna_news(),
            self._fetch_mehr_news(),
            self._fetch_fars_news()
        ])
        
        # Run all sources concurrently
        results = await asyncio.gather(*news_sources, return_exceptions=True)
        
        # Combine and deduplicate results
        all_news = []
        for result in results:
            if isinstance(result, list):
                all_news.extend(result)
            elif isinstance(result, Exception):
                log.warning(f"News source failed: {result}")
        
        # Remove duplicates based on title
        seen_titles = set()
        unique_news = []
        for news in all_news:
            title = news.get('title', '').lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(news)
        
        return unique_news[:20]  # Limit to 20 most recent
    
    async def _fetch_world_news_persian(self) -> List[Dict[str, Any]]:
        """Fetch Persian news from World News API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    'api-key': self.settings.WORLD_NEWS_API_KEY,
                    'language': 'fa',
                    'country': 'ir',
                    'number': 10,
                    'sort': 'published_desc'
                }
                response = await client.get('https://api.worldnewsapi.com/search-news', params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            'title': article.get('title', ''),
                            'description': article.get('text', ''),
                            'source': article.get('source', {}).get('name', 'World News'),
                            'url': article.get('url', ''),
                            'published_at': article.get('published_at', ''),
                            'language': 'fa'
                        }
                        for article in data.get('news', [])
                    ]
        except Exception as e:
            log.warning(f"World News API failed: {e}")
        return []
    
    async def _fetch_tasnim_news(self) -> List[Dict[str, Any]]:
        """Fetch news from Tasnim News Agency"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get('https://www.tasnimnews.com/api/news/latest')
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            'title': article.get('title', ''),
                            'description': article.get('summary', ''),
                            'source': 'تسنیم',
                            'url': article.get('link', ''),
                            'published_at': article.get('publish_date', ''),
                            'language': 'fa'
                        }
                        for article in data.get('data', [])[:5]
                    ]
        except Exception as e:
            log.warning(f"Tasnim News failed: {e}")
        return []
    
    async def _fetch_isna_news(self) -> List[Dict[str, Any]]:
        """Fetch news from ISNA News Agency"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get('https://www.isna.ir/api/news/latest')
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            'title': article.get('title', ''),
                            'description': article.get('summary', ''),
                            'source': 'ایسنا',
                            'url': article.get('link', ''),
                            'published_at': article.get('publish_date', ''),
                            'language': 'fa'
                        }
                        for article in data.get('data', [])[:5]
                    ]
        except Exception as e:
            log.warning(f"ISNA News failed: {e}")
        return []
    
    async def _fetch_mehr_news(self) -> List[Dict[str, Any]]:
        """Fetch news from Mehr News Agency"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get('https://mehrnews.com/api/news/latest')
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            'title': article.get('title', ''),
                            'description': article.get('summary', ''),
                            'source': 'مهر',
                            'url': article.get('link', ''),
                            'published_at': article.get('publish_date', ''),
                            'language': 'fa'
                        }
                        for article in data.get('data', [])[:5]
                    ]
        except Exception as e:
            log.warning(f"Mehr News failed: {e}")
        return []
    
    async def _fetch_fars_news(self) -> List[Dict[str, Any]]:
        """Fetch news from Fars News Agency"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get('https://www.farsnews.ir/api/news/latest')
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            'title': article.get('title', ''),
                            'description': article.get('summary', ''),
                            'source': 'فارس',
                            'url': article.get('link', ''),
                            'published_at': article.get('publish_date', ''),
                            'language': 'fa'
                        }
                        for article in data.get('data', [])[:5]
                    ]
        except Exception as e:
            log.warning(f"Fars News failed: {e}")
        return []


class PersianTranslationAPI:
    """Persian translation and text enhancement"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
    async def translate_to_persian(self, text: str, source_lang: str = 'en') -> str:
        """Translate text to Persian using Lingvanex API"""
        try:
            if not hasattr(self.settings, 'LINGVANEX_API_KEY') or not self.settings.LINGVANEX_API_KEY:
                return text
                
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                data = {
                    'from': source_lang,
                    'to': 'fa',
                    'data': text,
                    'platform': 'api'
                }
                headers = {
                    'Authorization': f'Bearer {self.settings.LINGVANEX_API_KEY}',
                    'Content-Type': 'application/json'
                }
                
                response = await client.post(
                    'https://api-b2b.backenster.com/b1/api/v3/translate',
                    json=data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get('result', text)
                    
        except Exception as e:
            log.warning(f"Translation failed: {e}")
        return text
    
    async def enhance_persian_text(self, text: str) -> str:
        """Enhance Persian text quality"""
        # Basic Persian text improvements
        improvements = [
            ('  ', ' '),  # Remove double spaces
            ('\n\n\n', '\n\n'),  # Remove triple newlines
            ('،،', '،'),  # Remove double commas
            ('  ', ' '),  # Remove double spaces again
        ]
        
        for old, new in improvements:
            text = text.replace(old, new)
        
        return text.strip()


class PersianFinancialData:
    """Persian financial and economic data"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
    async def fetch_iranian_market_data(self) -> Dict[str, Any]:
        """Fetch Iranian market data"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Tehran Stock Exchange data
                tse_response = await client.get('https://api.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyList')
                
                if tse_response.status_code == 200:
                    tse_data = tse_response.json()
                    return {
                        'tehran_stock_exchange': tse_data,
                        'currency_rates': await self._fetch_currency_rates(),
                        'crypto_iranian': await self._fetch_iranian_crypto()
                    }
        except Exception as e:
            log.warning(f"Iranian market data failed: {e}")
        return {}
    
    async def _fetch_currency_rates(self) -> Dict[str, Any]:
        """Fetch Iranian currency rates"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get('https://api.exchangerate-api.com/v4/latest/IRR')
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'usd_to_irr': data.get('rates', {}).get('USD', 0),
                        'eur_to_irr': data.get('rates', {}).get('EUR', 0),
                        'last_updated': data.get('date', '')
                    }
        except Exception as e:
            log.warning(f"Currency rates failed: {e}")
        return {}
    
    async def _fetch_iranian_crypto(self) -> Dict[str, Any]:
        """Fetch Iranian cryptocurrency data"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=irr&order=market_cap_desc&per_page=10')
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'crypto_data': data,
                        'currency': 'IRR'
                    }
        except Exception as e:
            log.warning(f"Iranian crypto data failed: {e}")
        return {}


class PersianContentEnhancer:
    """Main class to enhance Persian content quality"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.news_api = PersianNewsAPI(settings)
        self.translation_api = PersianTranslationAPI(settings)
        self.financial_api = PersianFinancialData(settings)
        
    async def get_enhanced_persian_data(self) -> Dict[str, Any]:
        """Get comprehensive Persian content data"""
        try:
            # Fetch all Persian data concurrently
            news_task = asyncio.create_task(self.news_api.fetch_persian_news())
            financial_task = asyncio.create_task(self.financial_api.fetch_iranian_market_data())
            
            news_data = await news_task
            financial_data = await financial_task
            
            return {
                'persian_news': news_data,
                'iranian_financial': financial_data,
                'enhanced': True,
                'language': 'fa'
            }
            
        except Exception as e:
            log.error(f"Persian content enhancement failed: {e}")
            return {
                'persian_news': [],
                'iranian_financial': {},
                'enhanced': False,
                'language': 'fa'
            }
    
    async def enhance_content_quality(self, content: str) -> str:
        """Enhance Persian content quality"""
        try:
            # Translate if needed
            if not self._is_persian_text(content):
                content = await self.translation_api.translate_to_persian(content)
            
            # Enhance Persian text
            content = await self.translation_api.enhance_persian_text(content)
            
            return content
            
        except Exception as e:
            log.warning(f"Content enhancement failed: {e}")
            return content
    
    def _is_persian_text(self, text: str) -> bool:
        """Check if text is in Persian"""
        persian_chars = set('ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی')
        text_chars = set(text)
        return len(text_chars.intersection(persian_chars)) > len(text_chars) * 0.3
