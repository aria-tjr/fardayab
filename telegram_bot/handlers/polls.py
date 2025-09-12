from __future__ import annotations

from aiogram import Router
from aiogram.types import PollAnswer

from telegram_bot.data.db import Database
from telegram_bot.utils.telemetry import add_poll_vote


def polls_router(db: Database) -> Router:
    router = Router()

    @router.poll_answer()
    async def on_poll_answer(pa: PollAnswer):
        # Anonymous poll: user info limited; we only aggregate counts
        try:
            poll_id = pa.poll_id
            # Paired with message is not directly provided in PollAnswer; we just count votes per option
            for idx, chosen in enumerate(pa.option_ids or []):
                await add_poll_vote(db, poll_id, chosen, delta=1)
        except Exception:
            pass

    return router

