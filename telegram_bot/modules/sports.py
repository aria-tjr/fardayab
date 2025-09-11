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

