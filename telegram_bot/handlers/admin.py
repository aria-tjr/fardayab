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
            "فرمان‌ها: /run, /status, /health, /refresh, /persian, /free, /style, /content, /intelligent, /analytics, /optimize, /settime HH:MM, /settz Area/City, /postlast3days"
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
            from telegram_bot.scheduler.realtime import HealthChecker
            health_checker = HealthChecker(settings)
            health_status = await health_checker.check_health()
            
            # quick DB check
            lr = await db.last_run()
            jobs = scheduler.get_jobs()
            keys = {
                "OPENAI": bool(settings.OPENAI_API_KEY),
                "NEWS": bool(settings.NEWSAPI_KEY or settings.NEWSDATA_KEY or settings.MEDIASTACK_KEY),
            }
            
            status_emoji = "✅" if health_status["overall"] else "⚠️"
            internet_emoji = "✅" if health_status["internet"] else "❌"
            openai_emoji = "✅" if health_status["openai"] else "❌"
            apis_emoji = "✅" if health_status["apis"] else "❌"
            
            await msg.answer(
                f"{status_emoji} **وضعیت سیستم**\n"
                f"🌐 اینترنت: {internet_emoji}\n"
                f"🤖 OpenAI: {openai_emoji}\n"
                f"📡 APIs: {apis_emoji}\n"
                f"⏰ آخرین بررسی: {health_status['last_check']}\n\n"
                f"📊 **جزئیات:**\n"
                f"- Jobs: {len(jobs)}\n"
                f"- آخرین اجرا: {('ok' if lr else '—')}\n"
                f"- کلیدها: OpenAI={keys['OPENAI']} News={keys['NEWS']}\n"
                f"- مدل: {settings.OPENAI_MODEL}\n"
                f"- Real-time: {'فعال' if settings.ENABLE_REAL_TIME_DATA else 'غیرفعال'}"
            )
        except Exception as e:
            await msg.answer(f"خطا در بررسی سلامت: {e}")

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
        # Content filtering
        from telegram_bot.utils.formatting import is_generic_social_media_advice
        if is_generic_social_media_advice(text):
            await msg.answer("⚠️ محتوای تولید شده حاوی توصیه‌های عمومی شبکه‌های اجتماعی است و فیلتر شد. لطفاً دوباره تلاش کنید.")
            return
            
        text = normalize_persian(clip_telegram_text(text))
        await msg.bot.send_message(chat_id=settings.TELEGRAM_CHANNEL_ID, text=text, disable_web_page_preview=True)
        await msg.answer("منتشر شد.")

    @router.message(Command("postlast3days"))
    async def post_last_3_days(msg: Message):
        if not is_admin(msg):
            return
        await msg.answer("شروع انتشار 3 روز گذشته…")

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
                await db.record_run(ts_seed, "postlast3days", "multi", sent.message_id, None, topic="postlast3days", content_hash=ch)
                posted += 1
                await asyncio.sleep(1.0)  # Shorter delay for faster posting
            except Exception as e:
                await msg.answer(f"خطا در ارسال پست: {e}")

        # Process last 3 days
        for i in range(3, 0, -1):
            day = today - timedelta(days=i)
            snap = await db.get_snapshot(day.isoformat())
            if not snap:
                await msg.answer(f"داده‌ای برای {day.isoformat()} یافت نشد.")
                continue
                
            data = (snap.get("data") or {})
            
            # Generate content for this day using current settings
            try:
                # Collect fresh data for this day's context
                fresh_data = await collect_all(settings)
                fresh_data["sentiment"] = await analyze_news_sentiment(settings, fresh_data.get("news") or [])
                
                # Generate posts based on current POST_MODE
                if settings.POST_MODE == 'split':
                    # Generate one post per topic for this day
                    seq = settings.topics()
                    for topic in seq:
                        try:
                            if topic in {"economy", "sports", "trends", "insight"}:
                                structured = await generate_topic_structured(settings, fresh_data, topic)
                                if structured and isinstance(structured, dict) and structured.get("body"):
                                    text = render_topic(structured)
                                else:
                                    vars = await generate_topic_variants(settings, fresh_data, topic, detail_level=settings.DETAIL_LEVEL)
                                    text = vars.get('A') or ""
                                
                                if not text.strip():
                                    # Fallback formatting
                                    from telegram_bot.utils.formatting import (
                                        format_economy_post, format_sports_post, format_trends_post, format_insight_post
                                    )
                                    if topic == 'economy':
                                        text = format_economy_post(fresh_data.get("crypto"), fresh_data.get("sentiment"))
                                    elif topic == 'sports':
                                        text = format_sports_post(fresh_data.get("sports"))
                                    elif topic == 'trends':
                                        text = format_trends_post(fresh_data.get("trends"), fresh_data.get("trends_compare"))
                                    else:
                                        text = format_insight_post(None)
                                
                                if text.strip():
                                    # Content filtering
                                    from telegram_bot.utils.formatting import is_generic_social_media_advice
                                    if not is_generic_social_media_advice(text):
                                        await _send_one(day, fresh_data, text)
                                    else:
                                        await msg.answer(f"⚠️ محتوای {topic} برای {day.isoformat()} فیلتر شد (توصیه‌های عمومی شبکه‌های اجتماعی)")
                        except Exception as e:
                            await msg.answer(f"خطا در تولید پست {topic} برای {day.isoformat()}: {e}")
                else:
                    # Generate combined post
                    try:
                        structured = await generate_combined_structured(settings, fresh_data)
                        if structured and isinstance(structured, dict):
                            text = render_combined(structured)
                        else:
                            vars = await generate_post_variants(settings, fresh_data)
                            text = vars.get('A') or ""
                        
                        if not text.strip():
                            text = format_channel_post(
                                economic=fresh_data.get("crypto"),
                                sports=fresh_data.get("sports"),
                                trends=fresh_data.get("trends"),
                                header_note=f"📅 {day.strftime('%Y-%m-%d')} — انتشار آرشیو",
                                sentiment=fresh_data.get("sentiment"),
                            )
                        
                        if text.strip():
                            # Content filtering
                            from telegram_bot.utils.formatting import is_generic_social_media_advice
                            if not is_generic_social_media_advice(text):
                                await _send_one(day, fresh_data, text)
                            else:
                                await msg.answer(f"⚠️ محتوای ترکیبی برای {day.isoformat()} فیلتر شد (توصیه‌های عمومی شبکه‌های اجتماعی)")
                    except Exception as e:
                        await msg.answer(f"خطا در تولید پست ترکیبی برای {day.isoformat()}: {e}")
                        
            except Exception as e:
                await msg.answer(f"خطا در پردازش {day.isoformat()}: {e}")

        # Pin the last message if enabled
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
            
        await msg.answer(f"انجام شد. {posted} پست از 3 روز گذشته منتشر شد.")

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

    @router.message(Command("refresh"))
    async def refresh_data(msg: Message):
        if not is_admin(msg):
            return
        await msg.answer("🔄 در حال به‌روزرسانی داده‌های Real-time...")
        try:
            from telegram_bot.scheduler.realtime import RealTimeScheduler, HealthChecker
            from telegram_bot.utils.connectivity import create_connectivity_system
            
            # Create temporary instances for refresh
            _, data_manager, _ = await create_connectivity_system(settings)
            realtime_scheduler = RealTimeScheduler(settings, data_manager)
            health_checker = HealthChecker(settings)
            
            # Force data update
            fresh_data = await realtime_scheduler.force_update()
            
            # Check health
            health_status = await health_checker.check_health()
            
            await msg.answer(
                f"✅ **داده‌ها به‌روزرسانی شدند**\n"
                f"🌐 اینترنت: {'✅' if health_status['internet'] else '❌'}\n"
                f"🤖 OpenAI: {'✅' if health_status['openai'] else '❌'}\n"
                f"📡 APIs: {'✅' if health_status['apis'] else '❌'}\n"
                f"📊 داده‌های جدید: {len(fresh_data.get('news', []))} خبر، {len(fresh_data.get('trends', []))} ترند"
            )
        except Exception as e:
            await msg.answer(f"❌ خطا در به‌روزرسانی: {e}")

    @router.message(Command("persian"))
    async def test_persian_apis(msg: Message):
        if not is_admin(msg):
            return
        await msg.answer("🇮🇷 در حال تست APIهای فارسی...")
        try:
            from telegram_bot.modules.persian_apis import PersianContentEnhancer
            persian_enhancer = PersianContentEnhancer(settings)
            
            # Test Persian content enhancement
            persian_data = await persian_enhancer.get_enhanced_persian_data()
            
            # Test translation
            test_text = "Hello, this is a test message for Persian translation."
            translated = await persian_enhancer.translation_api.translate_to_persian(test_text)
            
            # Count available APIs
            api_status = {
                "World News": bool(settings.WORLD_NEWS_API_KEY),
                "Lingvanex": bool(settings.LINGVANEX_API_KEY),
                "Tasnim": bool(settings.TASNIM_API_KEY),
                "ISNA": bool(settings.ISNA_API_KEY),
                "Mehr": bool(settings.MEHR_API_KEY),
                "Fars": bool(settings.FARS_API_KEY),
            }
            
            active_apis = sum(api_status.values())
            persian_news_count = len(persian_data.get('persian_news', []))
            
            await msg.answer(
                f"🇮🇷 **وضعیت APIهای فارسی**\n"
                f"📊 APIهای فعال: {active_apis}/6\n"
                f"📰 اخبار فارسی: {persian_news_count} مقاله\n"
                f"🔧 بهبود محتوا: {'✅' if persian_data.get('enhanced', False) else '❌'}\n"
                f"🌐 ترجمه: {'✅' if translated != test_text else '❌'}\n\n"
                f"**جزئیات APIها:**\n" +
                "\n".join([f"{name}: {'✅' if status else '❌'}" for name, status in api_status.items()]) +
                f"\n\n**مثال ترجمه:**\n{test_text}\n→ {translated}"
            )
        except Exception as e:
            await msg.answer(f"❌ خطا در تست APIهای فارسی: {e}")

    @router.message(Command("free"))
    async def test_free_persian_apis(msg: Message):
        if not is_admin(msg):
            return
        await msg.answer("🆓 در حال تست APIهای رایگان فارسی...")
        try:
            from telegram_bot.modules.free_persian_apis import FreePersianAPIs
            free_apis = FreePersianAPIs(settings)
            
            # Test all free APIs
            free_data = await free_apis.get_enhanced_persian_content()
            
            # Test Persian text processing
            test_text = "سلام، این یک متن تست برای پردازش فارسی است."
            text_analysis = await free_apis.process_persian_text(test_text)
            
            # Get calendar info
            calendar_info = await free_apis.get_persian_calendar_info()
            
            books_count = len(free_data.get('persian_books', []))
            countries_count = len(free_data.get('countries_info', []))
            apis_count = len(free_data.get('iranian_apis', []))
            
            await msg.answer(
                f"🆓 **APIهای رایگان فارسی**\n"
                f"📚 کتاب‌ها: {books_count} عنوان\n"
                f"🌍 کشورها: {countries_count} کشور\n"
                f"🔧 APIهای ایرانی: {apis_count} منبع\n"
                f"📅 تقویم فارسی: {'✅' if calendar_info else '❌'}\n"
                f"📝 پردازش متن: {'✅' if text_analysis.get('processed', False) else '❌'}\n\n"
                f"**جزئیات تقویم:**\n"
                f"سال: {calendar_info.get('persian_year', 'نامشخص')}\n"
                f"ماه: {calendar_info.get('persian_month_name', 'نامشخص')}\n"
                f"فصل: {calendar_info.get('season', 'نامشخص')}\n\n"
                f"**تحلیل متن:**\n"
                f"نسبت فارسی: {text_analysis.get('persian_ratio', 0):.2%}\n"
                f"کلمات فارسی: {text_analysis.get('persian_word_count', 0)}\n"
                f"کل کلمات: {text_analysis.get('total_words', 0)}"
            )
        except Exception as e:
            await msg.answer(f"❌ خطا در تست APIهای رایگان: {e}")

    @router.message(Command("style"))
    async def test_channel_style(msg: Message):
        if not is_admin(msg):
            return
        await msg.answer("🎨 در حال تست استایل کانال فردایاب...")
        try:
            from telegram_bot.modules.collector import collect_all
            from telegram_bot.ai.generator import generate_post_variants
            
            # Collect fresh data
            fresh_data = await collect_all(settings)
            
            # Generate post with Fardayab style
            variants = await generate_post_variants(settings, fresh_data)
            
            if variants.get('A'):
                await msg.answer(
                    f"🎨 **استایل کانال فردایاب**\n\n"
                    f"✅ پست تولید شد با استایل جدید\n"
                    f"📊 بخش‌ها: اقتصاد، ورزش، ترند، Insight\n"
                    f"🎯 تون: آموزشی/اطلاع‌رسانی\n"
                    f"📝 طول: {len(variants['A'])} کاراکتر\n\n"
                    f"**نمونه پست:**\n{variants['A'][:200]}..."
                )
            else:
                await msg.answer("❌ خطا در تولید پست با استایل جدید")
                
        except Exception as e:
            await msg.answer(f"❌ خطا در تست استایل: {e}")

    @router.message(Command("content"))
    async def test_content_types(msg: Message):
        if not is_admin(msg):
            return
        await msg.answer("📚 در حال تست انواع محتوا...")
        try:
            from telegram_bot.modules.content_types import EnhancedContentManager
            content_manager = EnhancedContentManager(settings)
            
            # Test all content types
            all_content = await content_manager.get_all_enhanced_content()
            
            # Count available content
            culture_count = len(all_content.get('culture_and_arts', {}).get('cultural_events', []))
            tech_count = len(all_content.get('technology_innovation', {}).get('iranian_tech', []))
            literature_count = 1 if all_content.get('literature_poetry', {}).get('daily_poem') else 0
            lifestyle_count = len(all_content.get('lifestyle_health', {}).get('health_tips', []))
            travel_count = len(all_content.get('travel_tourism', {}).get('destinations', []))
            
            total_content = culture_count + tech_count + literature_count + lifestyle_count + travel_count
            
            await msg.answer(
                f"📚 **انواع محتوای فردایاب**\n\n"
                f"🎭 فرهنگ و هنر: {culture_count} محتوا\n"
                f"🚀 تکنولوژی و نوآوری: {tech_count} محتوا\n"
                f"📖 ادبیات و شعر: {literature_count} شعر روز\n"
                f"🌱 سبک زندگی و سلامت: {lifestyle_count} نکته\n"
                f"✈️ سفر و گردشگری: {travel_count} مقصد\n\n"
                f"📊 **مجموع محتوا:** {total_content} مورد\n"
                f"✅ **وضعیت:** {'فعال' if all_content.get('enhanced_content_active', False) else 'غیرفعال'}\n\n"
                f"**دستورات تست:**\n"
                f"/content culture - تست فرهنگ و هنر\n"
                f"/content tech - تست تکنولوژی\n"
                f"/content literature - تست ادبیات\n"
                f"/content lifestyle - تست سبک زندگی\n"
                f"/content travel - تست سفر"
            )
        except Exception as e:
            await msg.answer(f"❌ خطا در تست انواع محتوا: {e}")

    @router.message(Command("intelligent"))
    async def test_intelligent_systems(msg: Message):
        if not is_admin(msg):
            return
        await msg.answer("🧠 در حال تست سیستم‌های هوشمند...")
        try:
            from telegram_bot.ai.intelligent_curator import IntelligentContentCurator
            from telegram_bot.ai.persian_processor import AdvancedPersianProcessor
            from telegram_bot.scheduler.intelligent_scheduler import IntelligentPostingScheduler
            from telegram_bot.analytics.channel_monitor import ChannelAnalyticsMonitor
            
            # Test intelligent curator
            curator = IntelligentContentCurator(settings)
            recommendations = await curator.get_content_recommendations()
            
            # Test Persian processor
            processor = AdvancedPersianProcessor(settings)
            test_text = "سلام، این یک متن تست برای پردازش هوشمند فارسی است."
            text_analysis = await processor.process_persian_text(test_text)
            
            # Test intelligent scheduler
            scheduler = IntelligentPostingScheduler(settings)
            content_types = ['economy', 'sports', 'trends', 'culture', 'technology']
            optimal_schedule = await scheduler.calculate_optimal_posting_schedule(content_types)
            
            # Test analytics monitor
            monitor = ChannelAnalyticsMonitor(settings)
            health_status = await monitor.monitor_channel_health(msg.bot)
            
            await msg.answer(
                f"🧠 **سیستم‌های هوشمند فردایاب**\n\n"
                f"🎯 **مشاور محتوا:**\n"
                f"توصیه‌ها: {len(recommendations.get('engagement_tips', []))} مورد\n"
                f"زمان‌های بهینه: {len(recommendations.get('optimal_posting_times', []))} زمان\n\n"
                f"📝 **پردازش فارسی:**\n"
                f"نسبت فارسی: {text_analysis.get('language_analysis', {}).get('persian_ratio', 0):.1%}\n"
                f"کیفیت محتوا: {text_analysis.get('content_quality', {}).get('overall_quality', 0):.2f}\n"
                f"قابلیت خوانایی: {text_analysis.get('readability_score', 0):.1f}/10\n\n"
                f"⏰ **زمان‌بندی هوشمند:**\n"
                f"زمان‌های بهینه: {len(optimal_schedule)} زمان\n"
                f"اولویت بالا: {optimal_schedule[0]['content_type'] if optimal_schedule else 'نامشخص'}\n\n"
                f"📊 **نظارت کانال:**\n"
                f"امتیاز سلامت: {health_status.get('health_score', 0):.1%}\n"
                f"وضعیت: {health_status.get('status', 'نامشخص')}\n"
                f"هشدارها: {len(health_status.get('warnings', []))} مورد\n"
                f"مشکلات: {len(health_status.get('issues', []))} مورد"
            )
        except Exception as e:
            await msg.answer(f"❌ خطا در تست سیستم‌های هوشمند: {e}")

    @router.message(Command("analytics"))
    async def get_channel_analytics(msg: Message):
        if not is_admin(msg):
            return
        await msg.answer("📊 در حال جمع‌آوری آمار کانال...")
        try:
            from telegram_bot.analytics.channel_monitor import ChannelAnalyticsMonitor
            monitor = ChannelAnalyticsMonitor(settings)
            
            # Generate comprehensive analytics report
            report = await monitor.generate_analytics_report(msg.bot)
            await msg.answer(report)
            
        except Exception as e:
            await msg.answer(f"❌ خطا در جمع‌آوری آمار: {e}")

    @router.message(Command("optimize"))
    async def optimize_channel_content(msg: Message):
        if not is_admin(msg):
            return
        await msg.answer("⚡ در حال بهینه‌سازی محتوا...")
        try:
            from telegram_bot.ai.intelligent_curator import IntelligentContentCurator
            from telegram_bot.modules.collector import collect_all
            
            # Collect fresh data
            fresh_data = await collect_all(settings)
            
            # Get intelligent curator
            curator = IntelligentContentCurator(settings)
            
            # Select best content mix
            optimal_content = await curator.select_best_content_mix(fresh_data)
            
            # Get recommendations
            recommendations = await curator.get_content_recommendations()
            
            await msg.answer(
                f"⚡ **بهینه‌سازی محتوا**\n\n"
                f"📊 **محتوای بهینه انتخاب شده:**\n"
                f"تعداد انواع محتوا: {len(optimal_content)}\n"
                f"انواع محتوا: {', '.join(optimal_content.keys())}\n\n"
                f"💡 **توصیه‌های بهینه‌سازی:**\n" +
                "\n".join([f"• {tip}" for tip in recommendations.get('engagement_tips', [])[:3]]) + "\n\n"
                f"⏰ **زمان‌های بهینه ارسال:**\n" +
                "\n".join([f"• {time[0]}:{time[1]:02d}" for time in recommendations.get('optimal_posting_times', [])[:3]]) + "\n\n"
                f"🎯 **موضوعات ترند:**\n" +
                "\n".join([f"• {topic}" for topic in recommendations.get('trending_topics', [])[:3]])
            )
        except Exception as e:
            await msg.answer(f"❌ خطا در بهینه‌سازی: {e}")

    return router
