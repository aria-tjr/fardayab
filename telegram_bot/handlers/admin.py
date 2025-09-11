from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from telegram_bot.config.settings import Settings
from telegram_bot.data.db import Database
from telegram_bot.scheduler.jobs import daily_job
from telegram_bot.scheduler.scheduler import build_scheduler, reschedule_times
from telegram_bot.scheduler.autoschedule import apply_autoschedule
from telegram_bot.utils.timeutils import parse_hhmm


def admin_router(settings: Settings, scheduler, db: Database) -> Router:
    router = Router()

    def is_admin(msg: Message) -> bool:
        return msg.from_user and msg.from_user.id == settings.ADMIN_USER_ID

    @router.message(CommandStart())
    async def start(msg: Message):
        if not is_admin(msg):
            return
        await msg.answer(
            "سلام! بات مدیریت کانال آماده است.\n"
            "فرمان‌ها: /run, /status, /settime HH:MM, /settz Area/City"
        )

    @router.message(Command("run"))
    async def run_now(msg: Message):
        if not is_admin(msg):
            return
        await msg.answer("اجرای فوری شروع شد…")
        await daily_job(msg.bot, settings, db, scheduler)
        await msg.answer("انجام شد.")

    @router.message(Command("status"))
    async def status(msg: Message):
        if not is_admin(msg):
            return
        lr = await db.last_run()
        lr_txt = "—"
        if lr:
            ts = datetime.fromtimestamp(lr["ts"], tz=ZoneInfo(settings.TIMEZONE))
            lr_txt = f"{ts.isoformat()} | {lr['status']} | {lr.get('variant') or '—'}"
        # collect current scheduled times
        jobs = scheduler.get_jobs()
        times = []
        lines = []
        for j in jobs:
            if j.id and j.id.startswith("daily_job"):
                trig = getattr(j, 'trigger', None)
                if hasattr(trig, 'fields'):
                    # CronTrigger: fields [year, month, day, week, day_of_week, hour, minute, second]
                    try:
                        h = next(f for f in trig.fields if f.name == 'hour').expressions[0]
                        m = next(f for f in trig.fields if f.name == 'minute').expressions[0]
                        tm = f"{int(str(h)):02d}:{int(str(m)):02d}"
                        top = (j.kwargs or {}).get('topic', '—')
                        times.append(tm)
                        lines.append(f"- {tm}: {top}")
                    except Exception:
                        pass
        times = sorted(set(times))

        await msg.answer(
            "وضعیت:\n"
            f"- منطقه زمانی: {settings.TIMEZONE}\n"
            f"- زمان‌ها/موضوعات: \n" + ("\n".join(sorted(lines)) if lines else settings.DAILY_RUN_AT) + "\n"
            f"- آخرین اجرا: {lr_txt}"
        )

    @router.message(Command("settime"))
    async def set_time(msg: Message):
        if not is_admin(msg):
            return
        parts = msg.text.split()
        if len(parts) != 2:
            await msg.answer("فرمت: /settime HH:MM")
            return
        try:
            t = parse_hhmm(parts[1])
        except Exception:
            await msg.answer("زمان نامعتبر. نمونه: 22:00")
            return
        reschedule_times(scheduler, settings.TIMEZONE, [parts[1]], bot=msg.bot, settings=settings, db=db)
        await db.set_setting("DAILY_RUN_TIMES", parts[1])
        await msg.answer(f"زمان‌بندی امروز به {parts[1]} تغییر یافت. (برای دائمی شدن، در .env DAILY_RUN_TIMES تغییر دهید)")

    @router.message(Command("settz"))
    async def set_tz(msg: Message):
        if not is_admin(msg):
            return
        parts = msg.text.split(maxsplit=1)
        if len(parts) != 2:
            await msg.answer("فرمت: /settz Area/City — مثل Asia/Tehran")
            return
        tz = parts[1].strip()
        try:
            ZoneInfo(tz)
        except Exception:
            await msg.answer("منطقه زمانی نامعتبر است.")
            return
        # Reschedule existing daily jobs with new timezone
        jobs = scheduler.get_jobs()
        times = []
        for j in jobs:
            if j.id and j.id.startswith("daily_job"):
                trig = getattr(j, 'trigger', None)
                if hasattr(trig, 'fields'):
                    try:
                        h = next(f for f in trig.fields if f.name == 'hour').expressions[0]
                        m = next(f for f in trig.fields if f.name == 'minute').expressions[0]
                        times.append(f"{int(str(h)):02d}:{int(str(m)):02d}")
                    except Exception:
                        pass
        if not times:
            times = [settings.DAILY_RUN_AT]
        reschedule_times(scheduler, tz, times, bot=msg.bot, settings=settings, db=db)
        await db.set_setting("TIMEZONE", tz)
        await msg.answer(f"منطقه زمانی به {tz} تغییر یافت. (برای دائمی شدن، در .env تغییر دهید)")

    @router.message(Command("settimes"))
    async def set_times(msg: Message):
        if not is_admin(msg):
            return
        parts = msg.text.split(maxsplit=1)
        if len(parts) != 2:
            await msg.answer("فرمت: /settimes HH:MM,HH:MM,HH:MM")
            return
        raw = parts[1]
        times = []
        try:
            for t in raw.split(','):
                t = t.strip()
                if not t:
                    continue
                parse_hhmm(t)  # validate
                times.append(t)
        except Exception:
            await msg.answer("زمان‌ها نامعتبرند. نمونه: 10:00,14:30,20:15")
            return
        reschedule_times(scheduler, settings.TIMEZONE, times, bot=msg.bot, settings=settings, db=db)
        await db.set_setting("DAILY_RUN_TIMES", ",".join(times))
        await msg.answer(f"زمان‌های اجرای روزانه تنظیم شد: {', '.join(times)} (برای دائمی شدن، در .env DAILY_RUN_TIMES تغییر دهید)")

    @router.message(Command("mode"))
    async def set_mode(msg: Message):
        if not is_admin(msg):
            return
        parts = msg.text.split(maxsplit=1)
        if len(parts) != 2 or parts[1] not in ("split", "combined"):
            await msg.answer("فرمت: /mode split|combined")
            return
        mode = parts[1]
        settings.__dict__["POST_MODE"] = mode
        await db.set_setting("POST_MODE", mode)
        await msg.answer(f"حالت انتشار به {mode} تغییر کرد.")

    @router.message(Command("detail"))
    async def set_detail(msg: Message):
        if not is_admin(msg):
            return
        parts = msg.text.split(maxsplit=1)
        if len(parts) != 2 or parts[1] not in ("high", "medium", "low"):
            await msg.answer("فرمت: /detail high|medium|low")
            return
        level = parts[1]
        settings.__dict__["DETAIL_LEVEL"] = level
        await db.set_setting("DETAIL_LEVEL", level)
        await msg.answer(f"سطح جزئیات به {level} تغییر کرد.")

    @router.message(Command("map"))
    async def map_time_topic(msg: Message):
        if not is_admin(msg):
            return
        parts = msg.text.split()
        if len(parts) != 3:
            await msg.answer("فرمت: /map HH:MM topic | موضوعات مجاز: economy,sports,trends,weather,insight")
            return
        tm, topic = parts[1], parts[2].lower()
        if topic not in {"economy","sports","trends","weather","insight"}:
            await msg.answer("موضوع نامعتبر.")
            return
        try:
            parse_hhmm(tm)
        except Exception:
            await msg.answer("زمان نامعتبر.")
            return
        await db.set_topic_map(tm, topic)
        # Re-apply autoschedule to pick mapping
        await apply_autoschedule(scheduler, msg.bot, settings, db, settings.TIMEZONE)
        await msg.answer(f"زمان {tm} به موضوع {topic} نگاشت شد و زمان‌بندی به‌روزرسانی شد.")

    @router.message(Command("unmap"))
    async def unmap_time(msg: Message):
        if not is_admin(msg):
            return
        parts = msg.text.split()
        if len(parts) != 2:
            await msg.answer("فرمت: /unmap HH:MM")
            return
        tm = parts[1]
        try:
            parse_hhmm(tm)
        except Exception:
            await msg.answer("زمان نامعتبر.")
            return
        await db.unset_topic_map(tm)
        await apply_autoschedule(scheduler, msg.bot, settings, db, settings.TIMEZONE)
        await msg.answer(f"نگاشت زمان {tm} حذف شد و زمان‌بندی به‌روزرسانی شد.")

    @router.message(Command("settopics"))
    async def set_topics(msg: Message):
        if not is_admin(msg):
            return
        parts = msg.text.split(maxsplit=1)
        if len(parts) != 2:
            await msg.answer("فرمت: /settopics economy,sports,trends,weather,insight")
            return
        raw = [t.strip().lower() for t in parts[1].split(',') if t.strip()]
        allowed = {"economy","sports","trends","weather","insight"}
        seq = [t for t in raw if t in allowed]
        if not seq:
            await msg.answer("موضوعات نامعتبر. مجاز: economy,sports,trends,weather,insight")
            return
        await db.set_setting("TOPIC_SEQUENCE", ",".join(seq))
        # Re-schedule using current times and new topics sequence
        jobs = scheduler.get_jobs()
        times = []
        for j in jobs:
            if j.id and j.id.startswith("daily_job"):
                trig = getattr(j,'trigger',None)
                if hasattr(trig,'fields'):
                    try:
                        h = next(f for f in trig.fields if f.name=='hour').expressions[0]
                        m = next(f for f in trig.fields if f.name=='minute').expressions[0]
                        times.append(f"{int(str(h)):02d}:{int(str(m)):02d}")
                    except Exception:
                        pass
        times = sorted(set(times))
        # monkey patch settings TOPIC_SEQUENCE for this runtime
        settings.__dict__["TOPIC_SEQUENCE"] = ",".join(seq)
        reschedule_times(scheduler, settings.TIMEZONE, times, bot=msg.bot, settings=settings, db=db)
        await msg.answer("ترتیب موضوعات به‌روزرسانی شد و روی زمان‌های فعلی اعمال شد.")

    return router
