import asyncio
import logging
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from telegram_bot.config.settings import Settings
from telegram_bot.utils.logging import setup_logging
from telegram_bot.handlers.admin import admin_router
from telegram_bot.scheduler.scheduler import build_scheduler
from telegram_bot.data.db import Database


async def main() -> None:
    load_dotenv("config/.env", override=False)
    settings = Settings()
    setup_logging(settings)

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    db = Database(settings)
    await db.init()

    scheduler = build_scheduler(settings, bot, db)
    scheduler.start()

    dp.include_router(admin_router(settings, scheduler, db))

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
