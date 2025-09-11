from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo


def parse_hhmm(s: str) -> time:
    hh, mm = s.strip().split(":")
    return time(hour=int(hh), minute=int(mm))


def now_tz(tz: str) -> datetime:
    return datetime.now(ZoneInfo(tz))
