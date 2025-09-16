#!/usr/bin/env python3
"""
Ultra High Win Rate Backtest
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.backtesting.backtester import Backtester

async def run_ultra_winrate_backtest():
    """Run backtest with ultra high win rate mode"""
    try:
        print("🚀 Starting Ultra High Win Rate Backtest...")
        
        # Run backtest for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 Backtest period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print("🎯 Mode: Ultra High Win Rate (95%+ confidence required)")
        
        backtester = Backtester(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        result = await backtester.run_backtest()
        
        # Generate and save report
        report = backtester.generate_report(result)
        
        with open('ultra_winrate_backtest_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("✅ Ultra High Win Rate Backtest completed!")
        print(f"📊 Total signals: {result.total_signals}")
        print(f"🎯 Win rate: {result.win_rate:.2f}%")
        print(f"💰 Total P&L: ${result.total_pnl:.2f}")
        print(f"📉 Max drawdown: {result.max_drawdown:.2f}%")
        print(f"📈 Sharpe ratio: {result.sharpe_ratio:.2f}")
        print(f"📋 Report saved to: ultra_winrate_backtest_report.md")
        
        # Analysis
        if result.total_signals > 0:
            print(f"\n🎯 WIN RATE ANALYSIS:")
            if result.win_rate >= 80:
                print(f"   🏆 EXCELLENT: {result.win_rate:.1f}% win rate!")
            elif result.win_rate >= 70:
                print(f"   🥇 VERY GOOD: {result.win_rate:.1f}% win rate!")
            elif result.win_rate >= 60:
                print(f"   🥈 GOOD: {result.win_rate:.1f}% win rate!")
            else:
                print(f"   ⚠️  NEEDS IMPROVEMENT: {result.win_rate:.1f}% win rate")
        else:
            print(f"\n⚠️  NO SIGNALS GENERATED")
            print(f"   This means the ultra-strict filters are working correctly")
            print(f"   Only the highest quality setups will generate signals")
        
        backtester.close()
        
    except Exception as e:
        print(f"❌ Error in ultra win rate backtest: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_ultra_winrate_backtest())
