from __future__ import annotations

import asyncio
from typing import Any

from telegram_bot.config.settings import Settings
from telegram_bot.modules.crypto import fetch_crypto_and_fx
from telegram_bot.modules.news import fetch_combined_news
from telegram_bot.modules.trends import fetch_trending
from telegram_bot.modules.sports import fetch_sports
from telegram_bot.modules.persian_apis import PersianContentEnhancer
from telegram_bot.modules.free_persian_apis import FreePersianAPIs
from telegram_bot.modules.content_types import EnhancedContentManager


def _get_fallback_data() -> dict[str, Any]:
    """Provide fallback data when APIs fail"""
    return {
        "crypto": {
            "btc_line": "بیت‌کوین: تحلیل در حال انجام...",
            "usd_line": "دلار: نرخ فعلی در حال بررسی...",
        },
        "news": [
            {"title": "اخبار اقتصادی روز", "desc": "تحلیل‌های جدید در حال آماده‌سازی...", "source": "internal"}
        ],
        "trends": ["#اقتصاد", "#کریپتو", "#بازار", "#تحلیل", "#اخبار"],
        "trends_compare": {"region": "united_states", "values": ["#crypto", "#economy", "#markets", "#analysis", "#news"]},
        "sports": [
            {"home": "تیم A", "away": "تیم B", "time": "امروز", "prediction": "مسابقه جذاب پیش‌رو است"}
        ],
    }

async def collect_all(settings: Settings) -> dict[str, Any]:
    import logging
    log = logging.getLogger(__name__)
    
    # Enhanced data collection with retry logic
    async def _collect_with_retry(func, *args, **kwargs):
        for attempt in range(settings.CONNECTION_RETRY_ATTEMPTS):
            try:
                result = await func(*args, **kwargs)
                if result:  # If we got data, return it
                    return result
            except Exception as e:
                log.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                if attempt < settings.CONNECTION_RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(settings.CONNECTION_RETRY_DELAY)
        return None

    # Initialize Persian content enhancer, free APIs, and enhanced content
    persian_enhancer = PersianContentEnhancer(settings)
    free_persian_apis = FreePersianAPIs(settings)
    enhanced_content = EnhancedContentManager(settings)

    # Run collectors concurrently with retry logic
    crypto_task = asyncio.create_task(_collect_with_retry(fetch_crypto_and_fx, settings.HTTP_TIMEOUT))
    news_task = asyncio.create_task(_collect_with_retry(
        fetch_combined_news,
        settings.NEWSAPI_KEY,
        settings.NEWSDATA_KEY,
        settings.MEDIASTACK_KEY,
        settings.NEWS_LANGUAGE,
        settings.HTTP_TIMEOUT,
    ))
    trends_task = asyncio.create_task(_collect_with_retry(fetch_trending, "iran", 10))
    trends_cmp_task = asyncio.create_task(_collect_with_retry(fetch_trending, settings.TRENDS_COMPARE_REGION, 10))
    sports_task = asyncio.create_task(_collect_with_retry(fetch_sports, settings))
    
    # Persian content collection
    persian_task = asyncio.create_task(persian_enhancer.get_enhanced_persian_data())
    free_persian_task = asyncio.create_task(free_persian_apis.get_enhanced_persian_content())
    enhanced_content_task = asyncio.create_task(enhanced_content.get_all_enhanced_content())

    crypto = await crypto_task
    news = await news_task
    trends = await trends_task
    trends_cmp = await trends_cmp_task
    sports = await sports_task
    persian_data = await persian_task
    free_persian_data = await free_persian_task
    enhanced_content_data = await enhanced_content_task

    # Enhanced debugging info
    log.info(f"Real-time data collection results - Crypto: {bool(crypto)}, News: {len(news) if news else 0}, Trends: {len(trends) if trends else 0}, Sports: {len(sports) if sports else 0}, Persian: {persian_data.get('enhanced', False)}, Free Persian: {free_persian_data.get('free_apis_active', False)}, Enhanced Content: {enhanced_content_data.get('enhanced_content_active', False)}")
    
    # Log connectivity status
    if settings.ENABLE_REAL_TIME_DATA:
        log.info("Real-time data collection enabled - using latest available data")

    # Use fallback data if all APIs failed
    if not any([crypto, news, trends, sports, persian_data.get('enhanced', False)]):
        log.warning("All APIs failed, using fallback data")
        return _get_fallback_data()

    # Use fallback for individual failed APIs
    if not crypto:
        crypto = _get_fallback_data()["crypto"]
    if not news:
        news = _get_fallback_data()["news"]
    if not trends:
        trends = _get_fallback_data()["trends"]
    if not sports:
        sports = _get_fallback_data()["sports"]

    # Enhance news with Persian content if available
    if persian_data.get('enhanced', False) and persian_data.get('persian_news'):
        # Merge Persian news with existing news
        persian_news = persian_data['persian_news']
        if news:
            news.extend(persian_news)
        else:
            news = persian_news
        log.info(f"Enhanced news with {len(persian_news)} Persian articles")

    return {
        "crypto": crypto,
        "news": news,
        "trends": trends,
        "trends_compare": {"region": settings.TRENDS_COMPARE_REGION, "values": trends_cmp or _get_fallback_data()["trends_compare"]["values"]},
        "sports": sports,
        "persian_enhanced": persian_data.get('enhanced', False),
        "iranian_financial": persian_data.get('iranian_financial', {}),
        "free_persian_content": free_persian_data,
        "persian_books": free_persian_data.get('persian_books', []),
        "countries_info": free_persian_data.get('countries_info', []),
        "persian_calendar": free_persian_data.get('persian_calendar', {}),
        "enhanced_content": enhanced_content_data,
        "culture_arts": enhanced_content_data.get('culture_and_arts', {}),
        "technology_innovation": enhanced_content_data.get('technology_innovation', {}),
        "literature_poetry": enhanced_content_data.get('literature_poetry', {}),
        "lifestyle_health": enhanced_content_data.get('lifestyle_health', {}),
        "travel_tourism": enhanced_content_data.get('travel_tourism', {}),
    }
