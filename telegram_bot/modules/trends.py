from __future__ import annotations

import asyncio
from typing import Any

from pytrends.request import TrendReq


def _blocking_trending(pn: str = "iran", limit: int = 10) -> list[str]:
    try:
        tr = TrendReq(hl='fa-IR', tz=210)  # Tehran offset ~ 3.5h (210 min)
        df = tr.trending_searches(pn=pn)
        if df is None:
            return []
        vals = [str(v).strip() for v in list(df[0].values)[:limit]]
        return [v for v in vals if v]
    except Exception:
        return []


async def fetch_trending(region: str = "iran", limit: int = 10) -> list[str]:
    # run the blocking call in a thread
    return await asyncio.to_thread(_blocking_trending, pn=region, limit=limit)

