from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from telegram_bot.config.settings import Settings
from telegram_bot.ai.intelligent_curator import IntelligentContentCurator
from telegram_bot.ai.persian_processor import AdvancedPersianProcessor

log = logging.getLogger(__name__)


class IntelligentPostingScheduler:
    """AI-powered intelligent posting scheduler for optimal engagement"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.curator = IntelligentContentCurator(settings)
        self.processor = AdvancedPersianProcessor(settings)
        self.posting_history = []
        self.engagement_data = {}
        self.optimal_times = []
        
    async def calculate_optimal_posting_schedule(self, content_types: List[str]) -> List[Dict[str, Any]]:
        """Calculate optimal posting schedule based on content types and audience patterns"""
        try:
            # Get optimal times for Persian audience
            optimal_times = await self.curator.get_optimal_posting_times()
            
            # Calculate schedule for next 24 hours
            schedule = []
            current_time = datetime.now()
            
            for hour, minute in optimal_times:
                # Calculate next occurrence of this time
                next_post_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_post_time <= current_time:
                    next_post_time += timedelta(days=1)
                
                # Select best content type for this time
                best_content_type = await self._select_best_content_for_time(hour, content_types)
                
                # Calculate engagement prediction
                engagement_prediction = await self._predict_engagement(hour, best_content_type)
                
                schedule.append({
                    'post_time': next_post_time,
                    'content_type': best_content_type,
                    'engagement_prediction': engagement_prediction,
                    'priority': self._calculate_priority(hour, best_content_type),
                    'optimization_tips': await self._get_optimization_tips(best_content_type, hour)
                })
            
            # Sort by priority and engagement prediction
            schedule.sort(key=lambda x: (x['priority'], x['engagement_prediction']), reverse=True)
            
            return schedule[:5]  # Return top 5 optimal times
            
        except Exception as e:
            log.error(f"Optimal schedule calculation failed: {e}")
            return []
    
    async def _select_best_content_for_time(self, hour: int, content_types: List[str]) -> str:
        """Select best content type for specific hour"""
        try:
            # Time-based content preferences
            time_preferences = {
                8: ['economy', 'news', 'trends'],      # Morning: Economy and news
                12: ['sports', 'culture', 'lifestyle'], # Lunch: Sports and culture
                16: ['trends', 'technology', 'travel'], # Afternoon: Trends and tech
                20: ['sports', 'literature', 'insight'], # Evening: Sports and literature
                22: ['insight', 'culture', 'lifestyle']  # Night: Insight and culture
            }
            
            # Get preferences for this hour
            preferred_types = time_preferences.get(hour, content_types)
            
            # Find intersection with available content types
            available_preferred = [ct for ct in preferred_types if ct in content_types]
            
            if available_preferred:
                return available_preferred[0]
            else:
                return content_types[0] if content_types else 'insight'
                
        except Exception as e:
            log.error(f"Content type selection failed: {e}")
            return 'insight'
    
    async def _predict_engagement(self, hour: int, content_type: str) -> float:
        """Predict engagement score for specific time and content type"""
        try:
            # Base engagement scores by hour
            hour_scores = {
                8: 0.8,   # Morning news
                12: 0.7,  # Lunch break
                16: 0.6,  # Afternoon
                20: 0.9,  # Evening peak
                22: 0.8,  # Night reading
            }
            
            # Content type engagement multipliers
            content_multipliers = {
                'economy': 0.9,
                'sports': 1.0,
                'trends': 0.8,
                'culture': 0.7,
                'technology': 0.8,
                'literature': 0.6,
                'lifestyle': 0.7,
                'travel': 0.6,
                'insight': 0.9,
            }
            
            base_score = hour_scores.get(hour, 0.5)
            content_multiplier = content_multipliers.get(content_type, 0.5)
            
            # Add some randomness for realistic prediction
            import random
            random_factor = random.uniform(0.9, 1.1)
            
            return min(1.0, base_score * content_multiplier * random_factor)
            
        except Exception as e:
            log.error(f"Engagement prediction failed: {e}")
            return 0.5
    
    def _calculate_priority(self, hour: int, content_type: str) -> float:
        """Calculate priority score for posting"""
        try:
            # Time-based priority
            time_priority = {
                8: 0.9,   # High priority for morning
                12: 0.7,  # Medium priority for lunch
                16: 0.6,  # Lower priority for afternoon
                20: 1.0,  # Highest priority for evening
                22: 0.8,  # High priority for night
            }
            
            # Content type priority
            content_priority = {
                'economy': 1.0,
                'sports': 0.9,
                'trends': 0.8,
                'insight': 0.9,
                'culture': 0.7,
                'technology': 0.8,
                'literature': 0.6,
                'lifestyle': 0.7,
                'travel': 0.6,
            }
            
            time_score = time_priority.get(hour, 0.5)
            content_score = content_priority.get(content_type, 0.5)
            
            return (time_score + content_score) / 2
            
        except Exception as e:
            log.error(f"Priority calculation failed: {e}")
            return 0.5
    
    async def _get_optimization_tips(self, content_type: str, hour: int) -> List[str]:
        """Get optimization tips for specific content type and time"""
        try:
            tips = []
            
            # Content type specific tips
            content_tips = {
                'economy': [
                    "از نمودارها و آمار استفاده کنید",
                    "پیش‌بینی‌های کوتاه و دقیق ارائه دهید",
                    "مقایسه با روز قبل اضافه کنید"
                ],
                'sports': [
                    "مسابقات مهم را برجسته کنید",
                    "آمار تیم‌ها را ذکر کنید",
                    "پیش‌بینی‌های جذاب ارائه دهید"
                ],
                'trends': [
                    "هشتگ‌های داغ را لیست کنید",
                    "توضیح دهید چرا مهم هستند",
                    "سوال تعاملی اضافه کنید"
                ],
                'culture': [
                    "از تصاویر و ویدیوها استفاده کنید",
                    "نظر شخصی اضافه کنید",
                    "مخاطبان را به بحث دعوت کنید"
                ],
                'technology': [
                    "توضیحات ساده ارائه دهید",
                    "مثال‌های عملی ذکر کنید",
                    "آینده‌نگری کنید"
                ],
                'literature': [
                    "شعر یا نقل قول اضافه کنید",
                    "تحلیل ادبی ارائه دهید",
                    "مخاطبان را به خواندن دعوت کنید"
                ],
                'lifestyle': [
                    "نکات عملی ارائه دهید",
                    "از تجربیات شخصی استفاده کنید",
                    "مخاطبان را به اشتراک‌گذاری دعوت کنید"
                ],
                'travel': [
                    "تصاویر زیبا اضافه کنید",
                    "راهنمای عملی ارائه دهید",
                    "تجربیات شخصی ذکر کنید"
                ],
                'insight': [
                    "نکته کوتاه و مفید ارائه دهید",
                    "مثال عملی اضافه کنید",
                    "مخاطبان را به فکر وادارید"
                ]
            }
            
            tips.extend(content_tips.get(content_type, []))
            
            # Time-specific tips
            if 8 <= hour <= 10:
                tips.append("محتوا را کوتاه و مختصر نگه دارید (صبح)")
            elif 12 <= hour <= 14:
                tips.append("از محتوای تعاملی استفاده کنید (ظهر)")
            elif 18 <= hour <= 22:
                tips.append("محتوا را جذاب و سرگرم‌کننده کنید (شب)")
            
            return tips[:3]  # Return top 3 tips
            
        except Exception as e:
            log.error(f"Optimization tips failed: {e}")
            return ["محتوا را جذاب و مفید نگه دارید"]
    
    async def schedule_intelligent_posts(self, bot, db, available_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Schedule intelligent posts based on optimal timing and content"""
        try:
            # Get available content types
            content_types = [key for key, value in available_content.items() if value]
            
            # Calculate optimal schedule
            schedule = await self.calculate_optimal_posting_schedule(content_types)
            
            # Process and schedule posts
            scheduled_posts = []
            
            for post_info in schedule:
                try:
                    # Get content for this type
                    content_type = post_info['content_type']
                    content_data = available_content.get(content_type, {})
                    
                    if not content_data:
                        continue
                    
                    # Generate optimized content
                    optimized_content = await self._generate_optimized_content(
                        content_type, content_data, post_info
                    )
                    
                    # Schedule the post
                    scheduled_post = {
                        'post_time': post_info['post_time'],
                        'content_type': content_type,
                        'content': optimized_content,
                        'engagement_prediction': post_info['engagement_prediction'],
                        'priority': post_info['priority'],
                        'optimization_tips': post_info['optimization_tips']
                    }
                    
                    scheduled_posts.append(scheduled_post)
                    
                except Exception as e:
                    log.error(f"Failed to schedule post for {post_info['content_type']}: {e}")
                    continue
            
            return scheduled_posts
            
        except Exception as e:
            log.error(f"Intelligent post scheduling failed: {e}")
            return []
    
    async def _generate_optimized_content(self, content_type: str, content_data: Any, post_info: Dict[str, Any]) -> str:
        """Generate optimized content for specific type and timing"""
        try:
            # This would integrate with your existing content generation
            # For now, return a placeholder
            base_content = f"محتوا برای {content_type} در ساعت {post_info['post_time'].hour}"
            
            # Apply Persian processing and optimization
            processed_content = await self.processor.enhance_content_for_engagement(base_content)
            
            # Apply time-specific optimizations
            hour = post_info['post_time'].hour'
            if 8 <= hour <= 10:
                processed_content = "🌅 صبح بخیر! " + processed_content
            elif 18 <= hour <= 22:
                processed_content = "🌙 عصر بخیر! " + processed_content
            
            return processed_content
            
        except Exception as e:
            log.error(f"Content generation failed: {e}")
            return f"محتوا برای {content_type}"
    
    async def analyze_posting_performance(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze posting performance and update strategies"""
        try:
            # Analyze engagement data
            analysis = await self.curator.analyze_content_performance(
                post_data.get('content', ''),
                post_data.get('engagement_data', {})
            )
            
            # Update posting history
            self.posting_history.append({
                'timestamp': datetime.now().isoformat(),
                'content_type': post_data.get('content_type', ''),
                'analysis': analysis
            })
            
            # Keep only last 100 posts
            if len(self.posting_history) > 100:
                self.posting_history = self.posting_history[-100:]
            
            return analysis
            
        except Exception as e:
            log.error(f"Performance analysis failed: {e}")
            return {}
    
    async def get_posting_recommendations(self) -> Dict[str, Any]:
        """Get intelligent posting recommendations"""
        try:
            # Analyze recent performance
            recent_posts = self.posting_history[-10:] if self.posting_history else []
            
            # Calculate performance metrics
            avg_engagement = 0
            best_content_types = []
            best_posting_times = []
            
            if recent_posts:
                engagements = [post['analysis'].get('engagement_score', 0) for post in recent_posts]
                avg_engagement = sum(engagements) / len(engagements)
                
                # Find best performing content types
                content_type_performance = {}
                for post in recent_posts:
                    content_type = post['content_type']
                    engagement = post['analysis'].get('engagement_score', 0)
                    if content_type not in content_type_performance:
                        content_type_performance[content_type] = []
                    content_type_performance[content_type].append(engagement)
                
                # Calculate averages
                for content_type, scores in content_type_performance.items():
                    avg_score = sum(scores) / len(scores)
                    if avg_score > avg_engagement:
                        best_content_types.append(content_type)
            
            # Get optimal posting times
            optimal_times = await self.curator.get_optimal_posting_times()
            
            return {
                'average_engagement': avg_engagement,
                'best_content_types': best_content_types,
                'optimal_posting_times': optimal_times,
                'total_posts_analyzed': len(self.posting_history),
                'recommendations': await self._get_specific_recommendations(recent_posts)
            }
            
        except Exception as e:
            log.error(f"Posting recommendations failed: {e}")
            return {}
    
    async def _get_specific_recommendations(self, recent_posts: List[Dict[str, Any]]) -> List[str]:
        """Get specific recommendations based on recent performance"""
        try:
            recommendations = []
            
            if not recent_posts:
                return ["شروع به ارسال محتوا کنید تا تحلیل‌های دقیق‌تری دریافت کنید"]
            
            # Analyze engagement trends
            recent_engagements = [post['analysis'].get('engagement_score', 0) for post in recent_posts]
            
            if len(recent_engagements) >= 3:
                trend = recent_engagements[-1] - recent_engagements[0]
                if trend > 0.5:
                    recommendations.append("روند تعامل در حال بهبود است - همین مسیر را ادامه دهید")
                elif trend < -0.5:
                    recommendations.append("روند تعامل در حال کاهش است - استراتژی را تغییر دهید")
            
            # Content type recommendations
            content_type_scores = {}
            for post in recent_posts:
                content_type = post['content_type']
                engagement = post['analysis'].get('engagement_score', 0)
                if content_type not in content_type_scores:
                    content_type_scores[content_type] = []
                content_type_scores[content_type].append(engagement)
            
            # Find best and worst performing types
            avg_scores = {ct: sum(scores)/len(scores) for ct, scores in content_type_scores.items()}
            best_type = max(avg_scores.items(), key=lambda x: x[1])
            worst_type = min(avg_scores.items(), key=lambda x: x[1])
            
            recommendations.append(f"محتوای {best_type[0]} بهترین عملکرد را دارد")
            recommendations.append(f"محتوای {worst_type[0]} نیاز به بهبود دارد")
            
            return recommendations[:5]  # Return top 5 recommendations
            
        except Exception as e:
            log.error(f"Specific recommendations failed: {e}")
            return ["محتوا را به طور مداوم بهبود دهید"]
