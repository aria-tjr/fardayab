#!/usr/bin/env python3
"""
Parameter optimization script for crypto signal bot
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import itertools
import json
from typing import Dict, List, Tuple
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.backtesting.backtester import Backtester
from src.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimization.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ParameterOptimizer:
    """Optimize strategy parameters using grid search"""
    
    def __init__(self):
        self.best_params = None
        self.best_score = -float('inf')
        self.results = []
        
    def define_parameter_space(self) -> Dict:
        """Define parameter search space"""
        return {
            # RSI parameters
            'RSI_OVERSOLD': [25, 30, 35, 40],
            'RSI_OVERBOUGHT': [60, 65, 70, 75],
            'TREND_RSI_LONG_MIN': [45, 50, 55, 60],
            'TREND_RSI_SHORT_MAX': [40, 45, 50, 55],
            
            # Confidence and volume filters
            'CONFIDENCE_THRESHOLD': [0.60, 0.65, 0.70, 0.75],
            'MIN_VOLUME_RATIO': [1.0, 1.2, 1.5, 2.0],
            'MIN_ATR_RATIO': [0.8, 1.0, 1.2, 1.5],
            
            # Risk management
            'STOP_LOSS_ATR_MULTIPLIER': [1.0, 1.5, 2.0, 2.5],
            'TAKE_PROFIT_ATR_MULTIPLIER': [1.5, 2.0, 2.5, 3.0],
            'MAX_DRAWDOWN_PCT': [3.0, 5.0, 7.0, 10.0],
            
            # Trading hours (more permissive)
            'TRADING_HOURS_START': [6, 8, 10],
            'TRADING_HOURS_END': [20, 22, 23],
        }
    
    def calculate_fitness_score(self, result) -> float:
        """Calculate fitness score for parameter combination"""
        if result.total_signals == 0:
            return -1000  # Penalize no signals heavily
        
        # Multi-objective optimization
        win_rate_score = result.win_rate * 10  # 0-1000 points
        profit_score = max(0, result.total_pnl) * 0.1  # Profit contribution
        signal_count_score = min(result.total_signals * 5, 100)  # Reward more signals, cap at 100
        drawdown_penalty = -result.max_drawdown * 5  # Penalize high drawdown
        sharpe_bonus = max(0, result.sharpe_ratio) * 50  # Reward positive Sharpe
        
        # Combined score with weights
        total_score = (
            win_rate_score * 0.4 +  # 40% weight on win rate
            profit_score * 0.2 +    # 20% weight on profit
            signal_count_score * 0.2 + # 20% weight on signal count
            drawdown_penalty * 0.1 +   # 10% penalty for drawdown
            sharpe_bonus * 0.1         # 10% bonus for Sharpe
        )
        
        return total_score
    
    async def test_parameter_combination(self, params: Dict) -> Tuple[Dict, float]:
        """Test a single parameter combination"""
        try:
            # Temporarily modify config
            original_values = {}
            for key, value in params.items():
                if hasattr(Config, key):
                    original_values[key] = getattr(Config, key)
                    setattr(Config, key, value)
            
            # Run backtest
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Shorter period for optimization
            
            backtester = Backtester(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            result = await backtester.run_backtest()
            score = self.calculate_fitness_score(result)
            
            backtester.close()
            
            # Restore original values
            for key, value in original_values.items():
                setattr(Config, key, value)
            
            return params, score, result
            
        except Exception as e:
            logger.error(f"Error testing parameters {params}: {e}")
            return params, -1000, None
    
    async def optimize_parameters(self, max_combinations: int = 100) -> Dict:
        """Optimize parameters using grid search"""
        try:
            logger.info("Starting parameter optimization...")
            
            param_space = self.define_parameter_space()
            
            # Generate all parameter combinations
            keys = list(param_space.keys())
            values = list(param_space.values())
            combinations = list(itertools.product(*values))
            
            # Limit combinations if too many
            if len(combinations) > max_combinations:
                import random
                combinations = random.sample(combinations, max_combinations)
                logger.info(f"Limited to {max_combinations} random combinations")
            
            logger.info(f"Testing {len(combinations)} parameter combinations...")
            
            best_score = -float('inf')
            best_params = None
            best_result = None
            
            for i, combination in enumerate(combinations):
                params = dict(zip(keys, combination))
                
                logger.info(f"Testing combination {i+1}/{len(combinations)}: {params}")
                
                params_dict, score, result = await self.test_parameter_combination(params)
                
                self.results.append({
                    'params': params_dict,
                    'score': score,
                    'result': {
                        'total_signals': result.total_signals if result else 0,
                        'win_rate': result.win_rate if result else 0,
                        'total_pnl': result.total_pnl if result else 0,
                        'max_drawdown': result.max_drawdown if result else 100,
                        'sharpe_ratio': result.sharpe_ratio if result else -10
                    }
                })
                
                if score > best_score:
                    best_score = score
                    best_params = params_dict
                    best_result = result
                    logger.info(f"New best score: {score:.2f} with params: {params_dict}")
                
                # Progress update
                if (i + 1) % 10 == 0:
                    logger.info(f"Completed {i+1}/{len(combinations)} combinations")
            
            # Save results
            with open('optimization_results.json', 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"Optimization completed. Best score: {best_score:.2f}")
            logger.info(f"Best parameters: {best_params}")
            
            if best_result:
                logger.info(f"Best result - Signals: {best_result.total_signals}, "
                          f"Win Rate: {best_result.win_rate:.1f}%, "
                          f"P&L: ${best_result.total_pnl:.2f}, "
                          f"Drawdown: {best_result.max_drawdown:.1f}%")
            
            return {
                'best_params': best_params,
                'best_score': best_score,
                'best_result': best_result,
                'all_results': self.results
            }
            
        except Exception as e:
            logger.error(f"Error in parameter optimization: {e}")
            raise

async def main():
    """Main optimization function"""
    try:
        optimizer = ParameterOptimizer()
        results = await optimizer.optimize_parameters(max_combinations=50)  # Limit for faster testing
        
        print("\n" + "="*60)
        print("🎯 PARAMETER OPTIMIZATION RESULTS")
        print("="*60)
        
        if results['best_params']:
            print(f"🏆 Best Score: {results['best_score']:.2f}")
            print(f"📊 Best Parameters:")
            for key, value in results['best_params'].items():
                print(f"   {key}: {value}")
            
            if results['best_result']:
                result = results['best_result']
                print(f"\n📈 Performance with Best Parameters:")
                print(f"   Total Signals: {result.total_signals}")
                print(f"   Win Rate: {result.win_rate:.1f}%")
                print(f"   Total P&L: ${result.total_pnl:.2f}")
                print(f"   Max Drawdown: {result.max_drawdown:.1f}%")
                print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
            
            # Generate optimized config
            print(f"\n🔧 Add these to your .env file:")
            for key, value in results['best_params'].items():
                print(f"{key}={value}")
        else:
            print("❌ No optimal parameters found")
        
        print("\n📋 Full results saved to optimization_results.json")
        
    except Exception as e:
        print(f"❌ Error in optimization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
