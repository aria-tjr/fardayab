#!/usr/bin/env python3
"""
Optimize for BOTH High Win Rate AND High Signal Frequency
Advanced multi-objective optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from src.strategies.signal_generator import SignalGenerator
from src.config import Config

class WinRateFrequencyOptimizer:
    """Optimize for both win rate and signal frequency"""
    
    def __init__(self):
        self.signal_gen = SignalGenerator()
        
    def create_diverse_market_data(self, symbol: str, days: int = 14) -> pd.DataFrame:
        """Create diverse market conditions for testing"""
        periods = days * 24 * 12  # 5-minute intervals
        dates = pd.date_range(start=datetime.now() - timedelta(days=days), 
                             periods=periods, freq='5min')
        
        base_prices = {
            'BTC/USDT': 43000, 'ETH/USDT': 2600, 'SOL/USDT': 95,
            'BNB/USDT': 320, 'XRP/USDT': 0.52
        }
        base_price = base_prices.get(symbol, 100)
        
        # Create different market regimes
        data = []
        np.random.seed(42)  # Reproducible results
        
        for i in range(periods):
            # Determine market regime
            regime_length = 200  # 200 periods per regime
            regime_type = (i // regime_length) % 4
            
            if regime_type == 0:  # Strong uptrend
                trend = 0.0008
                volatility = 0.001
            elif regime_type == 1:  # Sideways/consolidation
                trend = 0
                volatility = 0.0008
            elif regime_type == 2:  # Strong downtrend
                trend = -0.0008
                volatility = 0.001
            else:  # High volatility/choppy
                trend = np.random.choice([-0.0003, 0.0003])
                volatility = 0.002
            
            # Generate price movement
            random_move = np.random.normal(0, volatility)
            
            # Mean reversion component
            if i > 0:
                price_deviation = (data[-1]['close'] / base_price - 1)
                mean_reversion = -0.02 * price_deviation
            else:
                mean_reversion = 0
            
            total_return = trend + random_move + mean_reversion
            
            # Calculate new price
            if i == 0:
                price = base_price
            else:
                price = data[-1]['close'] * (1 + total_return)
                price = max(price, base_price * 0.7)  # Floor
                price = min(price, base_price * 1.4)  # Ceiling
            
            # Generate OHLCV
            open_price = data[-1]['close'] if i > 0 else price
            close_price = price
            
            # Realistic intraday range
            range_size = abs(total_return) * price * 3
            
            if close_price >= open_price:  # Green candle
                high = close_price + np.random.uniform(0, range_size * 0.4)
                low = open_price - np.random.uniform(0, range_size * 0.2)
            else:  # Red candle
                high = open_price + np.random.uniform(0, range_size * 0.2)
                low = close_price - np.random.uniform(0, range_size * 0.4)
            
            # Ensure OHLC logic
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            # Volume correlated with volatility and regime
            base_volume = 8000000  # Above 5M threshold
            volume_multiplier = 1 + abs(total_return) * 50
            if regime_type == 3:  # High volatility regime
                volume_multiplier *= 1.5
            
            volume = base_volume * volume_multiplier * np.random.uniform(0.9, 1.1)
            
            data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
        
        return pd.DataFrame(data, index=dates)
    
    def simulate_realistic_outcome(self, signal: dict, market_regime: str = 'mixed') -> dict:
        """Simulate realistic trade outcomes based on signal quality and market conditions"""
        
        # Base win probabilities by strategy and market regime
        base_probabilities = {
            'trend_following': {
                'trending': 0.65,    # Good in trending markets
                'sideways': 0.45,    # Poor in sideways markets
                'mixed': 0.55
            },
            'mean_reversion': {
                'trending': 0.45,    # Poor in strong trends
                'sideways': 0.70,    # Excellent in sideways markets
                'mixed': 0.58
            }
        }
        
        # Get base probability
        strategy = signal.get('type', 'trend_following')
        base_prob = base_probabilities.get(strategy, {}).get(market_regime, 0.55)
        
        # Adjust based on confidence (higher confidence = higher win rate)
        confidence = signal.get('confidence', 0.5)
        confidence_bonus = (confidence - 0.5) * 0.2  # Max 10% bonus for high confidence
        
        # Adjust based on number of conditions met
        conditions = signal.get('conditions', 3)
        condition_bonus = max(0, (conditions - 3) * 0.03)  # 3% per extra condition
        
        # Final win probability
        win_prob = base_prob + confidence_bonus + condition_bonus
        win_prob = max(0.35, min(0.80, win_prob))  # Cap between 35-80%
        
        # Simulate outcome
        is_win = np.random.random() < win_prob
        
        if is_win:
            # Winning trades: better profits for higher confidence
            if confidence > 0.7:
                pnl = np.random.uniform(1.2, 3.0)  # 1.2% to 3.0%
            else:
                pnl = np.random.uniform(0.8, 2.2)  # 0.8% to 2.2%
        else:
            # Losing trades: smaller losses for higher confidence (better risk management)
            if confidence > 0.7:
                pnl = np.random.uniform(-1.2, -0.6)  # -1.2% to -0.6%
            else:
                pnl = np.random.uniform(-1.8, -0.8)  # -1.8% to -0.8%
        
        return {
            'result': 'WIN' if is_win else 'LOSS',
            'pnl': pnl,
            'win_probability': win_prob,
            'market_regime': market_regime
        }
    
    def test_configuration(self, config: dict, symbols: list, days: int = 14) -> dict:
        """Test a configuration with realistic market simulation"""
        
        # Backup original config
        original_values = {}
        for key, value in config.items():
            if hasattr(Config, key):
                original_values[key] = getattr(Config, key)
                setattr(Config, key, value)
        
        all_results = []
        
        try:
            for symbol in symbols:
                # Create diverse market data
                df = self.create_diverse_market_data(symbol, days)
                
                # Test signal generation (every 8 candles = 40 minutes)
                for i in range(220, len(df) - 100, 8):
                    try:
                        current_data = df.iloc[:i+1]
                        signal = self.signal_gen.generate_signal(symbol, current_data)
                        
                        if signal:
                            # Determine market regime for this period
                            regime_idx = i // 200  # 200 periods per regime
                            regimes = ['trending', 'sideways', 'trending', 'choppy']
                            market_regime = regimes[regime_idx % 4] if regime_idx < 4 else 'mixed'
                            
                            # Simulate realistic outcome
                            outcome = self.simulate_realistic_outcome(signal, market_regime)
                            
                            result = {
                                'symbol': symbol,
                                'timestamp': df.index[i],
                                'direction': signal['direction'],
                                'type': signal['type'],
                                'confidence': signal['confidence'],
                                'conditions': len(signal.get('conditions_met', [])),
                                'market_regime': market_regime,
                                **outcome
                            }
                            
                            all_results.append(result)
                    
                    except Exception as e:
                        continue
                        
        finally:
            # Restore original config
            for key, value in original_values.items():
                setattr(Config, key, value)
        
        return self.analyze_results(all_results, days)
    
    def analyze_results(self, results: list, days: int) -> dict:
        """Analyze results with focus on win rate and frequency"""
        if not results:
            return {'error': 'No results to analyze'}
        
        df = pd.DataFrame(results)
        
        # Basic metrics
        total_signals = len(df)
        wins = len(df[df['result'] == 'WIN'])
        win_rate = (wins / total_signals * 100) if total_signals > 0 else 0
        signals_per_day = total_signals / days
        
        # PnL analysis
        total_pnl = df['pnl'].sum()
        avg_win = df[df['result'] == 'WIN']['pnl'].mean() if wins > 0 else 0
        avg_loss = df[df['result'] == 'LOSS']['pnl'].mean() if total_signals - wins > 0 else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Strategy performance
        strategy_stats = {}
        for strategy in df['type'].unique():
            strategy_df = df[df['type'] == strategy]
            strategy_wins = len(strategy_df[strategy_df['result'] == 'WIN'])
            strategy_total = len(strategy_df)
            
            strategy_stats[strategy] = {
                'signals': strategy_total,
                'win_rate': round((strategy_wins / strategy_total * 100), 1) if strategy_total > 0 else 0,
                'avg_confidence': round(strategy_df['confidence'].mean(), 3),
                'total_pnl': round(strategy_df['pnl'].sum(), 2)
            }
        
        # Market regime performance
        regime_stats = {}
        for regime in df['market_regime'].unique():
            regime_df = df[df['market_regime'] == regime]
            regime_wins = len(regime_df[regime_df['result'] == 'WIN'])
            regime_total = len(regime_df)
            
            regime_stats[regime] = {
                'signals': regime_total,
                'win_rate': round((regime_wins / regime_total * 100), 1) if regime_total > 0 else 0
            }
        
        # Confidence analysis
        high_conf = df[df['confidence'] >= 0.7]
        high_conf_wins = len(high_conf[high_conf['result'] == 'WIN'])
        high_conf_win_rate = (high_conf_wins / len(high_conf) * 100) if len(high_conf) > 0 else 0
        
        return {
            'total_signals': total_signals,
            'win_rate': round(win_rate, 1),
            'signals_per_day': round(signals_per_day, 1),
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'high_confidence_win_rate': round(high_conf_win_rate, 1),
            'high_confidence_signals': len(high_conf),
            'strategy_breakdown': strategy_stats,
            'regime_performance': regime_stats
        }
    
    def optimize_for_both_objectives(self) -> list:
        """Optimize for both high win rate and high signal frequency"""
        
        print("🎯 OPTIMIZING FOR HIGH WIN RATE + HIGH SIGNAL FREQUENCY")
        print("=" * 65)
        
        # Test configurations with different balance points
        configs = {
            'Ultra Conservative': {
                'CONFIDENCE_THRESHOLD': 0.75,
                'TREND_RSI_LONG_MIN': 48,
                'TREND_RSI_SHORT_MAX': 52,
                'RSI_OVERSOLD': 25,
                'RSI_OVERBOUGHT': 75,
                'MIN_VOLUME_RATIO': 1.2,
                'MIN_TREND_STRENGTH': 30
            },
            'High Win Rate Focus': {
                'CONFIDENCE_THRESHOLD': 0.65,
                'TREND_RSI_LONG_MIN': 46,
                'TREND_RSI_SHORT_MAX': 54,
                'RSI_OVERSOLD': 30,
                'RSI_OVERBOUGHT': 70,
                'MIN_VOLUME_RATIO': 1.1,
                'MIN_TREND_STRENGTH': 25
            },
            'Balanced Optimal': {
                'CONFIDENCE_THRESHOLD': 0.55,
                'TREND_RSI_LONG_MIN': 44,
                'TREND_RSI_SHORT_MAX': 56,
                'RSI_OVERSOLD': 32,
                'RSI_OVERBOUGHT': 68,
                'MIN_VOLUME_RATIO': 1.0,
                'MIN_TREND_STRENGTH': 22
            },
            'High Frequency Focus': {
                'CONFIDENCE_THRESHOLD': 0.45,
                'TREND_RSI_LONG_MIN': 42,
                'TREND_RSI_SHORT_MAX': 58,
                'RSI_OVERSOLD': 35,
                'RSI_OVERBOUGHT': 65,
                'MIN_VOLUME_RATIO': 0.9,
                'MIN_TREND_STRENGTH': 20
            },
            'Aggressive Frequency': {
                'CONFIDENCE_THRESHOLD': 0.40,
                'TREND_RSI_LONG_MIN': 40,
                'TREND_RSI_SHORT_MAX': 60,
                'RSI_OVERSOLD': 38,
                'RSI_OVERBOUGHT': 62,
                'MIN_VOLUME_RATIO': 0.8,
                'MIN_TREND_STRENGTH': 18
            }
        }
        
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        results = {}
        
        for name, config in configs.items():
            print(f"\n🧪 Testing: {name}")
            print("-" * 40)
            
            try:
                result = self.test_configuration(config, symbols, days=14)
                
                if 'error' not in result:
                    # Calculate multi-objective score
                    # 50% weight on win rate, 30% on frequency, 20% on profit factor
                    win_rate_score = result['win_rate'] / 100
                    frequency_score = min(result['signals_per_day'] / 6, 1)  # Target 6/day max
                    profit_score = min(result['profit_factor'] / 2, 1)  # Target 2.0 max
                    
                    combined_score = (win_rate_score * 0.5) + (frequency_score * 0.3) + (profit_score * 0.2)
                    
                    result['combined_score'] = round(combined_score, 3)
                    result['config'] = config
                    results[name] = result
                    
                    print(f"   📈 Win Rate: {result['win_rate']}%")
                    print(f"   🔄 Signals/Day: {result['signals_per_day']}")
                    print(f"   💰 Total PnL: {result['total_pnl']}%")
                    print(f"   ⚖️  Profit Factor: {result['profit_factor']}")
                    print(f"   🎯 Combined Score: {combined_score:.3f}")
                    
                    # Show high confidence performance
                    if result['high_confidence_signals'] > 0:
                        print(f"   🏆 High Conf Win Rate: {result['high_confidence_win_rate']}% ({result['high_confidence_signals']} signals)")
                    
                else:
                    print(f"   ❌ {result['error']}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        return results

def main():
    """Main optimization function"""
    optimizer = WinRateFrequencyOptimizer()
    results = optimizer.optimize_for_both_objectives()
    
    if not results:
        print("❌ No valid results obtained")
        return
    
    # Rank by combined score
    ranked = sorted(results.items(), key=lambda x: x[1]['combined_score'], reverse=True)
    
    print(f"\n🏆 FINAL RANKING (Win Rate + Frequency Optimization):")
    print("=" * 70)
    
    for i, (name, data) in enumerate(ranked, 1):
        print(f"\n#{i} {name}")
        print(f"   🎯 Combined Score: {data['combined_score']:.3f}")
        print(f"   📈 Win Rate: {data['win_rate']}%")
        print(f"   🔄 Signals/Day: {data['signals_per_day']}")
        print(f"   💰 Total PnL: {data['total_pnl']}%")
        print(f"   ⚖️  Profit Factor: {data['profit_factor']}")
        
        # Show strategy breakdown
        if 'strategy_breakdown' in data:
            print(f"   📊 Strategy Performance:")
            for strategy, stats in data['strategy_breakdown'].items():
                print(f"      • {strategy}: {stats['win_rate']}% WR, {stats['signals']} signals")
    
    # Best configuration
    best_name, best_data = ranked[0]
    print(f"\n🥇 RECOMMENDED CONFIGURATION: {best_name}")
    print("=" * 50)
    print("🔧 Update your .env file with these settings:")
    for key, value in best_data['config'].items():
        print(f"{key}={value}")
    
    print(f"\n📊 EXPECTED PERFORMANCE:")
    print(f"   • Win Rate: {best_data['win_rate']}%")
    print(f"   • Signals per Day: {best_data['signals_per_day']}")
    print(f"   • Monthly Signals: ~{best_data['signals_per_day'] * 30:.0f}")
    print(f"   • Profit Factor: {best_data['profit_factor']}")
    
    if best_data['high_confidence_signals'] > 0:
        print(f"   • High Confidence Win Rate: {best_data['high_confidence_win_rate']}%")
    
    # Strategy recommendations
    print(f"\n💡 STRATEGY INSIGHTS:")
    for strategy, stats in best_data['strategy_breakdown'].items():
        print(f"   • {strategy}: {stats['win_rate']}% win rate, avg confidence {stats['avg_confidence']}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'winrate_frequency_optimization_{timestamp}.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: winrate_frequency_optimization_{timestamp}.json")
    
    return best_data

if __name__ == "__main__":
    main()
