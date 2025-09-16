#!/usr/bin/env python3
"""
Test comprehensive backtest validation
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.backtesting.backtester import Backtester

async def test_comprehensive_validation():
    """Test comprehensive backtest validation"""
    try:
        print("🔍 Testing Comprehensive Backtest Validation...")
        
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
        
        with open('validated_backtest_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("✅ Comprehensive validation test completed!")
        print(f"📊 Total signals: {result.total_signals}")
        print(f"🎯 Win rate: {result.win_rate:.2f}%")
        print(f"💰 Total P&L: ${result.total_pnl:.2f}")
        print(f"📉 Max drawdown: {result.max_drawdown:.2f}%")
        print(f"📈 Sharpe ratio: {result.sharpe_ratio:.2f}")
        
        # Validation results
        if result.validation_result:
            validation = result.validation_result
            print(f"\n🔍 VALIDATION RESULTS:")
            print(f"   Overall Score: {validation.overall_score:.1f}/100")
            print(f"   Data Quality: {validation.data_quality_score:.1f}/100")
            print(f"   Trading Conditions: {validation.trading_conditions_score:.1f}/100")
            print(f"   Bias Detection: {validation.bias_detection_score:.1f}/100")
            print(f"   Overfitting: {validation.overfitting_score:.1f}/100")
            print(f"   Risk Management: {validation.risk_management_score:.1f}/100")
            
            if validation.is_valid:
                print(f"   ✅ VALIDATION: PASSED - Results are reliable")
            else:
                print(f"   ❌ VALIDATION: FAILED - Results need review")
            
            if validation.issues:
                print(f"\n⚠️  ISSUES FOUND ({len(validation.issues)}):")
                for i, issue in enumerate(validation.issues, 1):
                    print(f"   {i}. {issue}")
            
            if validation.recommendations:
                print(f"\n💡 RECOMMENDATIONS ({len(validation.recommendations)}):")
                for i, rec in enumerate(validation.recommendations, 1):
                    print(f"   {i}. {rec}")
        else:
            print(f"\n⚠️  No validation results available")
        
        print(f"\n📋 Detailed report saved to: validated_backtest_report.md")
        
        backtester.close()
        
    except Exception as e:
        print(f"❌ Error in validation test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_comprehensive_validation())
