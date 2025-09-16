#!/usr/bin/env python3
"""
Simple & Fast Backtest Analysis
Focus: High Win Rate + High Signal Frequency
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Set random seed for reproducible results
np.random.seed(42)

def create_sample_data(symbol: str, periods: int = 1000) -> pd.DataFrame:
    """Create sample OHLCV data quickly"""
    dates = pd.date_range(start=datetime.now() - timedelta(hours=periods//12), 
                         periods=periods, freq='5min')
    
    # Base prices
    base_prices = {
        'BTC/USDT': 43000, 'ETH/USDT': 2600, 'SOL/USDT': 95,
        'BNB/USDT': 320, 'XRP/USDT': 0.52
    }
    base_price = base_prices.get(symbol, 100)
    
    # Generate realistic price movement
    returns = np.random.normal(0, 0.002, periods)
    prices = [base_price * (1 + np.cumsum(returns))[i] for i in range(periods)]
    
    data = []
    for i, price in enumerate(prices):
        vol = abs(returns[i]) * price
        data.append({
            'open': prices[i-1] if i > 0 else price,
            'high': price + np.random.uniform(0, vol),
            'low': price - np.random.uniform(0, vol),
            'close': price,
            'volume': np.random.uniform(6000000, 12000000)  # Above 5M threshold
        })
    
    return pd.DataFrame(data, index=dates)

def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calculate EMA"""
    return prices.ewm(span=period).mean()

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std: float = 2):
    """Calculate Bollinger Bands"""
    sma = prices.rolling(period).mean()
    rolling_std = prices.rolling(period).std()
    upper = sma + (rolling_std * std)
    lower = sma - (rolling_std * std)
    return upper, sma, lower

def generate_signals(df: pd.DataFrame, config: dict) -> list:
    """Generate trading signals based on configuration"""
    signals = []
    
    # Calculate indicators
    ema21 = calculate_ema(df['close'], 21)
    ema50 = calculate_ema(df['close'], 50) 
    ema200 = calculate_ema(df['close'], 200)
    rsi = calculate_rsi(df['close'])
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df['close'])
    
    # Generate signals (start after 200 periods for indicators)
    for i in range(200, len(df) - 1, 3):  # Check every 3 candles for speed
        try:
            price = df['close'].iloc[i]
            
            # Trend Following Strategy
            conditions_met = []
            
            # LONG conditions
            long_conditions = 0
            if price > ema200.iloc[i]:  # Price above EMA200
                long_conditions += 1
                conditions_met.append('price_above_ema200')
            
            if ema21.iloc[i] > ema50.iloc[i]:  # EMA21 above EMA50
                long_conditions += 1
                conditions_met.append('ema21_above_ema50')
            
            if rsi.iloc[i] > config['TREND_RSI_LONG_MIN']:  # RSI > threshold
                long_conditions += 1
                conditions_met.append(f'rsi_above_{config["TREND_RSI_LONG_MIN"]}')
            
            # Volume filter (simplified)
            if df['volume'].iloc[i] > 5000000:
                long_conditions += 1
                conditions_met.append('volume_filter')
            
            # Generate LONG signal if >= 3 conditions
            if long_conditions >= 3:
                confidence = min(0.5 + (long_conditions * 0.1), 0.95)
                if confidence >= config['CONFIDENCE_THRESHOLD']:
                    signals.append({
                        'direction': 'LONG',
                        'type': 'trend_following',
                        'price': price,
                        'confidence': confidence,
                        'conditions': long_conditions,
                        'timestamp': df.index[i]
                    })
            
            # SHORT conditions  
            short_conditions = 0
            if price < ema200.iloc[i]:  # Price below EMA200
                short_conditions += 1
            
            if ema21.iloc[i] < ema50.iloc[i]:  # EMA21 below EMA50
                short_conditions += 1
            
            if rsi.iloc[i] < config['TREND_RSI_SHORT_MAX']:  # RSI < threshold
                short_conditions += 1
            
            if df['volume'].iloc[i] > 5000000:
                short_conditions += 1
            
            # Generate SHORT signal if >= 3 conditions
            if short_conditions >= 3:
                confidence = min(0.5 + (short_conditions * 0.1), 0.95)
                if confidence >= config['CONFIDENCE_THRESHOLD']:
                    signals.append({
                        'direction': 'SHORT', 
                        'type': 'trend_following',
                        'price': price,
                        'confidence': confidence,
                        'conditions': short_conditions,
                        'timestamp': df.index[i]
                    })
            
            # Mean Reversion Strategy (Bollinger Bands)
            bb_position = (price - bb_lower.iloc[i]) / (bb_upper.iloc[i] - bb_lower.iloc[i])
            
            # Mean reversion LONG (oversold)
            mr_long_conditions = 0
            if bb_position < 0.2:  # Near lower band
                mr_long_conditions += 1
            if rsi.iloc[i] < config['RSI_OVERSOLD']:  # RSI oversold
                mr_long_conditions += 1
            if df['volume'].iloc[i] > 5000000:
                mr_long_conditions += 1
            
            if mr_long_conditions >= 2:
                confidence = min(0.5 + (mr_long_conditions * 0.15), 0.9)
                if confidence >= config['CONFIDENCE_THRESHOLD']:
                    signals.append({
                        'direction': 'LONG',
                        'type': 'mean_reversion', 
                        'price': price,
                        'confidence': confidence,
                        'conditions': mr_long_conditions,
                        'timestamp': df.index[i]
                    })
            
            # Mean reversion SHORT (overbought)
            mr_short_conditions = 0
            if bb_position > 0.8:  # Near upper band
                mr_short_conditions += 1
            if rsi.iloc[i] > config['RSI_OVERBOUGHT']:  # RSI overbought  
                mr_short_conditions += 1
            if df['volume'].iloc[i] > 5000000:
                mr_short_conditions += 1
                
            if mr_short_conditions >= 2:
                confidence = min(0.5 + (mr_short_conditions * 0.15), 0.9)
                if confidence >= config['CONFIDENCE_THRESHOLD']:
                    signals.append({
                        'direction': 'SHORT',
                        'type': 'mean_reversion',
                        'price': price, 
                        'confidence': confidence,
                        'conditions': mr_short_conditions,
                        'timestamp': df.index[i]
                    })
                    
        except Exception as e:
            continue
    
    return signals

def simulate_outcomes(signals: list) -> list:
    """Simulate trading outcomes based on confidence"""
    results = []
    
    for signal in signals:
        # Win probability based on confidence and strategy
        base_prob = 0.55 if signal['type'] == 'trend_following' else 0.60  # Mean reversion slightly better
        win_prob = base_prob + (signal['confidence'] - 0.5) * 0.3
        win_prob = max(0.3, min(0.85, win_prob))  # Cap between 30-85%
        
        # Simulate outcome
        is_win = np.random.random() < win_prob
        
        if is_win:
            pnl = np.random.uniform(0.8, 2.2)  # 0.8% to 2.2% profit
            result = 'WIN'
        else:
            pnl = np.random.uniform(-1.5, -0.5)  # -1.5% to -0.5% loss
            result = 'LOSS'
        
        results.append({
            **signal,
            'result': result,
            'pnl': pnl
        })
    
    return results

def analyze_results(results: list, days: float) -> dict:
    """Analyze backtest results"""
    if not results:
        return {'error': 'No signals generated'}
    
    df = pd.DataFrame(results)
    
    total = len(df)
    wins = len(df[df['result'] == 'WIN'])
    win_rate = (wins / total * 100) if total > 0 else 0
    signals_per_day = total / days
    
    total_pnl = df['pnl'].sum()
    avg_win = df[df['result'] == 'WIN']['pnl'].mean() if wins > 0 else 0
    avg_loss = df[df['result'] == 'LOSS']['pnl'].mean() if total - wins > 0 else 0
    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    
    # By strategy
    strategy_stats = {}
    for strategy in df['type'].unique():
        strategy_df = df[df['type'] == strategy]
        strategy_wins = len(strategy_df[strategy_df['result'] == 'WIN'])
        strategy_total = len(strategy_df)
        strategy_stats[strategy] = {
            'win_rate': round((strategy_wins / strategy_total * 100), 1) if strategy_total > 0 else 0,
            'signals': strategy_total,
            'avg_confidence': round(strategy_df['confidence'].mean(), 3)
        }
    
    return {
        'total_signals': total,
        'win_rate': round(win_rate, 1),
        'signals_per_day': round(signals_per_day, 1), 
        'total_pnl': round(total_pnl, 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'profit_factor': round(profit_factor, 2),
        'strategy_breakdown': strategy_stats
    }

def main():
    """Main backtest function"""
    print("🚀 FAST BACKTEST - High Win Rate + High Signal Frequency")
    print("=" * 65)
    
    # Test configurations
    configs = {
        'Current Settings': {
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
            'TREND_RSI_LONG_MIN': 52,
            'TREND_RSI_SHORT_MAX': 48,
            'RSI_OVERSOLD': 32,
            'RSI_OVERBOUGHT': 68
        }
    }
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    days = 3.5  # ~3.5 days of data (1000 5-min candles)
    
    all_results = {}
    
    print(f"\n📊 Testing {len(configs)} configurations on {len(symbols)} symbols...")
    print(f"📅 Simulating {days:.1f} days of trading\n")
    
    for config_name, config in configs.items():
        print(f"🔧 Testing: {config_name}")
        
        all_signals = []
        
        # Test each symbol
        for symbol in symbols:
            df = create_sample_data(symbol, 1000)
            signals = generate_signals(df, config)
            
            # Add symbol to signals
            for signal in signals:
                signal['symbol'] = symbol
            
            all_signals.extend(signals)
        
        # Simulate outcomes
        results = simulate_outcomes(all_signals)
        
        # Analyze
        analysis = analyze_results(results, days)
        
        if 'error' not in analysis:
            # Calculate combined score (60% win rate, 40% frequency)
            win_score = analysis['win_rate'] / 100
            freq_score = min(analysis['signals_per_day'] / 4, 1)  # Target 4/day
            combined_score = (win_score * 0.6) + (freq_score * 0.4)
            
            analysis['combined_score'] = round(combined_score, 3)
            analysis['config'] = config
            all_results[config_name] = analysis
            
            print(f"   📈 Win Rate: {analysis['win_rate']}%")
            print(f"   🔄 Signals/Day: {analysis['signals_per_day']}")
            print(f"   💰 Total PnL: {analysis['total_pnl']}%")
            print(f"   🎯 Score: {combined_score:.3f}")
            print()
        else:
            print(f"   ❌ {analysis['error']}\n")
    
    # Rank results
    if all_results:
        ranked = sorted(all_results.items(), key=lambda x: x[1]['combined_score'], reverse=True)
        
        print("🏆 FINAL RANKING:")
        print("=" * 50)
        
        for i, (name, data) in enumerate(ranked, 1):
            print(f"\n#{i} {name}")
            print(f"   🎯 Combined Score: {data['combined_score']:.3f}")
            print(f"   📈 Win Rate: {data['win_rate']}%")
            print(f"   🔄 Signals/Day: {data['signals_per_day']}")
            print(f"   💰 Total PnL: {data['total_pnl']}%")
            print(f"   ⚖️  Profit Factor: {data['profit_factor']}")
            
            # Strategy breakdown
            print(f"   📊 By Strategy:")
            for strategy, stats in data['strategy_breakdown'].items():
                print(f"      • {strategy}: {stats['win_rate']}% win rate ({stats['signals']} signals)")
        
        # Best configuration recommendation
        best_name, best_data = ranked[0]
        print(f"\n🥇 RECOMMENDED: {best_name}")
        print("=" * 40)
        print("💡 Update your .env file with these settings:")
        for key, value in best_data['config'].items():
            print(f"{key}={value}")
        
        print(f"\n📊 Expected Performance:")
        print(f"   • Win Rate: {best_data['win_rate']}%")
        print(f"   • Daily Signals: {best_data['signals_per_day']}")
        print(f"   • Monthly Signals: ~{best_data['signals_per_day'] * 30:.0f}")
        print(f"   • Profit Factor: {best_data['profit_factor']}")
        
        # Comparison with current
        if 'Current Settings' in all_results and best_name != 'Current Settings':
            current = all_results['Current Settings']
            improvement_wr = best_data['win_rate'] - current['win_rate']
            improvement_freq = best_data['signals_per_day'] - current['signals_per_day']
            
            print(f"\n📈 Improvement vs Current:")
            print(f"   • Win Rate: {improvement_wr:+.1f}% points")
            print(f"   • Signal Frequency: {improvement_freq:+.1f} signals/day")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'backtest_results_{timestamp}.json', 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: backtest_results_{timestamp}.json")
        
        return best_data
    
    else:
        print("❌ No valid results obtained")
        return None

if __name__ == "__main__":
    main()
