"""
Content generation using OpenAI API
"""
import openai
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

from ..config import Config
from ..storage.models import DatabaseManager

logger = logging.getLogger(__name__)

class ContentGenerator:
    """Generates various types of content using OpenAI"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.db = DatabaseManager()
        self.language = Config.DEFAULT_LANGUAGE
        self.tone = Config.CONTENT_TONE
    
    async def generate_market_summary(self, market_data: Dict, signals: List[Dict]) -> Dict:
        """Generate daily market summary"""
        try:
            # Prepare market context
            market_context = self._prepare_market_context(market_data, signals)
            
            prompt = f"""
            شما یک تحلیلگر ارز دیجیتال حرفه‌ای هستید. بر اساس داده‌های زیر، یک خلاصه روزانه بازار کریپتو بنویسید.
            
            داده‌های بازار:
            {json.dumps(market_context, ensure_ascii=False, indent=2)}
            
            لطفاً یک خلاصه شامل موارد زیر بنویسید:
            1. تیتر جذاب و کوتاه
            2. وضعیت کلی بازار (صعودی/نزولی/خنثی)
            3. 3-5 نکته کلیدی از بازار
            4. تحلیل عملکرد سیگنال‌های امروز
            5. پیش‌بینی کوتاه‌مدت
            6. هشدار ریسک
            
            لحن: {self.tone}
            زبان: فارسی
            طول: 200-300 کلمه
            """
            
            response = await self._call_openai(prompt)
            
            content = {
                'content_type': 'market_summary',
                'title': f'خلاصه بازار کریپتو - {datetime.now().strftime("%Y/%m/%d")}',
                'content': response,
                'language': self.language,
                'tone': self.tone,
                'metadata': market_context
            }
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating market summary: {e}")
            return None
    
    async def generate_altcoin_spotlight(self, symbol: str, market_data: Dict) -> Dict:
        """Generate altcoin spotlight analysis"""
        try:
            if symbol not in market_data:
                return None
            
            df = market_data[symbol]['5m']
            current_price = df['close'].iloc[-1]
            price_change_24h = ((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100) if len(df) >= 24 else 0
            volume_24h = df['volume'].tail(24).sum()
            
            prompt = f"""
            شما یک تحلیلگر تکنیکال حرفه‌ای هستید. تحلیل کاملی از {symbol} ارائه دهید.
            
            داده‌های {symbol}:
            - قیمت فعلی: ${current_price:.4f}
            - تغییر 24 ساعته: {price_change_24h:.2f}%
            - حجم 24 ساعته: {volume_24h:,.0f}
            
            لطفاً تحلیل شامل موارد زیر باشد:
            1. تیتر جذاب
            2. تحلیل تکنیکال (سطح حمایت/مقاومت، روند)
            3. تحلیل حجم
            4. اندیکاتورهای کلیدی
            5. سناریوهای احتمالی
            6. توصیه معاملاتی
            7. هشدار ریسک
            
            لحن: {self.tone}
            زبان: فارسی
            طول: 300-400 کلمه
            """
            
            response = await self._call_openai(prompt)
            
            content = {
                'content_type': 'altcoin_spotlight',
                'title': f'تحلیل {symbol} - {datetime.now().strftime("%Y/%m/%d")}',
                'content': response,
                'language': self.language,
                'tone': self.tone,
                'metadata': {
                    'symbol': symbol,
                    'current_price': current_price,
                    'price_change_24h': price_change_24h,
                    'volume_24h': volume_24h
                }
            }
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating altcoin spotlight: {e}")
            return None
    
    async def generate_education_tip(self) -> Dict:
        """Generate educational content about trading"""
        try:
            education_topics = [
                "مدیریت ریسک در معاملات کریپتو",
                "روانشناسی معاملات و کنترل احساسات",
                "اندیکاتورهای تکنیکال و نحوه استفاده",
                "تحلیل فاندامنتال در ارزهای دیجیتال",
                "استراتژی‌های معاملاتی مختلف",
                "نحوه تنظیم حد ضرر و حد سود",
                "تحلیل حجم و اهمیت آن",
                "شناسایی الگوهای کندل‌استیک",
                "استفاده از فیبوناچی در تحلیل",
                "معرفی صرافی‌ها و کیف پول‌ها"
            ]
            
            # Select random topic (in real implementation, you might want to cycle through them)
            import random
            topic = random.choice(education_topics)
            
            prompt = f"""
            شما یک مربی معاملات حرفه‌ای هستید. یک نکته آموزشی مفصل درباره "{topic}" بنویسید.
            
            لطفاً شامل موارد زیر باشد:
            1. تیتر جذاب
            2. تعریف و توضیح مفهوم
            3. مثال‌های عملی
            4. نکات کاربردی
            5. اشتباهات رایج
            6. توصیه‌های عملی
            
            لحن: دوستانه و آموزشی
            زبان: فارسی
            طول: 400-500 کلمه
            """
            
            response = await self._call_openai(prompt)
            
            content = {
                'content_type': 'education_tip',
                'title': f'نکته آموزشی: {topic}',
                'content': response,
                'language': self.language,
                'tone': 'friendly',
                'metadata': {'topic': topic}
            }
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating education tip: {e}")
            return None
    
    async def generate_glossary_entry(self) -> Dict:
        """Generate glossary/insight about a trading concept"""
        try:
            glossary_terms = [
                "EMA (Exponential Moving Average)",
                "RSI (Relative Strength Index)",
                "Bollinger Bands",
                "Donchian Channels",
                "ATR (Average True Range)",
                "MACD",
                "Stochastic Oscillator",
                "Support and Resistance",
                "Breakout and Breakdown",
                "Volume Profile",
                "Market Cap",
                "Liquidity",
                "Volatility",
                "Risk/Reward Ratio",
                "Position Sizing"
            ]
            
            import random
            term = random.choice(glossary_terms)
            
            prompt = f"""
            شما یک متخصص تحلیل تکنیکال هستید. تعریف کاملی از "{term}" ارائه دهید.
            
            لطفاً شامل موارد زیر باشد:
            1. تیتر جذاب
            2. تعریف ساده و قابل فهم
            3. نحوه محاسبه (اگر قابل محاسبه است)
            4. نحوه تفسیر و استفاده
            5. مثال‌های عملی
            6. نکات مهم
            
            لحن: آموزشی و ساده
            زبان: فارسی
            طول: 300-400 کلمه
            """
            
            response = await self._call_openai(prompt)
            
            content = {
                'content_type': 'glossary_entry',
                'title': f'آشنایی با {term}',
                'content': response,
                'language': self.language,
                'tone': 'educational',
                'metadata': {'term': term}
            }
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating glossary entry: {e}")
            return None
    
    async def generate_weekly_report(self, performance_stats: Dict, signals: List[Dict]) -> Dict:
        """Generate weekly performance report"""
        try:
            prompt = f"""
            شما یک تحلیلگر عملکرد حرفه‌ای هستید. گزارش هفتگی عملکرد سیگنال‌ها را بنویسید.
            
            آمار عملکرد:
            {json.dumps(performance_stats, ensure_ascii=False, indent=2)}
            
            تعداد سیگنال‌های این هفته: {len(signals)}
            
            لطفاً گزارش شامل موارد زیر باشد:
            1. تیتر جذاب
            2. خلاصه عملکرد هفته
            3. آمار دقیق (نرخ برد، سود/زیان)
            4. تحلیل بهترین و بدترین سیگنال‌ها
            5. درس‌های آموخته شده
            6. پیش‌بینی هفته آینده
            7. توصیه‌های بهبود
            8. هشدار ریسک
            
            لحن: {self.tone}
            زبان: فارسی
            طول: 500-600 کلمه
            """
            
            response = await self._call_openai(prompt)
            
            content = {
                'content_type': 'weekly_report',
                'title': f'گزارش هفتگی عملکرد - هفته {datetime.now().strftime("%Y/%m/%d")}',
                'content': response,
                'language': self.language,
                'tone': self.tone,
                'metadata': {
                    'performance_stats': performance_stats,
                    'signals_count': len(signals)
                }
            }
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return None

    async def generate_promotional_post(self, performance_stats: Dict) -> Dict:
        """Generate a promotional/marketing post focusing on Win Rate and signal count"""
        try:
            prompt = f"""
            شما یک کپی‌رایتر حرفه‌ای هستید. یک پست تبلیغی برای کانال سیگنال‌ کریپتو بنویسید که روی نرخ برد واقعی (Win Rate) و تعداد سیگنال‌ها تمرکز دارد و مقایسه با سایر کانال‌ها را به شکل حرفه‌ای و غیر اغراق‌آمیز بیان می‌کند. دعوت به تعامل هم داشته باشد.

            آمار هفته اخیر:
            {json.dumps(performance_stats, ensure_ascii=False, indent=2)}

            الزامات:
            - لحن رسمی، حرفه‌ای و مطمئن
            - تاکید بر شفافیت و گزارش‌دهی هفتگی
            - عدم اشاره به نسبت ریسک به ریوارد
            - استفاده از ایموجی‌های مناسب
            - پایان با Call To Action برای عضویت و بازخورد
            - زبان: فارسی
            - طول: 120-180 کلمه
            """

            response = await self._call_openai(prompt)
            content = {
                'content_type': 'promo_post',
                'title': '🎯 چرا این کانال را انتخاب کنید؟',
                'content': response,
                'language': self.language,
                'tone': self.tone,
                'metadata': {'performance_stats': performance_stats}
            }
            return content
        except Exception as e:
            logger.error(f"Error generating promotional post: {e}")
            return None
    
    async def generate_signal_rationale(self, signal: Dict) -> str:
        """Generate detailed rationale for a signal"""
        try:
            prompt = f"""
            شما یک تحلیلگر تکنیکال حرفه‌ای هستید. توضیح کاملی از دلیل سیگنال {signal['direction']} برای {signal['symbol']} ارائه دهید.
            
            جزئیات سیگنال:
            {json.dumps(signal, ensure_ascii=False, indent=2)}
            
            لطفاً توضیح شامل موارد زیر باشد:
            1. تحلیل تکنیکال
            2. دلیل انتخاب این جهت
            3. سطح اعتماد
            4. مدیریت ریسک
            5. سناریوهای احتمالی
            
            لحن: {self.tone}
            زبان: فارسی
            طول: 150-200 کلمه
            """
            
            response = await self._call_openai(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error generating signal rationale: {e}")
            return "تحلیل تکنیکال نشان‌دهنده شرایط مناسب برای این سیگنال است."
    
    def _prepare_market_context(self, market_data: Dict, signals: List[Dict]) -> Dict:
        """Prepare market context for content generation"""
        try:
            # Get current prices
            current_prices = {}
            price_changes = {}
            
            for symbol, timeframes in market_data.items():
                if '5m' in timeframes:
                    df = timeframes['5m']
                    current_prices[symbol] = df['close'].iloc[-1]
                    if len(df) >= 24:
                        price_changes[symbol] = ((df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24] * 100)
                    else:
                        price_changes[symbol] = 0
            
            # Count signals by direction
            long_signals = len([s for s in signals if s['direction'] == 'LONG'])
            short_signals = len([s for s in signals if s['direction'] == 'SHORT'])
            
            return {
                'current_prices': current_prices,
                'price_changes_24h': price_changes,
                'total_signals_today': len(signals),
                'long_signals': long_signals,
                'short_signals': short_signals,
                'market_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error preparing market context: {e}")
            return {}
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model="gpt-5-mini-2025-08-07",
                    messages=[
                        {"role": "system", "content": "شما یک تحلیلگر ارز دیجیتال حرفه‌ای و متخصص در تحلیل تکنیکال هستید."},
                        {"role": "user", "content": prompt}
                    ],
                    max_completion_tokens=1000
                )
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return "خطا در تولید محتوا. لطفاً دوباره تلاش کنید."
    
    def add_hashtags_and_emojis(self, content: str, content_type: str) -> str:
        """Add relevant hashtags and emojis to content"""
        try:
            hashtags = {
                'market_summary': ['#کریپتو', '#بیتکوین', '#ارزدیجیتال', '#تحلیل_بازار', '#سیگنال'],
                'altcoin_spotlight': ['#آلتکوین', '#تحلیل_تکنیکال', '#سیگنال', '#کریپتو'],
                'education_tip': ['#آموزش', '#معاملات', '#کریپتو', '#مدیریت_ریسک'],
                'glossary_entry': ['#آموزش', '#تحلیل_تکنیکال', '#کریپتو', '#اصطلاحات'],
                'weekly_report': ['#گزارش_هفتگی', '#عملکرد', '#کریپتو', '#سیگنال']
            }
            
            emojis = {
                'market_summary': '📊📈💰',
                'altcoin_spotlight': '🔍💎📊',
                'education_tip': '📚💡🎓',
                'glossary_entry': '📖🔍💡',
                'weekly_report': '📊📈📋',
                'promo_post': '🎯🚀📈'
            }
            
            selected_hashtags = hashtags.get(content_type, ['#کریپتو', '#سیگنال'])
            selected_emojis = emojis.get(content_type, '📊💰')
            
            hashtag_string = ' '.join(selected_hashtags)
            emoji_string = selected_emojis
            
            return f"{emoji_string}\n\n{content}\n\n{hashtag_string}"
            
        except Exception as e:
            logger.error(f"Error adding hashtags and emojis: {e}")
            return content
