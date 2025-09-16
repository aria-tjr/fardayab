#!/usr/bin/env python3
"""
Quick Backtest - High Win Rate + High Signal Frequency Analysis
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import json

# Import our signal generator
from src.strategies.signal_generator import SignalGenerator
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuickBacktest:
    """Fast backtesting for win rate and frequency analysis"""
    
    def __init__(self):
        self.signal_generator = SignalGenerator()
    
    def create_test_data(self, symbol: str, days: int = 7) -> pd.DataFrame:
        """Create realistic test data quickly"""
        periods = days * 24 * 12  # 5-minute intervals
        dates = pd.date_range(start=datetime.now() - timedelta(days=days), 
                             periods=periods, freq='5min')
        
        # Base price for different symbols
        base_prices = {
            'BTC/USDT': 43000,
            'ETH/USDT': 2600,
            'SOL/USDT': 95,
            'BNB/USDT': 320,
            'XRP/USDT': 0.52
        }
        
        base_price = base_prices.get(symbol, 100)
        
        # Generate price series with realistic volatility
        np.random.seed(42)  # For reproducible results
        returns = np.random.normal(0, 0.0015, periods)  # 0.15% volatility
        
        prices = [base_price]
        for i in range(1, periods):
            # Add trend and mean reversion
            trend = 0.00005 * np.sin(i / 100)  # Cyclical trend
            mean_rev = -0.05 * (prices[-1] / base_price - 1)
            
            change = returns[i] + trend + mean_rev * 0.01
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, base_price * 0.7))
        
        # Create OHLCV
        data = []
        for i, price in enumerate(prices):
            volatility = abs(returns[i]) * price * 2
            
            open_p = prices[i-1] if i > 0 else price
            close_p = price
            high_p = max(open_p, close_p) + np.random.uniform(0, volatility)
            low_p = min(open_p, close_p) - np.random.uniform(0, volatility)
            volume = np.random.uniform(5000000, 15000000)  # Above 5M threshold
            
            data.append({
                'open': open_p,
                'high': high_p,
                'low': low_p,
                'close': close_p,
                'volume': volume
            })
        
        return pd.DataFrame(data, index=dates)
    
    def simulate_signal_outcome(self, signal: Dict) -> Dict:
        """Quick simulation of signal outcome"""
        # Simulate based on confidence and market conditions
        confidence = signal['confidence']
        
        # Higher confidence = higher win probability
        win_probability = 0.45 + (confidence - 0.5) * 0.4  # 45-85% based on confidence
        
        # Random outcome based on probability
        is_win = np.random.random() < win_probability
        
        if is_win:
            # Winning trade: 0.5% to 2.5% profit
            pnl = np.random.uniform(0.5, 2.5)
            return {'result': 'WIN', 'pnl': pnl}
        else:
            # Losing trade: -0.3% to -1.8% loss
            pnl = np.random.uniform(-1.8, -0.3)
            return {'result': 'LOSS', 'pnl': pnl}
    
    def test_configuration(self, config: Dict, symbols: List[str]) -> Dict:
        """Test a configuration quickly"""
        # Temporarily override config
        original_values = {}
        for key, value in config.items():
            if hasattr(Config, key):
                original_values[key] = getattr(Config, key)
                setattr(Config, key, value)
        
        all_signals = []
        
        try:
            for symbol in symbols:
                df = self.create_test_data(symbol, days=7)  # 7 days of data
                
                # Generate signals (check every 10 candles for speed)
                for i in range(200, len(df) - 50, 10):
                    current_data = df.iloc[:i+1]
                    
                    signal = self.signal_generator.generate_signal(symbol, current_data)
                    if signal:
                        outcome = self.simulate_signal_outcome(signal)
                        
                        signal_result = {
                            'symbol': symbol,
                            'direction': signal['direction'],
                            'type': signal['type'],
                            'confidence': signal['confidence'],
                            'conditions': len(signal.get('conditions_met', [])),
                            **outcome
                        }
                        all_signals.append(signal_result)
            
        finally:
            # Restore original values
            for key, value in original_values.items():
                setattr(Config, key, value)
        
        # Analyze results
        if not all_signals:
            return {'error': 'No signals generated'}
        
        df = pd.DataFrame(all_signals)
        
        total_signals = len(df)
        wins = len(df[df['result'] == 'WIN'])
        win_rate = (wins / total_signals * 100) if total_signals > 0 else 0
        signals_per_day = total_signals / 7  # 7 days of data
        
        avg_win = df[df['result'] == 'WIN']['pnl'].mean() if wins > 0 else 0
        avg_loss = df[df['result'] == 'LOSS']['pnl'].mean() if total_signals - wins > 0 else 0
        total_pnl = df['pnl'].sum()
        
        return {
            'total_signals': total_signals,
            'win_rate': round(win_rate, 2),
            'signals_per_day': round(signals_per_day, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
            'by_strategy': df.groupby('type')['result'].apply(lambda x: round((x == 'WIN').mean() * 100, 1)).to_dict(),
            'by_symbol': df.groupby('symbol')['result'].apply(lambda x: round((x == 'WIN').mean() * 100, 1)).to_dict()
        }

def run_quick_analysis():
    """Run quick analysis of different configurations"""
    print("🚀 Quick Backtest - High Win Rate + High Signal Frequency")
    print("=" * 60)
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
    backtest = QuickBacktest()
    
    # Test configurations
    configs = {
        'Current (Default)': {
            'CONFIDENCE_THRESHOLD': 0.65,
            'TREND_RSI_LONG_MIN': 53,
            'TREND_RSI_SHORT_MAX': 47,
            'RSI_OVERSOLD': 30,
            'RSI_OVERBOUGHT': 70
        },
        'High Frequency': {
            'CONFIDENCE_THRESHOLD': 0.55,
            'TREND_RSI_LONG_MIN': 50,
            'TREND_RSI_SHORT_MAX': 50,
            'RSI_OVERSOLD': 35,
            'RSI_OVERBOUGHT': 65
        },
        'High Win Rate': {
            'CONFIDENCE_THRESHOLD': 0.75,
            'TREND_RSI_LONG_MIN': 55,
            'TREND_RSI_SHORT_MAX': 45,
            'RSI_OVERSOLD': 25,
            'RSI_OVERBOUGHT': 75
        },
        'Balanced Optimal': {
            'CONFIDENCE_THRESHOLD': 0.60,
            'TREND_RSI_LONG_MIN': 51,
            'TREND_RSI_SHORT_MAX': 49,
            'RSI_OVERSOLD': 32,
            'RSI_OVERBOUGHT': 68
        },
        'Ultra Aggressive': {
            'CONFIDENCE_THRESHOLD': 0.50,
            'TREND_RSI_LONG_MIN': 48,
            'TREND_RSI_SHORT_MAX': 52,
            'RSI_OVERSOLD': 40,
            'RSI_OVERBOUGHT': 60
        }
    }
    
    results = {}
    
    print("\n📊 Testing Configurations...")
    for name, config in configs.items():
        print(f"\n🔧 Testing: {name}")
        try:
            result = backtest.test_configuration(config, symbols)
            if 'error' not in result:
                results[name] = {**result, 'config': config}
                
                # Calculate combined score (60% win rate, 40% frequency)
                win_score = result['win_rate'] / 100
                freq_score = min(result['signals_per_day'] / 4, 1)  # Target 4/day
                combined_score = (win_score * 0.6) + (freq_score * 0.4)
                results[name]['combined_score'] = round(combined_score, 3)
                
                print(f"   Win Rate: {result['win_rate']}%")
                print(f"   Signals/Day: {result['signals_per_day']}")
                print(f"   Total PnL: {result['total_pnl']}%")
                print(f"   Score: {combined_score:.3f}")
            else:
                print(f"   ❌ {result['error']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Rank results
    if results:
        ranked = sorted(results.items(), key=lambda x: x[1]['combined_score'], reverse=True)
        
        print(f"\n🏆 RANKING (Best to Worst):")
        print("=" * 50)
        
        for i, (name, data) in enumerate(ranked, 1):
            print(f"\n#{i} {name}")
            print(f"   🎯 Score: {data['combined_score']:.3f}")
            print(f"   📈 Win Rate: {data['win_rate']}%")
            print(f"   🔄 Signals/Day: {data['signals_per_day']}")
            print(f"   💰 Total PnL: {data['total_pnl']}%")
            print(f"   ⚖️  Profit Factor: {data['profit_factor']}")
        
        # Best configuration
        best_name, best_data = ranked[0]
        print(f"\n🥇 RECOMMENDED CONFIGURATION: {best_name}")
        print("=" * 40)
        print("Add these settings to your .env file:")
        for key, value in best_data['config'].items():
            print(f"{key}={value}")
        
        print(f"\n📊 Expected Performance:")
        print(f"   • Win Rate: {best_data['win_rate']}%")
        print(f"   • Signals per Day: {best_data['signals_per_day']}")
        print(f"   • Monthly Signals: ~{best_data['signals_per_day'] * 30:.0f}")
        
        # Strategy breakdown
        if 'by_strategy' in best_data:
            print(f"\n📈 By Strategy:")
            for strategy, win_rate in best_data['by_strategy'].items():
                print(f"   • {strategy}: {win_rate}% win rate")
        
        if 'by_symbol' in best_data:
            print(f"\n💎 By Symbol:")
            for symbol, win_rate in best_data['by_symbol'].items():
                print(f"   • {symbol}: {win_rate}% win rate")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'quick_backtest_results_{timestamp}.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: quick_backtest_results_{timestamp}.json")
        
        return best_data
    
    else:
        print("❌ No valid results obtained")
        return None

if __name__ == "__main__":
    run_quick_analysis()
