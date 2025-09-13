from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from openai import OpenAI

from telegram_bot.config.settings import Settings
from telegram_bot.utils.json_encoder import safe_json_dumps


SYSTEM_PROMPT_BASE = (
    "You are a senior Persian cryptocurrency and forex analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
    "Task: produce a daily Telegram post in Persian only with Fardayab's specific structure and style. "
    "Channel Context: فردایاب provides daily predictions and analysis exclusively for cryptocurrency and forex markets. "
    "Mandatory sections and rules: \n"
    "1) CRYPTOCURRENCY MARKETS (₿): Bitcoin, Ethereum, and major altcoins outlook with probable ranges, two scenarios (optimistic/pessimistic), short understandable reasons + comparison with yesterday. Include market cap, volume, and technical analysis.\n"
    "2) FOREX MARKETS (💱): Major currency pairs (USD/IRR, EUR/USD, GBP/USD, etc.) with price predictions, economic factors, and central bank policies affecting rates.\n"
    "3) DEFI & BLOCKCHAIN (🔗): DeFi protocols, yield farming opportunities, staking rewards, and blockchain innovations with market impact analysis.\n"
    "4) TRADING INSIGHTS (📈): Technical analysis patterns, support/resistance levels, trading volume analysis, and market sentiment indicators.\n"
    "5) REGULATORY NEWS (⚖️): Cryptocurrency regulations, government policies, central bank digital currencies (CBDC), and compliance updates.\n"
    "6) MARKET SENTIMENT (📊): Fear & Greed Index, social media sentiment, institutional adoption, and whale movements.\n"
    "7) ECONOMIC INDICATORS (📉): Inflation rates, interest rates, GDP growth, and their impact on crypto and forex markets.\n"
    "8) DAILY TRADING TIP (💡): One practical trading or investment insight to help users make better decisions.\n"
    "IMPORTANT: You have access to real-time market data and latest information. "
    "Generate content based on current market knowledge and latest trends. "
    "Never mention that data is empty or unavailable. Never reference past years like 2024. "
    f"Always use current year {datetime.now().year}. Focus on actionable insights and current market conditions. "
    "Style: Engaging, storytelling (not dry), VERY emoji-rich (use 2-3 emojis per line), bold headers with **text**, 3–6 smart hashtags. "
    "Tone: Educational/informational, not investment advice. Keep under ~300 words total. "
    "Include engagement elements like polls or discussion questions about market predictions."
)


def _build_user_prompt(data: dict[str, Any], variant: str, tone: str, persona: str) -> str:
    templ = (
        "Template (Persian only):\n"
        "₿ بازار کریپتو:\n"
        "- پیش‌بینی بیت‌کوین و اتریوم + علت کوتاه\n"
        "- سناریو خوش‌بینانه و بدبینانه با اعداد\n"
        "- مقایسه با دیروز (اگر موجود)\n\n"
        "💱 بازار فارکس:\n"
        "- جفت ارزهای اصلی + پیش‌بینی نرخ\n"
        "- عوامل اقتصادی موثر\n\n"
        "🔗 دیفای و بلاک‌چین:\n"
        "- پروتکل‌های جدید + فرصت‌های استیکینگ\n"
        "- نوآوری‌های بلاک‌چین\n\n"
        "💡 نکته معاملاتی روز:\n"
        "- یک نکته عملی برای معامله‌گران\n\n"
    )
    # Supply compact JSON data snapshot
    data_json = safe_json_dumps(data)
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
        f"\nData: {safe_json_dumps(data)}"
    )
    return await _call_openai(settings, "You are a helpful strategist.", prompt)


# --- Topic-specific generation ---

TOPIC_SYSTEMS = {
    "crypto": (
        "You are a Persian cryptocurrency analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Write a detailed but concise Persian Telegram post focused on cryptocurrency markets matching the channel's style. "
        "Include: Bitcoin, Ethereum, and major altcoins predictions with probable ranges, optimistic & pessimistic scenarios with numbers, "
        "short understandable reasons, comparison to yesterday (if provided), market cap, volume analysis, and smart hashtags. "
        "IMPORTANT: You have access to real-time crypto data and latest market information. "
        "Generate content based on current market knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Tone: Educational/informational, not investment advice. Include discussion questions about crypto predictions."
    ),
    "forex": (
        "You are a Persian forex analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. Focus on major currency pairs. "
        "Analyze USD/IRR, EUR/USD, GBP/USD, and other major pairs with price predictions, economic factors, "
        "central bank policies, and market sentiment. Include technical analysis and fundamental factors. "
        "IMPORTANT: You have access to real-time forex data and latest information. "
        "Generate content based on current market knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Include discussion questions about forex predictions and currency movements."
    ),
    "defi": (
        "You are a Persian DeFi and blockchain analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Focus on DeFi protocols, yield farming opportunities, staking rewards, and blockchain innovations. "
        "Include: Protocol analysis, APY comparisons, risk assessments, and market impact of new developments. "
        "IMPORTANT: You have access to real-time DeFi data and latest information. "
        "Generate content based on current DeFi knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Include discussion questions about DeFi strategies and protocol preferences."
    ),
    "trading": (
        "You are a Persian trading analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Focus on technical analysis, trading patterns, support/resistance levels, and market sentiment indicators. "
        "Include: Chart patterns, volume analysis, trading signals, and risk management tips. "
        "IMPORTANT: You have access to real-time trading data and latest information. "
        "Generate content based on current market knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Include discussion questions about trading strategies and market analysis."
    ),
    "regulatory": (
        "You are a Persian regulatory analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Focus on cryptocurrency regulations, government policies, central bank digital currencies (CBDC), and compliance updates. "
        "Include: Regulatory impact analysis, policy changes, compliance requirements, and market implications. "
        "IMPORTANT: You have access to real-time regulatory data and latest information. "
        "Generate content based on current regulatory knowledge and latest developments. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Include discussion questions about regulatory impacts and policy preferences."
    ),
    "sentiment": (
        "You are a Persian market sentiment analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Focus on Fear & Greed Index, social media sentiment, institutional adoption, and whale movements. "
        "Include: Sentiment indicators, social media trends, institutional flows, and market psychology analysis. "
        "IMPORTANT: You have access to real-time sentiment data and latest information. "
        "Generate content based on current market sentiment and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Include discussion questions about market sentiment and investor behavior."
    ),
    "economic": (
        "You are a Persian economic analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Focus on inflation rates, interest rates, GDP growth, and their impact on crypto and forex markets. "
        "Include: Economic indicators analysis, central bank policies, macroeconomic trends, and market correlations. "
        "IMPORTANT: You have access to real-time economic data and latest information. "
        "Generate content based on current economic knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Include discussion questions about economic impacts and market correlations."
    ),
    "insight": (
        "You are a Persian trading insight analyst for 'فردایاب' (Fardayab) channel using GPT-5-mini-2025-08-07. "
        "Deliver ONE insightful, useful and inspiring tip for crypto/forex trading to help users make better decisions. "
        "Focus on actionable trading insights, market analysis, or practical observations. "
        "Avoid generic social media advice, content marketing tips, or digital lifestyle advice. "
        "IMPORTANT: You have access to real-time market data and latest information. "
        "Generate content based on current market knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        f"Always use current year {datetime.now().year}. Use LOTS of emojis (2-3 per line), bold headers with **text**, and engaging tone. "
        "Keep it concise, relevant to today's data, include relevant hashtags, and add a call-to-action for user engagement."
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
        f"Data(JSON):\n{safe_json_dumps(data)}\n\n"
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
