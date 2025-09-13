from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class IntelligentContentCurator:
    """Advanced AI-powered content curation and management system"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        self.content_history = []
        self.performance_metrics = {}
        self.user_preferences = {}
        
    async def analyze_content_performance(self, content: str, engagement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content performance and extract insights"""
        try:
            # Analyze content characteristics
            content_analysis = {
                'length': len(content),
                'emoji_count': sum(1 for char in content if ord(char) > 127),
                'hashtag_count': content.count('#'),
                'persian_ratio': self._calculate_persian_ratio(content),
                'engagement_score': self._calculate_engagement_score(engagement_data),
                'topic_diversity': self._analyze_topic_diversity(content),
                'sentiment_score': self._analyze_sentiment(content)
            }
            
            # Store performance data
            self.performance_metrics[datetime.now().isoformat()] = content_analysis
            
            return content_analysis
            
        except Exception as e:
            log.error(f"Content performance analysis failed: {e}")
            return {}
    
    def _calculate_persian_ratio(self, text: str) -> float:
        """Calculate ratio of Persian characters in text"""
        persian_chars = set('ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی')
        text_chars = set(text)
        if not text_chars:
            return 0.0
        return len(text_chars.intersection(persian_chars)) / len(text_chars)
    
    def _calculate_engagement_score(self, engagement_data: Dict[str, Any]) -> float:
        """Calculate engagement score based on likes, comments, shares"""
        try:
            likes = engagement_data.get('likes', 0)
            comments = engagement_data.get('comments', 0)
            shares = engagement_data.get('shares', 0)
            views = engagement_data.get('views', 1)
            
            # Weighted engagement score
            score = (likes * 1.0 + comments * 3.0 + shares * 5.0) / max(views, 1)
            return min(score, 10.0)  # Cap at 10
            
        except Exception:
            return 0.0
    
    def _analyze_topic_diversity(self, content: str) -> float:
        """Analyze topic diversity in content"""
        topics = ['اقتصاد', 'ورزش', 'ترند', 'فرهنگ', 'تکنولوژی', 'ادبیات', 'سلامت', 'سفر']
        found_topics = sum(1 for topic in topics if topic in content)
        return found_topics / len(topics)
    
    def _analyze_sentiment(self, content: str) -> float:
        """Basic sentiment analysis for Persian text"""
        positive_words = ['خوب', 'عالی', 'مثبت', 'بهتر', 'موفق', 'پیشرفت', 'رشد', 'امیدوار']
        negative_words = ['بد', 'منفی', 'مشکل', 'کاهش', 'نگران', 'خطر', 'ریسک', 'افت']
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    async def get_optimal_posting_times(self) -> List[Tuple[int, int]]:
        """Get optimal posting times based on Persian audience patterns"""
        # Persian audience peak times (Tehran timezone)
        optimal_times = [
            (8, 0),   # 8:00 AM - Morning news
            (12, 0),  # 12:00 PM - Lunch break
            (16, 0),  # 4:00 PM - Afternoon break
            (20, 0),  # 8:00 PM - Evening leisure
            (22, 0),  # 10:00 PM - Night reading
        ]
        return optimal_times
    
    async def select_best_content_mix(self, available_content: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently select the best content mix for posting"""
        try:
            # Analyze available content
            content_scores = {}
            
            for content_type, content_data in available_content.items():
                if not content_data:
                    continue
                    
                score = await self._score_content_type(content_type, content_data)
                content_scores[content_type] = score
            
            # Select top performing content types
            sorted_content = sorted(content_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Create optimal content mix
            selected_content = {}
            for content_type, score in sorted_content[:6]:  # Top 6 content types
                if score > 0.5:  # Only include high-quality content
                    selected_content[content_type] = available_content[content_type]
            
            return selected_content
            
        except Exception as e:
            log.error(f"Content mix selection failed: {e}")
            return available_content
    
    async def _score_content_type(self, content_type: str, content_data: Any) -> float:
        """Score content type based on various factors"""
        try:
            score = 0.0
            
            # Base score for content type
            type_scores = {
                'economy': 0.9,      # High priority
                'sports': 0.8,       # High engagement
                'trends': 0.7,       # Good for virality
                'culture': 0.6,      # Cultural relevance
                'technology': 0.7,   # Modern appeal
                'literature': 0.5,   # Educational
                'lifestyle': 0.6,    # Broad appeal
                'travel': 0.5,       # Seasonal
                'insight': 0.8,      # High value
            }
            
            score += type_scores.get(content_type, 0.5)
            
            # Content quality factors
            if isinstance(content_data, dict):
                if content_data.get('trending'):
                    score += 0.2
                if content_data.get('prediction'):
                    score += 0.1
                if content_data.get('analysis'):
                    score += 0.1
            
            # Time-based adjustments
            current_hour = datetime.now().hour
            if content_type == 'economy' and 8 <= current_hour <= 10:
                score += 0.2  # Morning economy news
            elif content_type == 'sports' and 18 <= current_hour <= 22:
                score += 0.2  # Evening sports
            elif content_type == 'trends' and 12 <= current_hour <= 14:
                score += 0.1  # Lunch break trends
            
            return min(score, 1.0)
            
        except Exception:
            return 0.5
    
    async def generate_content_variations(self, base_content: str, content_type: str) -> List[str]:
        """Generate multiple variations of content for A/B testing"""
        try:
            variations = [base_content]
            
            # Generate variations based on content type
            if content_type == 'economy':
                # Add more technical vs simple variations
                variations.append(self._add_technical_details(base_content))
                variations.append(self._simplify_content(base_content))
            elif content_type == 'sports':
                # Add more emotional vs analytical variations
                variations.append(self._add_emotional_language(base_content))
                variations.append(self._add_analytical_language(base_content))
            elif content_type == 'trends':
                # Add more hashtags vs fewer hashtags
                variations.append(self._add_more_hashtags(base_content))
                variations.append(self._reduce_hashtags(base_content))
            
            return variations[:3]  # Return up to 3 variations
            
        except Exception as e:
            log.error(f"Content variation generation failed: {e}")
            return [base_content]
    
    def _add_technical_details(self, content: str) -> str:
        """Add technical details to content"""
        return content.replace('تحلیل', 'تحلیل فنی دقیق').replace('پیش‌بینی', 'پیش‌بینی مبتنی بر داده')
    
    def _simplify_content(self, content: str) -> str:
        """Simplify content for broader audience"""
        return content.replace('تحلیل فنی دقیق', 'تحلیل').replace('پیش‌بینی مبتنی بر داده', 'پیش‌بینی')
    
    def _add_emotional_language(self, content: str) -> str:
        """Add emotional language to content"""
        return content.replace('مسابقه', 'مسابقه هیجان‌انگیز').replace('تیم', 'تیم محبوب')
    
    def _add_analytical_language(self, content: str) -> str:
        """Add analytical language to content"""
        return content.replace('مسابقه هیجان‌انگیز', 'مسابقه').replace('تیم محبوب', 'تیم')
    
    def _add_more_hashtags(self, content: str) -> str:
        """Add more hashtags to content"""
        hashtags = ['#فردایاب', '#تحلیل', '#پیش‌بینی', '#ایران', '#اقتصاد', '#ورزش']
        existing_hashtags = [tag for tag in content.split() if tag.startswith('#')]
        new_hashtags = [tag for tag in hashtags if tag not in existing_hashtags]
        return content + ' ' + ' '.join(new_hashtags[:3])
    
    def _reduce_hashtags(self, content: str) -> str:
        """Reduce hashtags in content"""
        words = content.split()
        hashtags = [word for word in words if word.startswith('#')]
        if len(hashtags) > 3:
            # Keep only first 3 hashtags
            words = [word for word in words if not word.startswith('#')]
            words.extend(hashtags[:3])
        return ' '.join(words)
    
    async def optimize_content_for_engagement(self, content: str) -> str:
        """Optimize content for maximum engagement"""
        try:
            # Add engagement hooks
            if '?' not in content:
                content += '\n\nنظر شما چیست؟ 🤔'
            
            # Ensure proper emoji usage
            if content.count('📊') + content.count('⚽') + content.count('📱') < 3:
                content = content.replace('**اقتصاد**', '**📊 اقتصاد**')
                content = content.replace('**ورزش**', '**⚽ ورزش**')
                content = content.replace('**ترند**', '**📱 ترند**')
            
            # Add call-to-action
            if 'نظر' not in content and 'فکر' not in content:
                content += '\n\n💬 نظرات خود را با ما به اشتراک بگذارید!'
            
            return content
            
        except Exception as e:
            log.error(f"Content optimization failed: {e}")
            return content
    
    async def get_content_recommendations(self) -> Dict[str, Any]:
        """Get intelligent content recommendations"""
        try:
            current_time = datetime.now()
            recommendations = {
                'optimal_posting_times': await self.get_optimal_posting_times(),
                'content_mix_suggestion': self._get_content_mix_suggestion(current_time),
                'engagement_tips': self._get_engagement_tips(),
                'trending_topics': await self._get_trending_topics(),
                'quality_metrics': self._get_quality_metrics()
            }
            
            return recommendations
            
        except Exception as e:
            log.error(f"Content recommendations failed: {e}")
            return {}
    
    def _get_content_mix_suggestion(self, current_time: datetime) -> str:
        """Get content mix suggestion based on current time"""
        hour = current_time.hour
        
        if 6 <= hour <= 10:
            return "صبح: اقتصاد + اخبار + ترندهای صبحگاهی"
        elif 10 <= hour <= 14:
            return "ظهر: ورزش + فرهنگ + تکنولوژی"
        elif 14 <= hour <= 18:
            return "عصر: ترندها + سفر + سبک زندگی"
        elif 18 <= hour <= 22:
            return "شب: ورزش + ادبیات + Insight"
        else:
            return "شب: Insight + فرهنگ + تکنولوژی"
    
    def _get_engagement_tips(self) -> List[str]:
        """Get engagement optimization tips"""
        return [
            "از سوالات تعاملی استفاده کنید",
            "ایموجی‌های مناسب اضافه کنید",
            "هشتگ‌های مرتبط استفاده کنید",
            "محتوا را کوتاه و جذاب نگه دارید",
            "از داستان‌سرایی استفاده کنید"
        ]
    
    async def _get_trending_topics(self) -> List[str]:
        """Get trending topics for content inspiration"""
        return [
            "هوش مصنوعی در ایران",
            "اقتصاد دیجیتال",
            "ورزش‌های زمستانی",
            "ادبیات معاصر",
            "گردشگری داخلی",
            "تکنولوژی سبز"
        ]
    
    def _get_quality_metrics(self) -> Dict[str, Any]:
        """Get content quality metrics"""
        if not self.performance_metrics:
            return {}
        
        recent_metrics = list(self.performance_metrics.values())[-10:]  # Last 10 posts
        
        return {
            'average_engagement': sum(m.get('engagement_score', 0) for m in recent_metrics) / len(recent_metrics),
            'average_persian_ratio': sum(m.get('persian_ratio', 0) for m in recent_metrics) / len(recent_metrics),
            'average_topic_diversity': sum(m.get('topic_diversity', 0) for m in recent_metrics) / len(recent_metrics),
            'total_posts_analyzed': len(self.performance_metrics)
        }
