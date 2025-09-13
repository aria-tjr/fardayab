from __future__ import annotations

import asyncio
import logging
import random
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class TestStatus(Enum):
    """A/B test status"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestType(Enum):
    """A/B test types"""
    CONTENT_VARIANT = "content_variant"
    POSTING_TIME = "posting_time"
    ENGAGEMENT_ELEMENTS = "engagement_elements"
    VISUAL_STYLE = "visual_style"
    HASHTAG_STRATEGY = "hashtag_strategy"
    CALL_TO_ACTION = "call_to_action"


class MetricType(Enum):
    """Metrics to track"""
    VIEWS = "views"
    ENGAGEMENT = "engagement"
    COMMENTS = "comments"
    SHARES = "shares"
    SAVES = "saves"
    CLICKS = "clicks"
    CONVERSION = "conversion"


@dataclass
class TestVariant:
    """A/B test variant configuration"""
    variant_id: str
    name: str
    content: str
    configuration: Dict[str, Any]
    traffic_percentage: float
    metrics: Dict[str, float]
    performance_score: float = 0.0


@dataclass
class ABTest:
    """A/B test configuration"""
    test_id: str
    test_name: str
    test_type: TestType
    description: str
    variants: List[TestVariant]
    status: TestStatus
    start_date: datetime
    end_date: Optional[datetime]
    target_audience: str
    success_metrics: List[MetricType]
    minimum_sample_size: int
    confidence_level: float
    current_winner: Optional[str] = None
    statistical_significance: float = 0.0


class ABTestingManager:
    """Advanced A/B testing system for content optimization"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.active_tests = {}
        self.completed_tests = {}
        self.test_results = {}
        self.performance_history = {}
        
    async def create_test(self, test_name: str, test_type: TestType, 
                         base_content: str, variants: List[Dict[str, Any]],
                         target_audience: str = "all",
                         duration_days: int = 7,
                         traffic_split: List[float] = None) -> ABTest:
        """Create a new A/B test"""
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create test variants
        test_variants = []
        if not traffic_split:
            traffic_split = [1.0 / len(variants)] * len(variants)
        
        for i, (variant_config, traffic_percentage) in enumerate(zip(variants, traffic_split)):
            variant = TestVariant(
                variant_id=f"variant_{i+1}",
                name=variant_config.get("name", f"Variant {i+1}"),
                content=variant_config.get("content", base_content),
                configuration=variant_config.get("configuration", {}),
                traffic_percentage=traffic_percentage,
                metrics={}
            )
            test_variants.append(variant)
        
        # Create test
        test = ABTest(
            test_id=test_id,
            test_name=test_name,
            test_type=test_type,
            description=f"A/B test for {test_name}",
            variants=test_variants,
            status=TestStatus.DRAFT,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=duration_days),
            target_audience=target_audience,
            success_metrics=[MetricType.ENGAGEMENT, MetricType.VIEWS],
            minimum_sample_size=100,
            confidence_level=0.95
        )
        
        self.active_tests[test_id] = test
        return test
    
    async def start_test(self, test_id: str) -> bool:
        """Start an A/B test"""
        if test_id not in self.active_tests:
            return False
        
        test = self.active_tests[test_id]
        test.status = TestStatus.RUNNING
        test.start_date = datetime.now()
        
        log.info(f"Started A/B test: {test.test_name}")
        return True
    
    async def stop_test(self, test_id: str) -> bool:
        """Stop an A/B test"""
        if test_id not in self.active_tests:
            return False
        
        test = self.active_tests[test_id]
        test.status = TestStatus.COMPLETED
        test.end_date = datetime.now()
        
        # Analyze results
        winner = await self._analyze_test_results(test)
        test.current_winner = winner
        
        # Move to completed tests
        self.completed_tests[test_id] = test
        del self.active_tests[test_id]
        
        log.info(f"Completed A/B test: {test.test_name}, Winner: {winner}")
        return True
    
    async def get_test_variant(self, test_id: str, user_id: str = None) -> Optional[TestVariant]:
        """Get a test variant for a user"""
        if test_id not in self.active_tests:
            return None
        
        test = self.active_tests[test_id]
        if test.status != TestStatus.RUNNING:
            return None
        
        # Use user_id for consistent variant assignment
        if user_id:
            random.seed(hash(user_id + test_id))
        
        # Select variant based on traffic percentage
        rand = random.random()
        cumulative = 0.0
        
        for variant in test.variants:
            cumulative += variant.traffic_percentage
            if rand <= cumulative:
                return variant
        
        # Fallback to first variant
        return test.variants[0] if test.variants else None
    
    async def record_test_metric(self, test_id: str, variant_id: str, 
                               metric_type: MetricType, value: float):
        """Record a metric for a test variant"""
        if test_id not in self.active_tests:
            return False
        
        test = self.active_tests[test_id]
        variant = next((v for v in test.variants if v.variant_id == variant_id), None)
        
        if not variant:
            return False
        
        # Initialize metric if not exists
        if metric_type.value not in variant.metrics:
            variant.metrics[metric_type.value] = []
        
        # Record metric
        variant.metrics[metric_type.value].append({
            'value': value,
            'timestamp': datetime.now()
        })
        
        # Update performance score
        await self._update_variant_performance(variant, test)
        
        return True
    
    async def _update_variant_performance(self, variant: TestVariant, test: ABTest):
        """Update variant performance score"""
        total_score = 0.0
        metric_count = 0
        
        for metric_type in test.success_metrics:
            if metric_type.value in variant.metrics:
                values = [m['value'] for m in variant.metrics[metric_type.value]]
                if values:
                    avg_value = statistics.mean(values)
                    total_score += avg_value
                    metric_count += 1
        
        if metric_count > 0:
            variant.performance_score = total_score / metric_count
        else:
            variant.performance_score = 0.0
    
    async def _analyze_test_results(self, test: ABTest) -> Optional[str]:
        """Analyze A/B test results and determine winner"""
        if not test.variants:
            return None
        
        # Calculate performance scores
        for variant in test.variants:
            await self._update_variant_performance(variant, test)
        
        # Find winner based on performance score
        winner = max(test.variants, key=lambda v: v.performance_score)
        
        # Calculate statistical significance
        if len(test.variants) >= 2:
            test.statistical_significance = await self._calculate_statistical_significance(test)
        
        return winner.variant_id
    
    async def _calculate_statistical_significance(self, test: ABTest) -> float:
        """Calculate statistical significance of test results"""
        if len(test.variants) < 2:
            return 0.0
        
        # Get performance scores
        scores = [v.performance_score for v in test.variants]
        
        if len(scores) < 2:
            return 0.0
        
        # Calculate t-test for statistical significance
        try:
            from scipy import stats
            t_stat, p_value = stats.ttest_ind(scores[:len(scores)//2], scores[len(scores)//2:])
            return 1 - p_value  # Convert to confidence level
        except ImportError:
            # Fallback calculation
            mean_diff = abs(scores[0] - scores[1])
            avg_score = statistics.mean(scores)
            if avg_score > 0:
                return min(mean_diff / avg_score, 1.0)
            return 0.0
    
    async def get_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed test results"""
        test = self.active_tests.get(test_id) or self.completed_tests.get(test_id)
        if not test:
            return None
        
        results = {
            'test_id': test.test_id,
            'test_name': test.test_name,
            'test_type': test.test_type.value,
            'status': test.status.value,
            'start_date': test.start_date.isoformat(),
            'end_date': test.end_date.isoformat() if test.end_date else None,
            'variants': [],
            'winner': test.current_winner,
            'statistical_significance': test.statistical_significance,
            'recommendations': []
        }
        
        # Add variant results
        for variant in test.variants:
            variant_result = {
                'variant_id': variant.variant_id,
                'name': variant.name,
                'performance_score': variant.performance_score,
                'traffic_percentage': variant.traffic_percentage,
                'metrics': variant.metrics
            }
            results['variants'].append(variant_result)
        
        # Add recommendations
        if test.status == TestStatus.COMPLETED:
            results['recommendations'] = await self._generate_recommendations(test)
        
        return results
    
    async def _generate_recommendations(self, test: ABTest) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if test.current_winner:
            winner = next((v for v in test.variants if v.variant_id == test.current_winner), None)
            if winner:
                recommendations.append(f"Use {winner.name} as the primary variant")
        
        if test.statistical_significance > 0.95:
            recommendations.append("Results are statistically significant")
        elif test.statistical_significance > 0.80:
            recommendations.append("Results show some significance, consider longer testing")
        else:
            recommendations.append("Results are not statistically significant, consider more data")
        
        # Performance-based recommendations
        if test.variants:
            best_variant = max(test.variants, key=lambda v: v.performance_score)
            worst_variant = min(test.variants, key=lambda v: v.performance_score)
            
            improvement = best_variant.performance_score - worst_variant.performance_score
            if improvement > 0.2:
                recommendations.append(f"Significant improvement of {improvement:.2f} points")
            elif improvement > 0.1:
                recommendations.append(f"Moderate improvement of {improvement:.2f} points")
            else:
                recommendations.append("Minimal difference between variants")
        
        return recommendations
    
    async def get_active_tests(self) -> List[Dict[str, Any]]:
        """Get all active tests"""
        active_tests = []
        for test in self.active_tests.values():
            active_tests.append({
                'test_id': test.test_id,
                'test_name': test.test_name,
                'test_type': test.test_type.value,
                'status': test.status.value,
                'start_date': test.start_date.isoformat(),
                'variants_count': len(test.variants)
            })
        return active_tests
    
    async def get_completed_tests(self) -> List[Dict[str, Any]]:
        """Get all completed tests"""
        completed_tests = []
        for test in self.completed_tests.values():
            completed_tests.append({
                'test_id': test.test_id,
                'test_name': test.test_name,
                'test_type': test.test_type.value,
                'status': test.status.value,
                'start_date': test.start_date.isoformat(),
                'end_date': test.end_date.isoformat() if test.end_date else None,
                'winner': test.current_winner,
                'statistical_significance': test.statistical_significance
            })
        return completed_tests
    
    async def create_content_variants_test(self, base_content: str, content_type: str) -> ABTest:
        """Create a content variants A/B test"""
        # Generate content variants
        variants = [
            {
                "name": "Original",
                "content": base_content,
                "configuration": {"style": "original"}
            },
            {
                "name": "High Engagement",
                "content": await self._create_high_engagement_variant(base_content),
                "configuration": {"style": "high_engagement"}
            },
            {
                "name": "Visual Focus",
                "content": await self._create_visual_focus_variant(base_content),
                "configuration": {"style": "visual_focus"}
            }
        ]
        
        return await self.create_test(
            f"Content Variants - {content_type}",
            TestType.CONTENT_VARIANT,
            base_content,
            variants,
            duration_days=7
        )
    
    async def create_posting_time_test(self, content: str, content_type: str) -> ABTest:
        """Create a posting time A/B test"""
        variants = [
            {
                "name": "Morning (8:00 AM)",
                "content": content,
                "configuration": {"posting_time": "08:00", "timezone": "Asia/Tehran"}
            },
            {
                "name": "Afternoon (2:00 PM)",
                "content": content,
                "configuration": {"posting_time": "14:00", "timezone": "Asia/Tehran"}
            },
            {
                "name": "Evening (8:00 PM)",
                "content": content,
                "configuration": {"posting_time": "20:00", "timezone": "Asia/Tehran"}
            }
        ]
        
        return await self.create_test(
            f"Posting Time - {content_type}",
            TestType.POSTING_TIME,
            content,
            variants,
            duration_days=14
        )
    
    async def create_hashtag_strategy_test(self, content: str, content_type: str) -> ABTest:
        """Create a hashtag strategy A/B test"""
        variants = [
            {
                "name": "Minimal Hashtags",
                "content": content + "\n\n#کریپتو #بازار",
                "configuration": {"hashtag_count": 2, "strategy": "minimal"}
            },
            {
                "name": "Moderate Hashtags",
                "content": content + "\n\n#کریپتو #بیت_کوین #فارکس #معاملات #بازار",
                "configuration": {"hashtag_count": 5, "strategy": "moderate"}
            },
            {
                "name": "Extensive Hashtags",
                "content": content + "\n\n#کریپتو #بیت_کوین #اتریوم #فارکس #معاملات #بازار #تحلیل #پیش‌بینی #نکته #فردایاب",
                "configuration": {"hashtag_count": 10, "strategy": "extensive"}
            }
        ]
        
        return await self.create_test(
            f"Hashtag Strategy - {content_type}",
            TestType.HASHTAG_STRATEGY,
            content,
            variants,
            duration_days=10
        )
    
    async def _create_high_engagement_variant(self, content: str) -> str:
        """Create high engagement variant of content"""
        # Add engagement hooks
        engagement_hooks = ["🚨", "📊", "💰", "🔮"]
        hook = random.choice(engagement_hooks)
        
        # Add call to action
        ctas = [
            "نظر شما چیست؟",
            "آیا موافقید؟",
            "پیش‌بینی شما چیست؟",
            "تجربه خود را به اشتراک بگذارید"
        ]
        cta = random.choice(ctas)
        
        return f"{hook} {content}\n\n💬 {cta}"
    
    async def _create_visual_focus_variant(self, content: str) -> str:
        """Create visual focus variant of content"""
        # Add visual elements
        visual_elements = [
            "📊 [نمودار در ادامه]",
            "🖼️ [تصویر مرتبط]",
            "📈 [چارت تحلیل]",
            "💡 [راهنمای تصویری]"
        ]
        visual = random.choice(visual_elements)
        
        # Add visual call to action
        visual_cta = "این تصویر را ذخیره کنید"
        
        return f"{content}\n\n{visual}\n\n💾 {visual_cta}"
    
    async def get_test_insights(self) -> Dict[str, Any]:
        """Get overall A/B testing insights"""
        insights = {
            'total_tests': len(self.active_tests) + len(self.completed_tests),
            'active_tests': len(self.active_tests),
            'completed_tests': len(self.completed_tests),
            'successful_tests': 0,
            'average_improvement': 0.0,
            'best_performing_tests': [],
            'recommendations': []
        }
        
        # Analyze completed tests
        total_improvement = 0.0
        successful_tests = 0
        
        for test in self.completed_tests.values():
            if test.current_winner and test.statistical_significance > 0.8:
                successful_tests += 1
                
                # Calculate improvement
                if test.variants:
                    winner = next((v for v in test.variants if v.variant_id == test.current_winner), None)
                    if winner:
                        avg_performance = statistics.mean([v.performance_score for v in test.variants])
                        improvement = winner.performance_score - avg_performance
                        total_improvement += improvement
                        
                        insights['best_performing_tests'].append({
                            'test_name': test.test_name,
                            'test_type': test.test_type.value,
                            'improvement': improvement,
                            'significance': test.statistical_significance
                        })
        
        insights['successful_tests'] = successful_tests
        if successful_tests > 0:
            insights['average_improvement'] = total_improvement / successful_tests
        
        # Sort best performing tests
        insights['best_performing_tests'].sort(key=lambda x: x['improvement'], reverse=True)
        
        # Generate recommendations
        if insights['successful_tests'] > 0:
            insights['recommendations'].append("Continue A/B testing for content optimization")
        else:
            insights['recommendations'].append("Increase test duration or sample size")
        
        if insights['average_improvement'] > 0.2:
            insights['recommendations'].append("A/B testing is showing significant improvements")
        elif insights['average_improvement'] > 0.1:
            insights['recommendations'].append("A/B testing is showing moderate improvements")
        else:
            insights['recommendations'].append("Consider different testing strategies")
        
        return insights
