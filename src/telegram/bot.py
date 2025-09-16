"""
Telegram bot using aiogram v3
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import base64
import io

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

from ..config import Config
from ..storage.models import DatabaseManager

logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram bot for sending signals and content"""
    
    def __init__(self):
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher()
        self.channel_id = Config.TELEGRAM_CHANNEL_ID
        self.db = DatabaseManager()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup bot command handlers"""
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
        
        @self.dp.message(Command("status"))
        async def status_command(message: Message):
            try:
                # Get recent stats
                recent_signals = self.db.get_recent_signals(5)
                performance = self.db.get_performance_stats(7)
                
                status_text = f"""
📊 **وضعیت بات**

🔄 **آخرین فعالیت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 **آمار 7 روز گذشته:**
• کل سیگنال‌ها: {performance.get('total_signals', 0)}
• نرخ برد: {performance.get('win_rate', 0):.1f}%
• سود/زیان کل: {performance.get('total_pnl', 0):.2f}%

🔔 **آخرین سیگنال‌ها:**
"""
                
                for signal in recent_signals[:3]:
                    status_text += f"• {signal.symbol} {signal.direction} - {signal.confidence:.2f}\n"
                
                await message.answer(status_text, parse_mode=ParseMode.MARKDOWN)
                
            except Exception as e:
                logger.error(f"Error in status command: {e}")
                await message.answer("خطا در دریافت وضعیت. لطفاً دوباره تلاش کنید.")
        
        @self.dp.message(Command("signals"))
        async def signals_command(message: Message):
            try:
                recent_signals = self.db.get_recent_signals(10)
                
                if not recent_signals:
                    await message.answer("هیچ سیگنالی یافت نشد.")
                    return
                
                signals_text = "📊 **آخرین سیگنال‌ها**\n\n"
                
                for signal in recent_signals:
                    status_emoji = "✅" if signal.result == "WIN" else "❌" if signal.result == "LOSS" else "⏳"
                    signals_text += f"""
{status_emoji} **{signal.symbol}** {signal.direction}
💰 قیمت: ${signal.entry_price:.4f}
🎯 اعتماد: {signal.confidence:.2f}
📅 زمان: {signal.timestamp.strftime('%m/%d %H:%M')}
"""
                
                await message.answer(signals_text, parse_mode=ParseMode.MARKDOWN)
                
            except Exception as e:
                logger.error(f"Error in signals command: {e}")
                await message.answer("خطا در دریافت سیگنال‌ها. لطفاً دوباره تلاش کنید.")
        
        @self.dp.message(Command("performance"))
        async def performance_command(message: Message):
            try:
                performance = self.db.get_performance_stats(30)
                
                performance_text = f"""
📊 **آمار عملکرد 30 روز گذشته**

📈 **آمار کلی:**
• کل سیگنال‌ها: {performance.get('total_signals', 0)}
• سیگنال‌های برنده: {performance.get('winning_signals', 0)}
• سیگنال‌های بازنده: {performance.get('losing_signals', 0)}
• نرخ برد: {performance.get('win_rate', 0):.1f}%

💰 **آمار مالی:**
• سود/زیان کل: {performance.get('total_pnl', 0):.2f}%
• میانگین سود: {performance.get('avg_win', 0):.2f}%
• میانگین زیان: {performance.get('avg_loss', 0):.2f}%
• ضریب سود: {performance.get('profit_factor', 0):.2f}
"""
                
                await message.answer(performance_text, parse_mode=ParseMode.MARKDOWN)
                
            except Exception as e:
                logger.error(f"Error in performance command: {e}")
                await message.answer("خطا در دریافت آمار عملکرد. لطفاً دوباره تلاش کنید.")
        
        @self.dp.message(Command("help"))
        async def help_command(message: Message):
            help_text = """
📚 **راهنمای بات سیگنال کریپتو**

🤖 **درباره بات:**
این بات به صورت خودکار سیگنال‌های معاملاتی ارزهای دیجیتال تولید و ارسال می‌کند.

📊 **دستورات موجود:**
/start - شروع و معرفی بات
/status - وضعیت فعلی بات
/signals - نمایش آخرین سیگنال‌ها
/performance - آمار عملکرد
/help - نمایش این راهنما

⚠️ **هشدار مهم:**
• این سیگنال‌ها صرفاً برای اهداف آموزشی هستند
• معاملات کریپتو دارای ریسک بالایی است
• همیشه مدیریت ریسک را رعایت کنید
• این بات مسئولیتی در قبال ضررهای احتمالی ندارد

📞 **پشتیبانی:**
برای سوالات و پشتیبانی با تیم ما تماس بگیرید.
"""
            
            await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def send_signal(self, signal: Dict, chart_image: Optional[str] = None) -> bool:
        """Send a trading signal to the channel"""
        try:
            # Format signal message
            message_text = self._format_signal_message(signal)
            
            # Create inline keyboard for additional actions
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📊 جزئیات بیشتر", callback_data=f"signal_{signal.get('id', 'unknown')}"),
                    InlineKeyboardButton(text="📈 نمودار", callback_data=f"chart_{signal.get('id', 'unknown')}")
                ]
            ])
            
            if chart_image:
                # Send photo with caption
                photo_bytes = base64.b64decode(chart_image)
                photo = types.BufferedInputFile(photo_bytes, filename="signal_chart.png")
                
                await self.bot.send_photo(
                    chat_id=self.channel_id,
                    photo=photo,
                    caption=message_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
            else:
                # Send text message
                await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=message_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
            
            logger.info(f"Signal sent to channel: {signal['symbol']} {signal['direction']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending signal: {e}")
            return False
    
    async def send_content(self, content: Dict) -> bool:
        """Send generated content to the channel"""
        try:
            # Add hashtags and emojis
            from ..content.content_generator import ContentGenerator
            content_gen = ContentGenerator()
            formatted_content = content_gen.add_hashtags_and_emojis(
                content['content'], 
                content['content_type']
            )
            
            # Create message text
            message_text = f"**{content['title']}**\n\n{formatted_content}"
            
            # Add risk warning
            message_text += f"\n\n{Config.RISK_WARNING}"
            
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Content sent to channel: {content['content_type']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending content: {e}")
            return False
    
    async def send_market_summary(self, market_data: Dict, chart_image: Optional[str] = None) -> bool:
        """Send market summary with chart"""
        try:
            # Generate market summary content
            from ..content.content_generator import ContentGenerator
            content_gen = ContentGenerator()
            content = await content_gen.generate_market_summary(market_data, [])
            
            if not content:
                return False
            
            # Format message
            message_text = f"**{content['title']}**\n\n{content['content']}\n\n{Config.RISK_WARNING}"
            
            if chart_image:
                # Send photo with caption
                photo_bytes = base64.b64decode(chart_image)
                photo = types.BufferedInputFile(photo_bytes, filename="market_summary.png")
                
                await self.bot.send_photo(
                    chat_id=self.channel_id,
                    photo=photo,
                    caption=message_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Send text message
                await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=message_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            
            logger.info("Market summary sent to channel")
            return True
            
        except Exception as e:
            logger.error(f"Error sending market summary: {e}")
            return False
    
    def _format_signal_message(self, signal: Dict) -> str:
        """Format signal message for Telegram"""
        try:
            # Determine signal emoji
            signal_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
            direction_text = "خرید" if signal['direction'] == 'LONG' else "فروش"
            
            # Recent performance (focus on Win Rate and signal count per spec)
            perf = self.db.get_performance_stats(7)
            recent_win_rate = perf.get('win_rate', 0.0)
            total_signals = perf.get('total_signals', 0)
            winning_signals = perf.get('winning_signals', 0)

            # Format entry, stop loss, and take profit
            entry_price = f"${signal['entry_price']:.4f}"
            stop_loss = f"${signal['stop_loss']:.4f}" if signal['stop_loss'] else "N/A"
            take_profit = f"${signal['take_profit']:.4f}" if signal['take_profit'] else "N/A"
            
            # Format confidence as percentage
            confidence_pct = f"{signal['confidence'] * 100:.1f}%"
            
            # Create message
            message = f"""
{signal_emoji} **سیگنال {direction_text} | {signal['symbol']} | {signal['timeframe']}**

📊 **نوع:** {signal['type']}

💵 **قیمت ورود:** {entry_price}
🛑 **حد ضرر:** {stop_loss}
🎯 **حد سود:** {take_profit}
🎯 **اعتماد:** {confidence_pct}

🏆 **Win Rate اخیر:** {recent_win_rate:.1f}%
📈 **تعداد سیگنال‌های هفته:** {total_signals}

📋 **شرایط برآورده شده:**
"""
            
            # Add conditions met
            for condition in signal.get('conditions_met', []):
                message += f"• {condition}\n"
            
            # Add rationale
            if signal.get('rationale'):
                message += f"\n📊 **تحلیل تکنیکال:**\n"
                for item in signal['rationale'][:3]:  # Show first 3 items
                    message += f"• {item}\n"
            
            # Add risk warning
            message += f"\n{Config.RISK_WARNING}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting signal message: {e}")
            return f"سیگنال {signal.get('direction', 'UNKNOWN')} برای {signal.get('symbol', 'UNKNOWN')}"
    
    async def pin_welcome_message(self) -> bool:
        """Pin welcome message to channel"""
        try:
            welcome_text = """
🎯 **خوش آمدید به کانال سیگنال کریپتو**

📊 **درباره کانال:**
این کانال به صورت خودکار سیگنال‌های معاملاتی ارزهای دیجیتال و محتوای آموزشی تولید می‌کند.

🤖 **ویژگی‌های بات:**
• تولید سیگنال‌های خودکار بر اساس تحلیل تکنیکال
• تحلیل‌های روزانه بازار
• نکات آموزشی و مدیریت ریسک
• گزارش‌های هفتگی عملکرد

📈 **استراتژی‌های معاملاتی:**
• Trend Following (دنبال کردن روند)
• Mean Reversion (بازگشت به میانگین)
• ترکیب اندیکاتورهای EMA، RSI، Donchian، Bollinger Bands

⚠️ **قوانین مهم:**
• این سیگنال‌ها صرفاً برای اهداف آموزشی هستند
• معاملات کریپتو دارای ریسک بالایی است
• همیشه مدیریت ریسک را رعایت کنید
• این بات مسئولیتی در قبال ضررهای احتمالی ندارد

📞 **پشتیبانی:**
برای سوالات و پشتیبانی با تیم ما تماس بگیرید.

🔔 **برای دریافت آخرین سیگنال‌ها، کانال را دنبال کنید.**
"""
            
            message = await self.bot.send_message(
                chat_id=self.channel_id,
                text=welcome_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Pin the message
            await self.bot.pin_chat_message(
                chat_id=self.channel_id,
                message_id=message.message_id
            )
            
            logger.info("Welcome message pinned to channel")
            return True
            
        except Exception as e:
            logger.error(f"Error pinning welcome message: {e}")
            return False
    
    async def start_polling(self):
        """Start bot polling"""
        try:
            logger.info("Starting Telegram bot polling...")
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Error starting bot polling: {e}")
            raise
    
    async def stop(self):
        """Stop the bot"""
        try:
            await self.bot.session.close()
            logger.info("Telegram bot stopped")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
