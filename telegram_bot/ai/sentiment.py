from __future__ import annotations

import asyncio
import json
from typing import Any

from openai import OpenAI

from telegram_bot.config.settings import Settings


async def analyze_news_sentiment(settings: Settings, articles: list[dict]) -> dict:
    # Fallback naive
    if not settings.OPENAI_API_KEY or not articles:
        titles = [a.get("title") or "" for a in (articles or [])]
        # naive estimate: neutral when no AI
        return {"summary": "تحلیل احساسات در دسترس نیست.", "score": 0.0, "titles": titles[:5]}

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _run() -> dict:
        prompt = (
            "You will receive a list of news items (title+desc). "
            "Return a compact Persian summary of overall sentiment (bullish/bearish/neutral) and a score in [-1,1]. "
            "Also list 3-5 key topics as hashtags (English)." 
            f"\nData: {json.dumps(articles, ensure_ascii=False)}"
        )
        resp = client.responses.create(
            model=settings.OPENAI_MODEL,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": "You are a financial/news sentiment analyst."}]},
                {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
            ],
        )
        text = resp.output_text.strip()
        return {"summary": text, "score": 0.0}

    return await asyncio.to_thread(_run)
