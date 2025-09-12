from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None) -> Any:
    r = await client.get(url, params=params, timeout=client.timeout)
    r.raise_for_status()
    return r.json()


async def fetch_next_events_thesportsdb(api_key: str, league_ids: list[str], timeout: float = 15.0) -> list[dict]:
    if not league_ids:
        return []
    out: list[dict] = []
    async with httpx.AsyncClient(timeout=timeout) as client:
        for lid in league_ids:
            try:
                url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/eventsnextleague.php"
                data = await _get_json(client, url, {"id": lid})
                events = data.get("events") or []
                for ev in events:
                    home = ev.get("strHomeTeam")
                    away = ev.get("strAwayTeam")
                    dt = ev.get("dateEvent")
                    tm = ev.get("strTime")
                    out.append({
                        "home": home,
                        "away": away,
                        "date": dt,
                        "time": tm,
                        # naive adornment, prediction could be AI-enhanced later
                        "prediction": None,
                    })
            except Exception:
                continue
    # de-dup roughly by pair/date
    dedup: dict[tuple, dict] = {}
    for m in out:
        key = (m.get("home"), m.get("away"), m.get("date"))
        dedup[key] = m
    return list(dedup.values())


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
    r = await client.get(url, params=params, headers=headers, timeout=client.timeout)
    r.raise_for_status()
    return r.json()


async def fetch_fixtures_apisports(api_key: str, league_ids: list[str], date_iso: str, season: int | None = None, timeout: float = 15.0) -> list[dict]:
    if not api_key or not league_ids:
        return []
    headers = {"x-apisports-key": api_key}
    out: list[dict] = []
    async with httpx.AsyncClient(timeout=timeout) as client:
        for lid in league_ids:
            try:
                data = await _get_json(
                    client,
                    "https://v3.football.api-sports.io/fixtures",
                    params={"league": lid, "date": date_iso, **({"season": season} if season else {})},
                    headers=headers,
                )
                for r in (data.get("response") or []):
                    teams = r.get("teams") or {}
                    home = (teams.get("home") or {}).get("name")
                    away = (teams.get("away") or {}).get("name")
                    tm = (r.get("fixture") or {}).get("date")
                    out.append({
                        "home": home,
                        "away": away,
                        "time": tm,
                        "prediction": None,
                    })
            except Exception:
                continue
    return out


async def fetch_sports(settings) -> list[dict]:
    from telegram_bot.utils.timeutils import now_tz
    tz = settings.TIMEZONE
    day = now_tz(tz).date().isoformat()
    # Prefer API-Sports if key
    if settings.API_SPORTS_KEY:
        items = await fetch_fixtures_apisports(settings.API_SPORTS_KEY, settings.leagues_api_sports(), day, timeout=settings.HTTP_TIMEOUT)
        if items:
            return items
    # Fallback to TheSportsDB
    return await fetch_next_events_thesportsdb(settings.THESPORTSDB_KEY, settings.leagues(), timeout=settings.HTTP_TIMEOUT)
