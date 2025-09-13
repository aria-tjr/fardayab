from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class RetentionStrategy(Enum):
    """User retention strategies"""
    DAILY_VALUE = "daily_value"
    GAMIFICATION = "gamification"
    PERSONALIZATION = "personalization"
    SOCIAL_FEATURES = "social_features"
    EXCLUSIVE_CONTENT = "exclusive_content"
    NOTIFICATIONS = "notifications"


class UserSegment(Enum):
    """User segments for personalization"""
    NEW_USER = "new_user"
    ACTIVE_USER = "active_user"
    ENGAGED_USER = "engaged_user"
    VIP_USER = "vip_user"
    DORMANT_USER = "dormant_user"


class HabitType(Enum):
    """Types of habits to form"""
    DAILY_CHECK = "daily_check"
    CONTENT_SAVE = "content_save"
    COMMENT_INTERACTION = "comment_interaction"
    SHARE_CONTENT = "share_content"
    POLL_PARTICIPATION = "poll_participation"
    QUIZ_PARTICIPATION = "quiz_participation"


@dataclass
class UserProfile:
    """User profile for personalization"""
    user_id: str
    segment: UserSegment
    join_date: datetime
    last_active: datetime
    engagement_score: float
    preferences: Dict[str, Any]
    habits: Dict[HabitType, int]
    streak_count: int
    total_interactions: int
    favorite_topics: List[str]
    optimal_times: List[str]
    retention_risk: float


@dataclass
class RetentionAction:
    """Retention action configuration"""
    action_id: str
    action_type: RetentionStrategy
    title: str
    description: str
    trigger_conditions: Dict[str, Any]
    content: str
    engagement_elements: List[str]
    success_metrics: List[str]
    priority: int


@dataclass
class HabitFormation:
    """Habit formation configuration"""
    habit_type: HabitType
    target_frequency: int  # times per week
    current_frequency: int
    streak_goal: int
    reward_system: Dict[str, Any]
    reminder_frequency: int  # hours
    difficulty_level: str  # "easy", "medium", "hard"


class UserRetentionManager:
    """Advanced user retention and habit formation system"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.user_profiles = {}
        self.retention_actions = self._initialize_retention_actions()
        self.habit_formations = self._initialize_habit_formations()
        self.retention_campaigns = {}
        self.performance_tracking = {}
        
    def _initialize_retention_actions(self) -> List[RetentionAction]:
        """Initialize retention actions based on best practices"""
        return [
            RetentionAction(
                action_id="daily_tip",
                action_type=RetentionStrategy.DAILY_VALUE,
                title="نکته روزانه",
                description="ارائه نکته ارزشمند روزانه",
                trigger_conditions={"user_segment": ["new_user", "active_user"]},
                content="💡 نکته روز: {tip_content}",
                engagement_elements=["💡", "نکته", "روزانه"],
                success_metrics=["views", "saves", "shares"],
                priority=8
            ),
            RetentionAction(
                action_id="exclusive_analysis",
                action_type=RetentionStrategy.EXCLUSIVE_CONTENT,
                title="تحلیل انحصاری",
                description="تحلیل عمیق و انحصاری بازار",
                trigger_conditions={"user_segment": ["engaged_user", "vip_user"]},
                content="🔒 تحلیل انحصاری: {analysis_content}",
                engagement_elements=["🔒", "انحصاری", "تحلیل"],
                success_metrics=["views", "saves", "comments"],
                priority=9
            ),
            RetentionAction(
                action_id="gamification_streak",
                action_type=RetentionStrategy.GAMIFICATION,
                title="چالش استریک",
                description="چالش حفظ استریک روزانه",
                trigger_conditions={"streak_count": {"min": 3, "max": 30}},
                content="🔥 استریک شما: {streak_count} روز! هدف: {streak_goal}",
                engagement_elements=["🔥", "استریک", "چالش"],
                success_metrics=["engagement", "retention"],
                priority=7
            ),
            RetentionAction(
                action_id="personalized_prediction",
                action_type=RetentionStrategy.PERSONALIZATION,
                title="پیش‌بینی شخصی‌سازی شده",
                description="پیش‌بینی بر اساس علایق کاربر",
                trigger_conditions={"favorite_topics": ["bitcoin", "ethereum", "forex"]},
                content="🎯 پیش‌بینی شخصی شما: {prediction_content}",
                engagement_elements=["🎯", "شخصی", "پیش‌بینی"],
                success_metrics=["views", "saves", "comments"],
                priority=8
            ),
            RetentionAction(
                action_id="social_challenge",
                action_type=RetentionStrategy.SOCIAL_FEATURES,
                title="چالش اجتماعی",
                description="چالش تعاملی با سایر کاربران",
                trigger_conditions={"user_segment": ["active_user", "engaged_user"]},
                content="👥 چالش اجتماعی: {challenge_content}",
                engagement_elements=["👥", "چالش", "اجتماعی"],
                success_metrics=["participation", "comments", "shares"],
                priority=6
            ),
            RetentionAction(
                action_id="comeback_offer",
                action_type=RetentionStrategy.NOTIFICATIONS,
                title="پیشنهاد بازگشت",
                description="پیشنهاد ویژه برای کاربران غیرفعال",
                trigger_conditions={"last_active": {"days_ago": {"min": 7, "max": 30}}},
                content="🎁 خوش آمدید! پیشنهاد ویژه: {offer_content}",
                engagement_elements=["🎁", "ویژه", "بازگشت"],
                success_metrics=["re_engagement", "views"],
                priority=9
            )
        ]
    
    def _initialize_habit_formations(self) -> Dict[HabitType, HabitFormation]:
        """Initialize habit formation configurations"""
        return {
            HabitType.DAILY_CHECK: HabitFormation(
                habit_type=HabitType.DAILY_CHECK,
                target_frequency=7,  # daily
                current_frequency=0,
                streak_goal=30,
                reward_system={"streak_5": "نشان استریک 5 روزه", "streak_15": "نشان استریک 15 روزه", "streak_30": "نشان استریک 30 روزه"},
                reminder_frequency=24,  # daily
                difficulty_level="easy"
            ),
            HabitType.CONTENT_SAVE: HabitFormation(
                habit_type=HabitType.CONTENT_SAVE,
                target_frequency=3,  # 3 times per week
                current_frequency=0,
                streak_goal=20,
                reward_system={"saves_10": "نشان ذخیره‌کننده", "saves_50": "نشان کلکسیونر"},
                reminder_frequency=48,  # every 2 days
                difficulty_level="medium"
            ),
            HabitType.COMMENT_INTERACTION: HabitFormation(
                habit_type=HabitType.COMMENT_INTERACTION,
                target_frequency=2,  # 2 times per week
                current_frequency=0,
                streak_goal=15,
                reward_system={"comments_5": "نشان مشارکت‌کننده", "comments_20": "نشان فعال"},
                reminder_frequency=72,  # every 3 days
                difficulty_level="medium"
            ),
            HabitType.SHARE_CONTENT: HabitFormation(
                habit_type=HabitType.SHARE_CONTENT,
                target_frequency=1,  # once per week
                current_frequency=0,
                streak_goal=10,
                reward_system={"shares_5": "نشان اشتراک‌گذار", "shares_15": "نشان سفیر"},
                reminder_frequency=168,  # weekly
                difficulty_level="hard"
            ),
            HabitType.POLL_PARTICIPATION: HabitFormation(
                habit_type=HabitType.POLL_PARTICIPATION,
                target_frequency=2,  # 2 times per week
                current_frequency=0,
                streak_goal=12,
                reward_system={"polls_5": "نشان رأی‌دهنده", "polls_15": "نشان مشارکت‌کننده"},
                reminder_frequency=72,  # every 3 days
                difficulty_level="easy"
            ),
            HabitType.QUIZ_PARTICIPATION: HabitFormation(
                habit_type=HabitType.QUIZ_PARTICIPATION,
                target_frequency=1,  # once per week
                current_frequency=0,
                streak_goal=8,
                reward_system={"quizzes_3": "نشان دانش‌آموز", "quizzes_10": "نشان متخصص"},
                reminder_frequency=168,  # weekly
                difficulty_level="medium"
            )
        }
    
    async def create_user_profile(self, user_id: str, join_date: datetime = None) -> UserProfile:
        """Create a new user profile"""
        if join_date is None:
            join_date = datetime.now()
        
        profile = UserProfile(
            user_id=user_id,
            segment=UserSegment.NEW_USER,
            join_date=join_date,
            last_active=datetime.now(),
            engagement_score=0.0,
            preferences={},
            habits={habit_type: 0 for habit_type in HabitType},
            streak_count=0,
            total_interactions=0,
            favorite_topics=[],
            optimal_times=["08:00", "12:00", "18:00", "20:00"],
            retention_risk=0.5
        )
        
        self.user_profiles[user_id] = profile
        return profile
    
    async def update_user_activity(self, user_id: str, activity_type: str, 
                                 engagement_value: float = 1.0) -> bool:
        """Update user activity and engagement"""
        if user_id not in self.user_profiles:
            await self.create_user_profile(user_id)
        
        profile = self.user_profiles[user_id]
        
        # Update last active
        profile.last_active = datetime.now()
        
        # Update engagement score
        profile.engagement_score = (profile.engagement_score * 0.9) + (engagement_value * 0.1)
        
        # Update total interactions
        profile.total_interactions += 1
        
        # Update habits
        habit_mapping = {
            "view": HabitType.DAILY_CHECK,
            "save": HabitType.CONTENT_SAVE,
            "comment": HabitType.COMMENT_INTERACTION,
            "share": HabitType.SHARE_CONTENT,
            "poll": HabitType.POLL_PARTICIPATION,
            "quiz": HabitType.QUIZ_PARTICIPATION
        }
        
        if activity_type in habit_mapping:
            habit_type = habit_mapping[activity_type]
            profile.habits[habit_type] += 1
        
        # Update user segment
        await self._update_user_segment(profile)
        
        # Update retention risk
        await self._calculate_retention_risk(profile)
        
        return True
    
    async def _update_user_segment(self, profile: UserProfile):
        """Update user segment based on activity"""
        days_since_join = (datetime.now() - profile.join_date).days
        days_since_active = (datetime.now() - profile.last_active).days
        
        if days_since_active > 30:
            profile.segment = UserSegment.DORMANT_USER
        elif profile.engagement_score > 0.8 and profile.total_interactions > 100:
            profile.segment = UserSegment.VIP_USER
        elif profile.engagement_score > 0.6 and profile.total_interactions > 50:
            profile.segment = UserSegment.ENGAGED_USER
        elif profile.engagement_score > 0.3 and profile.total_interactions > 10:
            profile.segment = UserSegment.ACTIVE_USER
        else:
            profile.segment = UserSegment.NEW_USER
    
    async def _calculate_retention_risk(self, profile: UserProfile):
        """Calculate user retention risk"""
        days_since_active = (datetime.now() - profile.last_active).days
        engagement_score = profile.engagement_score
        total_interactions = profile.total_interactions
        
        # Calculate risk factors
        inactivity_risk = min(days_since_active / 30, 1.0)  # 0-1 scale
        engagement_risk = 1.0 - engagement_score  # 0-1 scale
        interaction_risk = max(0, 1.0 - (total_interactions / 100))  # 0-1 scale
        
        # Weighted average
        profile.retention_risk = (inactivity_risk * 0.5) + (engagement_risk * 0.3) + (interaction_risk * 0.2)
    
    async def get_retention_actions(self, user_id: str) -> List[RetentionAction]:
        """Get appropriate retention actions for a user"""
        if user_id not in self.user_profiles:
            await self.create_user_profile(user_id)
        
        profile = self.user_profiles[user_id]
        applicable_actions = []
        
        for action in self.retention_actions:
            if await self._is_action_applicable(action, profile):
                applicable_actions.append(action)
        
        # Sort by priority
        applicable_actions.sort(key=lambda x: x.priority, reverse=True)
        
        return applicable_actions[:3]  # Return top 3 actions
    
    async def _is_action_applicable(self, action: RetentionAction, profile: UserProfile) -> bool:
        """Check if a retention action is applicable to a user"""
        conditions = action.trigger_conditions
        
        # Check user segment
        if "user_segment" in conditions:
            if profile.segment.value not in conditions["user_segment"]:
                return False
        
        # Check streak count
        if "streak_count" in conditions:
            streak_range = conditions["streak_count"]
            if not (streak_range["min"] <= profile.streak_count <= streak_range["max"]):
                return False
        
        # Check favorite topics
        if "favorite_topics" in conditions:
            if not any(topic in profile.favorite_topics for topic in conditions["favorite_topics"]):
                return False
        
        # Check last active
        if "last_active" in conditions:
            days_ago = (datetime.now() - profile.last_active).days
            active_range = conditions["last_active"]["days_ago"]
            if not (active_range["min"] <= days_ago <= active_range["max"]):
                return False
        
        return True
    
    async def generate_retention_content(self, user_id: str, action: RetentionAction) -> str:
        """Generate personalized retention content"""
        if user_id not in self.user_profiles:
            await self.create_user_profile(user_id)
        
        profile = self.user_profiles[user_id]
        
        # Generate content based on action type
        if action.action_type == RetentionStrategy.DAILY_VALUE:
            content = await self._generate_daily_value_content(profile)
        elif action.action_type == RetentionStrategy.EXCLUSIVE_CONTENT:
            content = await self._generate_exclusive_content(profile)
        elif action.action_type == RetentionStrategy.GAMIFICATION:
            content = await self._generate_gamification_content(profile)
        elif action.action_type == RetentionStrategy.PERSONALIZATION:
            content = await self._generate_personalized_content(profile)
        elif action.action_type == RetentionStrategy.SOCIAL_FEATURES:
            content = await self._generate_social_content(profile)
        elif action.action_type == RetentionStrategy.NOTIFICATIONS:
            content = await self._generate_notification_content(profile)
        else:
            content = action.content
        
        # Personalize content
        content = content.format(
            tip_content=await self._get_daily_tip(),
            analysis_content=await self._get_exclusive_analysis(),
            streak_count=profile.streak_count,
            streak_goal=30,
            prediction_content=await self._get_personalized_prediction(profile),
            challenge_content=await self._get_social_challenge(),
            offer_content=await self._get_comeback_offer()
        )
        
        return content
    
    async def _generate_daily_value_content(self, profile: UserProfile) -> str:
        """Generate daily value content"""
        tips = [
            "همیشه قبل از معامله، تحلیل تکنیکال و فاندامنتال را بررسی کنید",
            "تنوع‌بخشی در سبد سرمایه‌گذاری، ریسک را کاهش می‌دهد",
            "احساسات خود را کنترل کنید و بر اساس منطق تصمیم‌گیری کنید",
            "همیشه حد ضرر تعیین کنید تا از ضررهای بزرگ جلوگیری کنید",
            "اخبار و رویدادهای مهم را دنبال کنید تا از تغییرات بازار آگاه باشید"
        ]
        
        tip = random.choice(tips)
        return f"💡 نکته روز: {tip}\n\n💾 این نکته را ذخیره کنید و در معاملات خود به کار ببرید!"
    
    async def _generate_exclusive_content(self, profile: UserProfile) -> str:
        """Generate exclusive content"""
        exclusive_analyses = [
            "تحلیل عمیق الگوی مثلث در نمودار بیت‌کوین و پیش‌بینی حرکت قیمت",
            "بررسی تأثیر اخبار فدرال رزرو بر بازار کریپتو و فرصت‌های معاملاتی",
            "تحلیل فاندامنتال اتریوم و تأثیرات آپدیت‌های اخیر بر قیمت",
            "بررسی الگوهای حجم معاملات و پیش‌بینی روند بازار"
        ]
        
        analysis = random.choice(exclusive_analyses)
        return f"🔒 تحلیل انحصاری: {analysis}\n\n📊 این تحلیل فقط برای کاربران ویژه آماده شده است!"
    
    async def _generate_gamification_content(self, profile: UserProfile) -> str:
        """Generate gamification content"""
        if profile.streak_count >= 30:
            return f"🏆 تبریک! شما 30 روز استریک دارید! شما یک قهرمان واقعی هستید! 🎉"
        elif profile.streak_count >= 15:
            return f"🔥 عالی! {profile.streak_count} روز استریک! فقط {30 - profile.streak_count} روز تا قهرمانی! 💪"
        elif profile.streak_count >= 5:
            return f"⭐ خوب! {profile.streak_count} روز استریک! ادامه دهید! 🚀"
        else:
            return f"🌟 شروع کنید! هدف: 30 روز استریک! شما می‌توانید! 💪"
    
    async def _generate_personalized_content(self, profile: UserProfile) -> str:
        """Generate personalized content"""
        if "bitcoin" in profile.favorite_topics:
            return "🎯 پیش‌بینی شخصی شما: بیت‌کوین در هفته آینده احتمالاً به 100,000 دلار نزدیک خواهد شد! 📈"
        elif "ethereum" in profile.favorite_topics:
            return "🎯 پیش‌بینی شخصی شما: اتریوم با توجه به آپدیت‌های اخیر، رشد مثبتی خواهد داشت! 🚀"
        elif "forex" in profile.favorite_topics:
            return "🎯 پیش‌بینی شخصی شما: جفت ارز EUR/USD احتمالاً در محدوده 1.05-1.10 نوسان خواهد داشت! 💱"
        else:
            return "🎯 پیش‌بینی شخصی شما: بازار کریپتو در هفته آینده نوسانات مثبتی خواهد داشت! 📊"
    
    async def _generate_social_content(self, profile: UserProfile) -> str:
        """Generate social content"""
        challenges = [
            "چالش: پیش‌بینی قیمت بیت‌کوین تا پایان هفته",
            "چالش: انتخاب بهترین ارز دیجیتال برای سرمایه‌گذاری",
            "چالش: تحلیل نمودار اتریوم و پیش‌بینی حرکت بعدی",
            "چالش: مقایسه عملکرد بیت‌کوین و طلا در سال جاری"
        ]
        
        challenge = random.choice(challenges)
        return f"👥 چالش اجتماعی: {challenge}\n\n💬 نظر خود را در کامنت‌ها بنویسید و با دیگران بحث کنید!"
    
    async def _generate_notification_content(self, profile: UserProfile) -> str:
        """Generate notification content"""
        offers = [
            "تحلیل رایگان بازار برای شما",
            "راهنمای معاملات پیشرفته",
            "لیست بهترین فرصت‌های سرمایه‌گذاری",
            "گزارش هفتگی بازار کریپتو"
        ]
        
        offer = random.choice(offers)
        return f"🎁 خوش آمدید! پیشنهاد ویژه: {offer}\n\n📱 این فرصت را از دست ندهید!"
    
    async def _get_daily_tip(self) -> str:
        """Get daily tip content"""
        return "همیشه قبل از معامله، تحلیل تکنیکال و فاندامنتال را بررسی کنید"
    
    async def _get_exclusive_analysis(self) -> str:
        """Get exclusive analysis content"""
        return "تحلیل عمیق الگوی مثلث در نمودار بیت‌کوین و پیش‌بینی حرکت قیمت"
    
    async def _get_personalized_prediction(self, profile: UserProfile) -> str:
        """Get personalized prediction content"""
        return "بیت‌کوین در هفته آینده احتمالاً به 100,000 دلار نزدیک خواهد شد"
    
    async def _get_social_challenge(self) -> str:
        """Get social challenge content"""
        return "چالش: پیش‌بینی قیمت بیت‌کوین تا پایان هفته"
    
    async def _get_comeback_offer(self) -> str:
        """Get comeback offer content"""
        return "تحلیل رایگان بازار برای شما"
    
    async def track_retention_performance(self, user_id: str, action_id: str, 
                                        metrics: Dict[str, Any]) -> bool:
        """Track retention action performance"""
        if user_id not in self.performance_tracking:
            self.performance_tracking[user_id] = {}
        
        if action_id not in self.performance_tracking[user_id]:
            self.performance_tracking[user_id][action_id] = {
                'total_views': 0,
                'total_engagement': 0,
                'success_rate': 0.0,
                'timestamp': datetime.now()
            }
        
        # Update metrics
        tracking = self.performance_tracking[user_id][action_id]
        tracking['total_views'] += metrics.get('views', 0)
        tracking['total_engagement'] += metrics.get('engagement', 0)
        tracking['success_rate'] = tracking['total_engagement'] / max(tracking['total_views'], 1)
        
        return True
    
    async def get_retention_insights(self) -> Dict[str, Any]:
        """Get retention insights and recommendations"""
        insights = {
            'total_users': len(self.user_profiles),
            'user_segments': {},
            'retention_rates': {},
            'top_retention_actions': [],
            'recommendations': []
        }
        
        # Analyze user segments
        for profile in self.user_profiles.values():
            segment = profile.segment.value
            if segment not in insights['user_segments']:
                insights['user_segments'][segment] = 0
            insights['user_segments'][segment] += 1
        
        # Analyze retention rates
        total_users = len(self.user_profiles)
        if total_users > 0:
            for segment, count in insights['user_segments'].items():
                insights['retention_rates'][segment] = count / total_users
        
        # Analyze top retention actions
        action_performance = {}
        for user_id, actions in self.performance_tracking.items():
            for action_id, metrics in actions.items():
                if action_id not in action_performance:
                    action_performance[action_id] = []
                action_performance[action_id].append(metrics['success_rate'])
        
        # Calculate average performance per action
        for action_id, success_rates in action_performance.items():
            if success_rates:
                avg_success = sum(success_rates) / len(success_rates)
                insights['top_retention_actions'].append({
                    'action_id': action_id,
                    'avg_success_rate': avg_success,
                    'usage_count': len(success_rates)
                })
        
        # Sort by success rate
        insights['top_retention_actions'].sort(key=lambda x: x['avg_success_rate'], reverse=True)
        
        # Generate recommendations
        if insights['user_segments'].get('dormant_user', 0) > total_users * 0.3:
            insights['recommendations'].append("High dormant user rate - implement comeback campaigns")
        
        if insights['user_segments'].get('new_user', 0) > total_users * 0.5:
            insights['recommendations'].append("Many new users - focus on onboarding and daily value")
        
        if insights['top_retention_actions']:
            best_action = insights['top_retention_actions'][0]
            insights['recommendations'].append(f"Focus on {best_action['action_id']} - highest success rate")
        
        return insights
