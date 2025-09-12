from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot

from telegram_bot.config.settings import Settings
from telegram_bot.data.db import Database
from telegram_bot.modules.collector import collect_all
from telegram_bot.utils.formatting import format_channel_post
from telegram_bot.utils.abtest import pick_variant
from telegram_bot.utils.telemetry import topic_variant_stats
from telegram_bot.utils.timeutils import now_tz
from telegram_bot.ai.generator import generate_post_variants, generate_admin_suggestions, generate_topic_variants
from telegram_bot.ai.structured import generate_combined_structured, generate_topic_structured
from telegram_bot.utils.render import render_combined, render_topic
from telegram_bot.ai.sentiment import analyze_news_sentiment
from telegram_bot.modules.crypto import fetch_btc_market_chart
from telegram_bot.modules.charts import btc_chart_url
from telegram_bot.ai.images import generate_image_url
from telegram_bot.utils import mcache


log = logging.getLogger(__name__)


async def daily_job(bot: Bot, settings: Settings, db: Database, scheduler=None, topic: str | None = None) -> None:
    ts = int(datetime.now().timestamp())
    try:
        tz = await db.get_setting("TIMEZONE", settings.TIMEZONE) or settings.TIMEZONE
        cache_key = "collect_all"
        cached = mcache.get(cache_key)
        if cached is None:
            data = await collect_all(settings)
            mcache.set(cache_key, data, ttl=900)  # 15 minutes
        else:
            data = cached
        # enrich with sentiment and yesterday snapshot
        data["sentiment"] = await analyze_news_sentiment(settings, data.get("news") or [])
        today = now_tz(tz).date()
        yday = type(today).fromordinal(today.toordinal() - 1)
        prev_snapshot = await db.get_snapshot(yday.isoformat())
        if prev_snapshot:
            data["yesterday"] = {"day": yday.isoformat(), "snapshot": prev_snapshot}
        # Determine topic for this run
        topic = (topic or (settings.POST_MODE == 'split' and 'economy') or 'combined').lower()
        # Generate variants according to mode (prefer structured → fallback to text)
        variants: dict[str, str]
        if settings.POST_MODE == 'split' and topic in {"economy", "sports", "trends", "weather", "insight"}:
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

        # Choose variant deterministically by date
        # Variant choice: bandit on poll stats if available
        if settings.POST_MODE == 'split' and topic in {"economy","trends"}:
            try:
                stats = await topic_variant_stats(db, topic)
                a = max(1, stats.get('A', 0))
                b = max(1, stats.get('B', 0))
                import random
                total = a + b
                r = random.random() * total
                variant = 'A' if r < a else 'B'
            except Exception:
                variant = pick_variant(today, settings.AB_SEED)
        else:
            variant = pick_variant(today, settings.AB_SEED)
        text = variants.get(variant) or ""

        if not text.strip():
            # Fallback to deterministic formatter
            insights = [
                "💡 جالب است بدانید: بیش از ۶۰٪ معاملات بیت‌کوین توسط ۱٪ آدرس‌ها انجام می‌شود.",
                "💡 دانستنی: بازارها در بلندمدت به سمت میانگین بازمی‌گردند؛ هیجان‌های کوتاه‌مدت پایدار نیستند.",
                "💡 نکته: تنوع‌بخشی ریسک را کاهش می‌دهد؛ هیچ‌وقت همه تخم‌مرغ‌ها در یک سبد!",
            ]
            idx = today.toordinal() % len(insights)
            if settings.POST_MODE == 'split':
                from telegram_bot.utils.formatting import (
                    format_economy_post, format_sports_post, format_trends_post, format_weather_post, format_insight_post
                )
                if topic == 'economy':
                    text = format_economy_post(data.get("crypto"), data.get("sentiment"))
                elif topic == 'sports':
                    text = format_sports_post(data.get("sports"))
                elif topic == 'trends':
                    text = format_trends_post(data.get("trends"), data.get("trends_compare"))
                elif topic == 'weather':
                    text = format_weather_post(data.get("weather"))
                else:
                    text = format_insight_post(insights[idx])
            else:
                text = format_channel_post(
                    economic=data.get("crypto"),
                    sports=data.get("sports"),
                    trends=data.get("trends"),
                    weather=data.get("weather"),
                    header_note="⚠️ تولید خودکار با فرمت رزرو (بدون OpenAI)",
                    sentiment=data.get("sentiment"),
                    insight=insights[idx],
                )

        # Prevent duplicate content within last few days
        import hashlib
        content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        if await db.has_recent_hash(content_hash, days=3):
            # try alternate variant
            alt = 'B' if variant == 'A' else 'A'
            text2 = variants.get(alt) or text
            content_hash2 = hashlib.sha256(text2.encode('utf-8')).hexdigest()
            if not await db.has_recent_hash(content_hash2, days=3):
                text = text2
                content_hash = content_hash2
        # Acquire lock per minute/topic to avoid overlap
        lock_key = f"post:{today.isoformat()}:{topic}:{variant}"
        got = await db.acquire_lock(lock_key, ttl=600)
        if not got:
            return
        msg = await bot.send_message(chat_id=settings.TELEGRAM_CHANNEL_ID, text=text)

        # Optional: chart image for BTC, economy topic only or combined
        if settings.ENABLE_CHARTS and (settings.POST_MODE != 'split' or topic == 'economy'):
            try:
                hist = await fetch_btc_market_chart(days=7, timeout=settings.HTTP_TIMEOUT)
                url = btc_chart_url(hist)
                if url:
                    await bot.send_photo(chat_id=settings.TELEGRAM_CHANNEL_ID, photo=url, caption="نمودار ۷روزه بیت‌کوین 📈")
            except Exception:
                log.warning("chart generation failed", exc_info=True)

        # Optional: AI image for select topics
        if settings.ENABLE_IMAGES and topic in {"economy","trends","insight"}:
            try:
                img_url = await generate_image_url(settings, topic, data)
                if img_url:
                    await bot.send_photo(chat_id=settings.TELEGRAM_CHANNEL_ID, photo=img_url, caption="پوستر روز 🖼️")
            except Exception:
                log.warning("image generation failed", exc_info=True)

        # Optional: poll for engagement (economy/trends posts)
        poll_msg = None
        if settings.ENABLE_POLL and (settings.POST_MODE != 'split' or topic in {'economy','trends'}):
            try:
                poll_msg = await bot.send_poll(
                    chat_id=settings.TELEGRAM_CHANNEL_ID,
                    question="فردا بیت‌کوین چگونه خواهد بود؟",
                    options=["صعودی", "نزولی", "رنج/خنثی"],
                    is_anonymous=True,
                    allows_multiple_answers=False,
                )
            except Exception:
                log.warning("poll failed", exc_info=True)
        await db.record_run(ts, "ok", variant, msg.message_id, None, topic=topic, content_hash=content_hash)
        # Link poll if any
        try:
            if poll_msg and getattr(poll_msg, 'poll', None):
                from telegram_bot.utils.telemetry import record_poll_message
                await record_poll_message(db, poll_msg.poll.id, poll_msg.message_id, topic, variant, ts)
        except Exception:
            log.warning("poll record failed", exc_info=True)
        # store snapshot of today for comparisons
        try:
            await db.set_snapshot(today.isoformat(), {"data": data, "variant": variant})
        except Exception:
            log.warning("snapshot save failed", exc_info=True)

        # Auto-schedule next posts based on bootstrap/regular cadence
        try:
            if scheduler is not None and settings.AUTO_SCHEDULE:
                from telegram_bot.scheduler.autoschedule import apply_autoschedule
                times = await apply_autoschedule(scheduler, bot, settings, db, tz)
                await bot.send_message(
                    chat_id=settings.ADMIN_USER_ID,
                    text="زمان‌بندی خودکار به‌روزرسانی شد: " + ", ".join(times),
                )
        except Exception:
            log.warning("autoschedule update failed", exc_info=True)

        # Admin report
        suggestions = await generate_admin_suggestions(settings, data)
        await bot.send_message(
            chat_id=settings.ADMIN_USER_ID,
            text=(
                "گزارش روزانه:\n"
                f"- واریانت پست: {variant}\n"
                f"- پیام منتشر شد. message_id={msg.message_id}\n\n"
                f"پیشنهادات:\n{suggestions}"
            ),
        )

    except Exception as e:
        log.exception("daily_job failed")
        await db.record_run(ts, "error", None, None, str(e))
        await bot.send_message(
            chat_id=settings.ADMIN_USER_ID,
            text=f"❌ اجرای روزانه با خطا مواجه شد:\n{e}",
        )
