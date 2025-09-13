from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class FreePersianAPIs:
    """Free Persian APIs for enhanced content"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
    async def fetch_ketabnak_books(self, query: str = "اقتصاد") -> List[Dict[str, Any]]:
        """Fetch Persian books from Ketabnak API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"https://api.ketabnak.com/search?q={query}")
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            'title': book.get('title', ''),
                            'author': book.get('author', ''),
                            'description': book.get('description', ''),
                            'category': book.get('category', ''),
                            'language': 'fa',
                            'source': 'کتابناک'
                        }
                        for book in data.get('books', [])[:5]
                    ]
        except Exception as e:
            log.warning(f"Ketabnak API failed: {e}")
        return []
    
    async def fetch_world_countries_info(self) -> List[Dict[str, Any]]:
        """Fetch countries information from World API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get("https://www.world-api.ir/api/countries")
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            'name': country.get('name', ''),
                            'capital': country.get('capital', ''),
                            'flag': country.get('flag', ''),
                            'population': country.get('population', ''),
                            'currency': country.get('currency', ''),
                            'language': 'fa'
                        }
                        for country in data.get('countries', [])[:10]
                    ]
        except Exception as e:
            log.warning(f"World API failed: {e}")
        return []
    
    async def fetch_iranian_apis_list(self) -> List[Dict[str, Any]]:
        """Fetch list of Iranian APIs from GitHub"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get("https://api.github.com/repos/Hameds/APIs-made-in-Iran/contents/README.md")
                
                if response.status_code == 200:
                    data = response.json()
                    # Parse markdown content for API list
                    content = data.get('content', '')
                    if content:
                        return [{'name': 'Iranian APIs Collection', 'description': 'List of Iranian APIs', 'source': 'GitHub'}]
        except Exception as e:
            log.warning(f"GitHub API failed: {e}")
        return []
    
    async def process_persian_text(self, text: str) -> Dict[str, Any]:
        """Process Persian text using Persian Tools"""
        try:
            # Basic Persian text processing
            persian_chars = set('ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی')
            text_chars = set(text)
            persian_ratio = len(text_chars.intersection(persian_chars)) / len(text_chars) if text_chars else 0
            
            # Count Persian words
            persian_words = [word for word in text.split() if any(char in persian_chars for char in word)]
            
            return {
                'is_persian': persian_ratio > 0.3,
                'persian_ratio': persian_ratio,
                'persian_word_count': len(persian_words),
                'total_words': len(text.split()),
                'processed': True
            }
        except Exception as e:
            log.warning(f"Persian text processing failed: {e}")
            return {'processed': False, 'error': str(e)}
    
    async def get_persian_calendar_info(self) -> Dict[str, Any]:
        """Get Persian calendar information"""
        # Persian month names
        persian_months = [
            'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
            'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
        ]
        
        # Persian weekday names
        persian_weekdays = [
            'شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه'
        ]
        
        try:
            from datetime import datetime
            import jdatetime
            
            now = datetime.now()
            persian_date = jdatetime.datetime.fromgregorian(datetime=now)
            
            return {
                'persian_year': persian_date.year,
                'persian_month': persian_date.month,
                'persian_day': persian_date.day,
                'persian_month_name': persian_months[persian_date.month - 1],
                'persian_weekday': persian_weekdays[persian_date.weekday()],
                'is_leap_year': jdatetime.date(persian_date.year, 1, 1).isleap(),
                'season': self._get_persian_season(persian_date.month)
            }
        except ImportError:
            log.warning("jdatetime not available, using fallback")
            # Calculate current Persian year manually (2025 = 1404)
            now = datetime.now()
            current_gregorian_year = now.year
            persian_year = current_gregorian_year - 621  # 2025 - 621 = 1404
            
            # Calculate approximate Persian month and day
            gregorian_month = now.month
            gregorian_day = now.day
            
            # Rough conversion: Gregorian to Persian
            if gregorian_month >= 3 and gregorian_month <= 5:
                persian_month = gregorian_month - 2  # March = 1 (Farvardin)
                persian_day = gregorian_day
            elif gregorian_month >= 6 and gregorian_month <= 8:
                persian_month = gregorian_month - 2  # June = 4 (Tir)
                persian_day = gregorian_day
            elif gregorian_month >= 9 and gregorian_month <= 11:
                persian_month = gregorian_month - 2  # September = 7 (Mehr)
                persian_day = gregorian_day
            else:  # December, January, February
                persian_month = gregorian_month + 10 if gregorian_month <= 2 else gregorian_month - 2
                persian_day = gregorian_day
            
            # Ensure valid month
            persian_month = max(1, min(12, persian_month))
            
            return {
                'persian_year': persian_year,
                'persian_month': persian_month,
                'persian_day': persian_day,
                'persian_month_name': persian_months[persian_month - 1],
                'persian_weekday': persian_weekdays[now.weekday()],
                'is_leap_year': False,
                'season': self._get_persian_season(persian_month)
            }
        except Exception as e:
            log.warning(f"Persian calendar failed: {e}")
            # Fallback with correct year and approximate month
            now = datetime.now()
            current_gregorian_year = now.year
            persian_year = current_gregorian_year - 621  # 2025 - 621 = 1404
            
            # Calculate approximate Persian month
            gregorian_month = now.month
            if gregorian_month >= 3 and gregorian_month <= 5:
                persian_month = gregorian_month - 2
            elif gregorian_month >= 6 and gregorian_month <= 8:
                persian_month = gregorian_month - 2
            elif gregorian_month >= 9 and gregorian_month <= 11:
                persian_month = gregorian_month - 2
            else:
                persian_month = gregorian_month + 10 if gregorian_month <= 2 else gregorian_month - 2
            
            persian_month = max(1, min(12, persian_month))
            
            return {
                'persian_year': persian_year,
                'persian_month': persian_month,
                'persian_day': now.day,
                'persian_month_name': persian_months[persian_month - 1],
                'persian_weekday': persian_weekdays[now.weekday()],
                'is_leap_year': False,
                'season': self._get_persian_season(persian_month)
            }
    
    def _get_persian_season(self, month: int) -> str:
        """Get Persian season based on month"""
        if month in [1, 2, 3]:
            return 'بهار'
        elif month in [4, 5, 6]:
            return 'تابستان'
        elif month in [7, 8, 9]:
            return 'پاییز'
        else:
            return 'زمستان'
    
    async def get_enhanced_persian_content(self) -> Dict[str, Any]:
        """Get comprehensive free Persian content"""
        try:
            # Fetch all free content concurrently
            books_task = asyncio.create_task(self.fetch_ketabnak_books("اقتصاد"))
            countries_task = asyncio.create_task(self.fetch_world_countries_info())
            apis_task = asyncio.create_task(self.fetch_iranian_apis_list())
            calendar_task = asyncio.create_task(self.get_persian_calendar_info())
            
            books = await books_task
            countries = await countries_task
            apis = await apis_task
            calendar = await calendar_task
            
            return {
                'persian_books': books,
                'countries_info': countries,
                'iranian_apis': apis,
                'persian_calendar': calendar,
                'free_apis_active': True,
                'total_sources': len(books) + len(countries) + len(apis)
            }
            
        except Exception as e:
            log.error(f"Free Persian content collection failed: {e}")
            return {
                'persian_books': [],
                'countries_info': [],
                'iranian_apis': [],
                'persian_calendar': {},
                'free_apis_active': False,
                'total_sources': 0
            }
