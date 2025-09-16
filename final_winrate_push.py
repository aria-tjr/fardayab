#!/usr/bin/env python3
"""
Final Push to 80%+ Win Rate
Focused optimization on the remaining 1.43% improvement
"""
import asyncio
import sys
import os
from improved_optimizer import ImprovedOptimizer

class FinalWinRatePush(ImprovedOptimizer):
    """Focused optimizer for the final push to 80%+ win rate"""
    
    def __init__(self):
        super().__init__()
        
        # More focused parameter ranges around the best performing area
        self.param_ranges = {
            'CONFIDENCE_THRESHOLD': (0.80, 0.90),  # Focused around 0.824
            'ULTRA_MIN_CONFIDENCE': (0.80, 0.90),  # Focused around 0.83
            'RSI_OVERSOLD': (28, 36),  # Focused around 32
            'RSI_OVERBOUGHT': (58, 65),  # Focused around 61
            'STOP_LOSS_ATR_MULTIPLIER': (1.4, 1.8),  # Focused around 1.614
            'TAKE_PROFIT_ATR_MULTIPLIER': (2.7, 3.2),  # Focused around 2.978
            'MIN_VOLUME_RATIO': (1.4, 1.8),  # Focused around 1.594
            'MIN_ATR_RATIO': (1.1, 1.4),  # Focused around 1.29
            'MIN_TREND_STRENGTH': (24, 30),  # Focused around 27
            'MIN_MOMENTUM_CONSISTENCY': (2, 3),  # Focused around 2
            'TRADING_HOURS_START': (11, 13),  # Focused around 12
            'TRADING_HOURS_END': (17, 19),  # Focused around 18
            'MIN_RSI_DIVERGENCE': (5, 9),  # Focused around 7
            'MAX_VOLATILITY': (0.035, 0.050),  # Focused around 0.042
            'POSITION_SIZE': (0.035, 0.050),  # Focused around 0.041
            'MAX_DRAWDOWN_PCT': (3.0, 4.0),  # Focused around 3.387
            'MAX_CONCURRENT_TRADES': (2, 4),  # Focused around 3
            'MAX_CONSECUTIVE_LOSSES': (2, 4)  # Focused around 3
        }
    
    def calculate_fitness(self, win_rate: float, total_signals: int, total_pnl: float, 
                         max_drawdown: float, sharpe_ratio: float, profit_factor: float,
                         trading_frequency: float) -> float:
        """Enhanced fitness calculation with heavy focus on win rate"""
        
        # Primary: Win rate (even more heavily weighted)
        win_rate_score = min(win_rate / 80.0, 1.0) * 60  # Increased from 50
        
        # Secondary: Signal generation (moderate weight)
        signal_score = min(total_signals / 15.0, 1.0) * 15  # Slightly reduced
        
        # Trading frequency bonus
        freq_score = min(trading_frequency / 0.8, 1.0) * 10  # Slightly reduced
        
        # Risk management
        drawdown_penalty = max(0, (max_drawdown - 8) / 8) * 8  # Slightly more lenient
        sharpe_bonus = max(0, min(sharpe_ratio / 1.0, 1.0)) * 5  # Reduced
        
        # Profit factor bonus
        pf_bonus = max(0, min((profit_factor - 1.0) / 1.0, 1.0)) * 5
        
        # PnL bonus
        pnl_bonus = max(0, min(total_pnl / 300, 1.0)) * 5  # Reduced
        
        # Calculate final fitness
        fitness = (win_rate_score + signal_score + freq_score + sharpe_bonus + 
                  pf_bonus + pnl_bonus - drawdown_penalty)
        
        return max(fitness, 0)

async def main():
    """Main function for final win rate push"""
    print("🎯 Final Push to 80%+ Win Rate")
    print("🔍 Focused optimization around best performing parameters")
    print("=" * 60)
    
    optimizer = FinalWinRatePush()
    
    try:
        # Run focused optimization
        results = await optimizer.optimize(iterations=50)  # More iterations
        
        # Show results
        print("\n" + "=" * 60)
        print("📊 FINAL PUSH RESULTS")
        print("=" * 60)
        
        if optimizer.best_result:
            best = optimizer.best_result
            print(f"🏆 Best Win Rate: {best.win_rate:.2f}%")
            print(f"📈 Total Signals: {best.total_signals}")
            print(f"📊 Trading Frequency: {best.trading_frequency:.2f} signals/day")
            print(f"💰 Total P&L: ${best.total_pnl:.2f}")
            print(f"📉 Max Drawdown: {best.max_drawdown:.2f}%")
            print(f"📊 Sharpe Ratio: {best.sharpe_ratio:.2f}")
            print(f"🎯 Fitness Score: {best.fitness_score:.2f}")
            
            # Check achievements
            if best.win_rate >= 80.0:
                print(f"\n🎉 TARGET ACHIEVED! Win rate: {best.win_rate:.2f}%")
                print("🏆 80%+ WIN RATE SUCCESSFULLY REACHED!")
            else:
                improvement_needed = 80.0 - best.win_rate
                print(f"\n⚠️  Close! Need {improvement_needed:.2f}% more to reach 80%")
                print(f"📈 Current: {best.win_rate:.2f}% | Target: 80.0%")
            
            if best.total_signals >= 10:
                print(f"✅ Signal generation target achieved: {best.total_signals} signals")
            else:
                print(f"⚠️  Signal generation needs improvement: {best.total_signals} signals")
        
        # Save results
        optimizer.save_results()
        
        print(f"\n📁 Results saved to:")
        print(f"  - improved_optimization_results.json")
        print(f"  - improved_optimization_report.md")
        print(f"  - .env (updated with best parameters)")
        
        # Show top 5 results
        print(f"\n🏅 TOP 5 RESULTS:")
        for i, result in enumerate(results[:5], 1):
            print(f"{i}. Win Rate: {result.win_rate:.2f}% | Signals: {result.total_signals} | "
                  f"Fitness: {result.fitness_score:.2f}")
        
    except Exception as e:
        print(f"❌ Error during final push: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
