"""
Scheduling system using APScheduler
"""
import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional
import traceback
import base64

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from aiogram.types import BufferedInputFile
from aiogram.enums import ParseMode

from ..config import Config
from ..exchange.data_fetcher import ExchangeDataFetcher
from ..strategies.signal_generator import SignalGenerator
from ..charts.chart_generator import ChartGenerator
from ..content.content_generator import ContentGenerator
from ..telegram.bot import TelegramBot
from ..storage.models import DatabaseManager

logger = logging.getLogger(__name__)

class SchedulerManager:
    """Manages all scheduled tasks"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.exchange_fetcher = ExchangeDataFetcher()
        self.signal_generator = SignalGenerator()
        self.chart_generator = ChartGenerator()
        self.content_generator = ContentGenerator()
        self.telegram_bot = TelegramBot()
        self.db = DatabaseManager()
        self.active_positions = []  # Track active positions
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Setup all scheduled jobs"""
        try:
            # Signal generation job - every 5 minutes
            self.scheduler.add_job(
                self._signal_generation_job,
                IntervalTrigger(seconds=Config.SIGNAL_CHECK_INTERVAL),
                id='signal_generation',
                name='Signal Generation',
                max_instances=1,
                replace_existing=True
            )
            
            # Market summary job - daily at 9:00 AM
            market_summary_time = Config.MARKET_SUMMARY_TIME.split(':')
            self.scheduler.add_job(
                self._market_summary_job,
                CronTrigger(
                    hour=int(market_summary_time[0]),
                    minute=int(market_summary_time[1])
                ),
                id='market_summary',
                name='Daily Market Summary',
                max_instances=1,
                replace_existing=True
            )
            
            # Education tip job - daily at 7:00 PM
            education_time = Config.EDUCATION_TIME.split(':')
            self.scheduler.add_job(
                self._education_tip_job,
                CronTrigger(
                    hour=int(education_time[0]),
                    minute=int(education_time[1])
                ),
                id='education_tip',
                name='Daily Education Tip',
                max_instances=1,
                replace_existing=True
            )
            
            # Altcoin spotlight job - daily at 12:00 PM
            spotlight_time = Config.ALTCOIN_SPOTLIGHT_TIME.split(':')
            self.scheduler.add_job(
                self._altcoin_spotlight_job,
                CronTrigger(
                    hour=int(spotlight_time[0]),
                    minute=int(spotlight_time[1])
                ),
                id='altcoin_spotlight',
                name='Daily Altcoin Spotlight',
                max_instances=1,
                replace_existing=True
            )
            
            # Weekly report job - Friday at 6:00 PM
            weekly_time = Config.WEEKLY_REPORT_TIME.split(':')
            self.scheduler.add_job(
                self._weekly_report_job,
                CronTrigger(
                    day_of_week=Config.WEEKLY_REPORT_DAY,
                    hour=int(weekly_time[0]),
                    minute=int(weekly_time[1])
                ),
                id='weekly_report',
                name='Weekly Performance Report',
                max_instances=1,
                replace_existing=True
            )

            # Promotional post right after weekly report (e.g., +10 minutes)
            promo_hour = int(weekly_time[0])
            promo_minute = (int(weekly_time[1]) + 10) % 60
            promo_hour = (promo_hour + (1 if int(weekly_time[1]) + 10 >= 60 else 0)) % 24
            self.scheduler.add_job(
                self._promotional_post_job,
                CronTrigger(
                    day_of_week=Config.WEEKLY_REPORT_DAY,
                    hour=promo_hour,
                    minute=promo_minute
                ),
                id='promo_post',
                name='Weekly Promotional Post',
                max_instances=1,
                replace_existing=True
            )
            
            # Glossary entry job - daily at 3:00 PM
            self.scheduler.add_job(
                self._glossary_entry_job,
                CronTrigger(hour=15, minute=0),
                id='glossary_entry',
                name='Daily Glossary Entry',
                max_instances=1,
                replace_existing=True
            )
            
            # Performance update job - every hour
            self.scheduler.add_job(
                self._performance_update_job,
                IntervalTrigger(hours=1),
                id='performance_update',
                name='Performance Update',
                max_instances=1,
                replace_existing=True
            )
            
            logger.info("All scheduled jobs configured successfully")
            
        except Exception as e:
            logger.error(f"Error setting up scheduled jobs: {e}")
            raise
    
    async def _signal_generation_job(self):
        """Generate and send trading signals"""
        try:
            logger.info("Starting signal generation job...")
            
            # Get volume-filtered pairs
            valid_pairs = await self.exchange_fetcher.get_volume_filtered_pairs()
            
            if not valid_pairs:
                logger.warning("No valid pairs found for signal generation")
                return
            
            # Get market data for valid pairs
            market_data = await self.exchange_fetcher.get_market_data(
                valid_pairs, Config.TIMEFRAMES
            )
            
            # Generate signals
            signals = self.signal_generator.generate_signals_batch(market_data, self.exchange_fetcher)
            
            if not signals:
                logger.info("No signals generated")
                return
            
            # Update active positions first
            self._update_active_positions()
            
            # Process and send signals with portfolio management
            for signal in signals:
                try:
                    # Check if we can open new position (portfolio management)
                    if not self._can_open_position(signal):
                        continue
                    
                    # Apply symbol weighting
                    signal = self._apply_symbol_weighting(signal)
                    
                    # Save signal to database
                    signal_id = self.db.save_signal(signal)
                    if signal_id:
                        signal['id'] = signal_id.id
                    
                    # Add to active positions
                    self.active_positions.append({
                        'signal_id': signal_id.id if signal_id else None,
                        'symbol': signal['symbol'],
                        'direction': signal['direction'],
                        'entry_time': signal['timestamp'],
                        'entry_price': signal['entry_price'],
                        'stop_loss': signal['stop_loss'],
                        'take_profit': signal['take_profit'],
                        'confidence': signal['confidence']
                    })
                    
                    # Generate chart
                    symbol_data = market_data.get(signal['symbol'], {})
                    if signal['timeframe'] in symbol_data:
                        df = symbol_data[signal['timeframe']]
                        indicators = self.signal_generator.calculate_indicators(df)
                        chart_image = self.chart_generator.create_signal_chart(
                            df, signal, indicators
                        )
                    else:
                        chart_image = None
                    
                    # Send signal to Telegram
                    await self.telegram_bot.send_signal(signal, chart_image)
                    
                    logger.info(f"Signal processed: {signal['symbol']} {signal['direction']}")
                    
                except Exception as e:
                    logger.error(f"Error processing signal {signal.get('symbol', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Signal generation job completed. Generated {len(signals)} signals")
            
        except Exception as e:
            logger.error(f"Error in signal generation job: {e}")
            logger.error(traceback.format_exc())
    
    async def _market_summary_job(self):
        """Generate and send daily market summary"""
        try:
            logger.info("Starting market summary job...")
            
            # Get market data
            market_data = await self.exchange_fetcher.get_market_data(
                Config.TRADING_PAIRS, Config.TIMEFRAMES
            )
            
            # Get recent signals
            recent_signals = self.db.get_recent_signals(10)
            
            # Generate market summary content
            content = await self.content_generator.generate_market_summary(
                market_data, recent_signals
            )
            
            if content:
                # Save content to database
                self.db.save_content(content)
                
                # Generate market summary chart
                chart_image = self.chart_generator.create_market_summary_chart(market_data)
                
                # Send to Telegram
                await self.telegram_bot.send_market_summary(market_data, chart_image)
                
                logger.info("Market summary sent successfully")
            else:
                logger.warning("Failed to generate market summary content")
            
        except Exception as e:
            logger.error(f"Error in market summary job: {e}")
            logger.error(traceback.format_exc())
    
    async def _education_tip_job(self):
        """Generate and send daily education tip"""
        try:
            logger.info("Starting education tip job...")
            
            # Generate education content
            content = await self.content_generator.generate_education_tip()
            
            if content:
                # Save content to database
                self.db.save_content(content)
                
                # Send to Telegram
                await self.telegram_bot.send_content(content)
                
                logger.info("Education tip sent successfully")
            else:
                logger.warning("Failed to generate education tip content")
            
        except Exception as e:
            logger.error(f"Error in education tip job: {e}")
            logger.error(traceback.format_exc())
    
    async def _altcoin_spotlight_job(self):
        """Generate and send daily altcoin spotlight"""
        try:
            logger.info("Starting altcoin spotlight job...")
            
            # Select a random altcoin (excluding BTC)
            altcoins = [pair for pair in Config.TRADING_PAIRS if pair != 'BTC/USDT']
            if not altcoins:
                logger.warning("No altcoins available for spotlight")
                return
            
            import random
            selected_altcoin = random.choice(altcoins)
            
            # Get market data for selected altcoin
            market_data = await self.exchange_fetcher.get_market_data(
                [selected_altcoin], Config.TIMEFRAMES
            )
            
            # Generate spotlight content
            content = await self.content_generator.generate_altcoin_spotlight(
                selected_altcoin, market_data
            )
            
            if content:
                # Save content to database
                self.db.save_content(content)
                
                # Send to Telegram
                await self.telegram_bot.send_content(content)
                
                logger.info(f"Altcoin spotlight sent for {selected_altcoin}")
            else:
                logger.warning(f"Failed to generate spotlight content for {selected_altcoin}")
            
        except Exception as e:
            logger.error(f"Error in altcoin spotlight job: {e}")
            logger.error(traceback.format_exc())
    
    async def _weekly_report_job(self):
        """Generate and send weekly performance report"""
        try:
            logger.info("Starting weekly report job...")
            
            # Get performance statistics
            performance_stats = self.db.get_performance_stats(7)
            
            # Get recent signals
            recent_signals = self.db.get_recent_signals(50)
            
            # Generate weekly report content
            content = await self.content_generator.generate_weekly_report(
                performance_stats, recent_signals
            )
            
            if content:
                # Save content to database
                self.db.save_content(content)
                
                # Generate performance chart
                chart_image = self.chart_generator.create_performance_chart(recent_signals)
                
                # Send to Telegram
                if chart_image:
                    # Send with chart
                    photo_bytes = base64.b64decode(chart_image)
                    photo = BufferedInputFile(photo_bytes, filename="weekly_report.png")
                    
                    message_text = f"**{content['title']}**\n\n{content['content']}\n\n{Config.RISK_WARNING}"
                    
                    await self.telegram_bot.bot.send_photo(
                        chat_id=self.telegram_bot.channel_id,
                        photo=photo,
                        caption=message_text,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    # Send without chart
                    await self.telegram_bot.send_content(content)
                
                logger.info("Weekly report sent successfully")
            else:
                logger.warning("Failed to generate weekly report content")
            
        except Exception as e:
            logger.error(f"Error in weekly report job: {e}")
            logger.error(traceback.format_exc())

    async def _promotional_post_job(self):
        """Generate and send a promotional post after weekly report"""
        try:
            logger.info("Starting promotional post job...")
            performance_stats = self.db.get_performance_stats(7)
            content = await self.content_generator.generate_promotional_post(performance_stats)
            if content:
                self.db.save_content(content)
                await self.telegram_bot.send_content(content)
                logger.info("Promotional post sent successfully")
            else:
                logger.warning("Failed to generate promotional post content")
        except Exception as e:
            logger.error(f"Error in promotional post job: {e}")
            logger.error(traceback.format_exc())
    
    async def _glossary_entry_job(self):
        """Generate and send daily glossary entry"""
        try:
            logger.info("Starting glossary entry job...")
            
            # Generate glossary content
            content = await self.content_generator.generate_glossary_entry()
            
            if content:
                # Save content to database
                self.db.save_content(content)
                
                # Send to Telegram
                await self.telegram_bot.send_content(content)
                
                logger.info("Glossary entry sent successfully")
            else:
                logger.warning("Failed to generate glossary entry content")
            
        except Exception as e:
            logger.error(f"Error in glossary entry job: {e}")
            logger.error(traceback.format_exc())
    
    async def _performance_update_job(self):
        """Update performance statistics"""
        try:
            logger.info("Starting performance update job...")
            
            # Update signal results (simulate P&L calculation)
            active_signals = self.db.get_active_signals()
            
            for signal in active_signals:
                # Check if signal should be closed (simplified logic)
                # In real implementation, this would check actual market conditions
                if signal.timestamp < datetime.utcnow() - timedelta(hours=24):
                    # Simulate result (in real implementation, this would be actual P&L)
                    import random
                    result = random.choice(['WIN', 'LOSS'])
                    pnl = random.uniform(-0.05, 0.08)  # -5% to +8%
                    exit_price = signal.entry_price * (1 + pnl)
                    
                    self.db.update_signal_result(signal.id, result, pnl, exit_price)
            
            logger.info("Performance update completed")
            
        except Exception as e:
            logger.error(f"Error in performance update job: {e}")
            logger.error(traceback.format_exc())
    
    def _can_open_position(self, signal: Dict) -> bool:
        """Check if we can open a new position based on portfolio management rules"""
        try:
            # Check maximum concurrent trades
            if len(self.active_positions) >= Config.MAX_CONCURRENT_TRADES:
                logger.debug(f"Maximum concurrent trades reached: {Config.MAX_CONCURRENT_TRADES}")
                return False
            
            # Check if we already have a position in this symbol
            for position in self.active_positions:
                if position['symbol'] == signal['symbol']:
                    logger.debug(f"Already have position in {signal['symbol']}")
                    return False
            
            # Check symbol weighting
            symbol_weight = Config.SYMBOL_WEIGHTS.get(signal['symbol'], 0.1)
            if symbol_weight < 0.15:  # Only trade symbols with weight >= 15%
                logger.debug(f"Symbol {signal['symbol']} has low weight: {symbol_weight}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking position eligibility: {e}")
            return False
    
    def _apply_symbol_weighting(self, signal: Dict) -> Dict:
        """Apply symbol weighting to position size"""
        try:
            symbol_weight = Config.SYMBOL_WEIGHTS.get(signal['symbol'], 0.1)
            adjusted_position_size = Config.POSITION_SIZE * symbol_weight
            
            # Add position size to signal metadata
            signal['position_size'] = adjusted_position_size
            signal['symbol_weight'] = symbol_weight
            
            return signal
            
        except Exception as e:
            logger.error(f"Error applying symbol weighting: {e}")
            return signal
    
    def _update_active_positions(self):
        """Update active positions and remove closed ones"""
        try:
            # Remove positions older than 24 hours
            current_time = datetime.now()
            self.active_positions = [
                pos for pos in self.active_positions 
                if (current_time - pos['entry_time']).total_seconds() < 24 * 3600
            ]
            
            logger.debug(f"Active positions: {len(self.active_positions)}")
            
        except Exception as e:
            logger.error(f"Error updating active positions: {e}")
    
    async def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            logger.info("Scheduler started successfully")
            
            # Pin welcome message
            await self.telegram_bot.pin_welcome_message()
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    async def stop(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown()
            await self.exchange_fetcher.close()
            await self.telegram_bot.stop()
            self.db.close()
            logger.info("Scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def get_job_status(self) -> Dict:
        """Get status of all scheduled jobs"""
        try:
            jobs = self.scheduler.get_jobs()
            status = {}
            
            for job in jobs:
                status[job.id] = {
                    'name': job.name,
                    'next_run_time': job.next_run_time,
                    'trigger': str(job.trigger)
                }
            
            return status
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return {}
    
    async def run_job_manually(self, job_id: str) -> bool:
        """Run a specific job manually"""
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return False
            
            # Get the job function
            job_func = getattr(self, f"_{job_id}_job")
            if not job_func:
                logger.error(f"Job function for {job_id} not found")
                return False
            
            # Run the job
            await job_func()
            logger.info(f"Job {job_id} executed manually")
            return True
            
        except Exception as e:
            logger.error(f"Error running job {job_id} manually: {e}")
            return False
