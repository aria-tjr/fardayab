"""
Main application orchestrator
"""
import asyncio
import logging
import signal
import sys
import traceback
from datetime import datetime
from typing import Optional

from .config import Config
from .scheduler.scheduler import SchedulerManager
from .telegram.bot import TelegramBot
from .storage.models import DatabaseManager

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

class CryptoSignalBot:
    """Main application class"""
    
    def __init__(self):
        self.config = Config()
        self.scheduler_manager: Optional[SchedulerManager] = None
        self.telegram_bot: Optional[TelegramBot] = None
        self.db: Optional[DatabaseManager] = None
        self.running = False
    
    async def initialize(self):
        """Initialize all components"""
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
        """Start the application"""
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
        """Stop the application"""
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
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run_manual_test(self):
        """Run manual test of all components"""
        try:
            logger.info("Running manual test...")
            
            # Test exchange connection
            from .exchange.data_fetcher import ExchangeDataFetcher
            exchange = ExchangeDataFetcher()
            valid_pairs = await exchange.get_volume_filtered_pairs()
            logger.info(f"Exchange test: Found {len(valid_pairs)} valid pairs")
            exchange.close()
            
            # Test signal generation
            from .strategies.signal_generator import SignalGenerator
            signal_gen = SignalGenerator()
            
            # Test with sample data
            import pandas as pd
            import numpy as np
            
            # Create sample OHLCV data
            dates = pd.date_range(start='2024-01-01', periods=200, freq='5min')
            sample_data = pd.DataFrame({
                'open': 100 + np.random.randn(200).cumsum(),
                'high': 100 + np.random.randn(200).cumsum() + 2,
                'low': 100 + np.random.randn(200).cumsum() - 2,
                'close': 100 + np.random.randn(200).cumsum(),
                'volume': np.random.randint(1000, 10000, 200)
            }, index=dates)
            
            signal = signal_gen.generate_signal('BTC/USDT', sample_data)
            if signal:
                logger.info(f"Signal generation test: {signal['direction']} signal generated")
            else:
                logger.info("Signal generation test: No signal generated")
            
            # Test content generation
            from .content.content_generator import ContentGenerator
            content_gen = ContentGenerator()
            
            content = await content_gen.generate_education_tip()
            if content:
                logger.info(f"Content generation test: {content['content_type']} generated")
            else:
                logger.info("Content generation test: Failed to generate content")
            
            # Test chart generation
            from .charts.chart_generator import ChartGenerator
            chart_gen = ChartGenerator()
            
            if signal:
                indicators = signal_gen.calculate_indicators(sample_data)
                chart_image = chart_gen.create_signal_chart(sample_data, signal, indicators)
                if chart_image:
                    logger.info("Chart generation test: Chart generated successfully")
                else:
                    logger.info("Chart generation test: Failed to generate chart")
            
            logger.info("Manual test completed successfully")
            
        except Exception as e:
            logger.error(f"Error in manual test: {e}")
            logger.error(traceback.format_exc())

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
            await bot.run_manual_test()
            return
        
        # Start application
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
