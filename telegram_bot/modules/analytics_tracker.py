from __future__ import annotations

import asyncio
import logging
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to track"""
    VIEWS = "views"
    ENGAGEMENT = "engagement"
    COMMENTS = "comments"
    SHARES = "shares"
    SAVES = "saves"
    CLICKS = "clicks"
    CONVERSION = "conversion"
    RETENTION = "retention"
    REVENUE = "revenue"


class TimeGranularity(Enum):
    """Time granularity for analytics"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ContentType(Enum):
    """Content types for analytics"""
    BREAKING_NEWS = "breaking_news"
    ANALYSIS = "analysis"
    EDUCATIONAL = "educational"
    MARKET_UPDATE = "market_update"
    PREDICTION = "prediction"
    POLL = "poll"
    QUIZ = "quiz"
    TIP = "tip"
    RECAP = "recap"


@dataclass
class MetricData:
    """Metric data structure"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    content_id: str
    content_type: ContentType
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class AnalyticsReport:
    """Analytics report structure"""
    report_id: str
    report_type: str
    time_period: Tuple[datetime, datetime]
    metrics: Dict[str, float]
    insights: List[str]
    recommendations: List[str]
    generated_at: datetime


@dataclass
class PerformanceBenchmark:
    """Performance benchmark structure"""
    content_type: ContentType
    metric_type: MetricType
    benchmark_value: float
    current_value: float
    performance_ratio: float
    trend: str  # "improving", "declining", "stable"


class AnalyticsTracker:
    """Advanced analytics and performance tracking system"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.metrics_data = []
        self.performance_benchmarks = {}
        self.analytics_reports = {}
        self.trend_analysis = {}
        self.correlation_analysis = {}
        
    async def track_metric(self, metric_type: MetricType, value: float, 
                          content_id: str, content_type: ContentType,
                          user_id: str = None, metadata: Dict[str, Any] = None) -> bool:
        """Track a metric"""
        metric_data = MetricData(
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            content_id=content_id,
            content_type=content_type,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        self.metrics_data.append(metric_data)
        
        # Update performance benchmarks
        await self._update_performance_benchmarks(metric_data)
        
        # Update trend analysis
        await self._update_trend_analysis(metric_data)
        
        return True
    
    async def _update_performance_benchmarks(self, metric_data: MetricData):
        """Update performance benchmarks"""
        key = (metric_data.content_type, metric_data.metric_type)
        
        if key not in self.performance_benchmarks:
            self.performance_benchmarks[key] = {
                'values': [],
                'benchmark_value': 0.0,
                'current_value': 0.0,
                'performance_ratio': 0.0,
                'trend': 'stable'
            }
        
        benchmark = self.performance_benchmarks[key]
        benchmark['values'].append(metric_data.value)
        
        # Keep only last 100 values
        if len(benchmark['values']) > 100:
            benchmark['values'] = benchmark['values'][-100:]
        
        # Calculate current value (average of last 10)
        recent_values = benchmark['values'][-10:]
        benchmark['current_value'] = statistics.mean(recent_values) if recent_values else 0.0
        
        # Calculate benchmark value (average of all values)
        benchmark['benchmark_value'] = statistics.mean(benchmark['values']) if benchmark['values'] else 0.0
        
        # Calculate performance ratio
        if benchmark['benchmark_value'] > 0:
            benchmark['performance_ratio'] = benchmark['current_value'] / benchmark['benchmark_value']
        
        # Determine trend
        if len(benchmark['values']) >= 5:
            recent_avg = statistics.mean(benchmark['values'][-5:])
            previous_avg = statistics.mean(benchmark['values'][-10:-5]) if len(benchmark['values']) >= 10 else recent_avg
            
            if recent_avg > previous_avg * 1.1:
                benchmark['trend'] = 'improving'
            elif recent_avg < previous_avg * 0.9:
                benchmark['trend'] = 'declining'
            else:
                benchmark['trend'] = 'stable'
    
    async def _update_trend_analysis(self, metric_data: MetricData):
        """Update trend analysis"""
        key = f"{metric_data.content_type.value}_{metric_data.metric_type.value}"
        
        if key not in self.trend_analysis:
            self.trend_analysis[key] = {
                'values': [],
                'timestamps': [],
                'trend_direction': 'stable',
                'trend_strength': 0.0
            }
        
        trend = self.trend_analysis[key]
        trend['values'].append(metric_data.value)
        trend['timestamps'].append(metric_data.timestamp)
        
        # Keep only last 50 data points
        if len(trend['values']) > 50:
            trend['values'] = trend['values'][-50:]
            trend['timestamps'] = trend['timestamps'][-50:]
        
        # Calculate trend direction and strength
        if len(trend['values']) >= 5:
            await self._calculate_trend(trend)
    
    async def _calculate_trend(self, trend_data: Dict[str, Any]):
        """Calculate trend direction and strength"""
        values = trend_data['values']
        
        if len(values) < 5:
            return
        
        # Simple linear regression to determine trend
        n = len(values)
        x = list(range(n))
        y = values
        
        # Calculate slope
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator != 0:
            slope = numerator / denominator
            
            # Determine trend direction
            if slope > 0.1:
                trend_data['trend_direction'] = 'increasing'
            elif slope < -0.1:
                trend_data['trend_direction'] = 'decreasing'
            else:
                trend_data['trend_direction'] = 'stable'
            
            # Calculate trend strength (R-squared)
            y_pred = [y_mean + slope * (x[i] - x_mean) for i in range(n)]
            ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
            ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
            
            if ss_tot != 0:
                r_squared = 1 - (ss_res / ss_tot)
                trend_data['trend_strength'] = max(0, r_squared)
    
    async def get_metrics_summary(self, time_period: Tuple[datetime, datetime] = None,
                                 content_type: ContentType = None,
                                 metric_type: MetricType = None) -> Dict[str, Any]:
        """Get metrics summary for specified filters"""
        if time_period is None:
            time_period = (datetime.now() - timedelta(days=30), datetime.now())
        
        # Filter metrics data
        filtered_data = self.metrics_data.copy()
        
        # Filter by time period
        start_time, end_time = time_period
        filtered_data = [m for m in filtered_data if start_time <= m.timestamp <= end_time]
        
        # Filter by content type
        if content_type:
            filtered_data = [m for m in filtered_data if m.content_type == content_type]
        
        # Filter by metric type
        if metric_type:
            filtered_data = [m for m in filtered_data if m.metric_type == metric_type]
        
        if not filtered_data:
            return {'error': 'No data found for the specified filters'}
        
        # Calculate summary statistics
        values = [m.value for m in filtered_data]
        
        summary = {
            'total_records': len(filtered_data),
            'time_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'statistics': {
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'min': min(values),
                'max': max(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0
            },
            'content_types': {},
            'metric_types': {},
            'daily_averages': await self._calculate_daily_averages(filtered_data)
        }
        
        # Group by content type
        content_type_groups = {}
        for metric in filtered_data:
            ct = metric.content_type.value
            if ct not in content_type_groups:
                content_type_groups[ct] = []
            content_type_groups[ct].append(metric.value)
        
        for ct, values in content_type_groups.items():
            summary['content_types'][ct] = {
                'count': len(values),
                'mean': statistics.mean(values),
                'total': sum(values)
            }
        
        # Group by metric type
        metric_type_groups = {}
        for metric in filtered_data:
            mt = metric.metric_type.value
            if mt not in metric_type_groups:
                metric_type_groups[mt] = []
            metric_type_groups[mt].append(metric.value)
        
        for mt, values in metric_type_groups.items():
            summary['metric_types'][mt] = {
                'count': len(values),
                'mean': statistics.mean(values),
                'total': sum(values)
            }
        
        return summary
    
    async def _calculate_daily_averages(self, filtered_data: List[MetricData]) -> Dict[str, float]:
        """Calculate daily averages for the filtered data"""
        daily_totals = {}
        daily_counts = {}
        
        for metric in filtered_data:
            date_key = metric.timestamp.date().isoformat()
            if date_key not in daily_totals:
                daily_totals[date_key] = 0
                daily_counts[date_key] = 0
            
            daily_totals[date_key] += metric.value
            daily_counts[date_key] += 1
        
        daily_averages = {}
        for date_key in daily_totals:
            daily_averages[date_key] = daily_totals[date_key] / daily_counts[date_key]
        
        return daily_averages
    
    async def generate_analytics_report(self, report_type: str, 
                                      time_period: Tuple[datetime, datetime] = None) -> AnalyticsReport:
        """Generate comprehensive analytics report"""
        if time_period is None:
            time_period = (datetime.now() - timedelta(days=30), datetime.now())
        
        report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get metrics summary
        summary = await self.get_metrics_summary(time_period)
        
        # Calculate key metrics
        metrics = {
            'total_views': summary['metric_types'].get('views', {}).get('total', 0),
            'total_engagement': summary['metric_types'].get('engagement', {}).get('total', 0),
            'total_comments': summary['metric_types'].get('comments', {}).get('total', 0),
            'total_shares': summary['metric_types'].get('shares', {}).get('total', 0),
            'total_saves': summary['metric_types'].get('saves', {}).get('total', 0),
            'engagement_rate': 0.0,
            'content_performance': {}
        }
        
        # Calculate engagement rate
        if metrics['total_views'] > 0:
            metrics['engagement_rate'] = metrics['total_engagement'] / metrics['total_views']
        
        # Calculate content performance
        for content_type, data in summary['content_types'].items():
            metrics['content_performance'][content_type] = {
                'total_views': data['total'],
                'average_engagement': data['mean'],
                'content_count': data['count']
            }
        
        # Generate insights
        insights = await self._generate_insights(summary, metrics)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(summary, metrics)
        
        report = AnalyticsReport(
            report_id=report_id,
            report_type=report_type,
            time_period=time_period,
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            generated_at=datetime.now()
        )
        
        self.analytics_reports[report_id] = report
        return report
    
    async def _generate_insights(self, summary: Dict[str, Any], metrics: Dict[str, Any]) -> List[str]:
        """Generate insights from analytics data"""
        insights = []
        
        # Engagement rate insights
        engagement_rate = metrics['engagement_rate']
        if engagement_rate > 0.8:
            insights.append("عالی! نرخ تعامل شما بسیار بالا است (بالای 80%)")
        elif engagement_rate > 0.6:
            insights.append("خوب! نرخ تعامل شما در سطح مناسبی است (60-80%)")
        elif engagement_rate > 0.4:
            insights.append("نرخ تعامل شما متوسط است (40-60%) - نیاز به بهبود دارد")
        else:
            insights.append("نرخ تعامل شما پایین است (زیر 40%) - نیاز به اقدام فوری دارد")
        
        # Content type performance insights
        content_performance = metrics['content_performance']
        if content_performance:
            best_content = max(content_performance.items(), key=lambda x: x[1]['average_engagement'])
            worst_content = min(content_performance.items(), key=lambda x: x[1]['average_engagement'])
            
            insights.append(f"بهترین نوع محتوا: {best_content[0]} (میانگین تعامل: {best_content[1]['average_engagement']:.2f})")
            insights.append(f"ضعیف‌ترین نوع محتوا: {worst_content[0]} (میانگین تعامل: {worst_content[1]['average_engagement']:.2f})")
        
        # Trend insights
        for key, trend_data in self.trend_analysis.items():
            if trend_data['trend_direction'] == 'increasing' and trend_data['trend_strength'] > 0.7:
                insights.append(f"روند مثبت قوی در {key} (قدرت روند: {trend_data['trend_strength']:.2f})")
            elif trend_data['trend_direction'] == 'decreasing' and trend_data['trend_strength'] > 0.7:
                insights.append(f"روند منفی قوی در {key} (قدرت روند: {trend_data['trend_strength']:.2f})")
        
        return insights
    
    async def _generate_recommendations(self, summary: Dict[str, Any], metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analytics"""
        recommendations = []
        
        # Engagement rate recommendations
        engagement_rate = metrics['engagement_rate']
        if engagement_rate < 0.6:
            recommendations.append("نرخ تعامل پایین - از عناصر تعاملی بیشتری استفاده کنید")
            recommendations.append("سوالات و نظرسنجی‌ها را افزایش دهید")
            recommendations.append("محتوای بصری و جذاب‌تر تولید کنید")
        
        # Content type recommendations
        content_performance = metrics['content_performance']
        if content_performance:
            # Find content types with low performance
            low_performance = [ct for ct, data in content_performance.items() 
                             if data['average_engagement'] < 0.5]
            
            if low_performance:
                recommendations.append(f"نوع محتوای {', '.join(low_performance)} نیاز به بهبود دارد")
            
            # Find content types with high performance
            high_performance = [ct for ct, data in content_performance.items() 
                              if data['average_engagement'] > 0.8]
            
            if high_performance:
                recommendations.append(f"نوع محتوای {', '.join(high_performance)} عملکرد عالی دارد - بیشتر تولید کنید")
        
        # Trend-based recommendations
        for key, trend_data in self.trend_analysis.items():
            if trend_data['trend_direction'] == 'decreasing' and trend_data['trend_strength'] > 0.5:
                recommendations.append(f"روند منفی در {key} - استراتژی خود را تغییر دهید")
            elif trend_data['trend_direction'] == 'increasing' and trend_data['trend_strength'] > 0.5:
                recommendations.append(f"روند مثبت در {key} - استراتژی فعلی را ادامه دهید")
        
        return recommendations
    
    async def get_performance_benchmarks(self) -> List[PerformanceBenchmark]:
        """Get performance benchmarks"""
        benchmarks = []
        
        for (content_type, metric_type), data in self.performance_benchmarks.items():
            benchmark = PerformanceBenchmark(
                content_type=content_type,
                metric_type=metric_type,
                benchmark_value=data['benchmark_value'],
                current_value=data['current_value'],
                performance_ratio=data['performance_ratio'],
                trend=data['trend']
            )
            benchmarks.append(benchmark)
        
        return benchmarks
    
    async def get_trend_analysis(self) -> Dict[str, Any]:
        """Get trend analysis results"""
        return self.trend_analysis
    
    async def get_correlation_analysis(self) -> Dict[str, float]:
        """Get correlation analysis between different metrics"""
        correlations = {}
        
        # Get all metric types
        metric_types = list(set(m.metric_type for m in self.metrics_data))
        
        # Calculate correlations between different metric types
        for i, metric_type1 in enumerate(metric_types):
            for metric_type2 in metric_types[i+1:]:
                values1 = [m.value for m in self.metrics_data if m.metric_type == metric_type1]
                values2 = [m.value for m in self.metrics_data if m.metric_type == metric_type2]
                
                if len(values1) == len(values2) and len(values1) > 1:
                    correlation = await self._calculate_correlation(values1, values2)
                    correlations[f"{metric_type1.value}_{metric_type2.value}"] = correlation
        
        return correlations
    
    async def _calculate_correlation(self, values1: List[float], values2: List[float]) -> float:
        """Calculate correlation coefficient between two sets of values"""
        if len(values1) != len(values2) or len(values1) < 2:
            return 0.0
        
        n = len(values1)
        mean1 = statistics.mean(values1)
        mean2 = statistics.mean(values2)
        
        numerator = sum((values1[i] - mean1) * (values2[i] - mean2) for i in range(n))
        denominator = (sum((values1[i] - mean1) ** 2 for i in range(n)) * 
                      sum((values2[i] - mean2) ** 2 for i in range(n))) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    async def get_analytics_dashboard_data(self) -> Dict[str, Any]:
        """Get data for analytics dashboard"""
        # Get recent metrics summary
        recent_summary = await self.get_metrics_summary(
            time_period=(datetime.now() - timedelta(days=7), datetime.now())
        )
        
        # Get performance benchmarks
        benchmarks = await self.get_performance_benchmarks()
        
        # Get trend analysis
        trends = await self.get_trend_analysis()
        
        # Get correlation analysis
        correlations = await self.get_correlation_analysis()
        
        return {
            'recent_summary': recent_summary,
            'benchmarks': [
                {
                    'content_type': b.content_type.value,
                    'metric_type': b.metric_type.value,
                    'benchmark_value': b.benchmark_value,
                    'current_value': b.current_value,
                    'performance_ratio': b.performance_ratio,
                    'trend': b.trend
                }
                for b in benchmarks
            ],
            'trends': trends,
            'correlations': correlations,
            'generated_at': datetime.now().isoformat()
        }
