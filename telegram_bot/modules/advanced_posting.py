from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class PostType(Enum):
    """Types of posts for different engagement strategies"""
    BREAKING_NEWS = "breaking_news"
    ANALYSIS = "analysis"
    EDUCATIONAL = "educational"
    MARKET_UPDATE = "market_update"
    PREDICTION = "prediction"
    ALERT = "alert"
    POLL = "poll"
    QUIZ = "quiz"
    TIP = "tip"
    RECAP = "recap"


class EngagementLevel(Enum):
    """Engagement levels for content optimization"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PostingStrategy:
    """Advanced posting strategy configuration"""
    post_type: PostType
    optimal_times: List[str]  # Best posting times
    engagement_hooks: List[str]  # Engagement triggers
    visual_elements: List[str]  # Visual components
    call_to_action: str  # CTA for engagement
    hashtags: List[str]  # Relevant hashtags
    priority: int  # 1-10 priority level
    max_frequency: int  # Max posts per day
    min_interval: int  # Min minutes between posts


@dataclass
class ContentTemplate:
    """Template for different content types"""
    template_id: str
    name: str
    structure: str
    engagement_elements: List[str]
    visual_requirements: List[str]
    success_metrics: List[str]


class AdvancedPostingManager:
    """Advanced posting manager based on top channel strategies"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.posting_strategies = self._initialize_strategies()
        self.content_templates = self._initialize_templates()
        self.engagement_history = {}
        self.performance_metrics = {}
        
    def _initialize_strategies(self) -> Dict[PostType, PostingStrategy]:
        """Initialize posting strategies based on top channel analysis"""
        return {
            PostType.BREAKING_NEWS: PostingStrategy(
                post_type=PostType.BREAKING_NEWS,
                optimal_times=["08:00", "12:00", "18:00", "22:00"],
                engagement_hooks=["🚨", "BREAKING", "فوری", "تازه‌ترین"],
                visual_elements=["chart", "image", "gif"],
                call_to_action="نظر شما چیست؟",
                hashtags=["#فوری", "#بازار", "#کریپتو", "#فارکس"],
                priority=10,
                max_frequency=5,
                min_interval=30
            ),
            PostType.ANALYSIS: PostingStrategy(
                post_type=PostType.ANALYSIS,
                optimal_times=["09:00", "15:00", "20:00"],
                engagement_hooks=["📊", "تحلیل", "بررسی", "نگاه کارشناسی"],
                visual_elements=["chart", "infographic", "table"],
                call_to_action="آیا با این تحلیل موافقید؟",
                hashtags=["#تحلیل", "#تکنیکال", "#فاندامنتال", "#بازار"],
                priority=8,
                max_frequency=3,
                min_interval=120
            ),
            PostType.EDUCATIONAL: PostingStrategy(
                post_type=PostType.EDUCATIONAL,
                optimal_times=["10:00", "16:00", "21:00"],
                engagement_hooks=["📚", "آموزش", "نکته", "راهنما"],
                visual_elements=["infographic", "diagram", "step_by_step"],
                call_to_action="سوالی دارید؟ بپرسید!",
                hashtags=["#آموزش", "#نکته", "#راهنما", "#معاملات"],
                priority=7,
                max_frequency=2,
                min_interval=180
            ),
            PostType.MARKET_UPDATE: PostingStrategy(
                post_type=PostType.MARKET_UPDATE,
                optimal_times=["08:30", "12:30", "18:30", "23:00"],
                engagement_hooks=["📈", "به‌روزرسانی", "وضعیت بازار", "آخرین قیمت‌ها"],
                visual_elements=["chart", "price_table", "trend_line"],
                call_to_action="کدام ارز را دنبال می‌کنید؟",
                hashtags=["#بازار", "#قیمت", "#به‌روزرسانی", "#کریپتو"],
                priority=9,
                max_frequency=4,
                min_interval=60
            ),
            PostType.PREDICTION: PostingStrategy(
                post_type=PostType.PREDICTION,
                optimal_times=["09:30", "14:00", "19:00"],
                engagement_hooks=["🔮", "پیش‌بینی", "تحلیل آینده", "سناریو"],
                visual_elements=["prediction_chart", "scenario_diagram"],
                call_to_action="پیش‌بینی شما چیست؟",
                hashtags=["#پیش‌بینی", "#آینده", "#تحلیل", "#بازار"],
                priority=8,
                max_frequency=2,
                min_interval=240
            ),
            PostType.ALERT: PostingStrategy(
                post_type=PostType.ALERT,
                optimal_times=["any"],  # Anytime for alerts
                engagement_hooks=["⚠️", "هشدار", "توجه", "مهم"],
                visual_elements=["alert_icon", "warning_banner"],
                call_to_action="آیا این هشدار را دریافت کردید؟",
                hashtags=["#هشدار", "#توجه", "#مهم", "#بازار"],
                priority=10,
                max_frequency=10,
                min_interval=15
            ),
            PostType.POLL: PostingStrategy(
                post_type=PostType.POLL,
                optimal_times=["11:00", "17:00", "21:30"],
                engagement_hooks=["🗳️", "نظرسنجی", "رأی‌گیری", "نظر شما"],
                visual_elements=["poll_chart", "options_display"],
                call_to_action="رأی خود را ثبت کنید",
                hashtags=["#نظرسنجی", "#رأی", "#نظر", "#مشارکت"],
                priority=6,
                max_frequency=2,
                min_interval=360
            ),
            PostType.QUIZ: PostingStrategy(
                post_type=PostType.QUIZ,
                optimal_times=["12:00", "18:00"],
                engagement_hooks=["🧠", "سوال", "چالش", "آزمون"],
                visual_elements=["question_display", "answer_options"],
                call_to_action="پاسخ خود را بدهید",
                hashtags=["#سوال", "#چالش", "#آزمون", "#دانش"],
                priority=5,
                max_frequency=1,
                min_interval=720
            ),
            PostType.TIP: PostingStrategy(
                post_type=PostType.TIP,
                optimal_times=["08:00", "13:00", "19:00"],
                engagement_hooks=["💡", "نکته", "راهنمایی", "توصیه"],
                visual_elements=["tip_icon", "highlight_box"],
                call_to_action="این نکته را ذخیره کنید",
                hashtags=["#نکته", "#راهنمایی", "#توصیه", "#معاملات"],
                priority=6,
                max_frequency=3,
                min_interval=120
            ),
            PostType.RECAP: PostingStrategy(
                post_type=PostType.RECAP,
                optimal_times=["23:30"],
                engagement_hooks=["📋", "خلاصه", "مرور", "جمع‌بندی"],
                visual_elements=["summary_chart", "timeline"],
                call_to_action="نظرتان درباره امروز چیست؟",
                hashtags=["#خلاصه", "#مرور", "#جمع‌بندی", "#روزانه"],
                priority=7,
                max_frequency=1,
                min_interval=1440
            )
        }
    
    def _initialize_templates(self) -> Dict[str, ContentTemplate]:
        """Initialize content templates for different post types"""
        return {
            "breaking_news": ContentTemplate(
                template_id="breaking_news",
                name="خبر فوری",
                structure="🚨 {title}\n\n{content}\n\n📊 {data}\n\n💬 {cta}",
                engagement_elements=["emoji", "urgency", "data", "cta"],
                visual_requirements=["chart", "image"],
                success_metrics=["views", "shares", "comments"]
            ),
            "analysis": ContentTemplate(
                template_id="analysis",
                name="تحلیل بازار",
                structure="📊 تحلیل {market}\n\n{analysis}\n\n📈 {prediction}\n\n❓ {cta}",
                engagement_elements=["data", "analysis", "prediction", "question"],
                visual_requirements=["chart", "infographic"],
                success_metrics=["views", "saves", "comments"]
            ),
            "educational": ContentTemplate(
                template_id="educational",
                name="آموزش",
                structure="📚 {topic}\n\n{content}\n\n💡 نکته: {tip}\n\n❓ {cta}",
                engagement_elements=["topic", "content", "tip", "question"],
                visual_requirements=["infographic", "diagram"],
                success_metrics=["saves", "shares", "comments"]
            ),
            "market_update": ContentTemplate(
                template_id="market_update",
                name="به‌روزرسانی بازار",
                structure="📈 وضعیت بازار\n\n{market_data}\n\n📊 {chart}\n\n💬 {cta}",
                engagement_elements=["data", "chart", "cta"],
                visual_requirements=["chart", "price_table"],
                success_metrics=["views", "shares"]
            ),
            "prediction": ContentTemplate(
                template_id="prediction",
                name="پیش‌بینی",
                structure="🔮 پیش‌بینی {timeframe}\n\n{prediction}\n\n📊 {confidence}\n\n❓ {cta}",
                engagement_elements=["prediction", "confidence", "question"],
                visual_requirements=["prediction_chart"],
                success_metrics=["views", "saves", "comments"]
            ),
            "poll": ContentTemplate(
                template_id="poll",
                name="نظرسنجی",
                structure="🗳️ {question}\n\n{options}\n\n💬 {cta}",
                engagement_elements=["question", "options", "cta"],
                visual_requirements=["poll_display"],
                success_metrics=["votes", "comments"]
            ),
            "quiz": ContentTemplate(
                template_id="quiz",
                name="سوال و جواب",
                structure="🧠 {question}\n\n{options}\n\n💡 {hint}\n\n❓ {cta}",
                engagement_elements=["question", "options", "hint", "cta"],
                visual_requirements=["question_display"],
                success_metrics=["answers", "comments"]
            ),
            "tip": ContentTemplate(
                template_id="tip",
                name="نکته روز",
                structure="💡 نکته روز\n\n{tip}\n\n📚 {explanation}\n\n💾 {cta}",
                engagement_elements=["tip", "explanation", "cta"],
                visual_requirements=["tip_icon"],
                success_metrics=["saves", "shares"]
            ),
            "recap": ContentTemplate(
                template_id="recap",
                name="خلاصه روز",
                structure="📋 خلاصه {date}\n\n{summary}\n\n📊 {highlights}\n\n💬 {cta}",
                engagement_elements=["summary", "highlights", "cta"],
                visual_requirements=["summary_chart"],
                success_metrics=["views", "saves", "comments"]
            )
        }
    
    async def get_optimal_posting_time(self, post_type: PostType) -> str:
        """Get optimal posting time based on strategy and engagement history"""
        strategy = self.posting_strategies[post_type]
        
        # Consider engagement history for this post type
        if post_type in self.engagement_history:
            best_times = self.engagement_history[post_type].get('best_times', strategy.optimal_times)
        else:
            best_times = strategy.optimal_times
        
        # Return random optimal time to avoid predictability
        return random.choice(best_times)
    
    async def generate_engagement_hooks(self, post_type: PostType, content: str) -> List[str]:
        """Generate engagement hooks based on content and strategy"""
        strategy = self.posting_strategies[post_type]
        hooks = []
        
        # Add strategy-specific hooks
        hooks.extend(strategy.engagement_hooks)
        
        # Add content-based hooks
        if "bitcoin" in content.lower() or "بیت‌کوین" in content:
            hooks.extend(["₿", "Bitcoin", "بیت‌کوین"])
        
        if "ethereum" in content.lower() or "اتریوم" in content:
            hooks.extend(["Ξ", "Ethereum", "اتریوم"])
        
        if "price" in content.lower() or "قیمت" in content:
            hooks.extend(["💰", "Price", "قیمت"])
        
        if "analysis" in content.lower() or "تحلیل" in content:
            hooks.extend(["📊", "Analysis", "تحلیل"])
        
        return hooks[:3]  # Return top 3 hooks
    
    async def create_visual_elements(self, post_type: PostType, content: str) -> List[str]:
        """Create visual elements based on content and strategy"""
        strategy = self.posting_strategies[post_type]
        visuals = []
        
        # Add strategy-specific visuals
        visuals.extend(strategy.visual_elements)
        
        # Add content-based visuals
        if "chart" in content.lower() or "نمودار" in content:
            visuals.append("chart")
        
        if "table" in content.lower() or "جدول" in content:
            visuals.append("table")
        
        if "image" in content.lower() or "تصویر" in content:
            visuals.append("image")
        
        return list(set(visuals))  # Remove duplicates
    
    async def generate_hashtags(self, post_type: PostType, content: str) -> List[str]:
        """Generate relevant hashtags based on content and strategy"""
        strategy = self.posting_strategies[post_type]
        hashtags = []
        
        # Add strategy-specific hashtags
        hashtags.extend(strategy.hashtags)
        
        # Add content-based hashtags
        content_lower = content.lower()
        
        if "crypto" in content_lower or "کریپتو" in content:
            hashtags.extend(["#کریپتو", "#ارز_دیجیتال", "#بلاک_چین"])
        
        if "forex" in content_lower or "فارکس" in content:
            hashtags.extend(["#فارکس", "#ارز", "#معاملات"])
        
        if "trading" in content_lower or "معاملات" in content:
            hashtags.extend(["#معاملات", "#ترید", "#سرمایه_گذاری"])
        
        if "news" in content_lower or "خبر" in content:
            hashtags.extend(["#خبر", "#اخبار", "#به‌روزرسانی"])
        
        # Remove duplicates and limit to 5 hashtags
        return list(set(hashtags))[:5]
    
    async def create_call_to_action(self, post_type: PostType, content: str) -> str:
        """Create effective call-to-action based on post type and content"""
        strategy = self.posting_strategies[post_type]
        
        # Use strategy CTA as base
        cta = strategy.call_to_action
        
        # Customize based on content
        if "question" in content.lower() or "سوال" in content:
            cta = "پاسخ خود را در کامنت‌ها بنویسید"
        elif "prediction" in content.lower() or "پیش‌بینی" in content:
            cta = "پیش‌بینی شما چیست؟"
        elif "analysis" in content.lower() or "تحلیل" in content:
            cta = "آیا با این تحلیل موافقید؟"
        elif "tip" in content.lower() or "نکته" in content:
            cta = "این نکته را ذخیره کنید"
        
        return cta
    
    async def optimize_content_for_engagement(self, content: str, post_type: PostType) -> str:
        """Optimize content for maximum engagement"""
        # Add engagement hooks
        hooks = await self.generate_engagement_hooks(post_type, content)
        if hooks:
            content = f"{hooks[0]} {content}"
        
        # Add visual elements indicators
        visuals = await self.create_visual_elements(post_type, content)
        if "chart" in visuals:
            content += "\n\n📊 [نمودار در ادامه]"
        if "image" in visuals:
            content += "\n\n🖼️ [تصویر مرتبط]"
        
        # Add call to action
        cta = await self.create_call_to_action(post_type, content)
        content += f"\n\n💬 {cta}"
        
        # Add hashtags
        hashtags = await self.generate_hashtags(post_type, content)
        if hashtags:
            content += f"\n\n{' '.join(hashtags)}"
        
        return content
    
    async def get_posting_schedule(self, date: datetime) -> List[Dict[str, Any]]:
        """Generate optimal posting schedule for a date"""
        schedule = []
        
        for post_type, strategy in self.posting_strategies.items():
            if strategy.max_frequency > 0:
                for i in range(strategy.max_frequency):
                    optimal_time = await self.get_optimal_posting_time(post_type)
                    schedule.append({
                        "post_type": post_type,
                        "scheduled_time": optimal_time,
                        "priority": strategy.priority,
                        "template": self.content_templates.get(f"{post_type.value}", None),
                        "strategy": strategy
                    })
        
        # Sort by priority and time
        schedule.sort(key=lambda x: (x["priority"], x["scheduled_time"]), reverse=True)
        
        return schedule
    
    async def track_engagement(self, post_type: PostType, metrics: Dict[str, Any]):
        """Track engagement metrics for optimization"""
        if post_type not in self.engagement_history:
            self.engagement_history[post_type] = {
                "total_posts": 0,
                "total_views": 0,
                "total_engagement": 0,
                "best_times": [],
                "best_hooks": [],
                "performance": []
            }
        
        history = self.engagement_history[post_type]
        history["total_posts"] += 1
        history["total_views"] += metrics.get("views", 0)
        history["total_engagement"] += metrics.get("engagement", 0)
        
        # Track performance
        performance = {
            "timestamp": datetime.now(),
            "metrics": metrics,
            "engagement_rate": metrics.get("engagement", 0) / max(metrics.get("views", 1), 1)
        }
        history["performance"].append(performance)
        
        # Keep only last 100 performance records
        if len(history["performance"]) > 100:
            history["performance"] = history["performance"][-100:]
    
    async def get_performance_insights(self) -> Dict[str, Any]:
        """Get performance insights for optimization"""
        insights = {
            "top_performing_types": [],
            "best_posting_times": [],
            "engagement_trends": {},
            "recommendations": []
        }
        
        for post_type, history in self.engagement_history.items():
            if history["total_posts"] > 0:
                avg_engagement = history["total_engagement"] / history["total_posts"]
                insights["top_performing_types"].append({
                    "type": post_type.value,
                    "avg_engagement": avg_engagement,
                    "total_posts": history["total_posts"]
                })
        
        # Sort by average engagement
        insights["top_performing_types"].sort(key=lambda x: x["avg_engagement"], reverse=True)
        
        return insights
    
    async def generate_content_variants(self, base_content: str, post_type: PostType) -> List[str]:
        """Generate multiple content variants for A/B testing"""
        variants = [base_content]
        
        # Create variants with different engagement hooks
        hooks = await self.generate_engagement_hooks(post_type, base_content)
        if len(hooks) > 1:
            for hook in hooks[1:]:
                variant = f"{hook} {base_content}"
                variants.append(variant)
        
        # Create variants with different CTAs
        cta_variants = [
            "نظر شما چیست؟",
            "آیا موافقید؟",
            "تجربه خود را به اشتراک بگذارید",
            "سوالی دارید؟"
        ]
        
        for cta in cta_variants[:2]:  # Limit to 2 CTA variants
            variant = base_content.replace(await self.create_call_to_action(post_type, base_content), cta)
            variants.append(variant)
        
        return variants[:5]  # Return max 5 variants
