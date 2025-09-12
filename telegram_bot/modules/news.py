from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
    r = await client.get(url, params=params, headers=headers, timeout=client.timeout)
    r.raise_for_status()
    return r.json()


async def fetch_newsapi(api_key: str, language: str = "fa", timeout: float = 15.0) -> list[dict]:
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


async def fetch_newsdata(api_key: str, language: str = "fa", timeout: float = 15.0) -> list[dict]:
    if not api_key:
        return []
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            data = await _get_json(
                client,
                "https://newsdata.io/api/1/news",
                params={"apikey": api_key, "language": language, "country": "ir", "page": 1},
            )
        except Exception:
            return []
    results = data.get("results", [])
    out: list[dict] = []
    for a in results:
        out.append({
            "title": a.get("title"),
            "desc": a.get("description"),
            "url": a.get("link"),
            "source": a.get("source_id"),
        })
    return out


async def fetch_mediastack(api_key: str, language: str = "fa", timeout: float = 15.0) -> list[dict]:
    if not api_key:
        return []
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            data = await _get_json(
                client,
                "http://api.mediastack.com/v1/news",
                params={
                    "access_key": api_key,
                    "languages": language,
                    "countries": "ir",
                    "sort": "published_desc",
                    "limit": 50,
                },
            )
        except Exception:
            return []
    items = data.get("data", [])
    out: list[dict] = []
    for a in items:
        out.append({
            "title": a.get("title"),
            "desc": a.get("description"),
            "url": a.get("url"),
            "source": a.get("source"),
        })
    return out


def _dedup_news(items: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for it in items:
        t = (it.get("title") or "").strip().lower()
        key = "".join(ch for ch in t if ch.isalnum() or ch.isspace())
        if key and key not in seen:
            seen.add(key)
            out.append(it)
    return out[:30]


async def fetch_combined_news(newsapi_key: str, newsdata_key: str, mediastack_key: str, language: str = "fa", timeout: float = 15.0) -> list[dict]:
    # Run sources concurrently
    import asyncio
    tasks = []
    tasks.append(asyncio.create_task(fetch_newsapi(newsapi_key, language, timeout)))
    tasks.append(asyncio.create_task(fetch_newsdata(newsdata_key, language, timeout)))
    tasks.append(asyncio.create_task(fetch_mediastack(mediastack_key, language, timeout)))
    res = await asyncio.gather(*tasks, return_exceptions=True)
    items: list[dict] = []
    for r in res:
        if isinstance(r, list):
            items.extend(r)
    return _dedup_news(items)
