from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

from aiogram import Bot

from telegram_bot.config.settings import Settings
from telegram_bot.data.db import Database
from telegram_bot.scheduler.jobs import daily_job
from telegram_bot.scheduler.autoschedule import compute_times
from telegram_bot.utils.timeutils import parse_hhmm

JOB_PREFIX = "daily_job"


def build_scheduler(settings: Settings, bot: Bot, db: Database) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=ZoneInfo(settings.TIMEZONE))
    # Choose times: if AUTO_SCHEDULE and no explicit times, start with bootstrap times
    tz = settings.TIMEZONE
    if settings.AUTO_SCHEDULE and not settings.DAILY_RUN_TIMES.strip():
        add_times = [t.strip() for t in settings.AUTO_BOOTSTRAP_TIMES.split(',') if t.strip()]
    else:
        add_times = settings.run_times()
    for i, t in enumerate(add_times):
        tm = parse_hhmm(t)
        job_id = f"{JOB_PREFIX}_{tm.hour:02d}{tm.minute:02d}"
        seq = settings.topics()
        topic = seq[i % len(seq)] if seq else "economy"
        scheduler.add_job(
            daily_job,
            trigger=CronTrigger(hour=tm.hour, minute=tm.minute, timezone=ZoneInfo(settings.TIMEZONE)),
            kwargs={"bot": bot, "settings": settings, "db": db, "scheduler": scheduler, "topic": topic},
            id=job_id,
            replace_existing=True,
        )
    return scheduler


def reschedule_times(scheduler: AsyncIOScheduler, timezone: str, times: list[str], *, bot: Bot, settings: Settings, db: Database) -> None:
    # Remove existing daily_job* jobs
    for job in scheduler.get_jobs():
        if job.id and job.id.startswith(JOB_PREFIX):
            scheduler.remove_job(job.id)
    # Add back requested times
    seq = settings.topics()
    for i, t in enumerate(times):
        tm = parse_hhmm(t)
        job_id = f"{JOB_PREFIX}_{tm.hour:02d}{tm.minute:02d}"
        topic = seq[i % len(seq)] if seq else "economy"
        scheduler.add_job(
            daily_job,
            trigger=CronTrigger(hour=tm.hour, minute=tm.minute, timezone=ZoneInfo(timezone)),
            kwargs={"bot": bot, "settings": settings, "db": db, "scheduler": scheduler, "topic": topic},
            id=job_id,
            replace_existing=True,
        )
