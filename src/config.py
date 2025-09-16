"""
Configuration management for the Crypto Signal Bot
"""
import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

class Config:
    """Main configuration class"""
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Exchange Configuration
    EXCHANGE_NAME = os.getenv('EXCHANGE_NAME', 'binance')
    EXCHANGE_API_KEY = os.getenv('EXCHANGE_API_KEY')
    EXCHANGE_SECRET = os.getenv('EXCHANGE_SECRET')
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///crypto_signals.db')
    
    # Content Configuration
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'fa')
    CONTENT_TONE = os.getenv('CONTENT_TONE', 'professional')
    
    # Signal Configuration (REALISTIC settings after validation)
    MIN_VOLUME_USD = int(os.getenv('MIN_VOLUME_USD', '5000000'))  # 5M USD volume filter
    RSI_OVERSOLD = int(os.getenv('RSI_OVERSOLD', '35'))  # Realistic oversold level
    RSI_OVERBOUGHT = int(os.getenv('RSI_OVERBOUGHT', '65'))  # Realistic overbought level  
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.50'))  # Realistic threshold for signal generation
    
    # Ultra High Win Rate Configuration
    ULTRA_HIGH_WINRATE_MODE = os.getenv('ULTRA_HIGH_WINRATE_MODE', 'false').lower() == 'true'
    # Slightly reduced to allow more high-quality signals while preserving high win rate
    ULTRA_MIN_CONFIDENCE = float(os.getenv('ULTRA_MIN_CONFIDENCE', '0.90'))
    MIN_VOLUME_RATIO = float(os.getenv('MIN_VOLUME_RATIO', '1.0'))  # Relaxed from 1.5 to 1.0 after debug analysis
    MIN_ATR_RATIO = float(os.getenv('MIN_ATR_RATIO', '1.2'))  # ATR must be 1.2x average (ultra-permissive)
    MIN_TREND_STRENGTH = float(os.getenv('MIN_TREND_STRENGTH', '25'))  # ADX minimum (ultra-permissive)
    MIN_RSI_DIVERGENCE = float(os.getenv('MIN_RSI_DIVERGENCE', '10'))  # RSI divergence (ultra-permissive)
    MAX_VOLATILITY = float(os.getenv('MAX_VOLATILITY', '0.05'))  # Max 5% volatility
    MIN_MOMENTUM_CONSISTENCY = int(os.getenv('MIN_MOMENTUM_CONSISTENCY', '3'))  # 3 consecutive candles
    
    # Risk Management - Optimized for better Sharpe ratio
    POSITION_SIZE = float(os.getenv('POSITION_SIZE', '0.05'))  # Reduced from 0.1
    MAX_DRAWDOWN_PCT = float(os.getenv('MAX_DRAWDOWN_PCT', '3.0'))  # Reduced for better risk control
    MAX_CONCURRENT_TRADES = int(os.getenv('MAX_CONCURRENT_TRADES', '2'))  # Allow 2 trades for diversification
    MAX_CONSECUTIVE_LOSSES = int(os.getenv('MAX_CONSECUTIVE_LOSSES', '3'))  # Balanced: max 3 consecutive losses
    POSITION_SIZE_REDUCTION = float(os.getenv('POSITION_SIZE_REDUCTION', '0.5'))  # Moderate reduction (50% reduction)
    
    # Take-Profit and Stop-Loss Parameters - Ultra-optimized for Sharpe ratio
    TAKE_PROFIT_ATR_MULTIPLIER = float(os.getenv('TAKE_PROFIT_ATR_MULTIPLIER', '2.4'))  # Better R:R ratio
    STOP_LOSS_ATR_MULTIPLIER = float(os.getenv('STOP_LOSS_ATR_MULTIPLIER', '1.2'))  # Tighter stop-loss
    MIN_RISK_REWARD_RATIO = float(os.getenv('MIN_RISK_REWARD_RATIO', '2.0'))  # Better R:R ratio (2:1)
    
    # Filter Configuration
    VOLUME_THRESHOLD = float(os.getenv('VOLUME_THRESHOLD', '1.2'))  # New
    ATR_THRESHOLD = float(os.getenv('ATR_THRESHOLD', '0.8'))  # New
    # Extended hours to enable more opportunities while still configurable
    TRADING_HOURS_START = int(os.getenv('TRADING_HOURS_START', '0'))  # 24/7 operation for crypto
    TRADING_HOURS_END = int(os.getenv('TRADING_HOURS_END', '23'))  # 24/7 operation for crypto

    # Trade pacing limits
    MAX_DAILY_TRADES = int(os.getenv('MAX_DAILY_TRADES', '6'))
    MIN_TIME_BETWEEN_TRADES = int(os.getenv('MIN_TIME_BETWEEN_TRADES', '1200'))  # 20 minutes
    
    # Symbol Weighting (for portfolio management)
    SYMBOL_WEIGHTS = {
        'SOL/USDT': 0.30,  # Best performer
        'XRP/USDT': 0.25,  # Good performer
        'ETH/USDT': 0.20,  # Average performer
        'BTC/USDT': 0.15,  # Poor performer
        'BNB/USDT': 0.10   # Poor performer
    }

    # Correlation threshold for diversification (lower = stricter)
    SYMBOL_CORRELATION_THRESHOLD = float(os.getenv('SYMBOL_CORRELATION_THRESHOLD', '0.4'))
    
    # Scheduling Configuration (per spec)
    SIGNAL_CHECK_INTERVAL = int(os.getenv('SIGNAL_CHECK_INTERVAL', '300'))  # Every 5 minutes
    MARKET_SUMMARY_TIME = os.getenv('MARKET_SUMMARY_TIME', '09:00')  # Daily 09:00
    EDUCATION_TIME = os.getenv('EDUCATION_TIME', '19:00')  # Daily 19:00
    ALTCOIN_SPOTLIGHT_TIME = os.getenv('ALTCOIN_SPOTLIGHT_TIME', '13:00')  # Daily 13:00
    WEEKLY_REPORT_DAY = int(os.getenv('WEEKLY_REPORT_DAY', '4'))  # Friday
    WEEKLY_REPORT_TIME = os.getenv('WEEKLY_REPORT_TIME', '17:00')  # Friday evening
    PROMO_POST_TIME = os.getenv('PROMO_POST_TIME', '18:00')  # After weekly report
    
    # Trading Pairs (per spec - 10 liquid coins)
    TRADING_PAIRS = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT',
        'ADA/USDT', 'MATIC/USDT', 'LTC/USDT', 'AVAX/USDT', 'OP/USDT'
    ]
    
    # Daily signal targets (per spec: 2-5 signals daily)
    MIN_DAILY_SIGNALS = int(os.getenv('MIN_DAILY_SIGNALS', '2'))
    MAX_DAILY_SIGNALS = int(os.getenv('MAX_DAILY_SIGNALS', '5'))
    
    # Timeframes (per spec - parallel processing)
    TIMEFRAMES = ['5m', '15m']  # Both timeframes processed in parallel
    PRIMARY_TIMEFRAME = '5m'  # Main timeframe for signals
    SECONDARY_TIMEFRAME = '15m'  # Confirmation timeframe

    # Trend strategy RSI thresholds (REALISTIC after debug analysis)
    TREND_RSI_LONG_MIN = int(os.getenv('TREND_RSI_LONG_MIN', '45'))  # Realistic: 45 for more LONG opportunities
    TREND_RSI_SHORT_MAX = int(os.getenv('TREND_RSI_SHORT_MAX', '55'))  # Realistic: 55 for more SHORT opportunities
    
    # Risk Warning (Persian)
    RISK_WARNING = """
⚠️ **هشدار ریسک:**
• این سیگنال‌ها صرفاً برای اهداف آموزشی و تحقیقاتی ارائه می‌شوند
• معاملات ارزهای دیجیتال دارای ریسک بالایی است و ممکن است منجر به از دست دادن سرمایه شود
• همیشه مدیریت ریسک را رعایت کنید و بیش از توان مالی خود سرمایه‌گذاری نکنید
• این بات مسئولیتی در قبال ضررهای احتمالی ندارد
    """
    
    # Risk Warning (English)
    RISK_WARNING_EN = """
⚠️ **Risk Warning:**
• These signals are provided for educational and research purposes only
• Cryptocurrency trading involves high risk and may result in loss of capital
• Always practice proper risk management and never invest more than you can afford to lose
• This bot is not responsible for any potential losses
    """
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_CHANNEL_ID',
            'OPENAI_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
