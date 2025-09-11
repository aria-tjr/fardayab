from __future__ import annotations

import aiosqlite
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from telegram_bot.config.settings import Settings


@dataclass
class Database:
    settings: Settings
    _db: aiosqlite.Connection | None = None

    async def init(self) -> None:
        Path(self.settings.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self.settings.DB_PATH)
        await self._db.execute("PRAGMA journal_mode=WAL;")
        await self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                status TEXT NOT NULL,
                variant TEXT,
                channel_message_id INTEGER,
                error TEXT,
                topic TEXT,
                content_hash TEXT
            );

            CREATE TABLE IF NOT EXISTS settings (
                k TEXT PRIMARY KEY,
                v TEXT
            );

            CREATE TABLE IF NOT EXISTS snapshots (
                day TEXT PRIMARY KEY, -- YYYY-MM-DD in timezone used that day
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS locks (
                k TEXT PRIMARY KEY,
                expire INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS topic_map (
                time TEXT PRIMARY KEY, -- HH:MM
                topic TEXT NOT NULL
            );
            """
        )
        # Backfill columns if older schema exists
        for col in ("topic", "content_hash"):
            try:
                await self._db.execute(f"ALTER TABLE runs ADD COLUMN {col} TEXT")
            except Exception:
                pass
        await self._db.commit()

    @property
    def conn(self) -> aiosqlite.Connection:
        assert self._db is not None
        return self._db

    async def record_run(self, ts: int, status: str, variant: str | None, msg_id: int | None, error: str | None, *, topic: str | None = None, content_hash: str | None = None) -> None:
        await self.conn.execute(
            "INSERT INTO runs (ts, status, variant, channel_message_id, error, topic, content_hash) VALUES (?,?,?,?,?,?,?)",
            (ts, status, variant, msg_id, error, topic, content_hash),
        )
        await self.conn.commit()

    async def last_run(self) -> dict | None:
        async with self.conn.execute(
            "SELECT ts, status, variant, channel_message_id, error FROM runs ORDER BY id DESC LIMIT 1"
        ) as cur:
            row = await cur.fetchone()
            if row:
                return {
                    "ts": row[0],
                    "status": row[1],
                    "variant": row[2],
                    "channel_message_id": row[3],
                    "error": row[4],
                }
        return None

    async def first_run_ts(self) -> int | None:
        async with self.conn.execute(
            "SELECT ts FROM runs ORDER BY id ASC LIMIT 1"
        ) as cur:
            row = await cur.fetchone()
            return int(row[0]) if row else None

    async def get_setting(self, key: str, default: str | None = None) -> str | None:
        async with self.conn.execute("SELECT v FROM settings WHERE k=?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else default

    async def set_setting(self, key: str, value: str) -> None:
        await self.conn.execute(
            "INSERT INTO settings(k, v) VALUES (?, ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
            (key, value),
        )
        await self.conn.commit()

    # Locks
    async def acquire_lock(self, key: str, ttl: int) -> bool:
        import time
        now = int(time.time())
        exp = now + ttl
        # Remove expired
        await self.conn.execute("DELETE FROM locks WHERE expire<?", (now,))
        try:
            await self.conn.execute("INSERT INTO locks(k, expire) VALUES (?,?)", (key, exp))
            await self.conn.commit()
            return True
        except Exception:
            return False

    async def release_lock(self, key: str) -> None:
        await self.conn.execute("DELETE FROM locks WHERE k=?", (key,))
        await self.conn.commit()

    # Topic mapping
    async def get_topic_map(self) -> dict[str, str]:
        out: dict[str, str] = {}
        async with self.conn.execute("SELECT time, topic FROM topic_map") as cur:
            async for row in cur:
                out[str(row[0])] = str(row[1])
        return out

    async def set_topic_map(self, time_hhmm: str, topic: str) -> None:
        await self.conn.execute(
            "INSERT INTO topic_map(time, topic) VALUES (?,?) ON CONFLICT(time) DO UPDATE SET topic=excluded.topic",
            (time_hhmm, topic),
        )
        await self.conn.commit()

    async def unset_topic_map(self, time_hhmm: str) -> None:
        await self.conn.execute("DELETE FROM topic_map WHERE time=?", (time_hhmm,))
        await self.conn.commit()

    # Content hash checks
    async def has_recent_hash(self, content_hash: str, days: int = 3) -> bool:
        import time
        cutoff = int(time.time()) - days * 86400
        async with self.conn.execute(
            "SELECT 1 FROM runs WHERE content_hash=? AND ts>=? LIMIT 1", (content_hash, cutoff)
        ) as cur:
            row = await cur.fetchone()
            return bool(row)

    async def get_snapshot(self, day: str) -> dict | None:
        async with self.conn.execute("SELECT payload FROM snapshots WHERE day=?", (day,)) as cur:
            row = await cur.fetchone()
            if row:
                import json
                try:
                    return json.loads(row[0])
                except Exception:
                    return None
        return None

    async def set_snapshot(self, day: str, payload: dict) -> None:
        import json
        s = json.dumps(payload, ensure_ascii=False)
        await self.conn.execute(
            "INSERT INTO snapshots(day, payload) VALUES(?, ?) ON CONFLICT(day) DO UPDATE SET payload=excluded.payload",
            (day, s),
        )
        await self.conn.commit()
