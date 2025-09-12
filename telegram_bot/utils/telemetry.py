from __future__ import annotations

from dataclasses import dataclass

from telegram_bot.data.db import Database


async def record_poll_message(db: Database, poll_id: str, message_id: int, topic: str, variant: str, ts: int) -> None:
    await db.conn.execute(
        """
        CREATE TABLE IF NOT EXISTS polls (
            poll_id TEXT PRIMARY KEY,
            message_id INTEGER,
            topic TEXT,
            variant TEXT,
            ts INTEGER
        );
        """
    )
    await db.conn.execute(
        """
        CREATE TABLE IF NOT EXISTS poll_votes (
            poll_id TEXT,
            option_index INTEGER,
            votes INTEGER,
            PRIMARY KEY(poll_id, option_index)
        );
        """
    )
    await db.conn.execute(
        "INSERT OR REPLACE INTO polls(poll_id, message_id, topic, variant, ts) VALUES (?,?,?,?,?)",
        (poll_id, message_id, topic, variant, ts),
    )
    await db.conn.commit()


async def add_poll_vote(db: Database, poll_id: str, option_index: int, delta: int = 1) -> None:
    await db.conn.execute(
        "INSERT INTO poll_votes(poll_id, option_index, votes) VALUES (?,?,?) ON CONFLICT(poll_id, option_index) DO UPDATE SET votes = votes + excluded.votes",
        (poll_id, option_index, delta),
    )
    await db.conn.commit()


async def topic_variant_stats(db: Database, topic: str) -> dict[str, int]:
    # Sum votes over last 14 days for polls of given topic
    import time
    cutoff = int(time.time()) - 14 * 86400
    out = {"A": 0, "B": 0}
    async with db.conn.execute(
        """
        SELECT p.variant, COALESCE(SUM(v.votes), 0)
        FROM polls p
        JOIN poll_votes v USING(poll_id)
        WHERE p.topic = ? AND p.ts >= ?
        GROUP BY p.variant
        """,
        (topic, cutoff),
    ) as cur:
        async for row in cur:
            out[str(row[0])] = int(row[1] or 0)
    return out


async def top_hours_by_votes(db: Database, k: int = 3, days: int = 14, tz: str = "Asia/Tehran") -> list[str]:
    """Return top k hours-of-day (HH:00) by total poll votes in last N days.
    Uses poll creation timestamps as proxy for post time.
    """
    import time
    from zoneinfo import ZoneInfo
    cutoff = int(time.time()) - days * 86400
    # gather (ts, votes)
    rows: list[tuple[int, int]] = []
    async with db.conn.execute(
        """
        SELECT p.ts, COALESCE(SUM(v.votes), 0) as votes
        FROM polls p
        LEFT JOIN poll_votes v USING(poll_id)
        WHERE p.ts >= ?
        GROUP BY p.poll_id
        """,
        (cutoff,),
    ) as cur:
        async for ts, votes in cur:
            rows.append((int(ts), int(votes or 0)))
    if not rows:
        return []
    # bucket by hour-of-day in local tz
    from datetime import datetime
    buckets: dict[int, int] = {}
    z = ZoneInfo(tz)
    for ts, v in rows:
        hh = datetime.fromtimestamp(ts, tz=z).hour
        buckets[hh] = buckets.get(hh, 0) + max(0, v)
    if not buckets:
        return []
    top = sorted(buckets.items(), key=lambda x: (-x[1], x[0]))[: max(1, k)]
    return [f"{h:02d}:00" for h, _ in top]
