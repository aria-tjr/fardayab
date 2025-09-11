from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None) -> Any:
    r = await client.get(url, params=params, timeout=client.timeout)
    r.raise_for_status()
    return r.json()


async def fetch_weather(openweather_key: str, cities: list[str], lang: str = "fa", timeout: float = 15.0) -> list[dict]:
    if not openweather_key or not cities:
        return []
    out: list[dict] = []
    async with httpx.AsyncClient(timeout=timeout) as client:
        for c in cities:
            try:
                data = await _get_json(
                    client,
                    "https://api.openweathermap.org/data/2.5/weather",
                    {"q": c, "appid": openweather_key, "units": "metric", "lang": lang},
                )
                desc = ((data.get("weather") or [{}])[0]).get("description")
                temp = (data.get("main") or {}).get("temp")
                out.append({"city": c, "desc": desc, "temp": temp})
            except Exception:
                out.append({"city": c, "desc": None, "temp": None})
    return out

