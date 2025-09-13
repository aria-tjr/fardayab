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


async def _retry_api_call(api_func, max_retries: int = 3, delay: float = 2.0):
    """Retry API call with exponential backoff"""
    import asyncio
    import logging
    
    log = logging.getLogger(__name__)
    
    for attempt in range(max_retries):
        try:
            result = await api_func()
            if result:
                return result
        except Exception as e:
            log.warning(f"API call attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                log.error(f"All {max_retries} API attempts failed")
    
    return None

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
    crypto_task = asyncio.create_task(_collect_with_retry(lambda: fetch_crypto_and_fx(settings)))
    news_task = asyncio.create_task(_collect_with_retry(
        lambda: fetch_combined_news(
            settings.NEWSAPI_KEY,
            settings.NEWSDATA_KEY,
            settings.MEDIASTACK_KEY,
            settings.NEWS_LANGUAGE,
            settings.HTTP_TIMEOUT,
        )
    ))
    trends_task = asyncio.create_task(_collect_with_retry(lambda: fetch_trending("iran", 10)))
    trends_cmp_task = asyncio.create_task(_collect_with_retry(lambda: fetch_trending(settings.TRENDS_COMPARE_REGION, 10)))
    sports_task = asyncio.create_task(_collect_with_retry(lambda: fetch_sports(settings)))
    
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

    # Retry failed APIs with exponential backoff
    if not crypto:
        log.info("Retrying crypto API with backoff...")
        crypto = await _retry_api_call(lambda: fetch_crypto_and_fx(settings))
    
    if not news:
        log.info("Retrying news API with backoff...")
        news = await _retry_api_call(lambda: fetch_combined_news(
            settings.NEWSAPI_KEY, 
            settings.NEWSDATA_KEY, 
            settings.MEDIASTACK_KEY, 
            settings.NEWS_LANGUAGE, 
            settings.HTTP_TIMEOUT
        ))
    
    if not trends:
        log.info("Retrying trends API with backoff...")
        trends = await _retry_api_call(lambda: fetch_trending(settings))
    
    if not sports:
        log.info("Retrying sports API with backoff...")
        sports = await _retry_api_call(lambda: fetch_sports(settings))

    # If all APIs still fail after retries, raise an error instead of using fallback
    if not any([crypto, news, trends, sports, persian_data.get('enhanced', False)]):
        log.error("All APIs failed after retries - no data available")
        raise Exception("Unable to fetch real data from any API source")

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
        "trends_compare": {"region": settings.TRENDS_COMPARE_REGION, "values": trends_cmp or []},
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
