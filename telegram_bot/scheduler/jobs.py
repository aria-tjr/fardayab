from __future__ import annotations

import asyncio
import hashlib
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
from telegram_bot.scheduler.intelligent_scheduler import IntelligentPostingScheduler


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
        if settings.POST_MODE == 'split' and topic in {"economy", "sports", "trends", "insight"}:
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
                    format_economy_post, format_sports_post, format_trends_post, format_insight_post
                )
                if topic == 'economy':
                    text = format_economy_post(data.get("crypto"), data.get("sentiment"))
                elif topic == 'sports':
                    text = format_sports_post(data.get("sports"))
                elif topic == 'trends':
                    text = format_trends_post(data.get("trends"), data.get("trends_compare"))
                else:
                    text = format_insight_post(insights[idx])
            else:
                text = format_channel_post(
                    economic=data.get("crypto"),
                    sports=data.get("sports"),
                    trends=data.get("trends"),
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
        # Content filtering and validation
        from telegram_bot.utils.formatting import clip_telegram_text, normalize_persian, format_sources, is_generic_social_media_advice
        
        # Filter out generic social media advice
        if is_generic_social_media_advice(text):
            log.warning("Filtered out generic social media advice content")
            # Try alternative variant if available
            alt = 'B' if variant == 'A' else 'A'
            text2 = variants.get(alt) or ""
            if text2 and not is_generic_social_media_advice(text2):
                text = text2
                content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
            else:
                # Use fallback content
                if settings.POST_MODE == 'split' and topic == 'insight':
                    text = "**💡 نکته طلایی روز** ✨\n─" * 20 + "\n🎯 همیشه قبل از سرمایه‌گذاری، ریسک خود را ارزیابی کنید. تنوع‌بخشی کلید موفقیت است! 💰\n\n#سرمایه‌گذاری #ریسک #تنوع‌بخشی #طلایی"
                else:
                    text = "**📊 تحلیل روز** 📈\n─" * 20 + "\n🔄 داده‌های جدید در حال پردازش است. به‌زودی تحلیل کامل ارائه خواهد شد. ⏳\n\n#به‌زودی #تحلیل #داده"
        
        # Optional sources, disclaimer, normalization and safe clipping
        if settings.INCLUDE_SOURCES:
            srcs = format_sources((data or {}).get("news"), settings.SOURCES_COUNT)
            if srcs:
                text = text.rstrip() + "\n" + srcs
        if settings.INCLUDE_DISCLAIMER and settings.DISCLAIMER_TEXT:
            text = (text.rstrip() + "\n\n" + settings.DISCLAIMER_TEXT).strip()
        text = normalize_persian(text)
        text = clip_telegram_text(text)
        msg = await bot.send_message(
            chat_id=settings.TELEGRAM_CHANNEL_ID,
            text=text,
            disable_web_page_preview=True,
        )

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
        # Pin management (keep latest pinned)
        if settings.PIN_POSTS:
            try:
                prev = await db.get_setting("PINNED_MSG_ID")
                if prev:
                    try:
                        await bot.unpin_chat_message(chat_id=settings.TELEGRAM_CHANNEL_ID, message_id=int(prev))
                    except Exception:
                        pass
                await bot.pin_chat_message(chat_id=settings.TELEGRAM_CHANNEL_ID, message_id=msg.message_id)
                await db.set_setting("PINNED_MSG_ID", str(msg.message_id))
            except Exception:
                log.warning("pin/unpin failed", exc_info=True)
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


async def intelligent_daily_job(bot: Bot, settings: Settings, db: Database, scheduler=None) -> None:
    """
    Intelligent daily job that creates multiple well-distributed posts throughout the day
    """
    ts = int(datetime.now().timestamp())
    try:
        log.info("🚀 Starting intelligent daily job with multi-posting...")
        
        # Initialize intelligent scheduler
        intelligent_scheduler = IntelligentPostingScheduler(settings)
        
        # Collect all data
        tz = await db.get_setting("TIMEZONE", settings.TIMEZONE) or settings.TIMEZONE
        cache_key = "collect_all_intelligent"
        cached = mcache.get(cache_key)
        if cached is None:
            data = await collect_all(settings)
            mcache.set(cache_key, data, ttl=900)  # 15 minutes
        else:
            data = cached
        
        # Enrich with sentiment and yesterday snapshot
        data["sentiment"] = await analyze_news_sentiment(settings, data.get("news") or [])
        today = now_tz(tz).date()
        yday = type(today).fromordinal(today.toordinal() - 1)
        prev_snapshot = await db.get_snapshot(yday.isoformat())
        if prev_snapshot:
            data["yesterday"] = {"day": yday.isoformat(), "snapshot": prev_snapshot}
        
        # Generate intelligent posting plan
        posting_plan = await intelligent_scheduler.generate_intelligent_posting_plan(data)
        
        log.info(f"📋 Generated posting plan: {posting_plan['total_posts']} posts, strategy: {posting_plan['strategy']}")
        
        # Execute the posting plan
        execution_results = await intelligent_scheduler.execute_intelligent_posting_plan(posting_plan, data)
        
        # Send immediate posts (for testing/demonstration)
        await _execute_immediate_posts(bot, settings, db, posting_plan, data)
        
        # Schedule future posts
        await _schedule_future_posts(bot, settings, db, scheduler, posting_plan, data)
        
        # Record execution
        await db.record_run(ts, "intelligent_ok", "multi", None, None, topic="intelligent_multi", content_hash=f"intelligent_{ts}")
        
        # Send admin report
        await _send_intelligent_admin_report(bot, settings, posting_plan, execution_results)
        
        log.info("✅ Intelligent daily job completed successfully")
        
    except Exception as e:
        log.exception("intelligent_daily_job failed")
        await db.record_run(ts, "intelligent_error", None, None, str(e))
        await bot.send_message(
            chat_id=settings.ADMIN_USER_ID,
            text=f"❌ اجرای هوشمند روزانه با خطا مواجه شد:\n{e}",
        )


async def _execute_immediate_posts(bot: Bot, settings: Settings, db: Database, posting_plan: dict, data: dict) -> None:
    """
    Execute immediate posts (within the next hour)
    """
    try:
        now = datetime.now()
        immediate_posts = [
            post for post in posting_plan["posts"] 
            if (post["scheduled_time"] - now).total_seconds() < 3600  # Next hour
        ]
        
        for post_plan in immediate_posts:
            try:
                # Generate content
                content = await _generate_intelligent_post_content(post_plan, data, settings)
                
                if content:
                    # Send the post
                    msg = await bot.send_message(
                        chat_id=settings.TELEGRAM_CHANNEL_ID,
                        text=content,
                        disable_web_page_preview=True,
                    )
                    
                    log.info(f"✅ Sent immediate post {post_plan['post_id']} ({post_plan['content_type']})")
                    
                    # Record the post
                    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
                    await db.record_run(
                        int(now.timestamp()), 
                        "immediate_ok", 
                        post_plan['content_type'], 
                        msg.message_id, 
                        None, 
                        topic=post_plan['content_type'], 
                        content_hash=content_hash
                    )
                    
            except Exception as e:
                log.error(f"❌ Failed to send immediate post {post_plan['post_id']}: {e}")
                
    except Exception as e:
        log.error(f"Failed to execute immediate posts: {e}")


async def _schedule_future_posts(bot: Bot, settings: Settings, db: Database, scheduler, posting_plan: dict, data: dict) -> None:
    """
    Schedule future posts using the scheduler
    """
    try:
        if not scheduler:
            log.warning("No scheduler available for future posts")
            return
            
        now = datetime.now()
        future_posts = [
            post for post in posting_plan["posts"] 
            if (post["scheduled_time"] - now).total_seconds() >= 3600  # After next hour
        ]
        
        for post_plan in future_posts:
            try:
                # Schedule the post
                job_id = f"intelligent_post_{post_plan['post_id']}_{int(now.timestamp())}"
                
                scheduler.add_job(
                    _send_scheduled_post,
                    'date',
                    run_date=post_plan["scheduled_time"],
                    args=[bot, settings, db, post_plan, data],
                    id=job_id,
                    replace_existing=True
                )
                
                log.info(f"📅 Scheduled post {post_plan['post_id']} for {post_plan['scheduled_time']}")
                
            except Exception as e:
                log.error(f"❌ Failed to schedule post {post_plan['post_id']}: {e}")
                
    except Exception as e:
        log.error(f"Failed to schedule future posts: {e}")


async def _send_scheduled_post(bot: Bot, settings: Settings, db: Database, post_plan: dict, data: dict) -> None:
    """
    Send a scheduled post
    """
    try:
        content = await _generate_intelligent_post_content(post_plan, data, settings)
        
        if content:
            msg = await bot.send_message(
                chat_id=settings.TELEGRAM_CHANNEL_ID,
                text=content,
                disable_web_page_preview=True,
            )
            
            log.info(f"✅ Sent scheduled post {post_plan['post_id']} ({post_plan['content_type']})")
            
            # Record the post
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            await db.record_run(
                int(datetime.now().timestamp()), 
                "scheduled_ok", 
                post_plan['content_type'], 
                msg.message_id, 
                None, 
                topic=post_plan['content_type'], 
                content_hash=content_hash
            )
            
    except Exception as e:
        log.error(f"❌ Failed to send scheduled post {post_plan['post_id']}: {e}")


async def _generate_intelligent_post_content(post_plan: dict, data: dict, settings: Settings) -> str:
    """
    Generate content for an intelligent post
    """
    try:
        content_type = post_plan["content_type"]
        
        # Get base content based on type
        if content_type == "economy" and data.get("crypto"):
            base_content = data["crypto"]
        elif content_type == "sports" and data.get("sports"):
            base_content = data["sports"]
        elif content_type == "trends" and data.get("trends"):
            base_content = data["trends"]
        elif content_type == "insight":
            base_content = "💡 نکته طلایی روز: همیشه قبل از تصمیم‌گیری، تمام گزینه‌ها را بررسی کنید."
        elif content_type == "culture" and data.get("culture"):
            base_content = data["culture"]
        elif content_type == "technology" and data.get("technology"):
            base_content = data["technology"]
        elif content_type == "literature" and data.get("literature"):
            base_content = data["literature"]
        elif content_type == "lifestyle" and data.get("lifestyle"):
            base_content = data["lifestyle"]
        elif content_type == "travel" and data.get("travel"):
            base_content = data["travel"]
        else:
            base_content = f"محتوای {content_type} برای زمان {post_plan['scheduled_time'].strftime('%H:%M')}"
        
        # Apply formatting
        if post_plan.get("formatting_style") == "bold_headers":
            formatted_content = f"**{content_type.upper()}**\n\n{base_content}"
        else:
            formatted_content = base_content
        
        # Add emojis
        if post_plan.get("emoji_usage") == "high":
            emoji_map = {
                "economy": "💰📈",
                "sports": "⚽🏆",
                "trends": "🔥📊",
                "insight": "💡🎯",
                "culture": "🎭📚",
                "technology": "🚀💻",
                "literature": "📖✍️",
                "lifestyle": "🌟💫",
                "travel": "✈️🌍"
            }
            emoji = emoji_map.get(content_type, "📝")
            formatted_content = f"{emoji} {formatted_content}"
        
        # Add engagement elements
        if post_plan.get("engagement_focus") == "peak":
            formatted_content += "\n\n#فردایاب #هوشمند #بهترین_محتوا"
        
        return formatted_content
        
    except Exception as e:
        log.error(f"Failed to generate intelligent post content: {e}")
        return None


async def _send_intelligent_admin_report(bot: Bot, settings: Settings, posting_plan: dict, execution_results: dict) -> None:
    """
    Send admin report for intelligent posting
    """
    try:
        report = f"""🤖 **گزارش هوشمند روزانه**

📊 **آمار کلی:**
• تعداد پست‌ها: {posting_plan['total_posts']}
• استراتژی: {posting_plan['strategy']}
• پیش‌بینی تعامل: {posting_plan['engagement_prediction']:.1%}
• تنوع محتوا: {posting_plan['content_diversity']:.1%}

✅ **نتایج اجرا:**
• پست‌های موفق: {execution_results['successful_posts']}
• پست‌های ناموفق: {execution_results['failed_posts']}
• زمان اجرا: {execution_results['execution_time'].strftime('%H:%M:%S')}

📅 **برنامه پست‌ها:**
"""
        
        for post in posting_plan["posts"]:
            status = "✅" if post["post_id"] <= execution_results['successful_posts'] else "⏳"
            report += f"• {status} پست {post['post_id']}: {post['content_type']} در {post['scheduled_time'].strftime('%H:%M')}\n"
        
        await bot.send_message(
            chat_id=settings.ADMIN_USER_ID,
            text=report
        )
        
    except Exception as e:
        log.error(f"Failed to send intelligent admin report: {e}")
