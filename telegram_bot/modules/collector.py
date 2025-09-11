from __future__ import annotations

import asyncio
from typing import Any

from telegram_bot.config.settings import Settings
from telegram_bot.modules.crypto import fetch_crypto_and_fx
from telegram_bot.modules.news import fetch_top_headlines
from telegram_bot.modules.trends import fetch_trending
from telegram_bot.modules.weather import fetch_weather
from telegram_bot.modules.sports import fetch_next_events_thesportsdb


async def collect_all(settings: Settings) -> dict[str, Any]:
    # Run collectors concurrently where possible
    crypto_task = asyncio.create_task(fetch_crypto_and_fx(settings.HTTP_TIMEOUT))
    news_task = asyncio.create_task(fetch_top_headlines(settings.NEWSAPI_KEY, settings.NEWS_LANGUAGE, settings.HTTP_TIMEOUT))
    trends_task = asyncio.create_task(fetch_trending("iran", limit=10))
    trends_cmp_task = asyncio.create_task(fetch_trending(settings.TRENDS_COMPARE_REGION, limit=10))
    weather_task = asyncio.create_task(fetch_weather(settings.OPENWEATHER_KEY, settings.cities(), lang="fa", timeout=settings.HTTP_TIMEOUT))
    sports_task = asyncio.create_task(fetch_next_events_thesportsdb(settings.THESPORTSDB_KEY, settings.leagues(), timeout=settings.HTTP_TIMEOUT))

    crypto = await crypto_task
    news = await news_task
    trends = await trends_task
    trends_cmp = await trends_cmp_task
    weather = await weather_task
    sports = await sports_task

    return {
        "crypto": crypto,
        "news": news,
        "trends": trends,
        "trends_compare": {"region": settings.TRENDS_COMPARE_REGION, "values": trends_cmp},
        "weather": weather,
        "sports": sports,
    }
