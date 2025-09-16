#!/usr/bin/env python3
"""
Improved Parameter Optimizer - Focused on 80%+ Win Rate
Addresses signal generation issues with more balanced approach
"""
import os
import sys
import json
import random
import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import logging

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.backtesting.backtester import Backtester

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class OptimizationResult:
    """Result of optimization iteration"""
    parameters: Dict[str, Any]
    win_rate: float
    total_signals: int
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    fitness_score: float
    trading_frequency: float

class ImprovedOptimizer:
    """Improved optimizer with better parameter ranges and signal generation"""
    
    def __init__(self):
        # More balanced parameter ranges for better signal generation
        self.param_ranges = {
            'CONFIDENCE_THRESHOLD': (0.70, 0.95),  # Lowered from 0.75-0.99
            'ULTRA_MIN_CONFIDENCE': (0.80, 0.95),  # Lowered from 0.85-0.99
            'RSI_OVERSOLD': (25, 40),  # More permissive
            'RSI_OVERBOUGHT': (60, 75),  # More permissive
            'STOP_LOSS_ATR_MULTIPLIER': (1.0, 2.5),  # Better risk management
            'TAKE_PROFIT_ATR_MULTIPLIER': (1.5, 3.0),  # Better reward
            'MIN_VOLUME_RATIO': (1.2, 2.5),  # More permissive
            'MIN_ATR_RATIO': (1.1, 2.0),  # More permissive
            'MIN_TREND_STRENGTH': (20, 45),  # More permissive
            'MIN_MOMENTUM_CONSISTENCY': (2, 4),  # More permissive
            'TRADING_HOURS_START': (10, 14),  # Focused hours
            'TRADING_HOURS_END': (14, 18),  # Focused hours
            'MIN_RSI_DIVERGENCE': (5, 15),  # More permissive
            'MAX_VOLATILITY': (0.03, 0.06),  # Balanced volatility
            'POSITION_SIZE': (0.03, 0.10),  # Conservative position sizing
            'MAX_DRAWDOWN_PCT': (3.0, 6.0),  # Balanced risk
            'MAX_CONCURRENT_TRADES': (1, 3),  # Allow some diversification
            'MAX_CONSECUTIVE_LOSSES': (2, 4)  # Balanced loss management
        }
        
        self.results = []
        self.best_result = None
    
    def create_random_parameters(self) -> Dict[str, Any]:
        """Create random parameters within ranges"""
        params = {}
        
        for param, (min_val, max_val) in self.param_ranges.items():
            if isinstance(min_val, int):
                params[param] = random.randint(min_val, max_val)
            else:
                params[param] = round(random.uniform(min_val, max_val), 3)
        
        # Ensure logical constraints
        if params['RSI_OVERBOUGHT'] - params['RSI_OVERSOLD'] < 15:
            params['RSI_OVERBOUGHT'] = params['RSI_OVERSOLD'] + 15
            params['RSI_OVERBOUGHT'] = min(params['RSI_OVERBOUGHT'], 75)
        
        if params['TRADING_HOURS_END'] <= params['TRADING_HOURS_START']:
            params['TRADING_HOURS_END'] = params['TRADING_HOURS_START'] + 4
        
        if params['TAKE_PROFIT_ATR_MULTIPLIER'] <= params['STOP_LOSS_ATR_MULTIPLIER']:
            params['TAKE_PROFIT_ATR_MULTIPLIER'] = params['STOP_LOSS_ATR_MULTIPLIER'] + 0.5
        
        return params
    
    def set_parameters(self, params: Dict[str, Any]):
        """Set parameters in Config class"""
        for param, value in params.items():
            if hasattr(Config, param):
                setattr(Config, param, value)
    
    async def evaluate_parameters(self, params: Dict[str, Any]) -> OptimizationResult:
        """Evaluate parameters using backtesting"""
        try:
            # Set parameters
            self.set_parameters(params)
            
            # Run backtest
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            backtester = Backtester(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            result = await backtester.run_backtest()
            backtester.close()
            
            # Calculate trading frequency
            days = (end_date - start_date).days
            trading_frequency = result.total_signals / days if days > 0 else 0
            
            # Calculate fitness score
            fitness = self.calculate_fitness(
                win_rate=result.win_rate,
                total_signals=result.total_signals,
                total_pnl=result.total_pnl,
                max_drawdown=result.max_drawdown,
                sharpe_ratio=result.sharpe_ratio,
                profit_factor=result.profit_factor,
                trading_frequency=trading_frequency
            )
            
            return OptimizationResult(
                parameters=params.copy(),
                win_rate=result.win_rate,
                total_signals=result.total_signals,
                total_pnl=result.total_pnl,
                max_drawdown=result.max_drawdown,
                sharpe_ratio=result.sharpe_ratio,
                profit_factor=result.profit_factor,
                fitness_score=fitness,
                trading_frequency=trading_frequency
            )
            
        except Exception as e:
            logger.error(f"Error evaluating parameters: {e}")
            # Return poor result for failed evaluations
            return OptimizationResult(
                parameters=params.copy(),
                win_rate=0.0,
                total_signals=0,
                total_pnl=-1000.0,
                max_drawdown=100.0,
                sharpe_ratio=-10.0,
                profit_factor=0.0,
                fitness_score=-1000.0,
                trading_frequency=0.0
            )
    
    def calculate_fitness(self, win_rate: float, total_signals: int, total_pnl: float, 
                         max_drawdown: float, sharpe_ratio: float, profit_factor: float,
                         trading_frequency: float) -> float:
        """Calculate fitness score with focus on win rate and signal generation"""
        
        # Primary: Win rate (heavily weighted)
        win_rate_score = min(win_rate / 80.0, 1.0) * 50
        
        # Secondary: Signal generation (moderate weight)
        signal_score = min(total_signals / 20.0, 1.0) * 20  # Target 20+ signals
        
        # Trading frequency bonus
        freq_score = min(trading_frequency / 1.0, 1.0) * 15  # Target 1+ signals/day
        
        # Risk management
        drawdown_penalty = max(0, (max_drawdown - 10) / 10) * 10  # Penalty for high drawdown
        sharpe_bonus = max(0, min(sharpe_ratio / 1.5, 1.0)) * 10  # Bonus for good Sharpe
        
        # Profit factor bonus
        pf_bonus = max(0, min((profit_factor - 1.0) / 1.0, 1.0)) * 5  # Bonus for good PF
        
        # PnL bonus
        pnl_bonus = max(0, min(total_pnl / 500, 1.0)) * 5  # Bonus for positive PnL
        
        # Calculate final fitness
        fitness = (win_rate_score + signal_score + freq_score + sharpe_bonus + 
                  pf_bonus + pnl_bonus - drawdown_penalty)
        
        return max(fitness, 0)
    
    async def optimize(self, iterations: int = 50) -> List[OptimizationResult]:
        """Run optimization with multiple iterations"""
        logger.info(f"Starting optimization with {iterations} iterations")
        
        for i in range(iterations):
            logger.info(f"Iteration {i+1}/{iterations}")
            
            # Create random parameters
            params = self.create_random_parameters()
            
            # Evaluate parameters
            result = await self.evaluate_parameters(params)
            self.results.append(result)
            
            # Update best result
            if self.best_result is None or result.fitness_score > self.best_result.fitness_score:
                self.best_result = result
            
            # Log progress
            logger.info(f"  Win rate: {result.win_rate:.2f}% | Signals: {result.total_signals} | "
                       f"Fitness: {result.fitness_score:.2f} | Trading freq: {result.trading_frequency:.2f}")
            
            # Early stopping if target achieved
            if result.win_rate >= 80.0 and result.total_signals >= 10:
                logger.info(f"Target achieved! Win rate: {result.win_rate:.2f}%, Signals: {result.total_signals}")
                break
        
        # Sort results by fitness
        self.results.sort(key=lambda x: x.fitness_score, reverse=True)
        
        return self.results
    
    def save_results(self):
        """Save optimization results"""
        try:
            # Save all results
            results_data = [asdict(result) for result in self.results]
            with open('improved_optimization_results.json', 'w') as f:
                json.dump(results_data, f, indent=2, default=str)
            
            # Save best parameters to .env
            if self.best_result:
                self.update_env_file('.env', self.best_result.parameters)
            
            # Generate report
            self.generate_report()
            
            logger.info("Results saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def update_env_file(self, path: str, updates: dict):
        """Update .env file with best parameters"""
        lines = []
        existing = {}
        
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            for line in lines:
                if not line or line.strip().startswith('#') or '=' not in line:
                    continue
                k, _, v = line.partition('=')
                existing[k.strip()] = v
        
        # Apply updates
        for k, v in updates.items():
            existing[k] = str(v)
        
        # Rebuild env content
        new_lines = []
        seen = set()
        for line in lines:
            if not line or line.strip().startswith('#') or '=' not in line:
                new_lines.append(line)
                continue
            k, _, _ = line.partition('=')
            key = k.strip()
            if key in updates:
                new_lines.append(f"{key}={existing[key]}")
                seen.add(key)
            else:
                new_lines.append(line)
        
        for k, v in existing.items():
            if k not in [l.partition('=')[0].strip() for l in new_lines if '=' in l]:
                new_lines.append(f"{k}={v}")
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(new_lines) + "\n")
    
    def generate_report(self):
        """Generate optimization report"""
        if not self.best_result:
            return
        
        report = f"""
# 🚀 Improved Parameter Optimization Report

## 📊 Best Results
- **Win Rate**: {self.best_result.win_rate:.2f}%
- **Total Signals**: {self.best_result.total_signals}
- **Trading Frequency**: {self.best_result.trading_frequency:.2f} signals/day
- **Total P&L**: ${self.best_result.total_pnl:.2f}
- **Max Drawdown**: {self.best_result.max_drawdown:.2f}%
- **Sharpe Ratio**: {self.best_result.sharpe_ratio:.2f}
- **Profit Factor**: {self.best_result.profit_factor:.2f}
- **Fitness Score**: {self.best_result.fitness_score:.2f}

## 🎯 Target Achievement
- **Target Win Rate**: 80%
- **Achieved**: {'✅ YES' if self.best_result.win_rate >= 80.0 else '❌ NO'}
- **Target Signals**: 10+
- **Achieved**: {'✅ YES' if self.best_result.total_signals >= 10 else '❌ NO'}

## 🔧 Best Parameters
"""
        
        for param, value in self.best_result.parameters.items():
            report += f"- **{param}**: {value}\n"
        
        report += f"""
## 📈 Top 10 Results
"""
        
        for i, result in enumerate(self.results[:10], 1):
            report += f"{i}. Win Rate: {result.win_rate:.2f}% | Signals: {result.total_signals} | "
            report += f"Fitness: {result.fitness_score:.2f} | Trading Freq: {result.trading_frequency:.2f}\n"
        
        report += f"""
## 🎯 Next Steps
"""
        
        if self.best_result.win_rate < 80.0:
            report += "- Continue optimization to reach 80%+ win rate\n"
        
        if self.best_result.total_signals < 10:
            report += "- Adjust parameters to generate more signals\n"
        
        if self.best_result.max_drawdown > 15:
            report += "- Improve risk management to reduce drawdown\n"
        
        report += f"- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        with open('improved_optimization_report.md', 'w', encoding='utf-8') as f:
            f.write(report)

async def main():
    """Main function"""
    print("🚀 Improved Parameter Optimizer")
    print("🎯 Target: 80%+ Win Rate with Good Signal Generation")
    print("=" * 50)
    
    optimizer = ImprovedOptimizer()
    
    try:
        # Run optimization
        results = await optimizer.optimize(iterations=30)
        
        # Show results
        print("\n" + "=" * 50)
        print("📊 OPTIMIZATION RESULTS")
        print("=" * 50)
        
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
                print(f"\n✅ WIN RATE TARGET ACHIEVED! {best.win_rate:.2f}%")
            else:
                print(f"\n⚠️  Win rate target not reached. Current: {best.win_rate:.2f}%")
            
            if best.total_signals >= 10:
                print(f"✅ SIGNAL GENERATION TARGET ACHIEVED! {best.total_signals} signals")
            else:
                print(f"⚠️  Signal generation needs improvement. Current: {best.total_signals} signals")
        
        # Save results
        optimizer.save_results()
        
        print(f"\n📁 Results saved to:")
        print(f"  - improved_optimization_results.json")
        print(f"  - improved_optimization_report.md")
        print(f"  - .env (updated with best parameters)")
        
    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
