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
    
    async def get_optimal_posting_times(self) -> List[datetime]:
        """
        Get optimal posting times for maximum engagement
        """
        try:
            # Get optimal times from curator
            optimal_times = await self.curator.get_optimal_posting_times()
            
            # Convert to datetime objects for today
            now = datetime.now()
            times = []
            
            for hour, minute in optimal_times:
                post_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if post_time <= now:
                    post_time += timedelta(days=1)
                times.append(post_time)
            
            # Sort by time
            times.sort()
            return times
            
        except Exception as e:
            log.error(f"Failed to get optimal posting times: {e}")
            # Fallback to default times
            now = datetime.now()
            default_times = [
                now.replace(hour=8, minute=0, second=0, microsecond=0),
                now.replace(hour=14, minute=0, second=0, microsecond=0),
                now.replace(hour=18, minute=0, second=0, microsecond=0),
                now.replace(hour=21, minute=0, second=0, microsecond=0),
            ]
            return [t for t in default_times if t > now]
        
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
            hour = post_info['post_time'].hour
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
    
    async def generate_intelligent_posting_plan(self, content_data: dict) -> dict:
        """
        Generate an intelligent multi-posting plan for the day
        """
        try:
            log.info("🎯 Generating intelligent multi-posting plan...")
            
            # Get optimal posting times
            optimal_times = await self.get_optimal_posting_times()
            
            # Analyze content variety and quality
            content_analysis = await self._analyze_content_for_posting(content_data)
            
            # Generate posting schedule
            posting_plan = {
                "total_posts": min(6, max(3, content_analysis.get("recommended_posts", 4))),
                "posts": [],
                "strategy": "intelligent_distribution",
                "engagement_prediction": content_analysis.get("engagement_score", 0.7),
                "content_diversity": content_analysis.get("diversity_score", 0.8)
            }
            
            # Create individual post plans
            for i in range(posting_plan["total_posts"]):
                post_time = optimal_times[i % len(optimal_times)]
                content_type = self._select_content_type_for_time(post_time, i)
                
                post_plan = {
                    "post_id": i + 1,
                    "scheduled_time": post_time,
                    "content_type": content_type,
                    "priority": "high" if i < 2 else "medium",
                    "engagement_focus": "peak" if i < 3 else "sustained",
                    "emoji_usage": "high" if i % 2 == 0 else "moderate",
                    "formatting_style": "bold_headers" if i < 4 else "standard"
                }
                
                posting_plan["posts"].append(post_plan)
            
            log.info(f"✅ Generated posting plan with {posting_plan['total_posts']} posts")
            return posting_plan
            
        except Exception as e:
            log.error(f"Failed to generate posting plan: {e}")
            return self._get_fallback_posting_plan()
    
    async def _analyze_content_for_posting(self, content_data: dict) -> dict:
        """
        Analyze content quality and variety for intelligent posting decisions
        """
        try:
            analysis = {
                "content_quality": 0.8,
                "diversity_score": 0.7,
                "engagement_score": 0.75,
                "recommended_posts": 4
            }
            
            # Analyze content types available
            content_types = []
            if content_data.get("economy"):
                content_types.append("economy")
            if content_data.get("sports"):
                content_types.append("sports")
            if content_data.get("trends"):
                content_types.append("trends")
            if content_data.get("insight"):
                content_types.append("insight")
            if content_data.get("culture"):
                content_types.append("culture")
            if content_data.get("technology"):
                content_types.append("technology")
            if content_data.get("literature"):
                content_types.append("literature")
            if content_data.get("lifestyle"):
                content_types.append("lifestyle")
            if content_data.get("travel"):
                content_types.append("travel")
            
            # Calculate diversity score
            analysis["diversity_score"] = min(1.0, len(content_types) / 6.0)
            
            # Calculate recommended number of posts based on content quality
            if analysis["diversity_score"] > 0.8:
                analysis["recommended_posts"] = 6
            elif analysis["diversity_score"] > 0.6:
                analysis["recommended_posts"] = 5
            else:
                analysis["recommended_posts"] = 4
            
            # Calculate engagement score based on content freshness and relevance
            analysis["engagement_score"] = min(1.0, analysis["diversity_score"] + 0.2)
            
            return analysis
            
        except Exception as e:
            log.error(f"Content analysis failed: {e}")
            return {
                "content_quality": 0.7,
                "diversity_score": 0.6,
                "engagement_score": 0.65,
                "recommended_posts": 4
            }
    
    def _select_content_type_for_time(self, post_time: datetime, post_index: int) -> str:
        """
        Select the best content type for a specific posting time
        """
        hour = post_time.hour
        
        # Morning posts (6-11): Economy, Technology, Lifestyle
        if 6 <= hour < 12:
            types = ["economy", "technology", "lifestyle", "culture"]
        # Afternoon posts (12-17): Sports, Trends, Literature
        elif 12 <= hour < 18:
            types = ["sports", "trends", "literature", "travel"]
        # Evening posts (18-23): Insight, Culture, Lifestyle
        else:
            types = ["insight", "culture", "lifestyle", "trends"]
        
        return types[post_index % len(types)]
    
    def _get_fallback_posting_plan(self) -> dict:
        """
        Get a fallback posting plan when intelligent analysis fails
        """
        return {
            "total_posts": 4,
            "posts": [
                {
                    "post_id": 1,
                    "scheduled_time": datetime.now().replace(hour=8, minute=0, second=0, microsecond=0),
                    "content_type": "economy",
                    "priority": "high",
                    "engagement_focus": "peak",
                    "emoji_usage": "high",
                    "formatting_style": "bold_headers"
                },
                {
                    "post_id": 2,
                    "scheduled_time": datetime.now().replace(hour=14, minute=0, second=0, microsecond=0),
                    "content_type": "sports",
                    "priority": "high",
                    "engagement_focus": "peak",
                    "emoji_usage": "high",
                    "formatting_style": "bold_headers"
                },
                {
                    "post_id": 3,
                    "scheduled_time": datetime.now().replace(hour=18, minute=0, second=0, microsecond=0),
                    "content_type": "trends",
                    "priority": "medium",
                    "engagement_focus": "sustained",
                    "emoji_usage": "moderate",
                    "formatting_style": "standard"
                },
                {
                    "post_id": 4,
                    "scheduled_time": datetime.now().replace(hour=21, minute=0, second=0, microsecond=0),
                    "content_type": "insight",
                    "priority": "medium",
                    "engagement_focus": "sustained",
                    "emoji_usage": "moderate",
                    "formatting_style": "standard"
                }
            ],
            "strategy": "fallback_distribution",
            "engagement_prediction": 0.65,
            "content_diversity": 0.6
        }
    
    async def execute_intelligent_posting_plan(self, posting_plan: dict, content_data: dict) -> dict:
        """
        Execute the intelligent posting plan
        """
        try:
            log.info(f"🚀 Executing intelligent posting plan with {posting_plan['total_posts']} posts")
            
            results = {
                "successful_posts": 0,
                "failed_posts": 0,
                "execution_time": datetime.now(),
                "posts_details": []
            }
            
            for post_plan in posting_plan["posts"]:
                try:
                    # Generate content for this specific post
                    post_content = await self._generate_post_content(
                        post_plan, content_data
                    )
                    
                    if post_content:
                        # Schedule the post
                        await self._schedule_single_post(post_plan, post_content)
                        
                        results["successful_posts"] += 1
                        results["posts_details"].append({
                            "post_id": post_plan["post_id"],
                            "content_type": post_plan["content_type"],
                            "scheduled_time": post_plan["scheduled_time"],
                            "status": "scheduled"
                        })
                        
                        log.info(f"✅ Scheduled post {post_plan['post_id']} ({post_plan['content_type']}) for {post_plan['scheduled_time']}")
                    else:
                        results["failed_posts"] += 1
                        log.warning(f"⚠️ Failed to generate content for post {post_plan['post_id']}")
                        
                except Exception as e:
                    results["failed_posts"] += 1
                    log.error(f"❌ Failed to execute post {post_plan['post_id']}: {e}")
            
            log.info(f"🎯 Intelligent posting execution completed: {results['successful_posts']} successful, {results['failed_posts']} failed")
            return results
            
        except Exception as e:
            log.error(f"Failed to execute posting plan: {e}")
            return {
                "successful_posts": 0,
                "failed_posts": posting_plan.get("total_posts", 0),
                "execution_time": datetime.now(),
                "posts_details": [],
                "error": str(e)
            }
    
    async def _generate_post_content(self, post_plan: dict, content_data: dict) -> str:
        """
        Generate content for a specific post based on the plan
        """
        try:
            content_type = post_plan["content_type"]
            
            # Get the appropriate content from content_data
            if content_type in content_data and content_data[content_type]:
                base_content = content_data[content_type]
            else:
                # Fallback content generation
                base_content = f"محتوای {content_type} برای زمان {post_plan['scheduled_time'].strftime('%H:%M')}"
            
            # Apply formatting based on post plan
            if post_plan.get("formatting_style") == "bold_headers":
                formatted_content = f"**{content_type.upper()}**\n\n{base_content}"
            else:
                formatted_content = base_content
            
            # Add emojis based on plan
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
            
            return formatted_content
            
        except Exception as e:
            log.error(f"Failed to generate post content: {e}")
            return None
    
    async def _schedule_single_post(self, post_plan: dict, content: str):
        """
        Schedule a single post (placeholder for actual scheduling implementation)
        """
        try:
            # This would integrate with your actual posting mechanism
            # For now, we'll just log the scheduling
            log.info(f"📅 Scheduling post: {post_plan['content_type']} at {post_plan['scheduled_time']}")
            log.info(f"Content preview: {content[:100]}...")
            
            # Here you would integrate with your actual posting system
            # For example, using APScheduler or your existing posting mechanism
            
        except Exception as e:
            log.error(f"Failed to schedule single post: {e}")
            raise
