from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
    r = await client.get(url, params=params, headers=headers, timeout=client.timeout)
    r.raise_for_status()
    return r.json()


async def fetch_top_headlines(api_key: str, language: str = "fa", timeout: float = 15.0) -> list[dict]:
    if not api_key:
        return []
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            data = await _get_json(
                client,
                "https://newsapi.org/v2/top-headlines",
                params={"language": language, "pageSize": 10},
                headers={"X-Api-Key": api_key},
            )
        except Exception:
            return []

    articles = data.get("articles", [])
    items: list[dict] = []
    for a in articles:
        items.append({
            "title": a.get("title"),
            "desc": a.get("description"),
            "url": a.get("url"),
            "source": (a.get("source") or {}).get("name"),
        })
    return items

