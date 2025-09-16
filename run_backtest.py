#!/usr/bin/env python3
"""
Simple backtest runner script
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.backtesting.backtester import Backtester

async def main():
    """Run backtest"""
    try:
        print("🚀 Starting comprehensive backtest...")
        
        # Run backtest for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Backtest period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        backtester = Backtester(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        result = await backtester.run_backtest()
        
        # Generate and save report
        report = backtester.generate_report(result)
        
        with open('backtest_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("✅ Backtest completed!")
        print(f"📊 Total signals: {result.total_signals}")
        print(f"🎯 Win rate: {result.win_rate:.2f}%")
        print(f"💰 Total P&L: ${result.total_pnl:.2f}")
        print(f"📉 Max drawdown: {result.max_drawdown:.2f}%")
        print(f"📈 Sharpe ratio: {result.sharpe_ratio:.2f}")
        print(f"📋 Report saved to: backtest_report.md")
        
        backtester.close()
        
    except Exception as e:
        print(f"❌ Error in backtest: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
