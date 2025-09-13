from __future__ import annotations

import asyncio
import logging
import random
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class EngagementType(Enum):
    """Types of engagement elements"""
    EMOJI = "emoji"
    QUESTION = "question"
    POLL = "poll"
    CALL_TO_ACTION = "call_to_action"
    HASHTAG = "hashtag"
    VISUAL = "visual"
    INTERACTIVE = "interactive"


class EngagementLevel(Enum):
    """Engagement intensity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VIRAL = "viral"


@dataclass
class EngagementElement:
    """Engagement element configuration"""
    element_type: EngagementType
    content: str
    position: str  # "start", "middle", "end"
    engagement_score: float
    usage_count: int = 0
    success_rate: float = 0.0


@dataclass
class EngagementStrategy:
    """Engagement strategy configuration"""
    strategy_id: str
    name: str
    elements: List[EngagementElement]
    target_engagement: float
    success_metrics: List[str]
    usage_limit: int = 10


class EngagementOptimizer:
    """Advanced engagement optimization system"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engagement_elements = self._initialize_engagement_elements()
        self.engagement_strategies = self._initialize_strategies()
        self.performance_tracking = {}
        self.user_interaction_history = {}
        
    def _initialize_engagement_elements(self) -> Dict[EngagementType, List[EngagementElement]]:
        """Initialize engagement elements based on top channel analysis"""
        return {
            EngagementType.EMOJI: [
                EngagementElement(EngagementType.EMOJI, "🚨", "start", 0.9),
                EngagementElement(EngagementType.EMOJI, "📊", "start", 0.8),
                EngagementElement(EngagementType.EMOJI, "💰", "start", 0.85),
                EngagementElement(EngagementType.EMOJI, "🔮", "start", 0.75),
                EngagementElement(EngagementType.EMOJI, "💡", "start", 0.7),
                EngagementElement(EngagementType.EMOJI, "🎯", "end", 0.6),
                EngagementElement(EngagementType.EMOJI, "🔥", "end", 0.8),
                EngagementElement(EngagementType.EMOJI, "⚡", "end", 0.7),
                EngagementElement(EngagementType.EMOJI, "🎉", "end", 0.65),
                EngagementElement(EngagementType.EMOJI, "💎", "middle", 0.75),
            ],
            EngagementType.QUESTION: [
                EngagementElement(EngagementType.QUESTION, "نظر شما چیست؟", "end", 0.8),
                EngagementElement(EngagementType.QUESTION, "آیا موافقید؟", "end", 0.75),
                EngagementElement(EngagementType.QUESTION, "پیش‌بینی شما چیست؟", "end", 0.85),
                EngagementElement(EngagementType.QUESTION, "کدام ارز را ترجیح می‌دهید؟", "end", 0.7),
                EngagementElement(EngagementType.QUESTION, "تجربه شما چیست؟", "end", 0.65),
                EngagementElement(EngagementType.QUESTION, "سوالی دارید؟", "end", 0.6),
                EngagementElement(EngagementType.QUESTION, "آیا این تحلیل درست است؟", "end", 0.8),
                EngagementElement(EngagementType.QUESTION, "کدام استراتژی بهتر است؟", "end", 0.75),
            ],
            EngagementType.CALL_TO_ACTION: [
                EngagementElement(EngagementType.CALL_TO_ACTION, "نظر خود را بنویسید", "end", 0.7),
                EngagementElement(EngagementType.CALL_TO_ACTION, "این پست را ذخیره کنید", "end", 0.6),
                EngagementElement(EngagementType.CALL_TO_ACTION, "برای دوستان ارسال کنید", "end", 0.8),
                EngagementElement(EngagementType.CALL_TO_ACTION, "در کامنت‌ها بحث کنید", "end", 0.75),
                EngagementElement(EngagementType.CALL_TO_ACTION, "سوال بپرسید", "end", 0.65),
                EngagementElement(EngagementType.CALL_TO_ACTION, "تجربه خود را به اشتراک بگذارید", "end", 0.7),
                EngagementElement(EngagementType.CALL_TO_ACTION, "نکته اضافی دارید؟", "end", 0.6),
                EngagementElement(EngagementType.CALL_TO_ACTION, "موافقید؟", "end", 0.55),
            ],
            EngagementType.HASHTAG: [
                EngagementElement(EngagementType.HASHTAG, "#کریپتو", "end", 0.6),
                EngagementElement(EngagementType.HASHTAG, "#بیت_کوین", "end", 0.7),
                EngagementElement(EngagementType.HASHTAG, "#فارکس", "end", 0.65),
                EngagementElement(EngagementType.HASHTAG, "#معاملات", "end", 0.6),
                EngagementElement(EngagementType.HASHTAG, "#تحلیل", "end", 0.55),
                EngagementElement(EngagementType.HASHTAG, "#پیش‌بینی", "end", 0.6),
                EngagementElement(EngagementType.HASHTAG, "#نکته", "end", 0.5),
                EngagementElement(EngagementType.HASHTAG, "#بازار", "end", 0.6),
                EngagementElement(EngagementType.HASHTAG, "#سرمایه_گذاری", "end", 0.55),
                EngagementElement(EngagementType.HASHTAG, "#فردایاب", "end", 0.4),
            ],
            EngagementType.VISUAL: [
                EngagementElement(EngagementType.VISUAL, "📊 [نمودار]", "middle", 0.8),
                EngagementElement(EngagementType.VISUAL, "🖼️ [تصویر]", "middle", 0.7),
                EngagementElement(EngagementType.VISUAL, "📈 [چارت]", "middle", 0.85),
                EngagementElement(EngagementType.VISUAL, "📋 [جدول]", "middle", 0.6),
                EngagementElement(EngagementType.VISUAL, "🎯 [نکته کلیدی]", "middle", 0.75),
                EngagementElement(EngagementType.VISUAL, "💡 [راهنما]", "middle", 0.7),
            ],
            EngagementType.INTERACTIVE: [
                EngagementElement(EngagementType.INTERACTIVE, "رأی دهید", "end", 0.9),
                EngagementElement(EngagementType.INTERACTIVE, "انتخاب کنید", "end", 0.85),
                EngagementElement(EngagementType.INTERACTIVE, "پاسخ دهید", "end", 0.8),
                EngagementElement(EngagementType.INTERACTIVE, "شرکت کنید", "end", 0.75),
                EngagementElement(EngagementType.INTERACTIVE, "نظر خود را ثبت کنید", "end", 0.7),
            ]
        }
    
    def _initialize_strategies(self) -> List[EngagementStrategy]:
        """Initialize engagement strategies"""
        return [
            EngagementStrategy(
                strategy_id="high_engagement",
                name="تعامل بالا",
                elements=[
                    self.engagement_elements[EngagementType.EMOJI][0],  # 🚨
                    self.engagement_elements[EngagementType.QUESTION][2],  # پیش‌بینی شما چیست؟
                    self.engagement_elements[EngagementType.CALL_TO_ACTION][2],  # برای دوستان ارسال کنید
                    self.engagement_elements[EngagementType.HASHTAG][1],  # #بیت_کوین
                ],
                target_engagement=0.8,
                success_metrics=["comments", "shares", "saves"]
            ),
            EngagementStrategy(
                strategy_id="educational",
                name="آموزشی",
                elements=[
                    self.engagement_elements[EngagementType.EMOJI][4],  # 💡
                    self.engagement_elements[EngagementType.QUESTION][6],  # آیا این تحلیل درست است؟
                    self.engagement_elements[EngagementType.CALL_TO_ACTION][1],  # این پست را ذخیره کنید
                    self.engagement_elements[EngagementType.VISUAL][4],  # 🎯 [نکته کلیدی]
                ],
                target_engagement=0.7,
                success_metrics=["saves", "shares", "comments"]
            ),
            EngagementStrategy(
                strategy_id="viral_potential",
                name="پتانسیل ویرال",
                elements=[
                    self.engagement_elements[EngagementType.EMOJI][6],  # 🔥
                    self.engagement_elements[EngagementType.QUESTION][0],  # نظر شما چیست؟
                    self.engagement_elements[EngagementType.CALL_TO_ACTION][2],  # برای دوستان ارسال کنید
                    self.engagement_elements[EngagementType.INTERACTIVE][0],  # رأی دهید
                ],
                target_engagement=0.9,
                success_metrics=["shares", "views", "comments"]
            ),
            EngagementStrategy(
                strategy_id="discussion_starter",
                name="شروع بحث",
                elements=[
                    self.engagement_elements[EngagementType.EMOJI][2],  # 💰
                    self.engagement_elements[EngagementType.QUESTION][7],  # کدام استراتژی بهتر است؟
                    self.engagement_elements[EngagementType.CALL_TO_ACTION][3],  # در کامنت‌ها بحث کنید
                    self.engagement_elements[EngagementType.HASHTAG][2],  # #فارکس
                ],
                target_engagement=0.75,
                success_metrics=["comments", "replies", "engagement_time"]
            )
        ]
    
    async def optimize_content_engagement(self, content: str, content_type: str, 
                                        target_engagement: EngagementLevel = EngagementLevel.MEDIUM) -> str:
        """Optimize content for maximum engagement"""
        # Select appropriate strategy based on content type and target engagement
        strategy = await self._select_engagement_strategy(content_type, target_engagement)
        
        # Apply engagement elements
        optimized_content = await self._apply_engagement_elements(content, strategy)
        
        # Add visual elements if needed
        if self._needs_visual_elements(content):
            optimized_content = await self._add_visual_elements(optimized_content, content_type)
        
        # Add interactive elements
        if target_engagement in [EngagementLevel.HIGH, EngagementLevel.VIRAL]:
            optimized_content = await self._add_interactive_elements(optimized_content, content_type)
        
        return optimized_content
    
    async def _select_engagement_strategy(self, content_type: str, target_engagement: EngagementLevel) -> EngagementStrategy:
        """Select the best engagement strategy based on content type and target"""
        # Map content types to strategies
        content_type_mapping = {
            "breaking_news": "high_engagement",
            "analysis": "educational",
            "prediction": "viral_potential",
            "educational": "educational",
            "market_update": "discussion_starter",
            "poll": "viral_potential",
            "quiz": "discussion_starter",
            "tip": "educational",
            "recap": "discussion_starter"
        }
        
        # Get strategy ID
        strategy_id = content_type_mapping.get(content_type, "discussion_starter")
        
        # Adjust based on target engagement
        if target_engagement == EngagementLevel.VIRAL:
            strategy_id = "viral_potential"
        elif target_engagement == EngagementLevel.HIGH:
            strategy_id = "high_engagement"
        
        # Find strategy
        strategy = next((s for s in self.engagement_strategies if s.strategy_id == strategy_id), 
                       self.engagement_strategies[0])
        
        return strategy
    
    async def _apply_engagement_elements(self, content: str, strategy: EngagementStrategy) -> str:
        """Apply engagement elements to content"""
        optimized_content = content
        
        # Apply elements in order
        for element in strategy.elements:
            if element.position == "start":
                optimized_content = f"{element.content} {optimized_content}"
            elif element.position == "end":
                optimized_content = f"{optimized_content}\n\n{element.content}"
            elif element.position == "middle":
                # Insert in the middle of the content
                sentences = optimized_content.split('.')
                if len(sentences) > 2:
                    middle_index = len(sentences) // 2
                    sentences.insert(middle_index, f" {element.content}")
                    optimized_content = '.'.join(sentences)
        
        return optimized_content
    
    def _needs_visual_elements(self, content: str) -> bool:
        """Check if content needs visual elements"""
        visual_keywords = ["نمودار", "چارت", "جدول", "تصویر", "گراف", "آمار", "داده"]
        return any(keyword in content for keyword in visual_keywords)
    
    async def _add_visual_elements(self, content: str, content_type: str) -> str:
        """Add visual elements to content"""
        visual_elements = {
            "analysis": "📊 [نمودار تحلیل]",
            "prediction": "🔮 [چارت پیش‌بینی]",
            "market_update": "📈 [نمودار بازار]",
            "educational": "💡 [راهنمای تصویری]",
            "breaking_news": "🚨 [تصویر خبر]"
        }
        
        visual_element = visual_elements.get(content_type, "📊 [نمودار]")
        
        # Insert visual element in the middle
        sentences = content.split('.')
        if len(sentences) > 2:
            middle_index = len(sentences) // 2
            sentences.insert(middle_index, f" {visual_element}")
            content = '.'.join(sentences)
        else:
            content += f"\n\n{visual_element}"
        
        return content
    
    async def _add_interactive_elements(self, content: str, content_type: str) -> str:
        """Add interactive elements to content"""
        interactive_elements = {
            "poll": "🗳️ [نظرسنجی در کامنت‌ها]",
            "quiz": "🧠 [سوال در کامنت‌ها]",
            "prediction": "🔮 [پیش‌بینی خود را بنویسید]",
            "analysis": "📊 [نظر خود را بدهید]"
        }
        
        interactive_element = interactive_elements.get(content_type, "💬 [نظر خود را بنویسید]")
        content += f"\n\n{interactive_element}"
        
        return content
    
    async def generate_engagement_variants(self, content: str, content_type: str, 
                                         num_variants: int = 3) -> List[str]:
        """Generate multiple engagement variants for A/B testing"""
        variants = []
        
        # Create variants with different engagement levels
        engagement_levels = [EngagementLevel.LOW, EngagementLevel.MEDIUM, EngagementLevel.HIGH]
        
        for i, level in enumerate(engagement_levels[:num_variants]):
            variant = await self.optimize_content_engagement(content, content_type, level)
            variants.append(variant)
        
        return variants
    
    async def track_engagement_performance(self, content_id: str, engagement_metrics: Dict[str, Any]):
        """Track engagement performance for optimization"""
        # Store performance data
        if content_id not in self.performance_tracking:
            self.performance_tracking[content_id] = {
                'total_views': 0,
                'total_engagement': 0,
                'engagement_rate': 0.0,
                'element_performance': {},
                'timestamp': datetime.now()
            }
        
        # Update metrics
        tracking = self.performance_tracking[content_id]
        tracking['total_views'] += engagement_metrics.get('views', 0)
        tracking['total_engagement'] += engagement_metrics.get('engagement', 0)
        tracking['engagement_rate'] = tracking['total_engagement'] / max(tracking['total_views'], 1)
        
        # Track element performance
        for element_type, performance in engagement_metrics.get('element_performance', {}).items():
            if element_type not in tracking['element_performance']:
                tracking['element_performance'][element_type] = []
            tracking['element_performance'][element_type].append(performance)
    
    async def get_engagement_insights(self) -> Dict[str, Any]:
        """Get engagement insights for optimization"""
        insights = {
            'best_performing_elements': [],
            'engagement_trends': {},
            'optimization_recommendations': [],
            'success_rates': {}
        }
        
        # Analyze element performance
        element_performance = {}
        for content_id, tracking in self.performance_tracking.items():
            for element_type, performances in tracking['element_performance'].items():
                if element_type not in element_performance:
                    element_performance[element_type] = []
                element_performance[element_type].extend(performances)
        
        # Calculate average performance per element type
        for element_type, performances in element_performance.items():
            if performances:
                avg_performance = sum(performances) / len(performances)
                insights['best_performing_elements'].append({
                    'element_type': element_type,
                    'avg_performance': avg_performance,
                    'usage_count': len(performances)
                })
        
        # Sort by performance
        insights['best_performing_elements'].sort(key=lambda x: x['avg_performance'], reverse=True)
        
        # Generate recommendations
        if insights['best_performing_elements']:
            best_element = insights['best_performing_elements'][0]
            insights['optimization_recommendations'].append(
                f"Use more {best_element['element_type']} elements (avg performance: {best_element['avg_performance']:.2f})"
            )
        
        return insights
    
    async def auto_optimize_engagement(self) -> Dict[str, Any]:
        """Automatically optimize engagement based on performance data"""
        insights = await self.get_engagement_insights()
        
        optimizations = {
            'element_adjustments': [],
            'strategy_adjustments': [],
            'content_improvements': []
        }
        
        # Adjust element usage based on performance
        for element_data in insights['best_performing_elements']:
            if element_data['avg_performance'] > 0.7:
                optimizations['element_adjustments'].append({
                    'element_type': element_data['element_type'],
                    'action': 'increase_usage',
                    'reason': 'high_performance'
                })
            elif element_data['avg_performance'] < 0.3:
                optimizations['element_adjustments'].append({
                    'element_type': element_data['element_type'],
                    'action': 'decrease_usage',
                    'reason': 'low_performance'
                })
        
        # Adjust strategies based on overall performance
        overall_engagement = sum(tracking['engagement_rate'] for tracking in self.performance_tracking.values()) / max(len(self.performance_tracking), 1)
        
        if overall_engagement < 0.5:
            optimizations['strategy_adjustments'].append({
                'action': 'increase_interactive_elements',
                'reason': 'low_overall_engagement'
            })
        elif overall_engagement > 0.8:
            optimizations['strategy_adjustments'].append({
                'action': 'maintain_current_strategy',
                'reason': 'high_overall_engagement'
            })
        
        return optimizations
