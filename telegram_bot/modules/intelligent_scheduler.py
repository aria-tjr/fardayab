from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from telegram_bot.config.settings import Settings
from telegram_bot.modules.advanced_posting import AdvancedPostingManager, PostType

log = logging.getLogger(__name__)


class ContentPriority(Enum):
    """Content priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class EngagementPattern(Enum):
    """User engagement patterns"""
    MORNING_ACTIVE = "morning_active"
    AFTERNOON_ACTIVE = "afternoon_active"
    EVENING_ACTIVE = "evening_active"
    NIGHT_ACTIVE = "night_active"
    CONSTANT = "constant"


@dataclass
class OptimalTiming:
    """Optimal timing configuration"""
    time_slot: str
    engagement_score: float
    content_types: List[PostType]
    frequency: int  # posts per day
    success_rate: float


@dataclass
class ContentPlan:
    """Content planning structure"""
    post_id: str
    content_type: PostType
    priority: ContentPriority
    scheduled_time: datetime
    content_data: Dict[str, Any]
    engagement_hooks: List[str]
    visual_elements: List[str]
    hashtags: List[str]
    call_to_action: str
    expected_engagement: float
    fallback_plan: Optional[Dict[str, Any]] = None


class IntelligentContentScheduler:
    """Intelligent content scheduler based on top channel strategies"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.posting_manager = AdvancedPostingManager(settings)
        self.optimal_timings = self._initialize_optimal_timings()
        self.user_engagement_patterns = {}
        self.content_performance_history = {}
        self.scheduled_posts = []
        
    def _initialize_optimal_timings(self) -> List[OptimalTiming]:
        """Initialize optimal timing patterns based on top channel analysis"""
        return [
            OptimalTiming(
                time_slot="08:00-09:00",
                engagement_score=0.85,
                content_types=[PostType.BREAKING_NEWS, PostType.MARKET_UPDATE, PostType.TIP],
                frequency=2,
                success_rate=0.78
            ),
            OptimalTiming(
                time_slot="12:00-13:00",
                engagement_score=0.92,
                content_types=[PostType.ANALYSIS, PostType.POLL, PostType.EDUCATIONAL],
                frequency=1,
                success_rate=0.82
            ),
            OptimalTiming(
                time_slot="15:00-16:00",
                engagement_score=0.88,
                content_types=[PostType.MARKET_UPDATE, PostType.PREDICTION, PostType.ANALYSIS],
                frequency=1,
                success_rate=0.75
            ),
            OptimalTiming(
                time_slot="18:00-19:00",
                engagement_score=0.95,
                content_types=[PostType.ANALYSIS, PostType.EDUCATIONAL, PostType.QUIZ],
                frequency=2,
                success_rate=0.88
            ),
            OptimalTiming(
                time_slot="20:00-21:00",
                engagement_score=0.90,
                content_types=[PostType.PREDICTION, PostType.RECAP, PostType.POLL],
                frequency=1,
                success_rate=0.80
            ),
            OptimalTiming(
                time_slot="22:00-23:00",
                engagement_score=0.87,
                content_types=[PostType.RECAP, PostType.TIP, PostType.MARKET_UPDATE],
                frequency=1,
                success_rate=0.76
            )
        ]
    
    async def analyze_user_engagement_patterns(self, engagement_data: Dict[str, Any]) -> EngagementPattern:
        """Analyze user engagement patterns to optimize posting times"""
        # Analyze engagement by time slots
        time_engagement = engagement_data.get('time_engagement', {})
        
        morning_score = time_engagement.get('08:00-12:00', 0)
        afternoon_score = time_engagement.get('12:00-16:00', 0)
        evening_score = time_engagement.get('16:00-20:00', 0)
        night_score = time_engagement.get('20:00-24:00', 0)
        
        # Determine dominant pattern
        scores = {
            EngagementPattern.MORNING_ACTIVE: morning_score,
            EngagementPattern.AFTERNOON_ACTIVE: afternoon_score,
            EngagementPattern.EVENING_ACTIVE: evening_score,
            EngagementPattern.NIGHT_ACTIVE: night_score
        }
        
        max_pattern = max(scores, key=scores.get)
        
        # Check if engagement is relatively constant
        if all(score > 0.7 for score in scores.values()):
            return EngagementPattern.CONSTANT
        
        return max_pattern
    
    async def get_optimal_posting_times(self, content_type: PostType, 
                                      engagement_pattern: EngagementPattern) -> List[str]:
        """Get optimal posting times based on content type and engagement pattern"""
        # Get base optimal times for content type
        base_times = await self.posting_manager.get_optimal_posting_time(content_type)
        
        # Adjust based on engagement pattern
        pattern_adjustments = {
            EngagementPattern.MORNING_ACTIVE: ["08:00", "09:00", "10:00"],
            EngagementPattern.AFTERNOON_ACTIVE: ["12:00", "13:00", "14:00", "15:00"],
            EngagementPattern.EVENING_ACTIVE: ["18:00", "19:00", "20:00", "21:00"],
            EngagementPattern.NIGHT_ACTIVE: ["20:00", "21:00", "22:00", "23:00"],
            EngagementPattern.CONSTANT: ["08:00", "12:00", "16:00", "20:00"]
        }
        
        optimal_times = pattern_adjustments.get(engagement_pattern, [base_times])
        
        # Filter by content type compatibility
        compatible_times = []
        for timing in self.optimal_timings:
            if content_type in timing.content_types:
                compatible_times.extend(timing.time_slot.split('-'))
        
        # Return intersection of optimal times and compatible times
        if compatible_times:
            return [time for time in optimal_times if any(time in slot for slot in compatible_times)]
        
        return optimal_times
    
    async def create_content_plan(self, content_type: PostType, content_data: Dict[str, Any],
                                priority: ContentPriority = ContentPriority.MEDIUM) -> ContentPlan:
        """Create a comprehensive content plan"""
        post_id = f"{content_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get optimal timing
        engagement_pattern = await self.analyze_user_engagement_patterns(content_data)
        optimal_times = await self.get_optimal_posting_times(content_type, engagement_pattern)
        scheduled_time = datetime.now().replace(hour=int(optimal_times[0].split(':')[0]), 
                                              minute=int(optimal_times[0].split(':')[1]))
        
        # Generate engagement elements
        engagement_hooks = await self.posting_manager.generate_engagement_hooks(content_type, str(content_data))
        visual_elements = await self.posting_manager.create_visual_elements(content_type, str(content_data))
        hashtags = await self.posting_manager.generate_hashtags(content_type, str(content_data))
        call_to_action = await self.posting_manager.create_call_to_action(content_type, str(content_data))
        
        # Calculate expected engagement based on historical data
        expected_engagement = await self._calculate_expected_engagement(content_type, scheduled_time)
        
        # Create fallback plan
        fallback_plan = await self._create_fallback_plan(content_type, content_data)
        
        return ContentPlan(
            post_id=post_id,
            content_type=content_type,
            priority=priority,
            scheduled_time=scheduled_time,
            content_data=content_data,
            engagement_hooks=engagement_hooks,
            visual_elements=visual_elements,
            hashtags=hashtags,
            call_to_action=call_to_action,
            expected_engagement=expected_engagement,
            fallback_plan=fallback_plan
        )
    
    async def _calculate_expected_engagement(self, content_type: PostType, scheduled_time: datetime) -> float:
        """Calculate expected engagement based on historical data"""
        base_engagement = 0.5  # Base engagement rate
        
        # Adjust based on content type performance
        if content_type in self.content_performance_history:
            history = self.content_performance_history[content_type]
            avg_engagement = sum(h['engagement_rate'] for h in history) / len(history)
            base_engagement = avg_engagement
        
        # Adjust based on timing
        hour = scheduled_time.hour
        if 8 <= hour <= 10 or 18 <= hour <= 21:  # Peak hours
            base_engagement *= 1.2
        elif 22 <= hour <= 23:  # Night hours
            base_engagement *= 0.8
        
        # Adjust based on day of week
        weekday = scheduled_time.weekday()
        if weekday < 5:  # Weekdays
            base_engagement *= 1.1
        else:  # Weekends
            base_engagement *= 0.9
        
        return min(base_engagement, 1.0)  # Cap at 1.0
    
    async def _create_fallback_plan(self, content_type: PostType, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback plan for content"""
        return {
            "alternative_times": ["12:00", "18:00", "21:00"],
            "simplified_content": str(content_data)[:500],  # Truncated version
            "minimal_hooks": ["📊", "💡"],
            "essential_hashtags": ["#بازار", "#کریپتو"],
            "simple_cta": "نظر شما چیست؟"
        }
    
    async def schedule_content_batch(self, content_batch: List[Tuple[PostType, Dict[str, Any], ContentPriority]]) -> List[ContentPlan]:
        """Schedule a batch of content with optimal timing"""
        plans = []
        
        for content_type, content_data, priority in content_batch:
            plan = await self.create_content_plan(content_type, content_data, priority)
            plans.append(plan)
        
        # Sort by priority and expected engagement
        plans.sort(key=lambda x: (x.priority.value, -x.expected_engagement))
        
        # Adjust timing to avoid conflicts
        plans = await self._resolve_timing_conflicts(plans)
        
        # Add to scheduled posts
        self.scheduled_posts.extend(plans)
        
        return plans
    
    async def _resolve_timing_conflicts(self, plans: List[ContentPlan]) -> List[ContentPlan]:
        """Resolve timing conflicts between scheduled posts"""
        # Group plans by scheduled time
        time_groups = {}
        for plan in plans:
            time_key = plan.scheduled_time.strftime('%H:%M')
            if time_key not in time_groups:
                time_groups[time_key] = []
            time_groups[time_key].append(plan)
        
        # Resolve conflicts by adjusting times
        resolved_plans = []
        for time_key, group_plans in time_groups.items():
            if len(group_plans) == 1:
                resolved_plans.extend(group_plans)
            else:
                # Sort by priority
                group_plans.sort(key=lambda x: x.priority.value)
                
                # Keep first plan at original time
                resolved_plans.append(group_plans[0])
                
                # Adjust others by 30-minute intervals
                for i, plan in enumerate(group_plans[1:], 1):
                    adjusted_time = plan.scheduled_time + timedelta(minutes=30 * i)
                    plan.scheduled_time = adjusted_time
                    resolved_plans.append(plan)
        
        return resolved_plans
    
    async def get_daily_schedule(self, date: datetime) -> List[ContentPlan]:
        """Get optimized daily posting schedule"""
        # Get base schedule from posting manager
        base_schedule = await self.posting_manager.get_posting_schedule(date)
        
        # Convert to ContentPlan objects
        plans = []
        for item in base_schedule:
            content_data = {
                "scheduled_time": item["scheduled_time"],
                "post_type": item["post_type"],
                "priority": ContentPriority.MEDIUM
            }
            
            plan = await self.create_content_plan(
                item["post_type"], 
                content_data, 
                ContentPriority(item["priority"])
            )
            plans.append(plan)
        
        # Optimize schedule
        optimized_plans = await self._optimize_daily_schedule(plans)
        
        return optimized_plans
    
    async def _optimize_daily_schedule(self, plans: List[ContentPlan]) -> List[ContentPlan]:
        """Optimize daily schedule for maximum engagement"""
        # Sort by expected engagement
        plans.sort(key=lambda x: -x.expected_engagement)
        
        # Limit to optimal number of posts per day (based on best practices)
        max_posts_per_day = 8
        if len(plans) > max_posts_per_day:
            plans = plans[:max_posts_per_day]
        
        # Ensure variety in content types
        content_types_used = set()
        optimized_plans = []
        
        for plan in plans:
            if plan.content_type not in content_types_used or len(optimized_plans) < 3:
                optimized_plans.append(plan)
                content_types_used.add(plan.content_type)
        
        return optimized_plans
    
    async def track_content_performance(self, post_id: str, metrics: Dict[str, Any]):
        """Track content performance for future optimization"""
        # Find the plan
        plan = next((p for p in self.scheduled_posts if p.post_id == post_id), None)
        if not plan:
            return
        
        # Calculate engagement rate
        views = metrics.get('views', 0)
        engagement = metrics.get('engagement', 0)
        engagement_rate = engagement / max(views, 1)
        
        # Store performance data
        performance_data = {
            'post_id': post_id,
            'content_type': plan.content_type,
            'scheduled_time': plan.scheduled_time,
            'metrics': metrics,
            'engagement_rate': engagement_rate,
            'timestamp': datetime.now()
        }
        
        # Add to performance history
        if plan.content_type not in self.content_performance_history:
            self.content_performance_history[plan.content_type] = []
        
        self.content_performance_history[plan.content_type].append(performance_data)
        
        # Keep only last 50 records per content type
        if len(self.content_performance_history[plan.content_type]) > 50:
            self.content_performance_history[plan.content_type] = \
                self.content_performance_history[plan.content_type][-50:]
    
    async def get_performance_insights(self) -> Dict[str, Any]:
        """Get performance insights for optimization"""
        insights = {
            'best_performing_types': [],
            'optimal_timing_insights': {},
            'engagement_trends': {},
            'recommendations': []
        }
        
        # Analyze content type performance
        for content_type, history in self.content_performance_history.items():
            if history:
                avg_engagement = sum(h['engagement_rate'] for h in history) / len(history)
                insights['best_performing_types'].append({
                    'type': content_type.value,
                    'avg_engagement': avg_engagement,
                    'total_posts': len(history)
                })
        
        # Sort by average engagement
        insights['best_performing_types'].sort(key=lambda x: x['avg_engagement'], reverse=True)
        
        # Analyze timing performance
        timing_performance = {}
        for content_type, history in self.content_performance_history.items():
            for record in history:
                hour = record['scheduled_time'].hour
                time_slot = f"{hour:02d}:00-{(hour+1):02d}:00"
                
                if time_slot not in timing_performance:
                    timing_performance[time_slot] = []
                timing_performance[time_slot].append(record['engagement_rate'])
        
        # Calculate average engagement per time slot
        for time_slot, rates in timing_performance.items():
            insights['optimal_timing_insights'][time_slot] = sum(rates) / len(rates)
        
        # Generate recommendations
        if insights['best_performing_types']:
            best_type = insights['best_performing_types'][0]
            insights['recommendations'].append(
                f"Focus more on {best_type['type']} content (avg engagement: {best_type['avg_engagement']:.2f})"
            )
        
        return insights
    
    async def auto_optimize_schedule(self) -> Dict[str, Any]:
        """Automatically optimize posting schedule based on performance data"""
        insights = await self.get_performance_insights()
        
        optimizations = {
            'schedule_adjustments': [],
            'content_type_adjustments': [],
            'timing_adjustments': []
        }
        
        # Adjust content type frequency based on performance
        for type_data in insights['best_performing_types']:
            if type_data['avg_engagement'] > 0.7:
                optimizations['content_type_adjustments'].append({
                    'type': type_data['type'],
                    'action': 'increase_frequency',
                    'reason': 'high_engagement'
                })
            elif type_data['avg_engagement'] < 0.3:
                optimizations['content_type_adjustments'].append({
                    'type': type_data['type'],
                    'action': 'decrease_frequency',
                    'reason': 'low_engagement'
                })
        
        # Adjust timing based on performance
        best_timing = max(insights['optimal_timing_insights'].items(), key=lambda x: x[1])
        worst_timing = min(insights['optimal_timing_insights'].items(), key=lambda x: x[1])
        
        optimizations['timing_adjustments'].append({
            'action': 'increase_posts_at',
            'time_slot': best_timing[0],
            'reason': f'high_engagement_{best_timing[1]:.2f}'
        })
        
        optimizations['timing_adjustments'].append({
            'action': 'decrease_posts_at',
            'time_slot': worst_timing[0],
            'reason': f'low_engagement_{worst_timing[1]:.2f}'
        })
        
        return optimizations
