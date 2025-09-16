#!/usr/bin/env python3
"""
High Frequency Trading Optimizer
Target: 80%+ Win Rate with 3+ Trades per Day
"""
import asyncio
import sys
import os
from improved_optimizer import ImprovedOptimizer

class HighFrequencyOptimizer(ImprovedOptimizer):
    """Optimizer focused on high win rate + high trading frequency"""
    
    def __init__(self):
        super().__init__()
        
        # More permissive parameter ranges for higher signal generation
        self.param_ranges = {
            'CONFIDENCE_THRESHOLD': (0.70, 0.85),  # Lowered for more signals
            'ULTRA_MIN_CONFIDENCE': (0.75, 0.90),  # Lowered for more signals
            'RSI_OVERSOLD': (30, 45),  # More permissive
            'RSI_OVERBOUGHT': (55, 70),  # More permissive
            'STOP_LOSS_ATR_MULTIPLIER': (1.2, 2.0),  # Tighter stops for more trades
            'TAKE_PROFIT_ATR_MULTIPLIER': (1.8, 2.5),  # Better R:R ratio
            'MIN_VOLUME_RATIO': (1.1, 2.0),  # More permissive
            'MIN_ATR_RATIO': (1.0, 1.5),  # More permissive
            'MIN_TREND_STRENGTH': (15, 35),  # More permissive
            'MIN_MOMENTUM_CONSISTENCY': (1, 3),  # More permissive
            'TRADING_HOURS_START': (8, 16),  # Extended hours
            'TRADING_HOURS_END': (16, 22),  # Extended hours
            'MIN_RSI_DIVERGENCE': (3, 12),  # More permissive
            'MAX_VOLATILITY': (0.04, 0.08),  # More permissive
            'POSITION_SIZE': (0.02, 0.08),  # Smaller positions for more trades
            'MAX_DRAWDOWN_PCT': (4.0, 8.0),  # Slightly more permissive
            'MAX_CONCURRENT_TRADES': (2, 5),  # Allow more concurrent trades
            'MAX_CONSECUTIVE_LOSSES': (3, 6)  # More permissive
        }
    
    def calculate_fitness(self, win_rate: float, total_signals: int, total_pnl: float, 
                         max_drawdown: float, sharpe_ratio: float, profit_factor: float,
                         trading_frequency: float) -> float:
        """Enhanced fitness calculation with heavy focus on trading frequency"""
        
        # Primary: Win rate (heavily weighted)
        win_rate_score = min(win_rate / 80.0, 1.0) * 40  # Slightly reduced
        
        # Secondary: Trading frequency (heavily weighted)
        freq_score = min(trading_frequency / 3.0, 1.0) * 35  # Target 3+ trades/day
        
        # Signal generation bonus
        signal_score = min(total_signals / 30.0, 1.0) * 15  # Target 30+ signals in 30 days
        
        # Risk management
        drawdown_penalty = max(0, (max_drawdown - 12) / 12) * 8  # More lenient
        sharpe_bonus = max(0, min(sharpe_ratio / 1.0, 1.0)) * 5  # Reduced
        
        # Profit factor bonus
        pf_bonus = max(0, min((profit_factor - 1.0) / 1.0, 1.0)) * 5
        
        # PnL bonus
        pnl_bonus = max(0, min(total_pnl / 200, 1.0)) * 5  # Reduced
        
        # Calculate final fitness
        fitness = (win_rate_score + freq_score + signal_score + sharpe_bonus + 
                  pf_bonus + pnl_bonus - drawdown_penalty)
        
        return max(fitness, 0)
    
    async def optimize(self, iterations: int = 100) -> list:
        """Run optimization with more iterations for high frequency"""
        print(f"🎯 High Frequency Optimization")
        print(f"📊 Target: 80%+ Win Rate + 3+ Trades per Day")
        print(f"🔄 Running {iterations} iterations...")
        print("=" * 60)
        
        for i in range(iterations):
            if i % 10 == 0:
                print(f"📈 Iteration {i+1}/{iterations}")
            
            # Create random parameters
            params = self.create_random_parameters()
            
            # Evaluate parameters
            result = await self.evaluate_parameters(params)
            self.results.append(result)
            
            # Update best result
            if self.best_result is None or result.fitness_score > self.best_result.fitness_score:
                self.best_result = result
            
            # Log progress every 10 iterations
            if i % 10 == 0:
                print(f"  Win rate: {result.win_rate:.2f}% | Signals: {result.total_signals} | "
                      f"Freq: {result.trading_frequency:.2f}/day | Fitness: {result.fitness_score:.2f}")
            
            # Early stopping if both targets achieved
            if (result.win_rate >= 80.0 and result.trading_frequency >= 3.0):
                print(f"🎉 TARGET ACHIEVED! Win rate: {result.win_rate:.2f}%, "
                      f"Trading freq: {result.trading_frequency:.2f}/day")
                break
        
        # Sort results by fitness
        self.results.sort(key=lambda x: x.fitness_score, reverse=True)
        
        return self.results

async def main():
    """Main function for high frequency optimization"""
    print("🚀 High Frequency Trading Optimizer")
    print("🎯 Target: 80%+ Win Rate with 3+ Trades per Day")
    print("⚙️  Optimizing for maximum trading frequency while maintaining high win rate")
    print("=" * 70)
    
    optimizer = HighFrequencyOptimizer()
    
    try:
        # Run optimization
        results = await optimizer.optimize(iterations=100)
        
        # Show results
        print("\n" + "=" * 70)
        print("📊 HIGH FREQUENCY OPTIMIZATION RESULTS")
        print("=" * 70)
        
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
            win_rate_ok = best.win_rate >= 80.0
            freq_ok = best.trading_frequency >= 3.0
            
            print(f"\n🎯 TARGET ACHIEVEMENT:")
            print(f"  Win Rate 80%+: {'✅ YES' if win_rate_ok else '❌ NO'} ({best.win_rate:.2f}%)")
            print(f"  Trading Freq 3+/day: {'✅ YES' if freq_ok else '❌ NO'} ({best.trading_frequency:.2f})")
            
            if win_rate_ok and freq_ok:
                print(f"\n🎉 BOTH TARGETS ACHIEVED!")
                print(f"   🏆 Win Rate: {best.win_rate:.2f}% (Target: 80%+)")
                print(f"   📈 Trading Frequency: {best.trading_frequency:.2f}/day (Target: 3+)")
            elif win_rate_ok:
                print(f"\n⚠️  Win rate achieved, but need more trading frequency")
                print(f"   Current: {best.trading_frequency:.2f}/day | Target: 3.0+/day")
            elif freq_ok:
                print(f"\n⚠️  Trading frequency achieved, but need higher win rate")
                print(f"   Current: {best.win_rate:.2f}% | Target: 80%+")
            else:
                print(f"\n⚠️  Both targets need improvement")
                print(f"   Win Rate: {best.win_rate:.2f}% (need 80%+)")
                print(f"   Trading Freq: {best.trading_frequency:.2f}/day (need 3+)")
        
        # Show top 10 results
        print(f"\n🏅 TOP 10 RESULTS:")
        for i, result in enumerate(results[:10], 1):
            status = "✅" if result.win_rate >= 80.0 and result.trading_frequency >= 3.0 else "⚠️"
            print(f"{i:2d}. {status} WR: {result.win_rate:6.2f}% | "
                  f"Signals: {result.total_signals:2d} | "
                  f"Freq: {result.trading_frequency:4.2f}/day | "
                  f"Fitness: {result.fitness_score:5.2f}")
        
        # Save results
        optimizer.save_results()
        
        print(f"\n📁 Results saved to:")
        print(f"  - improved_optimization_results.json")
        print(f"  - improved_optimization_report.md")
        print(f"  - .env (updated with best parameters)")
        
        # Show parameter recommendations
        if optimizer.best_result:
            print(f"\n🔧 RECOMMENDED PARAMETERS:")
            print(f"   CONFIDENCE_THRESHOLD: {optimizer.best_result.parameters['CONFIDENCE_THRESHOLD']}")
            print(f"   RSI_OVERSOLD: {optimizer.best_result.parameters['RSI_OVERSOLD']}")
            print(f"   RSI_OVERBOUGHT: {optimizer.best_result.parameters['RSI_OVERBOUGHT']}")
            print(f"   MIN_VOLUME_RATIO: {optimizer.best_result.parameters['MIN_VOLUME_RATIO']}")
            print(f"   MIN_ATR_RATIO: {optimizer.best_result.parameters['MIN_ATR_RATIO']}")
            print(f"   TRADING_HOURS: {optimizer.best_result.parameters['TRADING_HOURS_START']}-{optimizer.best_result.parameters['TRADING_HOURS_END']}")
        
    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
