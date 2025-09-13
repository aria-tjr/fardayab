from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class ChannelAnalyticsMonitor:
    """Comprehensive channel analytics and monitoring system"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        self.analytics_data = {}
        self.performance_metrics = {}
        self.audience_insights = {}
        
    async def collect_channel_analytics(self, bot) -> Dict[str, Any]:
        """Collect comprehensive channel analytics"""
        try:
            # Get channel information
            channel_info = await self._get_channel_info(bot)
            
            # Get recent posts analytics
            posts_analytics = await self._get_posts_analytics(bot)
            
            # Get audience insights
            audience_insights = await self._get_audience_insights(bot)
            
            # Get engagement metrics
            engagement_metrics = await self._get_engagement_metrics(bot)
            
            # Get content performance
            content_performance = await self._get_content_performance(bot)
            
            # Compile comprehensive analytics
            analytics = {
                'channel_info': channel_info,
                'posts_analytics': posts_analytics,
                'audience_insights': audience_insights,
                'engagement_metrics': engagement_metrics,
                'content_performance': content_performance,
                'timestamp': datetime.now().isoformat(),
                'overall_health_score': await self._calculate_overall_health_score(
                    channel_info, posts_analytics, audience_insights, engagement_metrics
                )
            }
            
            # Store analytics data
            self.analytics_data[datetime.now().isoformat()] = analytics
            
            return analytics
            
        except Exception as e:
            log.error(f"Channel analytics collection failed: {e}")
            return {}
    
    async def _get_channel_info(self, bot) -> Dict[str, Any]:
        """Get basic channel information"""
        try:
            channel_id = self.settings.TELEGRAM_CHANNEL_ID
            
            # Get channel information
            chat = await bot.get_chat(channel_id)
            
            return {
                'channel_id': channel_id,
                'title': chat.title,
                'description': chat.description,
                'username': chat.username,
                'member_count': getattr(chat, 'member_count', 0),
                'is_verified': getattr(chat, 'is_verified', False),
                'is_public': not getattr(chat, 'is_private', True)
            }
            
        except Exception as e:
            log.error(f"Channel info collection failed: {e}")
            return {}
    
    async def _get_posts_analytics(self, bot) -> Dict[str, Any]:
        """Get analytics for recent posts"""
        try:
            # This would require Telegram Bot API analytics
            # For now, return mock data structure
            return {
                'total_posts_24h': 0,
                'total_posts_7d': 0,
                'total_posts_30d': 0,
                'average_posts_per_day': 0,
                'posting_frequency_score': 0.0,
                'content_diversity_score': 0.0
            }
            
        except Exception as e:
            log.error(f"Posts analytics collection failed: {e}")
            return {}
    
    async def _get_audience_insights(self, bot) -> Dict[str, Any]:
        """Get audience insights and demographics"""
        try:
            # This would require Telegram Bot API analytics
            # For now, return mock data structure
            return {
                'active_users_24h': 0,
                'active_users_7d': 0,
                'active_users_30d': 0,
                'audience_growth_rate': 0.0,
                'audience_retention_rate': 0.0,
                'peak_activity_hours': [],
                'audience_engagement_level': 'medium'
            }
            
        except Exception as e:
            log.error(f"Audience insights collection failed: {e}")
            return {}
    
    async def _get_engagement_metrics(self, bot) -> Dict[str, Any]:
        """Get engagement metrics for recent posts"""
        try:
            # This would require Telegram Bot API analytics
            # For now, return mock data structure
            return {
                'average_likes_per_post': 0,
                'average_comments_per_post': 0,
                'average_shares_per_post': 0,
                'engagement_rate': 0.0,
                'engagement_trend': 'stable',
                'most_engaged_content_types': [],
                'engagement_quality_score': 0.0
            }
            
        except Exception as e:
            log.error(f"Engagement metrics collection failed: {e}")
            return {}
    
    async def _get_content_performance(self, bot) -> Dict[str, Any]:
        """Get content performance analytics"""
        try:
            # This would require Telegram Bot API analytics
            # For now, return mock data structure
            return {
                'top_performing_content_types': [],
                'content_quality_score': 0.0,
                'content_diversity_score': 0.0,
                'content_consistency_score': 0.0,
                'content_innovation_score': 0.0,
                'content_relevance_score': 0.0
            }
            
        except Exception as e:
            log.error(f"Content performance collection failed: {e}")
            return {}
    
    async def _calculate_overall_health_score(self, channel_info: Dict, posts_analytics: Dict, 
                                            audience_insights: Dict, engagement_metrics: Dict) -> float:
        """Calculate overall channel health score"""
        try:
            scores = []
            
            # Channel info score
            if channel_info.get('member_count', 0) > 0:
                scores.append(0.8)  # Good if has members
            else:
                scores.append(0.2)  # Poor if no members
            
            # Posts analytics score
            posting_frequency = posts_analytics.get('posting_frequency_score', 0)
            scores.append(posting_frequency)
            
            # Audience insights score
            audience_growth = audience_insights.get('audience_growth_rate', 0)
            scores.append(min(1.0, max(0.0, audience_growth + 0.5)))
            
            # Engagement metrics score
            engagement_rate = engagement_metrics.get('engagement_rate', 0)
            scores.append(min(1.0, max(0.0, engagement_rate)))
            
            # Content performance score
            content_quality = posts_analytics.get('content_quality_score', 0)
            scores.append(content_quality)
            
            # Calculate weighted average
            if scores:
                return sum(scores) / len(scores)
            else:
                return 0.5
                
        except Exception as e:
            log.error(f"Health score calculation failed: {e}")
            return 0.5
    
    async def generate_analytics_report(self, bot) -> str:
        """Generate comprehensive analytics report"""
        try:
            # Collect analytics data
            analytics = await self.collect_channel_analytics(bot)
            
            if not analytics:
                return "❌ خطا در جمع‌آوری داده‌های تحلیلی"
            
            # Generate report
            report_lines = []
            
            # Header
            report_lines.append("📊 **گزارش تحلیلی کانال فردایاب**")
            report_lines.append("=" * 40)
            
            # Channel info
            channel_info = analytics.get('channel_info', {})
            if channel_info:
                report_lines.append(f"📢 **اطلاعات کانال:**")
                report_lines.append(f"نام: {channel_info.get('title', 'نامشخص')}")
                report_lines.append(f"اعضا: {channel_info.get('member_count', 0):,}")
                report_lines.append(f"وضعیت: {'عمومی' if channel_info.get('is_public') else 'خصوصی'}")
                report_lines.append("")
            
            # Posts analytics
            posts_analytics = analytics.get('posts_analytics', {})
            if posts_analytics:
                report_lines.append(f"📝 **آمار پست‌ها:**")
                report_lines.append(f"۲۴ ساعت گذشته: {posts_analytics.get('total_posts_24h', 0)} پست")
                report_lines.append(f"۷ روز گذشته: {posts_analytics.get('total_posts_7d', 0)} پست")
                report_lines.append(f"میانگین روزانه: {posts_analytics.get('average_posts_per_day', 0):.1f} پست")
                report_lines.append("")
            
            # Audience insights
            audience_insights = analytics.get('audience_insights', {})
            if audience_insights:
                report_lines.append(f"👥 **اطلاعات مخاطبان:**")
                report_lines.append(f"کاربران فعال (۲۴س): {audience_insights.get('active_users_24h', 0)}")
                report_lines.append(f"کاربران فعال (۷روز): {audience_insights.get('active_users_7d', 0)}")
                report_lines.append(f"نرخ رشد: {audience_insights.get('audience_growth_rate', 0):.1%}")
                report_lines.append("")
            
            # Engagement metrics
            engagement_metrics = analytics.get('engagement_metrics', {})
            if engagement_metrics:
                report_lines.append(f"💬 **آمار تعامل:**")
                report_lines.append(f"میانگین لایک: {engagement_metrics.get('average_likes_per_post', 0):.1f}")
                report_lines.append(f"میانگین کامنت: {engagement_metrics.get('average_comments_per_post', 0):.1f}")
                report_lines.append(f"نرخ تعامل: {engagement_metrics.get('engagement_rate', 0):.1%}")
                report_lines.append("")
            
            # Overall health score
            health_score = analytics.get('overall_health_score', 0)
            health_emoji = "🟢" if health_score > 0.7 else "🟡" if health_score > 0.4 else "🔴"
            report_lines.append(f"🏥 **وضعیت کلی کانال:**")
            report_lines.append(f"امتیاز سلامت: {health_emoji} {health_score:.1%}")
            
            # Recommendations
            recommendations = await self._generate_recommendations(analytics)
            if recommendations:
                report_lines.append("")
                report_lines.append("💡 **توصیه‌ها:**")
                for i, rec in enumerate(recommendations, 1):
                    report_lines.append(f"{i}. {rec}")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            log.error(f"Analytics report generation failed: {e}")
            return f"❌ خطا در تولید گزارش: {e}"
    
    async def _generate_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analytics"""
        try:
            recommendations = []
            
            # Analyze posting frequency
            posts_analytics = analytics.get('posts_analytics', {})
            avg_posts_per_day = posts_analytics.get('average_posts_per_day', 0)
            
            if avg_posts_per_day < 1:
                recommendations.append("تعداد پست‌های روزانه را افزایش دهید")
            elif avg_posts_per_day > 5:
                recommendations.append("تعداد پست‌ها را کمی کاهش دهید تا کیفیت حفظ شود")
            
            # Analyze engagement
            engagement_metrics = analytics.get('engagement_metrics', {})
            engagement_rate = engagement_metrics.get('engagement_rate', 0)
            
            if engagement_rate < 0.05:
                recommendations.append("محتوای تعاملی‌تر تولید کنید")
            elif engagement_rate > 0.2:
                recommendations.append("تعامل عالی است - همین مسیر را ادامه دهید")
            
            # Analyze audience growth
            audience_insights = analytics.get('audience_insights', {})
            growth_rate = audience_insights.get('audience_growth_rate', 0)
            
            if growth_rate < 0:
                recommendations.append("استراتژی جذب مخاطب را بازنگری کنید")
            elif growth_rate > 0.1:
                recommendations.append("رشد مخاطب عالی است")
            
            # Analyze content diversity
            content_diversity = posts_analytics.get('content_diversity_score', 0)
            if content_diversity < 0.5:
                recommendations.append("تنوع محتوا را افزایش دهید")
            
            # Analyze overall health
            health_score = analytics.get('overall_health_score', 0)
            if health_score < 0.4:
                recommendations.append("کانال نیاز به بهبود کلی دارد")
            elif health_score > 0.8:
                recommendations.append("کانال در وضعیت عالی قرار دارد")
            
            return recommendations[:5]  # Return top 5 recommendations
            
        except Exception as e:
            log.error(f"Recommendations generation failed: {e}")
            return ["محتوا را به طور مداوم بهبود دهید"]
    
    async def monitor_channel_health(self, bot) -> Dict[str, Any]:
        """Monitor channel health and alert on issues"""
        try:
            # Collect current analytics
            analytics = await self.collect_channel_analytics(bot)
            
            # Check for issues
            issues = []
            warnings = []
            
            # Check posting frequency
            posts_analytics = analytics.get('posts_analytics', {})
            avg_posts_per_day = posts_analytics.get('average_posts_per_day', 0)
            
            if avg_posts_per_day == 0:
                issues.append("هیچ پستی در ۲۴ ساعت گذشته ارسال نشده")
            elif avg_posts_per_day < 0.5:
                warnings.append("تعداد پست‌ها کم است")
            
            # Check engagement
            engagement_metrics = analytics.get('engagement_metrics', {})
            engagement_rate = engagement_metrics.get('engagement_rate', 0)
            
            if engagement_rate < 0.01:
                issues.append("نرخ تعامل بسیار پایین است")
            elif engagement_rate < 0.05:
                warnings.append("نرخ تعامل نیاز به بهبود دارد")
            
            # Check audience growth
            audience_insights = analytics.get('audience_insights', {})
            growth_rate = audience_insights.get('audience_growth_rate', 0)
            
            if growth_rate < -0.1:
                issues.append("مخاطبان در حال کاهش هستند")
            elif growth_rate < 0:
                warnings.append("رشد مخاطب منفی است")
            
            # Check overall health
            health_score = analytics.get('overall_health_score', 0)
            
            if health_score < 0.3:
                issues.append("وضعیت کلی کانال بحرانی است")
            elif health_score < 0.6:
                warnings.append("وضعیت کلی کانال نیاز به بهبود دارد")
            
            return {
                'health_score': health_score,
                'issues': issues,
                'warnings': warnings,
                'status': 'critical' if issues else 'warning' if warnings else 'healthy',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            log.error(f"Channel health monitoring failed: {e}")
            return {
                'health_score': 0.0,
                'issues': [f"خطا در نظارت: {e}"],
                'warnings': [],
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get performance trends over specified days"""
        try:
            # Get analytics data for the specified period
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Filter analytics data for the period
            period_data = {}
            for timestamp, data in self.analytics_data.items():
                data_time = datetime.fromisoformat(timestamp)
                if start_date <= data_time <= end_date:
                    period_data[timestamp] = data
            
            if not period_data:
                return {'error': 'داده‌های کافی برای تحلیل روند موجود نیست'}
            
            # Calculate trends
            trends = {
                'posting_frequency_trend': self._calculate_trend(
                    [data.get('posts_analytics', {}).get('average_posts_per_day', 0) 
                     for data in period_data.values()]
                ),
                'engagement_trend': self._calculate_trend(
                    [data.get('engagement_metrics', {}).get('engagement_rate', 0) 
                     for data in period_data.values()]
                ),
                'audience_growth_trend': self._calculate_trend(
                    [data.get('audience_insights', {}).get('audience_growth_rate', 0) 
                     for data in period_data.values()]
                ),
                'health_score_trend': self._calculate_trend(
                    [data.get('overall_health_score', 0) 
                     for data in period_data.values()]
                )
            }
            
            return trends
            
        except Exception as e:
            log.error(f"Performance trends calculation failed: {e}")
            return {'error': f'خطا در محاسبه روندها: {e}'}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values"""
        try:
            if len(values) < 2:
                return 'stable'
            
            # Calculate simple linear trend
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            change = second_avg - first_avg
            change_percent = abs(change) / max(first_avg, 0.001) * 100
            
            if change_percent < 5:
                return 'stable'
            elif change > 0:
                return 'increasing'
            else:
                return 'decreasing'
                
        except Exception:
            return 'stable'
