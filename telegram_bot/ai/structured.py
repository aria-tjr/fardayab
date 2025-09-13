from __future__ import annotations

import asyncio
import json
from typing import Any

from openai import OpenAI

from telegram_bot.config.settings import Settings
from telegram_bot.ai.schema import combined_schema, topic_schema


async def _responses_schema(client: OpenAI, model: str, system: str, prompt: str, schema: dict) -> dict | None:
    def _run() -> dict | None:
        try:
            resp = client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": [{"type": "input_text", "text": system}]},
                    {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
                ],
                response_format={"type": "json_schema", "json_schema": schema},
            )
            txt = resp.output_text
            return json.loads(txt)
        except Exception:
            return None
    return await asyncio.to_thread(_run)


async def generate_combined_structured(settings: Settings, data: dict[str, Any]) -> dict | None:
    if not (settings.OPENAI_API_KEY and settings.STRUCTURED_GENERATION):
        return None
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    system = (
        "Produce a Persian-only structured daily post covering economy, sports, trends, and an insight using GPT-5-mini-2025-08-07. "
        f"Style should be {settings.TONE}; persona: {settings.PERSONA}. "
        "IMPORTANT: You have access to real-time data and latest information. "
        "Generate content based on current knowledge and latest trends. "
        "Never mention that data is empty or unavailable. Never reference past years like 2024. "
        "Always use current year 2025. Focus on actionable insights and current conditions."
    )
    prompt = json.dumps({"data": data}, ensure_ascii=False)
    return await _responses_schema(client, settings.OPENAI_MODEL, system, prompt, combined_schema())


async def generate_topic_structured(settings: Settings, data: dict[str, Any], topic: str) -> dict | None:
    if not (settings.OPENAI_API_KEY and settings.STRUCTURED_GENERATION):
        return None
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    system = f"Produce a Persian-only structured post body and hashtags for topic: {topic} using GPT-5-mini-2025-08-07. Style should be {settings.TONE}; persona: {settings.PERSONA}. IMPORTANT: You have access to real-time data and latest information. Generate content based on current knowledge and latest trends. Never mention that data is empty or unavailable. Never reference past years like 2024. Always use current year 2025."
    prompt = json.dumps({"topic": topic, "data": data}, ensure_ascii=False)
    return await _responses_schema(client, settings.OPENAI_MODEL, system, prompt, topic_schema(topic))
