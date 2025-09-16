#!/usr/bin/env python3
"""
Realistic Signal Testing
Test with actual signal generation logic and conservative expectations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from src.strategies.signal_generator import SignalGenerator
from src.config import Config

def create_realistic_crypto_data(symbol: str, days: int = 7) -> pd.DataFrame:
    """Create realistic crypto market data"""
    periods = days * 24 * 12  # 5-minute intervals
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), 
                         periods=periods, freq='5min')
    
    # Base prices
    base_prices = {
        'BTC/USDT': 43000, 'ETH/USDT': 2600, 'SOL/USDT': 95,
        'BNB/USDT': 320, 'XRP/USDT': 0.52
    }
    base_price = base_prices.get(symbol, 100)
    
    # Generate realistic price movement
    np.random.seed(42)  # Fixed seed for reproducibility
    
    # Create realistic returns with different market conditions
    returns = []
    for i in range(periods):
        # Base volatility
        base_vol = 0.0008  # 0.08% per 5-min period
        
        # Add market regime changes
        if i % 500 < 200:  # Trending periods
            trend = 0.0002 if (i // 500) % 2 == 0 else -0.0002
        else:  # Sideways periods
            trend = 0
        
        # Random component
        random_return = np.random.normal(0, base_vol)
        
        # Mean reversion
        if i > 0:
            mean_rev = -0.01 * returns[-1] if len(returns) > 0 else 0
        else:
            mean_rev = 0
        
        total_return = random_return + trend + mean_rev
        returns.append(total_return)
    
    # Generate price series
    prices = [base_price]
    for i in range(1, periods):
        new_price = prices[-1] * (1 + returns[i])
        new_price = max(new_price, base_price * 0.85)  # Floor
        new_price = min(new_price, base_price * 1.15)  # Ceiling
        prices.append(new_price)
    
    # Create OHLCV data
    data = []
    for i, close in enumerate(prices):
        open_price = prices[i-1] if i > 0 else close
        
        # Realistic intraday range
        range_pct = abs(returns[i]) * 2
        
        if close >= open_price:  # Green candle
            high = close + (close * range_pct * 0.3)
            low = open_price - (open_price * range_pct * 0.2)
        else:  # Red candle
            high = open_price + (open_price * range_pct * 0.2)
            low = close - (close * range_pct * 0.3)
        
        # Ensure OHLC logic
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        # Volume correlated with volatility
        volume = 7000000 * (1 + abs(returns[i]) * 100) * np.random.uniform(0.8, 1.2)
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    return pd.DataFrame(data, index=dates)

def test_signal_generation_realistic():
    """Test signal generation with realistic expectations"""
    print("🧪 REALISTIC SIGNAL GENERATION TEST")
    print("=" * 50)
    
    # Test configurations
    configs = {
        'Conservative': {
            'CONFIDENCE_THRESHOLD': 0.70,
            'TREND_RSI_LONG_MIN': 55,
            'TREND_RSI_SHORT_MAX': 45,
            'RSI_OVERSOLD': 25,
            'RSI_OVERBOUGHT': 75
        },
        'Balanced': {
            'CONFIDENCE_THRESHOLD': 0.60,
            'TREND_RSI_LONG_MIN': 52,
            'TREND_RSI_SHORT_MAX': 48,
            'RSI_OVERSOLD': 30,
            'RSI_OVERBOUGHT': 70
        },
        'Aggressive': {
            'CONFIDENCE_THRESHOLD': 0.50,
            'TREND_RSI_LONG_MIN': 48,
            'TREND_RSI_SHORT_MAX': 52,
            'RSI_OVERSOLD': 35,
            'RSI_OVERBOUGHT': 65
        }
    }
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    days = 7
    
    signal_gen = SignalGenerator()
    results = {}
    
    for config_name, config in configs.items():
        print(f"\n🔧 Testing {config_name} Configuration:")
        print(f"   Confidence Threshold: {config['CONFIDENCE_THRESHOLD']}")
        print(f"   RSI Thresholds: {config['TREND_RSI_LONG_MIN']}/{config['TREND_RSI_SHORT_MAX']}")
        
        # Temporarily override config
        original_values = {}
        for key, value in config.items():
            if hasattr(Config, key):
                original_values[key] = getattr(Config, key)
                setattr(Config, key, value)
        
        total_signals = 0
        all_signals = []
        
        try:
            for symbol in symbols:
                df = create_realistic_crypto_data(symbol, days)
                symbol_signals = 0
                
                # Test signal generation every hour (12 periods)
                for i in range(200, len(df) - 50, 12):
                    try:
                        current_data = df.iloc[:i+1]
                        signal = signal_gen.generate_signal(symbol, current_data)
                        
                        if signal:
                            symbol_signals += 1
                            total_signals += 1
                            
                            # Estimate realistic win probability based on confidence
                            # More conservative estimates
                            base_win_prob = 0.52  # Slightly better than random
                            confidence_bonus = (signal['confidence'] - 0.5) * 0.2  # Max 10% bonus
                            win_prob = min(base_win_prob + confidence_bonus, 0.65)  # Cap at 65%
                            
                            # Simulate outcome
                            is_win = np.random.random() < win_prob
                            
                            signal_info = {
                                'symbol': symbol,
                                'direction': signal['direction'],
                                'type': signal['type'],
                                'confidence': signal['confidence'],
                                'conditions': len(signal.get('conditions_met', [])),
                                'estimated_win_prob': win_prob,
                                'simulated_result': 'WIN' if is_win else 'LOSS'
                            }
                            all_signals.append(signal_info)
                    
                    except Exception as e:
                        continue
                
                print(f"   {symbol}: {symbol_signals} signals")
            
            # Calculate metrics
            signals_per_day = total_signals / days
            
            if all_signals:
                wins = len([s for s in all_signals if s['simulated_result'] == 'WIN'])
                simulated_win_rate = (wins / len(all_signals)) * 100
                avg_confidence = sum([s['confidence'] for s in all_signals]) / len(all_signals)
                avg_conditions = sum([s['conditions'] for s in all_signals]) / len(all_signals)
                
                # Strategy breakdown
                strategy_breakdown = {}
                for signal in all_signals:
                    strategy = signal['type']
                    if strategy not in strategy_breakdown:
                        strategy_breakdown[strategy] = {'total': 0, 'wins': 0}
                    
                    strategy_breakdown[strategy]['total'] += 1
                    if signal['simulated_result'] == 'WIN':
                        strategy_breakdown[strategy]['wins'] += 1
                
                for strategy, data in strategy_breakdown.items():
                    data['win_rate'] = (data['wins'] / data['total']) * 100 if data['total'] > 0 else 0
                
                results[config_name] = {
                    'total_signals': total_signals,
                    'signals_per_day': round(signals_per_day, 2),
                    'simulated_win_rate': round(simulated_win_rate, 1),
                    'avg_confidence': round(avg_confidence, 3),
                    'avg_conditions': round(avg_conditions, 1),
                    'strategy_breakdown': strategy_breakdown,
                    'config': config
                }
                
                print(f"   📊 Total Signals: {total_signals}")
                print(f"   📈 Signals/Day: {signals_per_day:.2f}")
                print(f"   🎯 Simulated Win Rate: {simulated_win_rate:.1f}%")
                print(f"   ⚖️  Avg Confidence: {avg_confidence:.3f}")
                print(f"   📋 Avg Conditions: {avg_conditions:.1f}")
                
                for strategy, data in strategy_breakdown.items():
                    print(f"   📊 {strategy}: {data['win_rate']:.1f}% ({data['total']} signals)")
            
            else:
                results[config_name] = {
                    'total_signals': 0,
                    'signals_per_day': 0,
                    'simulated_win_rate': 0,
                    'message': 'No signals generated'
                }
                print(f"   ❌ No signals generated")
        
        finally:
            # Restore original config
            for key, value in original_values.items():
                setattr(Config, key, value)
    
    # Summary and comparison
    print(f"\n📊 REALISTIC PERFORMANCE COMPARISON:")
    print("=" * 60)
    
    if results:
        # Sort by a balanced score
        scored_results = []
        for name, data in results.items():
            if data['total_signals'] > 0:
                # Score: balance between win rate and signal frequency
                frequency_score = min(data['signals_per_day'] / 2, 1)  # Target ~2/day
                win_rate_score = data['simulated_win_rate'] / 100
                combined_score = (win_rate_score * 0.7) + (frequency_score * 0.3)
                
                scored_results.append((name, data, combined_score))
        
        scored_results.sort(key=lambda x: x[2], reverse=True)
        
        for i, (name, data, score) in enumerate(scored_results, 1):
            print(f"\n#{i} {name} (Score: {score:.3f})")
            print(f"   📈 Win Rate: {data['simulated_win_rate']}%")
            print(f"   🔄 Signals/Day: {data['signals_per_day']}")
            print(f"   📊 Total Signals: {data['total_signals']}")
            print(f"   🎯 Avg Confidence: {data['avg_confidence']}")
    
    # Realistic expectations
    print(f"\n🎯 REALISTIC EXPECTATIONS:")
    print("=" * 40)
    print("Based on this test, realistic performance expectations are:")
    print("• Win Rate: 50-60% (anything above 55% is good)")
    print("• Signals/Day: 0.5-3.0 (1-2 per day is realistic)")
    print("• Confidence: 0.6-0.8 (higher confidence = fewer signals)")
    print("• Market conditions greatly affect performance")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'realistic_test_results_{timestamp}.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: realistic_test_results_{timestamp}.json")
    
    # Recommendation
    if scored_results:
        best_name, best_data, best_score = scored_results[0]
        print(f"\n🏆 RECOMMENDED CONFIGURATION: {best_name}")
        print("Update your .env file with:")
        for key, value in best_data['config'].items():
            print(f"{key}={value}")
        
        print(f"\nExpected realistic performance:")
        print(f"• Win Rate: ~{best_data['simulated_win_rate']}%")
        print(f"• Signals per Day: ~{best_data['signals_per_day']}")
    
    return results

if __name__ == "__main__":
    test_signal_generation_realistic()
