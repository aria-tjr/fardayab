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
    out = {"A": 0, "B": 0}
    async with db.conn.execute(
        "SELECT p.variant, SUM(v.votes) FROM polls p JOIN poll_votes v USING(poll_id) WHERE p.topic=? GROUP BY p.variant",
        (topic,),
    ) as cur:
        async for row in cur:
            out[str(row[0])] = int(row[1] or 0)
    return out

