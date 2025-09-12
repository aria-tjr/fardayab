from __future__ import annotations

import asyncio
from typing import Any

from openai import OpenAI

from telegram_bot.config.settings import Settings


def build_image_prompt(topic: str, data: dict[str, Any]) -> str:
    base = "پوستر تمیز و مینیمال برای پست تلگرام، سبک انفورگرافیک با آیکون‌ها و تایپوگرافی فارسی."
    if topic == "economy":
        return base + " موضوع: بیت‌کوین و دلار امروز؛ نمودار ساده روند، رنگ‌های تیره با طلایی."
    if topic == "trends":
        return base + " موضوع: ترندهای داغ ایران؛ هشتگ‌ها با استایل کارت."
    if topic == "insight":
        return base + " موضوع: نکته روز در مورد بازار؛ لامپ ایده، زمینه روشن."
    if topic == "sports":
        return base + " موضوع: مسابقات فوتبال امروز؛ دو تیم با پس‌زمینه استادیوم."
    return base


async def generate_image_url(settings: Settings, topic: str, data: dict[str, Any]) -> str | None:
    if not settings.OPENAI_API_KEY:
        return None
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = build_image_prompt(topic, data)

    def _run() -> str | None:
        try:
            resp = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=getattr(settings, "IMAGE_SIZE", "1024x1024"),
            )
            url = resp.data[0].url
            return url
        except Exception:
            return None

    return await asyncio.to_thread(_run)
