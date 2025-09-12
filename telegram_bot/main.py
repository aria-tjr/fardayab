import asyncio
import logging
from pathlib import Path
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from telegram_bot.config.settings import Settings
from telegram_bot.utils.logging import setup_logging
from telegram_bot.handlers.admin import admin_router
from telegram_bot.scheduler.scheduler import build_scheduler
from telegram_bot.scheduler.autoschedule import apply_autoschedule
from telegram_bot.data.db import Database
from telegram_bot.handlers.polls import polls_router


def _load_env() -> None:
    # Try a few likely locations so this works in Docker and local
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent / "config/.env",   # project_root/config/.env
        here.parent / "config/.env",          # telegram_bot/config/.env (if provided)
        Path.cwd() / "config/.env",           # CWD/config/.env
        Path.cwd() / ".env",                  # CWD/.env
    ]
    for p in candidates:
        if p.is_file():
            load_dotenv(p, override=False)
            break
    else:
        # Fallback to default behavior (env already in process)
        load_dotenv(override=False)


async def main() -> None:
    _load_env()
    settings = Settings()
    setup_logging(settings)

    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Configure config/.env or environment.")

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    db = Database(settings)
    await db.init()

    scheduler = build_scheduler(settings, bot, db)
    scheduler.start()
    # Align schedule with DB topic map and dynamic times at startup
    try:
        await apply_autoschedule(scheduler, bot, settings, db, settings.TIMEZONE)
    except Exception:
        logging.getLogger(__name__).warning("autoschedule at startup failed", exc_info=True)

    dp.include_router(admin_router(settings, scheduler, db))
    dp.include_router(polls_router(db))

    logging.getLogger(__name__).info(
        "Bot started. Timezone=%s Daily=%s Channel=%s",
        settings.TIMEZONE,
        settings.DAILY_RUN_AT,
        settings.TELEGRAM_CHANNEL_ID,
    )

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
