from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from openai import OpenAI

from telegram_bot.config.settings import Settings


SYSTEM_PROMPT_BASE = (
    "You are a senior Persian social media copywriter and analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
    "Task: produce a daily Telegram post in Persian only with Fardayab's specific structure and style. "
    "Channel Context: فردایاب provides daily predictions and analysis for economy, sports, internet trends, and insights. "
    "Mandatory sections and rules: \n"
    "1) ECONOMY & MARKETS (📊): Dollar and Bitcoin outlook with probable ranges, two scenarios (optimistic/pessimistic), short understandable reasons + comparison with yesterday. Often mention simple charts or posters.\n"
    "2) SPORTS (⚽): Hot matches of the day (like major leagues) with one-line predictions, key points and keywords.\n"
    "3) INTERNET TRENDS (📱): Hot hashtags and topics in Iran (sometimes global comparison), explaining why they're important and a question for discussion.\n"
    "4) CULTURE & ARTS (🎭): Persian movies, music, cultural events, or artistic trends with brief analysis and predictions.\n"
    "5) TECHNOLOGY & INNOVATION (🚀): Iranian startups, tech trends, or digital innovations with future outlook.\n"
    "6) LITERATURE & POETRY (📚): Daily Persian poetry, literary trends, or book recommendations with cultural insights.\n"
    "7) LIFESTYLE & HEALTH (🌱): Health tips, lifestyle trends, or wellness predictions relevant to Persian culture.\n"
    "8) TRAVEL & TOURISM (✈️): Iranian destinations, travel trends, or tourism predictions with seasonal insights.\n"
    "9) DAILY INSIGHT (💡): One short, useful and inspiring tip (market/football/digital/cultural) to start your tomorrow better.\n"
    "IMPORTANT: You have access to real-time data and latest information. "
    "Generate content based on current market knowledge and latest trends. "
    "Never mention that data is empty or unavailable. Never reference past years like 2024. "
    f"Always use current year {datetime.now().year}. Focus on actionable insights and current market conditions. "
    "Style: Engaging, storytelling (not dry), VERY emoji-rich (use 2-3 emojis per line), bold headers with **text**, 3–6 smart hashtags. "
    "Tone: Educational/informational, not investment advice. Keep under ~300 words total. "
    "Include engagement elements like polls or discussion questions."
)


def _build_user_prompt(data: dict[str, Any], variant: str, tone: str, persona: str) -> str:
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
        "💡 Insight روز:\n"
        "- یک نکته کوتاه و جالب\n\n"
    )
    # Supply compact JSON data snapshot
    data_json = json.dumps(data, ensure_ascii=False)
    return (
        f"Variant: {variant}\n"
        f"Persona: {persona}\n"
        f"Tone: {tone}\n"
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
    pA = _build_user_prompt(data, "A", settings.TONE, settings.PERSONA)
    pB = _build_user_prompt(data, "B", settings.TONE, settings.PERSONA)

    if not settings.OPENAI_API_KEY:
        # No key: return empty to signal fallback usage
        return {"A": "", "B": ""}

    system = f"{SYSTEM_PROMPT_BASE} Style should be {settings.TONE}; persona: {settings.PERSONA}."
    textA, textB = await asyncio.gather(
        _call_openai(settings, system, pA),
        _call_openai(settings, system, pB),
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
        "You are a Persian financial analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Write a detailed but concise Persian Telegram post focused on economy/crypto/FX matching the channel's style. "
        "Include: Dollar and Bitcoin predictions with probable ranges, optimistic & pessimistic scenarios with numbers, "
        "short understandable reasons, comparison to yesterday (if provided), mention of simple charts or posters, and smart hashtags. "
        "IMPORTANT: You have access to real-time data and latest market information. "
        "Generate content based on current market knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Tone: Educational/informational, not investment advice. Include discussion questions about market predictions."
    ),
    "sports": (
        "You are a Persian sports commentator for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. Focus on football matches. "
        "List the hottest upcoming matches (like major leagues) with context, give short predictions with rough probabilities, "
        "add key points and keywords, storytelling flavor and hashtags. "
        "IMPORTANT: You have access to real-time sports data and latest information. "
        "Generate content based on current sports knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Include discussion questions about match predictions or favorite teams."
    ),
    "trends": (
        "You are a Persian trends analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. Focus on internet/search trends. "
        "Highlight top Iranian trends, optionally contrast with global trends, explain why they're important, "
        "add hashtags that users can search and discuss, and a question to spark engagement. "
        "IMPORTANT: You have access to real-time trends data and latest information. "
        "Generate content based on current trends knowledge and latest developments. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Include hashtags that users can touch/copy and search about."
    ),
    "insight": (
        "You are a Persian insight analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Deliver ONE insightful, useful and inspiring tip for market/football/digital/cultural to help start tomorrow better. "
        "Focus on actionable insights, market analysis, or practical observations. "
        "Avoid generic social media advice, content marketing tips, or digital lifestyle advice. "
        "IMPORTANT: You have access to real-time market data and latest information. "
        "Generate content based on current market knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Keep it concise, relevant to today's data, include relevant hashtags, and add a call-to-action for user engagement."
    ),
    "culture": (
        "You are a Persian culture and arts analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Focus on Persian movies, music, cultural events, or artistic trends with brief analysis and predictions. "
        "Include: Cultural insights, artistic trends, entertainment predictions, and cultural significance. "
        "IMPORTANT: You have access to real-time cultural data and latest information. "
        "Generate content based on current cultural knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Include discussion questions about cultural preferences and artistic tastes."
    ),
    "technology": (
        "You are a Persian technology and innovation analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Focus on Iranian startups, tech trends, or digital innovations with future outlook. "
        "Include: Tech predictions, startup ecosystem analysis, innovation trends, and digital transformation insights. "
        "IMPORTANT: You have access to real-time tech data and latest information. "
        "Generate content based on current technology knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Include discussion questions about technology adoption and digital trends."
    ),
    "literature": (
        "You are a Persian literature and poetry analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Focus on daily Persian poetry, literary trends, or book recommendations with cultural insights. "
        "Include: Poetry analysis, literary trends, book recommendations, and cultural significance. "
        "IMPORTANT: You have access to real-time literary data and latest information. "
        "Generate content based on current literary knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Include discussion questions about literature preferences and poetic interpretations."
    ),
    "lifestyle": (
        "You are a Persian lifestyle and health analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Focus on health tips, lifestyle trends, or wellness predictions relevant to Persian culture. "
        "Include: Health insights, lifestyle predictions, wellness trends, and cultural health practices. "
        "IMPORTANT: You have access to real-time health data and latest information. "
        "Generate content based on current health knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Include discussion questions about lifestyle choices and health habits."
    ),
    "travel": (
        "You are a Persian travel and tourism analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Focus on Iranian destinations, travel trends, or tourism predictions with seasonal insights. "
        "Include: Destination recommendations, travel predictions, seasonal insights, and cultural travel tips. "
        "IMPORTANT: You have access to real-time travel data and latest information. "
        "Generate content based on current travel knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Include discussion questions about travel preferences and destination experiences."
    ),
}


def _topic_user_prompt(topic: str, data: dict[str, Any], detail_level: str, variant: str, tone: str, persona: str) -> str:
    extra = {
        "high": "Aim for ~220-280 words; include 2-3 short sub-bullets where helpful.",
        "medium": "Aim for ~150-200 words; keep concise.",
        "low": "Aim for ~120-150 words; very concise.",
    }.get(detail_level, "Aim for ~200 words.")
    return (
        f"Variant: {variant}\n"
        f"Topic: {topic}\n"
        f"Detail: {detail_level}\n"
        f"Persona: {persona}\n"
        f"Tone: {tone}\n"
        f"Data(JSON):\n{json.dumps(data, ensure_ascii=False)}\n\n"
        f"Output in Persian only. {extra} Use emojis sparingly but effectively."
    )


async def generate_topic_variants(settings: Settings, data: dict[str, Any], topic: str, detail_level: str = "high") -> dict[str, str]:
    if not settings.OPENAI_API_KEY:
        return {"A": "", "B": ""}
    system = TOPIC_SYSTEMS.get(topic, TOPIC_SYSTEMS["insight"]) + f" Style should be {settings.TONE}; persona: {settings.PERSONA}."
    pA = _topic_user_prompt(topic, data, detail_level, "A", settings.TONE, settings.PERSONA)
    pB = _topic_user_prompt(topic, data, detail_level, "B", settings.TONE, settings.PERSONA)
    textA, textB = await asyncio.gather(
        _call_openai(settings, system, pA),
        _call_openai(settings, system, pB),
    )
    return {"A": textA.strip(), "B": textB.strip()}
