from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot

from telegram_bot.config.settings import Settings
from telegram_bot.data.db import Database


def _times_from_csv(csv: str) -> list[str]:
    return [t.strip() for t in csv.split(',') if t.strip()]


async def compute_times(settings: Settings, db: Database, tz: str) -> list[str]:
    # If user specified DAILY_RUN_TIMES, prefer it
    explicit = settings.DAILY_RUN_TIMES.strip()
    if explicit:
        return _times_from_csv(explicit)

    if not settings.AUTO_SCHEDULE:
        return [settings.DAILY_RUN_AT]

    # Bootstrap logic: within first N days since first run, use bootstrap times
    first_ts = await db.first_run_ts()
    now = datetime.now(ZoneInfo(tz))
    if first_ts is None:
        # No history: choose bootstrap times
        return _times_from_csv(settings.AUTO_BOOTSTRAP_TIMES)

    first_dt = datetime.fromtimestamp(first_ts, tz=ZoneInfo(tz))
    days = (now.date() - first_dt.date()).days
    if days < settings.AUTO_BOOTSTRAP_DAYS:
        return _times_from_csv(settings.AUTO_BOOTSTRAP_TIMES)
    return _times_from_csv(settings.AUTO_REGULAR_TIMES)


async def apply_autoschedule(scheduler, bot: Bot, settings: Settings, db: Database, tz: str) -> list[str]:
    from apscheduler.triggers.cron import CronTrigger
    # Compute times, then replace existing daily_job* jobs with new ones
    times = await compute_times(settings, db, tz)
    # Remove existing
    for job in scheduler.get_jobs():
        if job.id and job.id.startswith("daily_job"):
            scheduler.remove_job(job.id)
    # Add new with topic mapping
    seq = settings.topics()
    for idx, t in enumerate(times):
        hh, mm = [int(x) for x in t.split(":", 1)]
        job_id = f"daily_job_{hh:02d}{mm:02d}"
        topic = seq[idx % len(seq)] if seq else "economy"
        scheduler.add_job(
            func=__import__("telegram_bot.scheduler.jobs", fromlist=["daily_job"]).daily_job,
            trigger=CronTrigger(hour=hh, minute=mm, timezone=ZoneInfo(tz)),
            kwargs={"bot": bot, "settings": settings, "db": db, "scheduler": scheduler, "topic": topic},
            id=job_id,
            replace_existing=True,
        )
    return times
