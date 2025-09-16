#!/usr/bin/env python3
"""
Quick optimization demo - runs a few generations to show the system working
"""
import asyncio
import sys
import os
from continuous_optimizer import GeneticOptimizer

async def main():
    """Run a quick optimization demo"""
    print("🚀 Quick Optimization Demo")
    print("🎯 Target: 80%+ Win Rate")
    print("⚙️  Running 5 generations with 20 individuals each")
    print("=" * 50)
    
    # Create optimizer with smaller population for demo
    optimizer = GeneticOptimizer(
        target_win_rate=80.0,
        min_trading_frequency=0.5,
        population_size=20,
        max_generations=5,
        mutation_rate=0.2,
        crossover_rate=0.8,
        elite_size=3
    )
    
    try:
        # Run optimization
        results = await optimizer.optimize()
        
        # Show results
        print("\n" + "=" * 50)
        print("📊 OPTIMIZATION RESULTS")
        print("=" * 50)
        
        if results:
            best = results[0]
            print(f"🏆 Best Win Rate: {best.win_rate:.2f}%")
            print(f"📈 Trading Frequency: {best.trading_frequency:.2f} signals/day")
            print(f"💰 Total P&L: ${best.total_pnl:.2f}")
            print(f"📉 Max Drawdown: {best.max_drawdown:.2f}%")
            print(f"📊 Sharpe Ratio: {best.sharpe_ratio:.2f}")
            print(f"🎯 Fitness Score: {best.fitness_score:.2f}")
            
            print(f"\n🔧 Best Parameters:")
            for param, value in best.parameters.items():
                print(f"  {param}: {value}")
            
            # Check if target achieved
            if best.win_rate >= 80.0:
                print(f"\n✅ TARGET ACHIEVED! Win rate: {best.win_rate:.2f}%")
            else:
                print(f"\n⚠️  Target not yet reached. Current: {best.win_rate:.2f}%")
                print("   Run more generations or adjust parameters")
        
        print(f"\n📁 Results saved to:")
        print(f"  - optimization_best_individuals.json")
        print(f"  - optimization_stats.json")
        print(f"  - continuous_optimization_report.md")
        
    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
