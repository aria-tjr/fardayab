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
from telegram_bot.modules.collector import collect_all
from telegram_bot.ai.generator import (
    generate_post_variants,
    generate_topic_variants,
)
from telegram_bot.ai.structured import (
    generate_combined_structured,
    generate_topic_structured,
)
from telegram_bot.utils.render import render_combined, render_topic
from telegram_bot.ai.sentiment import analyze_news_sentiment
from telegram_bot.utils.formatting import (
    clip_telegram_text,
    normalize_persian,
    format_channel_post,
    format_economy_post,
    format_sports_post,
    format_trends_post,
    format_insight_post,
)
from telegram_bot.utils.abtest import pick_variant
import asyncio
import hashlib
from datetime import datetime, timedelta, time


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

    @router.message(Command("health"))
    async def health(msg: Message):
        if not is_admin(msg):
            return
        try:
            # quick DB check
            lr = await db.last_run()
            jobs = scheduler.get_jobs()
            keys = {
                "OPENAI": bool(settings.OPENAI_API_KEY),
                "NEWS": bool(settings.NEWSAPI_KEY or settings.NEWSDATA_KEY or settings.MEDIASTACK_KEY),
            }
            await msg.answer(
                "سلامت سیستم:\n"
                f"- Jobs: {len(jobs)}\n"
                f"- آخرین اجرا: {('ok' if lr else '—')}\n"
                f"- کلیدها: OpenAI={keys['OPENAI']} News={keys['NEWS']}\n"
            )
        except Exception as e:
            await msg.answer(f"Health error: {e}")

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
            await msg.answer("فرمت: /map HH:MM topic | موضوعات مجاز: economy,sports,trends,insight")
            return
        tm, topic = parts[1], parts[2].lower()
        if topic not in {"economy","sports","trends","insight"}:
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
            await msg.answer("فرمت: /settopics economy,sports,trends,insight")
            return
        raw = [t.strip().lower() for t in parts[1].split(',') if t.strip()]
        allowed = {"economy","sports","trends","insight"}
        seq = [t for t in raw if t in allowed]
        if not seq:
            await msg.answer("موضوعات نامعتبر. مجاز: economy,sports,trends,insight")
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

    @router.message(Command("pin"))
    async def pin_toggle(msg: Message):
        if not is_admin(msg):
            return
        parts = msg.text.split()
        if len(parts) != 2 or parts[1] not in ("on", "off"):
            await msg.answer("فرمت: /pin on|off")
            return
        val = parts[1] == "on"
        settings.__dict__["PIN_POSTS"] = val
        await db.set_setting("PIN_POSTS", "1" if val else "0")
        await msg.answer(f"پین خودکار: {'فعال' if val else 'غیرفعال'}")

    @router.message(Command("dryrun"))
    async def dryrun(msg: Message):
        if not is_admin(msg):
            return
        parts = msg.text.split(maxsplit=1)
        topic = (parts[1].strip().lower() if len(parts) == 2 else None)
        await msg.answer("در حال تولید پیش‌نمایش…")
        data = await collect_all(settings)
        data["sentiment"] = await analyze_news_sentiment(settings, data.get("news") or [])
        variants: dict[str, str]
        if topic and settings.POST_MODE == 'split' and topic in {"economy","sports","trends","insight"}:
            structured = await generate_topic_structured(settings, data, topic)
            if structured and isinstance(structured, dict) and structured.get("body"):
                variants = {"A": render_topic(structured), "B": render_topic(structured)}
            else:
                variants = await generate_topic_variants(settings, data, topic, detail_level=settings.DETAIL_LEVEL)
        else:
            structured = await generate_combined_structured(settings, data)
            if structured and isinstance(structured, dict):
                variants = {"A": render_combined(structured), "B": render_combined(structured)}
            else:
                variants = await generate_post_variants(settings, data)
        a = normalize_persian(clip_telegram_text(variants.get('A') or ''))
        b = normalize_persian(clip_telegram_text(variants.get('B') or ''))
        await msg.answer("پیش‌نمایش A:\n" + a[:1000])
        await msg.answer("پیش‌نمایش B:\n" + b[:1000])

    @router.message(Command("repost"))
    async def repost(msg: Message):
        if not is_admin(msg):
            return
        parts = msg.text.split()
        if len(parts) < 2 or parts[1] not in ("A","B"):
            await msg.answer("فرمت: /repost A|B [topic]")
            return
        variant_force = parts[1]
        topic = parts[2].lower() if len(parts) >= 3 else None
        await msg.answer("در حال بازنشر…")
        data = await collect_all(settings)
        data["sentiment"] = await analyze_news_sentiment(settings, data.get("news") or [])
        if topic and settings.POST_MODE == 'split' and topic in {"economy","sports","trends","insight"}:
            structured = await generate_topic_structured(settings, data, topic)
            if structured and isinstance(structured, dict) and structured.get("body"):
                text = render_topic(structured)
            else:
                var = await generate_topic_variants(settings, data, topic, detail_level=settings.DETAIL_LEVEL)
                text = var.get(variant_force) or ''
        else:
            structured = await generate_combined_structured(settings, data)
            if structured and isinstance(structured, dict):
                text = render_combined(structured)
            else:
                var = await generate_post_variants(settings, data)
                text = var.get(variant_force) or ''
        text = normalize_persian(clip_telegram_text(text))
        await msg.bot.send_message(chat_id=settings.TELEGRAM_CHANNEL_ID, text=text, disable_web_page_preview=True)
        await msg.answer("منتشر شد.")

    @router.message(Command("seed"))
    async def seed(msg: Message):
        if not is_admin(msg):
            return
        # Usage:
        # /seed lastweek [per_day]
        # /seed days N [per_day]
        # /seed N [per_day]
        tokens = msg.text.split()
        days = 7
        per_day = 1
        if len(tokens) >= 2:
            t1 = tokens[1].lower()
            if t1 == "lastweek":
                days = 7
                if len(tokens) >= 3 and tokens[2].isdigit():
                    per_day = max(1, int(tokens[2]))
            elif t1 == "days":
                days = int(tokens[2]) if len(tokens) >= 3 and tokens[2].isdigit() else 7
                per_day = int(tokens[3]) if len(tokens) >= 4 and tokens[3].isdigit() else 1
            elif t1.isdigit():
                days = int(t1)
                per_day = int(tokens[2]) if len(tokens) >= 3 and tokens[2].isdigit() else 1
        await msg.answer(f"شروع پست‌گذاری آرشیو ({days} روز گذشته، روزانه {per_day} پست)…")

        today = datetime.now(ZoneInfo(settings.TIMEZONE)).date()
        posted = 0
        last_message_id = None
        # Helper to finalize and send one text
        async def _send_one(day_date, data_obj, text_body):
            nonlocal posted, last_message_id
            from telegram_bot.utils.formatting import format_sources
            if settings.INCLUDE_SOURCES:
                srcs = format_sources((data_obj or {}).get("news"), settings.SOURCES_COUNT)
                if srcs:
                    text_body = text_body.rstrip() + "\n" + srcs
            if settings.INCLUDE_DISCLAIMER and settings.DISCLAIMER_TEXT:
                text_body = (text_body.rstrip() + "\n\n" + settings.DISCLAIMER_TEXT).strip()
            text_body = normalize_persian(clip_telegram_text(text_body))
            try:
                sent = await msg.bot.send_message(chat_id=settings.TELEGRAM_CHANNEL_ID, text=text_body, disable_web_page_preview=True)
                last_message_id = sent.message_id
                ch = hashlib.sha256(text_body.encode('utf-8')).hexdigest()
                ts_seed = int(datetime.combine(day_date, time(12, 0), tzinfo=ZoneInfo(settings.TIMEZONE)).timestamp())
                await db.record_run(ts_seed, "seed", "multi", sent.message_id, None, topic="seed", content_hash=ch)
                posted += 1
                await asyncio.sleep(2.0)
            except Exception:
                pass

        for i in range(days, 0, -1):
            day = today - timedelta(days=i)
            snap = await db.get_snapshot(day.isoformat())
            if not snap:
                continue
            data = (snap.get("data") or {})
            # build a plan for the day: topics sequence, then combined, then repeat top topics with alternate variants
            plan: list[tuple[str, str]] = []  # (kind, topic) where kind in {"topic","combined"}
            seq = settings.topics()
            for t in seq:
                plan.append(("topic", t))
            plan.append(("combined", ""))
            # fill up to per_day by repeating economy/trends/insight cycles
            extras = ["economy", "trends", "insight", "sports"]
            j = 0
            while len(plan) < per_day:
                plan.append(("topic", extras[j % len(extras)]))
                j += 1
            # generate and send according to plan
            used_hashes: set[str] = set()
            toggle = True  # toggle A/B
            for kind, tname in plan[:per_day]:
                text = ""
                if kind == "combined":
                    try:
                        structured = await generate_combined_structured(settings, data)
                    except Exception:
                        structured = None
                    if structured and isinstance(structured, dict):
                        text = render_combined(structured)
                    else:
                        try:
                            vars = await generate_post_variants(settings, data)
                        except Exception:
                            vars = {"A": "", "B": ""}
                        text = vars.get('A' if toggle else 'B') or ""
                        toggle = not toggle
                    if not text.strip():
                        text = format_channel_post(
                            economic=data.get("crypto"),
                            sports=data.get("sports"),
                            trends=data.get("trends"),
                            header_note="⚠️ انتشار آرشیو — تولید خودکار ساده",
                            sentiment=data.get("sentiment"),
                        )
                else:  # topic
                    try:
                        structured = await generate_topic_structured(settings, data, tname)
                    except Exception:
                        structured = None
                    if structured and isinstance(structured, dict) and structured.get("body"):
                        text = render_topic(structured)
                    else:
                        try:
                            vars = await generate_topic_variants(settings, data, tname, detail_level=settings.DETAIL_LEVEL)
                        except Exception:
                            vars = {"A": "", "B": ""}
                        text = vars.get('A' if toggle else 'B') or ""
                        toggle = not toggle
                    if not text.strip():
                        # minimal fallback per topic
                        from telegram_bot.utils.formatting import (
                            format_economy_post, format_sports_post, format_trends_post, format_insight_post
                        )
                        if tname == 'economy':
                            text = format_economy_post(data.get("crypto"), data.get("sentiment"))
                        elif tname == 'sports':
                            text = format_sports_post(data.get("sports"))
                        elif tname == 'trends':
                            text = format_trends_post(data.get("trends"), data.get("trends_compare"))
                        # weather topic removed
                        else:
                            text = format_insight_post(None)

                # prevent duplicates within same day seed set
                h = hashlib.sha256((text or "").encode('utf-8')).hexdigest()
                if h in used_hashes or not (text or '').strip():
                    continue
                used_hashes.add(h)
                await _send_one(day, data, text)
        # Pin the last seeded message if enabled
        try:
            if settings.PIN_POSTS and last_message_id:
                prev = await db.get_setting("PINNED_MSG_ID")
                if prev:
                    try:
                        await msg.bot.unpin_chat_message(chat_id=settings.TELEGRAM_CHANNEL_ID, message_id=int(prev))
                    except Exception:
                        pass
                await msg.bot.pin_chat_message(chat_id=settings.TELEGRAM_CHANNEL_ID, message_id=last_message_id)
                await db.set_setting("PINNED_MSG_ID", str(last_message_id))
        except Exception:
            pass
        await msg.answer(f"انجام شد. {posted} پست از آرشیو منتشر شد.")

    return router
