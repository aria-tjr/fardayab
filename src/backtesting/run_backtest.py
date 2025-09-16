"""
Backtest runner script
"""
import asyncio
import logging
from datetime import datetime, timedelta
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.backtesting.backtester import Backtester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backtest.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def run_comprehensive_backtest():
    """Run comprehensive backtest with multiple time periods"""
    try:
        # Define backtest periods
        backtest_periods = [
            {
                'name': 'Last 30 Days',
                'start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'end': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'name': 'Last 90 Days',
                'start': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                'end': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'name': 'Last 6 Months',
                'start': (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'),
                'end': datetime.now().strftime('%Y-%m-%d')
            }
        ]
        
        results = {}
        
        for period in backtest_periods:
            logger.info(f"Running backtest for {period['name']}")
            
            try:
                backtester = Backtester(period['start'], period['end'])
                result = await backtester.run_backtest()
                results[period['name']] = result
                
                # Generate report for this period
                report = backtester.generate_report(result)
                
                # Save report to file
                filename = f"backtest_report_{period['name'].replace(' ', '_').lower()}.md"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                logger.info(f"Backtest completed for {period['name']}")
                logger.info(f"Report saved to {filename}")
                
                backtester.close()
                
            except Exception as e:
                logger.error(f"Error in backtest for {period['name']}: {e}")
                continue
        
        # Generate comprehensive analysis
        await generate_comprehensive_analysis(results)
        
    except Exception as e:
        logger.error(f"Error in comprehensive backtest: {e}")
        raise

async def generate_comprehensive_analysis(results: dict):
    """Generate comprehensive analysis of all backtest results"""
    try:
        analysis = """
# 🔍 تحلیل جامع بک‌تست بات سیگنال کریپتو

## 📊 خلاصه نتایج

"""
        
        for period_name, result in results.items():
            analysis += f"""
### {period_name}
- **کل سیگنال‌ها**: {result.total_signals}
- **نرخ برد**: {result.win_rate:.2f}%
- **سود/زیان کل**: ${result.total_pnl:.2f}
- **حداکثر افت**: {result.max_drawdown:.2f}%
- **نسبت شارپ**: {result.sharpe_ratio:.2f}
- **ضریب سود**: {result.profit_factor:.2f}

"""
        
        # Identify patterns and issues
        analysis += """
## 🔍 شناسایی الگوها و مشکلات

### نقاط قوت:
"""
        
        # Analyze strengths
        avg_win_rate = sum(r.win_rate for r in results.values()) / len(results) if results else 0
        avg_profit_factor = sum(r.profit_factor for r in results.values()) / len(results) if results else 0
        avg_sharpe = sum(r.sharpe_ratio for r in results.values()) / len(results) if results else 0
        
        if avg_win_rate > 60:
            analysis += "- ✅ **نرخ برد بالا**: استراتژی در شناسایی سیگنال‌های صحیح موفق است\n"
        
        if avg_profit_factor > 1.5:
            analysis += "- ✅ **ضریب سود مناسب**: نسبت سود به زیان مطلوب است\n"
        
        if avg_sharpe > 1.0:
            analysis += "- ✅ **نسبت شارپ مناسب**: بازده نسبت به ریسک مطلوب است\n"
        
        analysis += """
### نقاط ضعف و نیاز به بهبود:
"""
        
        # Analyze weaknesses
        if avg_win_rate < 50:
            analysis += "- ⚠️ **نرخ برد پایین**: استراتژی نیاز به بهبود در شناسایی سیگنال‌ها دارد\n"
            analysis += "  - **توصیه**: تنظیم پارامترهای اندیکاتورها، بهبود فیلترهای ورود\n"
        
        max_drawdown = max(r.max_drawdown for r in results.values()) if results else 0
        if max_drawdown > 20:
            analysis += "- ⚠️ **حداکثر افت بالا**: مدیریت ریسک نیاز به بهبود دارد\n"
            analysis += "  - **توصیه**: کاهش اندازه موقعیت، بهبود حد ضرر، تنوع‌بخشی بیشتر\n"
        
        if avg_profit_factor < 1.2:
            analysis += "- ⚠️ **ضریب سود پایین**: نسبت سود به زیان نامطلوب است\n"
            analysis += "  - **توصیه**: بهبود نسبت ریسک/سود، تنظیم حد سود و حد ضرر\n"
        
        if avg_sharpe < 0.5:
            analysis += "- ⚠️ **نسبت شارپ پایین**: بازده نسبت به ریسک نامطلوب است\n"
            analysis += "  - **توصیه**: بهبود استراتژی، کاهش نوسان‌پذیری\n"
        
        # Analyze by symbol
        analysis += """
### تحلیل عملکرد به تفکیک نماد:
"""
        
        symbol_performance = {}
        for result in results.values():
            for symbol, metrics in result.signals_by_symbol.items():
                if symbol not in symbol_performance:
                    symbol_performance[symbol] = []
                symbol_performance[symbol].append(metrics)
        
        for symbol, metrics_list in symbol_performance.items():
            avg_win_rate = sum(m['win_rate'] for m in metrics_list) / len(metrics_list)
            avg_pnl = sum(m['total_pnl'] for m in metrics_list) / len(metrics_list)
            
            analysis += f"""
#### {symbol}
- **میانگین نرخ برد**: {avg_win_rate:.2f}%
- **میانگین سود/زیان**: ${avg_pnl:.2f}
"""
            
            if avg_win_rate < 40:
                analysis += f"  - ⚠️ **عملکرد ضعیف**: {symbol} نیاز به بررسی دارد\n"
            elif avg_win_rate > 70:
                analysis += f"  - ✅ **عملکرد عالی**: {symbol} بهترین عملکرد را دارد\n"
        
        # Recommendations
        analysis += """
## 🚀 توصیه‌های بهبود

### 1. بهبود استراتژی:
"""
        
        if avg_win_rate < 50:
            analysis += """
- **تنظیم پارامترهای اندیکاتورها**:
  - RSI: تغییر از 47/53 به 40/60 برای سیگنال‌های بیشتر
  - EMA: اضافه کردن EMA 12 برای واکنش سریع‌تر
  - Donchian: کاهش دوره از 20 به 14 برای حساسیت بیشتر

- **اضافه کردن فیلترهای جدید**:
  - فیلتر حجم: فقط معاملات با حجم بالای میانگین 20 روزه
  - فیلتر نوسان: حذف سیگنال‌ها در بازارهای کم‌نوسان
  - فیلتر زمان: معامله فقط در ساعات پرحجم بازار

"""
        
        if max_drawdown > 15:
            analysis += """
- **بهبود مدیریت ریسک**:
  - کاهش اندازه موقعیت از 10% به 5%
  - استفاده از حد ضرر متحرک (Trailing Stop)
  - تنوع‌بخشی بیشتر بین نمادها
  - محدودیت تعداد معاملات همزمان

"""
        
        analysis += """
### 2. بهبود فنی:
- **بهینه‌سازی زمان‌بندی**: بررسی بهترین ساعات معاملات
- **فیلتر کیفیت سیگنال**: فقط سیگنال‌های با اعتماد بالای 80%
- **مدیریت پورتفولیو**: تخصیص وزن متفاوت به نمادها
- **بررسی همبستگی**: حذف سیگنال‌های همبسته

### 3. نظارت و بهبود مستمر:
- **بک‌تست ماهانه**: بررسی عملکرد در دوره‌های مختلف
- **A/B Testing**: تست استراتژی‌های مختلف
- **تحلیل بازار**: تطبیق استراتژی با شرایط بازار
- **به‌روزرسانی پارامترها**: تنظیم بر اساس عملکرد اخیر

"""
        
        # Save comprehensive analysis
        with open('comprehensive_backtest_analysis.md', 'w', encoding='utf-8') as f:
            f.write(analysis)
        
        logger.info("Comprehensive analysis saved to comprehensive_backtest_analysis.md")
        
    except Exception as e:
        logger.error(f"Error generating comprehensive analysis: {e}")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_backtest())
