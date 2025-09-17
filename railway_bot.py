#!/usr/bin/env python3
"""
Railway-optimized single-file bot
Avoids all import issues by including everything in one file
"""

import sys
import os
import asyncio
import logging
import signal
import traceback
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
import aiohttp
import ccxt.async_support as ccxt
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import openai
import matplotlib.pyplot as plt
import mplfinance as mpf
import base64
import io

# Add paths
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Configuration
class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # Binance
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')
    
    # Trading
    TRADING_PAIRS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 
                     'ADA/USDT', 'MATIC/USDT', 'LTC/USDT', 'AVAX/USDT', 'OP/USDT']
    TIMEFRAMES = ['5m', '15m']
    CONFIDENCE_THRESHOLD = 0.52
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    TREND_RSI_LONG_MIN = 44
    TREND_RSI_SHORT_MAX = 56
    MIN_VOLUME_RATIO = 0.9
    RISK_WARNING = "⚠️ **هشدار ریسک:** این سیگنال‌ها صرفاً برای اهداف آموزشی هستند. معاملات کریپتو دارای ریسک بالایی است. همیشه مدیریت ریسک را رعایت کنید."
    
    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        if not cls.TELEGRAM_CHANNEL_ID:
            raise ValueError("TELEGRAM_CHANNEL_ID not set")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set")

# Database Manager
class DatabaseManager:
    def __init__(self):
        self.db_path = 'crypto_signals.db'
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create signals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                confidence REAL NOT NULL,
                timeframe TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                conditions_met TEXT,
                rationale TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                result TEXT DEFAULT 'PENDING'
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database tables created successfully")
    
    def save_signal(self, signal_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO signals (symbol, direction, entry_price, stop_loss, take_profit, 
                               confidence, timeframe, signal_type, conditions_met, rationale)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal_data['symbol'],
            signal_data['direction'],
            signal_data['entry_price'],
            signal_data.get('stop_loss'),
            signal_data.get('take_profit'),
            signal_data['confidence'],
            signal_data['timeframe'],
            signal_data['type'],
            json.dumps(signal_data.get('conditions_met', [])),
            json.dumps(signal_data.get('rationale', []))
        ))
        
        signal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return signal_id
    
    def get_recent_signals(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM signals 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        signals = []
        for row in rows:
            signals.append({
                'id': row[0],
                'symbol': row[1],
                'direction': row[2],
                'entry_price': row[3],
                'stop_loss': row[4],
                'take_profit': row[5],
                'confidence': row[6],
                'timeframe': row[7],
                'signal_type': row[8],
                'conditions_met': json.loads(row[9]) if row[9] else [],
                'rationale': json.loads(row[10]) if row[10] else [],
                'timestamp': datetime.fromisoformat(row[11]),
                'result': row[12]
            })
        
        return signals
    
    def get_performance_stats(self, days=7):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT COUNT(*) as total_signals,
                   SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as winning_signals,
                   SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losing_signals
            FROM signals 
            WHERE timestamp >= ?
        ''', (since_date,))
        
        row = cursor.fetchone()
        conn.close()
        
        total_signals = row[0] or 0
        winning_signals = row[1] or 0
        losing_signals = row[2] or 0
        
        win_rate = (winning_signals / total_signals * 100) if total_signals > 0 else 0
        
        return {
            'total_signals': total_signals,
            'winning_signals': winning_signals,
            'losing_signals': losing_signals,
            'win_rate': win_rate
        }
    
    def close(self):
        pass

# Exchange Data Fetcher
class ExchangeDataFetcher:
    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': Config.BINANCE_API_KEY,
            'secret': Config.BINANCE_SECRET_KEY,
            'sandbox': False,
            'enableRateLimit': True,
        })
    
    async def get_volume_filtered_pairs(self):
        try:
            tickers = await self.exchange.fetch_tickers()
            valid_pairs = []
            
            for pair in Config.TRADING_PAIRS:
                if pair in tickers:
                    ticker = tickers[pair]
                    volume_usd = ticker['quoteVolume']
                    
                    if volume_usd > 5000000:  # $5M minimum
                        valid_pairs.append(pair)
                        logger.info(f"{pair} passed volume filter: ${volume_usd:,.0f}")
            
            return valid_pairs
        except Exception as e:
            logger.error(f"Error fetching volume filtered pairs: {e}")
            return []
    
    async def fetch_ohlcv(self, symbol, timeframe, limit=200):
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return None
    
    async def close(self):
        await self.exchange.close()

# Signal Generator
class SignalGenerator:
    def __init__(self):
        pass
    
    def calculate_indicators(self, df):
        # Simple RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Simple EMA calculation
        ema21 = df['close'].ewm(span=21).mean()
        ema50 = df['close'].ewm(span=50).mean()
        ema200 = df['close'].ewm(span=200).mean()
        
        return {
            'rsi': rsi,
            'ema21': ema21,
            'ema50': ema50,
            'ema200': ema200
        }
    
    def generate_signal(self, symbol, df):
        try:
            if len(df) < 200:
                return None
            
            indicators = self.calculate_indicators(df)
            current_price = df['close'].iloc[-1]
            current_rsi = indicators['rsi'].iloc[-1]
            current_ema21 = indicators['ema21'].iloc[-1]
            current_ema50 = indicators['ema50'].iloc[-1]
            current_ema200 = indicators['ema200'].iloc[-1]
            
            conditions_met = []
            confidence = 0
            
            # Check for LONG signal
            if (current_price > current_ema200 and 
                current_ema21 > current_ema50 and 
                current_rsi > Config.TREND_RSI_LONG_MIN):
                
                conditions_met.append("Price > EMA200")
                conditions_met.append("EMA21 > EMA50 (bullish cross)")
                conditions_met.append(f"RSI > {Config.TREND_RSI_LONG_MIN}")
                confidence = 0.6
                
                if len(conditions_met) >= 3:
                    return {
                        'symbol': symbol,
                        'direction': 'LONG',
                        'entry_price': current_price,
                        'stop_loss': current_price * 0.98,  # 2% stop loss
                        'take_profit': current_price * 1.04,  # 4% take profit
                        'confidence': confidence,
                        'timeframe': '5m',
                        'type': 'trend_following',
                        'conditions_met': conditions_met,
                        'rationale': ['Bullish trend detected', 'RSI shows strength', 'EMA alignment positive']
                    }
            
            # Check for SHORT signal
            elif (current_price < current_ema200 and 
                  current_ema21 < current_ema50 and 
                  current_rsi < Config.TREND_RSI_SHORT_MAX):
                
                conditions_met.append("Price < EMA200")
                conditions_met.append("EMA21 < EMA50 (bearish cross)")
                conditions_met.append(f"RSI < {Config.TREND_RSI_SHORT_MAX}")
                confidence = 0.6
                
                if len(conditions_met) >= 3:
                    return {
                        'symbol': symbol,
                        'direction': 'SHORT',
                        'entry_price': current_price,
                        'stop_loss': current_price * 1.02,  # 2% stop loss
                        'take_profit': current_price * 0.96,  # 4% take profit
                        'confidence': confidence,
                        'timeframe': '5m',
                        'type': 'trend_following',
                        'conditions_met': conditions_met,
                        'rationale': ['Bearish trend detected', 'RSI shows weakness', 'EMA alignment negative']
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None

# Content Generator
class ContentGenerator:
    def __init__(self):
        openai.api_key = Config.OPENAI_API_KEY
    
    async def generate_education_tip(self):
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a crypto trading education expert. Write educational content in Persian about risk management in crypto trading."},
                    {"role": "user", "content": "Write a short educational tip about risk management in crypto trading."}
                ],
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            
            return {
                'title': '💡 نکته آموزشی: مدیریت ریسک',
                'content': content,
                'content_type': 'education_tip'
            }
        except Exception as e:
            logger.error(f"Error generating education tip: {e}")
            return None

# Telegram Bot
class TelegramBot:
    def __init__(self):
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher()
        self.channel_id = Config.TELEGRAM_CHANNEL_ID
        self.db = DatabaseManager()
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.dp.message(Command("start"))
        async def start_command(message: Message):
            await message.answer(
                "🤖 **بات سیگنال کریپتو**\n\n"
                "این بات به صورت خودکار سیگنال‌های معاملاتی و محتوای آموزشی تولید می‌کند.\n\n"
                "دستورات موجود:\n"
                "/status - وضعیت بات\n"
                "/signals - آخرین سیگنال‌ها\n"
                "/performance - آمار عملکرد\n"
                "/help - راهنما",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def send_signal(self, signal):
        try:
            message_text = self._format_signal_message(signal)
            
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Signal sent to channel: {signal['symbol']} {signal['direction']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending signal: {e}")
            return False
    
    def _format_signal_message(self, signal):
        signal_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
        direction_text = "خرید" if signal['direction'] == 'LONG' else "فروش"
        
        perf = self.db.get_performance_stats(7)
        recent_win_rate = perf.get('win_rate', 0.0)
        total_signals = perf.get('total_signals', 0)
        
        message = f"""
{signal_emoji} **سیگنال {direction_text} | {signal['symbol']} | {signal['timeframe']}**

📊 **نوع:** {signal['type']}

💵 **قیمت ورود:** ${signal['entry_price']:.4f}
🛑 **حد ضرر:** ${signal['stop_loss']:.4f}
🎯 **حد سود:** ${signal['take_profit']:.4f}
🎯 **اعتماد:** {signal['confidence'] * 100:.1f}%

🏆 **Win Rate اخیر:** {recent_win_rate:.1f}%
📈 **تعداد سیگنال‌های هفته:** {total_signals}

📋 **شرایط برآورده شده:**
"""
        
        for condition in signal.get('conditions_met', []):
            message += f"• {condition}\n"
        
        message += f"\n{Config.RISK_WARNING}"
        
        return message
    
    async def start_polling(self):
        try:
            logger.info("Starting Telegram bot polling...")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Error starting bot polling: {e}")
            raise
    
    async def stop(self):
        try:
            await self.bot.session.close()
            logger.info("Telegram bot stopped")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

# Scheduler Manager
class SchedulerManager:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db = DatabaseManager()
        self.exchange = ExchangeDataFetcher()
        self.signal_gen = SignalGenerator()
        self.telegram_bot = TelegramBot()
        self.content_gen = ContentGenerator()
        self._setup_jobs()
    
    def _setup_jobs(self):
        # Signal generation every 5 minutes
        self.scheduler.add_job(
            self._signal_generation_job,
            trigger=IntervalTrigger(minutes=5),
            id='signal_generation',
            name='Signal Generation'
        )
        
        # Daily content at 9 AM
        self.scheduler.add_job(
            self._daily_content_job,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_content',
            name='Daily Content'
        )
    
    async def _signal_generation_job(self):
        try:
            logger.info("Running signal generation job...")
            
            # Get valid pairs
            valid_pairs = await self.exchange.get_volume_filtered_pairs()
            
            for pair in valid_pairs[:3]:  # Limit to 3 pairs
                for timeframe in Config.TIMEFRAMES:
                    # Fetch data
                    df = await self.exchange.fetch_ohlcv(pair, timeframe, 200)
                    if df is None:
                        continue
                    
                    # Generate signal
                    signal = self.signal_gen.generate_signal(pair, df)
                    if signal and signal['confidence'] >= Config.CONFIDENCE_THRESHOLD:
                        # Save signal
                        signal_id = self.db.save_signal(signal)
                        signal['id'] = signal_id
                        
                        # Send to Telegram
                        await self.telegram_bot.send_signal(signal)
                        
                        logger.info(f"Signal generated and sent: {pair} {signal['direction']}")
                        break  # Only one signal per pair
            
        except Exception as e:
            logger.error(f"Error in signal generation job: {e}")
    
    async def _daily_content_job(self):
        try:
            logger.info("Running daily content job...")
            
            # Generate education tip
            content = await self.content_gen.generate_education_tip()
            if content:
                # Send content
                await self.telegram_bot.send_content(content)
                logger.info("Daily content sent")
            
        except Exception as e:
            logger.error(f"Error in daily content job: {e}")
    
    async def start(self):
        self.scheduler.start()
        logger.info("Scheduler started successfully")
    
    async def stop(self):
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

# Main Bot Class
class CryptoSignalBot:
    def __init__(self):
        self.config = Config()
        self.scheduler_manager = None
        self.telegram_bot = None
        self.db = None
        self.running = False
    
    async def initialize(self):
        try:
            logger.info("Initializing Crypto Signal Bot...")
            
            # Validate configuration
            self.config.validate()
            logger.info("Configuration validated successfully")
            
            # Initialize database
            self.db = DatabaseManager()
            logger.info("Database initialized successfully")
            
            # Initialize scheduler manager
            self.scheduler_manager = SchedulerManager()
            logger.info("Scheduler manager initialized successfully")
            
            # Initialize Telegram bot
            self.telegram_bot = TelegramBot()
            logger.info("Telegram bot initialized successfully")
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing application: {e}")
            raise
    
    async def start(self):
        try:
            logger.info("Starting Crypto Signal Bot...")
            
            # Start scheduler
            await self.scheduler_manager.start()
            logger.info("Scheduler started")
            
            # Start Telegram bot polling in background
            bot_task = asyncio.create_task(self.telegram_bot.start_polling())
            
            self.running = True
            logger.info("Crypto Signal Bot started successfully")
            
            # Keep the application running
            try:
                await bot_task
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            finally:
                await self.stop()
                
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            raise
    
    async def stop(self):
        try:
            logger.info("Stopping Crypto Signal Bot...")
            
            self.running = False
            
            # Stop scheduler
            if self.scheduler_manager:
                await self.scheduler_manager.stop()
                logger.info("Scheduler stopped")
            
            # Stop Telegram bot
            if self.telegram_bot:
                await self.telegram_bot.stop()
                logger.info("Telegram bot stopped")
            
            # Close database
            if self.db:
                self.db.close()
                logger.info("Database connection closed")
            
            logger.info("Crypto Signal Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping application: {e}")
    
    def setup_signal_handlers(self):
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main entry point"""
    bot = CryptoSignalBot()
    
    try:
        # Setup signal handlers
        bot.setup_signal_handlers()
        
        # Initialize application
        await bot.initialize()
        
        # Check if running in test mode
        if len(sys.argv) > 1 and sys.argv[1] == '--test':
            logger.info("Running in test mode...")
            return
        
        # Start application
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
