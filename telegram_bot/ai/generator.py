from __future__ import annotations

import asyncio
import json
from typing import Any

from openai import OpenAI

from telegram_bot.config.settings import Settings


SYSTEM_PROMPT = (
    "You are a senior Persian social media copywriter and analyst. "
    "Task: produce a daily Telegram post in Persian only with a fixed structure and rich content. "
    "Mandatory sections and rules: \n"
    "1) ECONOMY (📊): Include predictions (with short, clear reasons), plus two scenarios (optimistic, pessimistic). Compare with yesterday when available.\n"
    "2) SPORTS (⚽): List hot matches and add a one-line prediction per match.\n"
    "3) INTERNET TRENDS (📱): Show likely trending tags. Optionally compare with another region.\n"
    "4) WEATHER (🌦️): City - brief description - temperature.\n"
    "5) INSIGHT OF THE DAY (💡): One short, surprising or useful fact.\n"
    "Style: engaging, storytelling (not dry), emoji-rich, 3–6 smart hashtags. Keep under ~250 words total."
)


def _build_user_prompt(data: dict[str, Any], variant: str) -> str:
    templ = (
        "Template (Persian only):\n"
        "📊 اقتصاد:\n"
        "- پیش‌بینی + علت کوتاه\n"
        "- سناریو خوش‌بینانه و بدبینانه با اعداد\n"
        "- مقایسه با دیروز (اگر موجود)\n\n"
        "⚽ ورزش:\n"
        "- چند بازی داغ + پیش‌بینی یک‌خطی\n\n"
        "📱 ترند اینترنت:\n"
        "- چند هشتگ احتمالی + قیاس کوتاه با منطقه دیگر (اگر موجود)\n\n"
        "🌦️ آب‌وهوا:\n"
        "- شهر — توصیف — دما\n\n"
        "💡 Insight روز:\n"
        "- یک نکته کوتاه و جالب\n\n"
    )
    # Supply compact JSON data snapshot
    data_json = json.dumps(data, ensure_ascii=False)
    return (
        f"Variant: {variant}\n"
        f"Data (JSON):\n{data_json}\n\n"
        f"{templ}"
        "Guidelines: include reasons, scenarios, yesterday comparison if provided, storytelling tone; 3-6 hashtags; readable numbers; Persian only."
    )


async def _call_openai(settings: Settings, system_prompt: str, user_prompt: str) -> str:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def _run() -> str:
        resp = client.responses.create(
            model=settings.OPENAI_MODEL,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
            ],
        )
        return resp.output_text

    return await asyncio.to_thread(_run)


async def generate_post_variants(settings: Settings, data: dict[str, Any]) -> dict[str, str]:
    # Build two variants for A/B
    pA = _build_user_prompt(data, "A")
    pB = _build_user_prompt(data, "B")

    if not settings.OPENAI_API_KEY:
        # No key: return empty to signal fallback usage
        return {"A": "", "B": ""}

    textA, textB = await asyncio.gather(
        _call_openai(settings, SYSTEM_PROMPT, pA),
        _call_openai(settings, SYSTEM_PROMPT, pB),
    )
    return {"A": textA.strip(), "B": textB.strip()}


async def generate_admin_suggestions(settings: Settings, data: dict[str, Any]) -> str:
    if not settings.OPENAI_API_KEY:
        return "پیشنهادات در دسترس نیست (OpenAI API KEY تنظیم نشده است)."

    prompt = (
        "Given today's aggregated data and channel focus, propose:\n"
        "1) 2-3 best posting times in the next 24h (timezone-aware).\n"
        "2) 3 brief growth tips (cross-promo, partnerships, content hooks).\n"
        "Keep it concise in Persian."
        f"\nData: {json.dumps(data, ensure_ascii=False)}"
    )
    return await _call_openai(settings, "You are a helpful strategist.", prompt)


# --- Topic-specific generation ---

TOPIC_SYSTEMS = {
    "economy": (
        "You are a senior Persian market analyst and copywriter. "
        "Write a detailed but concise Persian Telegram post focused ONLY on economy/crypto/FX. "
        "Include: predictions with short reasons, optimistic & pessimistic scenarios with numbers, "
        "comparison to yesterday (if provided), and smart hashtags. Keep engaging tone with emojis."
    ),
    "sports": (
        "You are a senior Persian sports commentator. Focus ONLY on football matches. "
        "List the hottest upcoming matches with context (form, key injuries if present in data), "
        "give short predictions with rough probabilities, add storytelling flavor and hashtags."
    ),
    "trends": (
        "You are a Persian trends analyst and copywriter. Focus ONLY on internet/search trends. "
        "Highlight top Iranian trends, optionally contrast with compare-region trends, explain why they matter, "
        "add 5-8 smart hashtags and a question to spark discussion."
    ),
    "weather": (
        "You are a Persian weather explainer. Focus ONLY on weather for the selected cities. "
        "Provide brief forecasts, temperature ranges, alerts if any (based on data), and a friendly tip."
    ),
    "insight": (
        "You are a Persian educator/copywriter. Deliver ONE insightful, timely tip related to markets, sports culture, or digital life, "
        "grounded in today's data if possible, with a short actionable takeaway and hashtags."
    ),
}


def _topic_user_prompt(topic: str, data: dict[str, Any], detail_level: str, variant: str) -> str:
    extra = {
        "high": "Aim for ~220-280 words; include 2-3 short sub-bullets where helpful.",
        "medium": "Aim for ~150-200 words; keep concise.",
        "low": "Aim for ~120-150 words; very concise.",
    }.get(detail_level, "Aim for ~200 words.")
    return (
        f"Variant: {variant}\n"
        f"Topic: {topic}\n"
        f"Detail: {detail_level}\n"
        f"Data(JSON):\n{json.dumps(data, ensure_ascii=False)}\n\n"
        f"Output in Persian only. {extra} Use emojis sparingly but effectively."
    )


async def generate_topic_variants(settings: Settings, data: dict[str, Any], topic: str, detail_level: str = "high") -> dict[str, str]:
    if not settings.OPENAI_API_KEY:
        return {"A": "", "B": ""}
    system = TOPIC_SYSTEMS.get(topic, TOPIC_SYSTEMS["insight"])
    pA = _topic_user_prompt(topic, data, detail_level, "A")
    pB = _topic_user_prompt(topic, data, detail_level, "B")
    textA, textB = await asyncio.gather(
        _call_openai(settings, system, pA),
        _call_openai(settings, system, pB),
    )
    return {"A": textA.strip(), "B": textB.strip()}
