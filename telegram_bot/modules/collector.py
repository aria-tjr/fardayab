from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from telegram_bot.config.settings import Settings
from telegram_bot.modules.crypto import fetch_crypto_and_fx
from telegram_bot.modules.news import fetch_combined_news
from telegram_bot.modules.trends import fetch_trending
from telegram_bot.modules.sports import fetch_sports
from telegram_bot.modules.persian_apis import PersianContentEnhancer
from telegram_bot.modules.free_persian_apis import FreePersianAPIs
from telegram_bot.modules.crypto_content_types import CryptoForexContentManager
from telegram_bot.modules.technical_analysis import AdvancedTechnicalAnalysis, AdvancedMarketScanner
from telegram_bot.modules.portfolio_tracker import AdvancedPortfolioTracker
from telegram_bot.modules.advanced_news import AdvancedNewsAggregator
from telegram_bot.modules.trading_signals import AdvancedTradingSignals
from telegram_bot.modules.ai_predictions import AIPredictor
from telegram_bot.modules.risk_management import AdvancedRiskManager
from telegram_bot.modules.binance_api import BinanceAPI, BinanceWebSocketManager
from telegram_bot.modules.advanced_posting import AdvancedPostingManager, PostType
from telegram_bot.modules.intelligent_scheduler import IntelligentContentScheduler, ContentPriority
from telegram_bot.modules.engagement_optimizer import EngagementOptimizer, EngagementLevel
from telegram_bot.modules.visual_enhancer import VisualContentEnhancer, VisualStyle
from telegram_bot.modules.ab_testing import ABTestingManager, TestType
from telegram_bot.modules.user_retention import UserRetentionManager, RetentionStrategy
from telegram_bot.modules.analytics_tracker import AnalyticsTracker, MetricType, ContentType


async def _retry_api_call(api_func, max_retries: int = 3, delay: float = 2.0):
    """Retry API call with exponential backoff"""
    import asyncio
    import logging
    
    log = logging.getLogger(__name__)
    
    for attempt in range(max_retries):
        try:
            result = await api_func()
            if result:
                return result
        except Exception as e:
            log.warning(f"API call attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                log.error(f"All {max_retries} API attempts failed")
    
    return None

async def collect_all(settings: Settings) -> dict[str, Any]:
    import logging
    log = logging.getLogger(__name__)
    
    # Enhanced data collection with retry logic
    async def _collect_with_retry(func, *args, **kwargs):
        for attempt in range(settings.CONNECTION_RETRY_ATTEMPTS):
            try:
                result = await func(*args, **kwargs)
                if result:  # If we got data, return it
                    return result
            except Exception as e:
                log.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                if attempt < settings.CONNECTION_RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(settings.CONNECTION_RETRY_DELAY)
        return None

    # Initialize all advanced modules
    persian_enhancer = PersianContentEnhancer(settings)
    free_persian_apis = FreePersianAPIs(settings)
    crypto_forex_content = CryptoForexContentManager(settings)
    technical_analysis = AdvancedTechnicalAnalysis(settings)
    market_scanner = AdvancedMarketScanner(settings)
    portfolio_tracker = AdvancedPortfolioTracker(settings)
    news_aggregator = AdvancedNewsAggregator(settings)
    trading_signals = AdvancedTradingSignals(settings)
    ai_predictor = AIPredictor(settings)
    risk_manager = AdvancedRiskManager(settings)
    binance_api = BinanceAPI(settings)
    binance_ws_manager = BinanceWebSocketManager(binance_api)

    # Run collectors concurrently with retry logic
    crypto_task = asyncio.create_task(_collect_with_retry(lambda: fetch_crypto_and_fx(settings)))
    news_task = asyncio.create_task(_collect_with_retry(
        lambda: fetch_combined_news(
            settings.NEWSAPI_KEY,
            settings.NEWSDATA_KEY,
            settings.MEDIASTACK_KEY,
            settings.NEWS_LANGUAGE,
            settings.HTTP_TIMEOUT,
        )
    ))
    trends_task = asyncio.create_task(_collect_with_retry(lambda: fetch_trending("iran", 10)))
    trends_cmp_task = asyncio.create_task(_collect_with_retry(lambda: fetch_trending(settings.TRENDS_COMPARE_REGION, 10)))
    sports_task = asyncio.create_task(_collect_with_retry(lambda: fetch_sports(settings)))
    
    # Advanced content collection with error handling
    async def safe_persian_data():
        try:
            return await persian_enhancer.get_enhanced_persian_data()
        except Exception as e:
            log.warning(f"Persian data collection failed: {e}")
            return {}
    
    async def safe_free_persian_data():
        try:
            return await free_persian_apis.get_enhanced_persian_content()
        except Exception as e:
            log.warning(f"Free Persian data collection failed: {e}")
            return {}
    
    async def safe_crypto_forex_content():
        try:
            return await crypto_forex_content.get_all_crypto_forex_content()
        except Exception as e:
            log.warning(f"Crypto/Forex content collection failed: {e}")
            return {}
    
    persian_task = asyncio.create_task(safe_persian_data())
    free_persian_task = asyncio.create_task(safe_free_persian_data())
    crypto_forex_content_task = asyncio.create_task(safe_crypto_forex_content())
    
    # Advanced analysis tasks with error handling
    async def safe_crypto_news():
        try:
            return await news_aggregator.fetch_crypto_news()
        except Exception as e:
            log.warning(f"Crypto news collection failed: {e}")
            return []
    
    async def safe_forex_news():
        try:
            return await news_aggregator.fetch_forex_news()
        except Exception as e:
            log.warning(f"Forex news collection failed: {e}")
            return []
    
    async def safe_crypto_scanner():
        try:
            return await market_scanner.scan_crypto_markets()
        except Exception as e:
            log.warning(f"Crypto scanner failed: {e}")
            return []
    
    async def safe_forex_scanner():
        try:
            return await market_scanner.scan_forex_markets()
        except Exception as e:
            log.warning(f"Forex scanner failed: {e}")
            return []
    
    async def safe_btc_analysis():
        try:
            return await technical_analysis.get_comprehensive_analysis("BTC")
        except Exception as e:
            log.warning(f"BTC analysis failed: {e}")
            return {}
    
    async def safe_eth_analysis():
        try:
            return await technical_analysis.get_comprehensive_analysis("ETH")
        except Exception as e:
            log.warning(f"ETH analysis failed: {e}")
            return {}
    
    async def safe_btc_predictions():
        try:
            return await ai_predictor.get_comprehensive_predictions("BTC")
        except Exception as e:
            log.warning(f"BTC predictions failed: {e}")
            return {}
    
    async def safe_eth_predictions():
        try:
            return await ai_predictor.get_comprehensive_predictions("ETH")
        except Exception as e:
            log.warning(f"ETH predictions failed: {e}")
            return {}
    
    async def safe_btc_signals():
        try:
            return await trading_signals.generate_signals("BTC")
        except Exception as e:
            log.warning(f"BTC signals failed: {e}")
            return []
    
    async def safe_eth_signals():
        try:
            return await trading_signals.generate_signals("ETH")
        except Exception as e:
            log.warning(f"ETH signals failed: {e}")
            return []
    
    crypto_news_task = asyncio.create_task(safe_crypto_news())
    forex_news_task = asyncio.create_task(safe_forex_news())
    crypto_scanner_task = asyncio.create_task(safe_crypto_scanner())
    forex_scanner_task = asyncio.create_task(safe_forex_scanner())
    btc_analysis_task = asyncio.create_task(safe_btc_analysis())
    eth_analysis_task = asyncio.create_task(safe_eth_analysis())
    btc_predictions_task = asyncio.create_task(safe_btc_predictions())
    eth_predictions_task = asyncio.create_task(safe_eth_predictions())
    btc_signals_task = asyncio.create_task(safe_btc_signals())
    eth_signals_task = asyncio.create_task(safe_eth_signals())
    
    # Binance data collection with error handling
    async def safe_binance_market_summary():
        try:
            return await binance_api.get_market_summary()
        except Exception as e:
            log.warning(f"Binance market summary failed: {e}")
            return {}
    
    async def safe_binance_crypto_prices():
        try:
            return await binance_api.get_crypto_prices()
        except Exception as e:
            log.warning(f"Binance crypto prices failed: {e}")
            return {}
    
    async def safe_binance_forex_rates():
        try:
            return await binance_api.get_forex_rates()
        except Exception as e:
            log.warning(f"Binance forex rates failed: {e}")
            return {}
    
    binance_market_summary_task = asyncio.create_task(safe_binance_market_summary())
    binance_crypto_prices_task = asyncio.create_task(safe_binance_crypto_prices())
    binance_forex_rates_task = asyncio.create_task(safe_binance_forex_rates())

    crypto = await crypto_task
    news = await news_task
    trends = await trends_task
    trends_cmp = await trends_cmp_task
    sports = await sports_task
    persian_data = await persian_task
    free_persian_data = await free_persian_task
    crypto_forex_content_data = await crypto_forex_content_task
    
    # Advanced analysis results
    crypto_news = await crypto_news_task
    forex_news = await forex_news_task
    crypto_scanner = await crypto_scanner_task
    forex_scanner = await forex_scanner_task
    btc_analysis = await btc_analysis_task
    eth_analysis = await eth_analysis_task
    btc_predictions = await btc_predictions_task
    eth_predictions = await eth_predictions_task
    btc_signals = await btc_signals_task
    eth_signals = await eth_signals_task
    
    # Binance data results
    binance_market_summary = await binance_market_summary_task
    binance_crypto_prices = await binance_crypto_prices_task
    binance_forex_rates = await binance_forex_rates_task

    # Enhanced debugging info
    log.info(f"Real-time data collection results - Crypto: {bool(crypto)}, News: {len(news) if news else 0}, Trends: {len(trends) if trends else 0}, Sports: {len(sports) if sports else 0}, Persian: {persian_data.get('enhanced', False)}, Free Persian: {free_persian_data.get('free_apis_active', False)}, Crypto/Forex Content: {crypto_forex_content_data.get('crypto_forex_content_active', False)}")
    
    # Log connectivity status
    if settings.ENABLE_REAL_TIME_DATA:
        log.info("Real-time data collection enabled - using latest available data")

    # Retry failed APIs with exponential backoff
    if not crypto:
        log.info("Retrying crypto API with backoff...")
        crypto = await _retry_api_call(lambda: fetch_crypto_and_fx(settings))
    
    if not news:
        log.info("Retrying news API with backoff...")
        news = await _retry_api_call(lambda: fetch_combined_news(
            settings.NEWSAPI_KEY, 
            settings.NEWSDATA_KEY, 
            settings.MEDIASTACK_KEY, 
            settings.NEWS_LANGUAGE, 
            settings.HTTP_TIMEOUT
        ))
    
    if not trends:
        log.info("Retrying trends API with backoff...")
        trends = await _retry_api_call(lambda: fetch_trending(settings))
    
    if not sports:
        log.info("Retrying sports API with backoff...")
        sports = await _retry_api_call(lambda: fetch_sports(settings))

    # If all APIs still fail after retries, raise an error instead of using fallback
    if not any([crypto, news, trends, sports, persian_data.get('enhanced', False)]):
        log.error("All APIs failed after retries - no data available")
        raise Exception("Unable to fetch real data from any API source")

    # Enhance news with Persian content if available
    if persian_data.get('enhanced', False) and persian_data.get('persian_news'):
        # Merge Persian news with existing news
        persian_news = persian_data['persian_news']
        if news:
            news.extend(persian_news)
        else:
            news = persian_news
        log.info(f"Enhanced news with {len(persian_news)} Persian articles")

    # Initialize advanced features
    posting_manager = AdvancedPostingManager(settings)
    content_scheduler = IntelligentContentScheduler(settings)
    engagement_optimizer = EngagementOptimizer(settings)
    visual_enhancer = VisualContentEnhancer(settings)
    ab_testing = ABTestingManager(settings)
    user_retention = UserRetentionManager(settings)
    analytics_tracker = AnalyticsTracker(settings)

    # Advanced posting strategies
    async def safe_posting_strategies():
        try:
            strategies = await posting_manager.get_posting_schedule(datetime.now())
            return {"strategies": strategies, "count": len(strategies)}
        except Exception as e:
            log.warning(f"Posting strategies failed: {e}")
            return {"strategies": [], "count": 0}

    # Intelligent content scheduling
    async def safe_content_scheduling():
        try:
            daily_schedule = await content_scheduler.get_daily_schedule(datetime.now())
            return {"daily_schedule": daily_schedule, "count": len(daily_schedule)}
        except Exception as e:
            log.warning(f"Content scheduling failed: {e}")
            return {"daily_schedule": [], "count": 0}

    # Engagement optimization
    async def safe_engagement_optimization():
        try:
            # Test engagement optimization on sample content
            sample_content = "تحلیل بازار کریپتو امروز"
            optimized_content = await engagement_optimizer.optimize_content_engagement(
                sample_content, "analysis", EngagementLevel.HIGH
            )
            return {"optimized_content": optimized_content, "success": True}
        except Exception as e:
            log.warning(f"Engagement optimization failed: {e}")
            return {"optimized_content": "", "success": False}

    # Visual content enhancement
    async def safe_visual_enhancement():
        try:
            sample_data = {"price_data": [50000, 51000, 49000], "symbol": "BTC/USDT"}
            visual_content = await visual_enhancer.generate_visual_content(
                "market_update", sample_data, VisualStyle.MODERN
            )
            return {"visual_content": visual_content, "success": True}
        except Exception as e:
            log.warning(f"Visual enhancement failed: {e}")
            return {"visual_content": {}, "success": False}

    # A/B testing
    async def safe_ab_testing():
        try:
            # Create a sample A/B test
            test = await ab_testing.create_content_variants_test(
                "تحلیل بازار کریپتو", "analysis"
            )
            return {"test_created": True, "test_id": test.test_id}
        except Exception as e:
            log.warning(f"A/B testing failed: {e}")
            return {"test_created": False, "test_id": None}

    # User retention
    async def safe_user_retention():
        try:
            # Get retention insights
            insights = await user_retention.get_retention_insights()
            return {"insights": insights, "success": True}
        except Exception as e:
            log.warning(f"User retention failed: {e}")
            return {"insights": {}, "success": False}

    # Analytics tracking
    async def safe_analytics_tracking():
        try:
            # Track sample metrics
            await analytics_tracker.track_metric(
                MetricType.VIEWS, 100, "sample_content", ContentType.ANALYSIS
            )
            await analytics_tracker.track_metric(
                MetricType.ENGAGEMENT, 25, "sample_content", ContentType.ANALYSIS
            )
            
            # Get dashboard data
            dashboard_data = await analytics_tracker.get_analytics_dashboard_data()
            return {"dashboard_data": dashboard_data, "success": True}
        except Exception as e:
            log.warning(f"Analytics tracking failed: {e}")
            return {"dashboard_data": {}, "success": False}

    # Execute advanced features concurrently
    posting_strategies = await safe_posting_strategies()
    content_scheduling = await safe_content_scheduling()
    engagement_optimization = await safe_engagement_optimization()
    visual_enhancement = await safe_visual_enhancement()
    ab_testing_result = await safe_ab_testing()
    user_retention_result = await safe_user_retention()
    analytics_tracking = await safe_analytics_tracking()

    return {
        "crypto": crypto,
        "news": news,
        "trends": trends,
        "trends_compare": {"region": settings.TRENDS_COMPARE_REGION, "values": trends_cmp or []},
        "sports": sports,
        "persian_enhanced": persian_data.get('enhanced', False),
        "iranian_financial": persian_data.get('iranian_financial', {}),
        "free_persian_content": free_persian_data,
        "persian_books": free_persian_data.get('persian_books', []),
        "countries_info": free_persian_data.get('countries_info', []),
        "persian_calendar": free_persian_data.get('persian_calendar', {}),
        "crypto_forex_content": crypto_forex_content_data,
        "cryptocurrency": crypto_forex_content_data.get('cryptocurrency', {}),
        "forex": crypto_forex_content_data.get('forex', {}),
        "trading": crypto_forex_content_data.get('trading', {}),
        "regulatory": crypto_forex_content_data.get('regulatory', {}),
        
        # Advanced analysis data
        "advanced_news": {
            "crypto_news": crypto_news,
            "forex_news": forex_news
        },
        "market_scanner": {
            "crypto_opportunities": crypto_scanner,
            "forex_opportunities": forex_scanner
        },
        "technical_analysis": {
            "btc_analysis": btc_analysis,
            "eth_analysis": eth_analysis
        },
        "ai_predictions": {
            "btc_predictions": btc_predictions,
            "eth_predictions": eth_predictions
        },
        "trading_signals": {
            "btc_signals": btc_signals,
            "eth_signals": eth_signals
        },
        "advanced_modules": {
            "technical_analysis": True,
            "portfolio_tracker": True,
            "news_aggregator": True,
            "trading_signals": True,
            "ai_predictions": True,
            "risk_management": True,
            "market_scanner": True,
            "binance_api": True
        },
        
        # Binance real-time data
        "binance_data": {
            "market_summary": binance_market_summary,
            "crypto_prices": binance_crypto_prices,
            "forex_rates": binance_forex_rates
        },
        
        # Advanced posting and engagement features
        "advanced_posting": {
            "strategies": posting_strategies,
            "content_scheduling": content_scheduling,
            "engagement_optimization": engagement_optimization,
            "visual_enhancement": visual_enhancement,
            "ab_testing": ab_testing_result,
            "user_retention": user_retention_result,
            "analytics_tracking": analytics_tracking
        },
        
        # Advanced modules status
        "advanced_modules": {
            "technical_analysis": True,
            "portfolio_tracker": True,
            "news_aggregator": True,
            "trading_signals": True,
            "ai_predictions": True,
            "risk_management": True,
            "market_scanner": True,
            "binance_api": True,
            "advanced_posting": True,
            "intelligent_scheduler": True,
            "engagement_optimizer": True,
            "visual_enhancer": True,
            "ab_testing": True,
            "user_retention": True,
            "analytics_tracker": True
        }
    }
