#!/usr/bin/env python3
"""
Rigorous Backtest Validation
Ensure results are realistic and accurate
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
from src.strategies.signal_generator import SignalGenerator
from src.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RigorousBacktest:
    """More realistic backtesting with proper validation"""
    
    def __init__(self):
        self.signal_generator = SignalGenerator()
        
    def create_realistic_data(self, symbol: str, days: int = 7) -> pd.DataFrame:
        """Create more realistic market data with proper OHLCV relationships"""
        periods = days * 24 * 12  # 5-minute intervals
        dates = pd.date_range(start=datetime.now() - timedelta(days=days), 
                             periods=periods, freq='5min')
        
        # Base prices for different symbols
        base_prices = {
            'BTC/USDT': 43000, 'ETH/USDT': 2600, 'SOL/USDT': 95,
            'BNB/USDT': 320, 'XRP/USDT': 0.52
        }
        base_price = base_prices.get(symbol, 100)
        
        # More realistic price movement with proper volatility
        np.random.seed(hash(symbol) % 1000)  # Different seed per symbol
        
        # Generate returns with realistic characteristics
        returns = np.random.normal(0, 0.001, periods)  # Lower volatility
        
        # Add some market regimes (trending vs sideways)
        for i in range(0, periods, 200):
            regime = np.random.choice(['trend_up', 'trend_down', 'sideways'], p=[0.3, 0.3, 0.4])
            end_idx = min(i + 200, periods)
            
            if regime == 'trend_up':
                returns[i:end_idx] += np.linspace(0, 0.0005, end_idx - i)
            elif regime == 'trend_down':
                returns[i:end_idx] += np.linspace(0, -0.0005, end_idx - i)
            # sideways: no additional trend
        
        # Generate price series
        prices = [base_price]
        for i in range(1, periods):
            # Mean reversion component
            mean_reversion = -0.02 * (prices[-1] / base_price - 1)
            total_return = returns[i] + mean_reversion
            
            new_price = prices[-1] * (1 + total_return)
            new_price = max(new_price, base_price * 0.8)  # Price floor
            prices.append(new_price)
        
        # Create proper OHLCV data
        data = []
        for i, close_price in enumerate(prices):
            # Previous close becomes current open
            open_price = prices[i-1] if i > 0 else close_price
            
            # Intraday volatility
            volatility = abs(returns[i]) * close_price * 3
            
            # Generate high and low with realistic constraints
            if close_price >= open_price:  # Green candle
                high = max(open_price, close_price) + np.random.uniform(0, volatility * 0.5)
                low = min(open_price, close_price) - np.random.uniform(0, volatility * 0.3)
            else:  # Red candle
                high = max(open_price, close_price) + np.random.uniform(0, volatility * 0.3)
                low = min(open_price, close_price) - np.random.uniform(0, volatility * 0.5)
            
            # Ensure OHLC logic
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            # Volume correlated with volatility and price movement
            base_volume = 7000000  # Above 5M threshold
            volume_mult = 1 + abs(returns[i]) * 50  # Higher volume on big moves
            volume = base_volume * volume_mult * np.random.uniform(0.8, 1.2)
            
            data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
        
        return pd.DataFrame(data, index=dates)
    
    def realistic_trade_simulation(self, signal: dict, future_data: pd.DataFrame) -> dict:
        """More realistic trade outcome simulation"""
        try:
            entry_price = signal['entry_price']
            direction = signal['direction']
            confidence = signal['confidence']
            
            # Calculate realistic SL/TP based on ATR
            atr_period = 14
            if len(future_data) >= atr_period:
                # Calculate ATR
                high_low = future_data['high'] - future_data['low']
                high_close = np.abs(future_data['high'] - future_data['close'].shift())
                low_close = np.abs(future_data['low'] - future_data['close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = ranges.max(axis=1)
                atr = true_range.rolling(atr_period).mean().iloc[-1]
                
                # Set realistic SL/TP
                if direction == 'LONG':
                    stop_loss = entry_price - (atr * 1.5)
                    take_profit = entry_price + (atr * 2.0)
                else:
                    stop_loss = entry_price + (atr * 1.5)
                    take_profit = entry_price - (atr * 2.0)
            else:
                # Fallback to percentage-based
                if direction == 'LONG':
                    stop_loss = entry_price * 0.985  # 1.5% stop loss
                    take_profit = entry_price * 1.02   # 2% take profit
                else:
                    stop_loss = entry_price * 1.015   # 1.5% stop loss
                    take_profit = entry_price * 0.98   # 2% take profit
            
            # Simulate trade execution over next 24-48 hours
            max_periods = min(len(future_data), 576)  # Max 48 hours (576 5-min periods)
            
            for i in range(1, max_periods):
                current_high = future_data['high'].iloc[i]
                current_low = future_data['low'].iloc[i]
                
                if direction == 'LONG':
                    # Check stop loss first (more likely to hit)
                    if current_low <= stop_loss:
                        pnl_pct = (stop_loss - entry_price) / entry_price * 100
                        return {
                            'result': 'LOSS',
                            'pnl': pnl_pct,
                            'exit_price': stop_loss,
                            'duration_minutes': i * 5,
                            'exit_reason': 'stop_loss'
                        }
                    
                    # Check take profit
                    if current_high >= take_profit:
                        pnl_pct = (take_profit - entry_price) / entry_price * 100
                        return {
                            'result': 'WIN',
                            'pnl': pnl_pct,
                            'exit_price': take_profit,
                            'duration_minutes': i * 5,
                            'exit_reason': 'take_profit'
                        }
                
                else:  # SHORT
                    # Check stop loss first
                    if current_high >= stop_loss:
                        pnl_pct = (entry_price - stop_loss) / entry_price * 100
                        return {
                            'result': 'LOSS',
                            'pnl': pnl_pct,
                            'exit_price': stop_loss,
                            'duration_minutes': i * 5,
                            'exit_reason': 'stop_loss'
                        }
                    
                    # Check take profit
                    if current_low <= take_profit:
                        pnl_pct = (entry_price - take_profit) / entry_price * 100
                        return {
                            'result': 'WIN',
                            'pnl': pnl_pct,
                            'exit_price': take_profit,
                            'duration_minutes': i * 5,
                            'exit_reason': 'take_profit'
                        }
            
            # If no SL/TP hit, close at market after timeout
            final_price = future_data['close'].iloc[min(288, len(future_data)-1)]  # 24 hours max
            
            if direction == 'LONG':
                pnl_pct = (final_price - entry_price) / entry_price * 100
            else:
                pnl_pct = (entry_price - final_price) / entry_price * 100
            
            result = 'WIN' if pnl_pct > 0 else 'LOSS'
            
            return {
                'result': result,
                'pnl': pnl_pct,
                'exit_price': final_price,
                'duration_minutes': min(288, len(future_data)-1) * 5,
                'exit_reason': 'timeout'
            }
            
        except Exception as e:
            logger.error(f"Error in trade simulation: {e}")
            return {
                'result': 'ERROR',
                'pnl': 0,
                'exit_price': entry_price,
                'duration_minutes': 0,
                'exit_reason': 'error'
            }
    
    def run_realistic_backtest(self, config: dict, symbols: list, days: int = 14) -> dict:
        """Run realistic backtest with proper validation"""
        logger.info(f"Running realistic backtest with config: {config}")
        
        # Override config temporarily
        original_values = {}
        for key, value in config.items():
            if hasattr(Config, key):
                original_values[key] = getattr(Config, key)
                setattr(Config, key, value)
        
        all_results = []
        
        try:
            for symbol in symbols:
                logger.info(f"Backtesting {symbol}...")
                
                # Create realistic data
                df = self.create_realistic_data(symbol, days)
                
                # Generate signals (less frequently for realism)
                signals_generated = 0
                for i in range(200, len(df) - 300, 15):  # Check every 15 candles (75 minutes)
                    try:
                        current_data = df.iloc[:i+1]
                        
                        # Generate signal using actual signal generator
                        signal = self.signal_generator.generate_signal(symbol, current_data)
                        
                        if signal and signals_generated < 50:  # Limit signals per symbol
                            signals_generated += 1
                            
                            # Get future data for simulation
                            future_data = df.iloc[i:i+600]  # Next 50 hours
                            
                            if len(future_data) > 10:
                                # Simulate realistic trade outcome
                                outcome = self.realistic_trade_simulation(signal, future_data)
                                
                                result = {
                                    'symbol': symbol,
                                    'timestamp': df.index[i],
                                    'direction': signal['direction'],
                                    'type': signal['type'],
                                    'confidence': signal['confidence'],
                                    'entry_price': signal['entry_price'],
                                    'conditions_met': len(signal.get('conditions_met', [])),
                                    **outcome
                                }
                                
                                all_results.append(result)
                                
                                logger.info(f"{symbol}: {signal['direction']} - {outcome['result']} "
                                          f"({outcome['pnl']:.2f}% in {outcome['duration_minutes']}min)")
                    
                    except Exception as e:
                        logger.error(f"Error processing signal: {e}")
                        continue
                        
        finally:
            # Restore original config
            for key, value in original_values.items():
                setattr(Config, key, value)
        
        return self.analyze_realistic_results(all_results, days)
    
    def analyze_realistic_results(self, results: list, days: int) -> dict:
        """Analyze results with realistic metrics"""
        if not results:
            return {'error': 'No results to analyze'}
        
        df = pd.DataFrame(results)
        
        # Basic statistics
        total_signals = len(df)
        wins = len(df[df['result'] == 'WIN'])
        losses = len(df[df['result'] == 'LOSS'])
        errors = len(df[df['result'] == 'ERROR'])
        
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        signals_per_day = total_signals / days
        
        # PnL statistics
        winning_trades = df[df['result'] == 'WIN']['pnl']
        losing_trades = df[df['result'] == 'LOSS']['pnl']
        
        total_pnl = df['pnl'].sum()
        avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades.mean() if len(losing_trades) > 0 else 0
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Risk metrics
        max_drawdown = self.calculate_max_drawdown(df['pnl'].tolist())
        sharpe_ratio = self.calculate_sharpe_ratio(df['pnl'].tolist())
        
        # Duration analysis
        avg_duration = df['duration_minutes'].mean()
        
        # Exit reason analysis
        exit_reasons = df['exit_reason'].value_counts().to_dict()
        
        # Strategy breakdown
        strategy_stats = {}
        for strategy in df['type'].unique():
            strategy_df = df[df['type'] == strategy]
            strategy_wins = len(strategy_df[strategy_df['result'] == 'WIN'])
            strategy_total = len(strategy_df[strategy_df['result'].isin(['WIN', 'LOSS'])])
            
            strategy_stats[strategy] = {
                'win_rate': round((strategy_wins / strategy_total * 100), 1) if strategy_total > 0 else 0,
                'signals': len(strategy_df),
                'avg_pnl': round(strategy_df['pnl'].mean(), 2),
                'total_pnl': round(strategy_df['pnl'].sum(), 2)
            }
        
        return {
            'total_signals': total_signals,
            'winning_trades': wins,
            'losing_trades': losses,
            'error_trades': errors,
            'win_rate': round(win_rate, 2),
            'signals_per_day': round(signals_per_day, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'avg_duration_minutes': round(avg_duration, 1),
            'exit_reasons': exit_reasons,
            'strategy_breakdown': strategy_stats,
            'sample_trades': results[-10:] if len(results) >= 10 else results  # Last 10 trades
        }
    
    def calculate_max_drawdown(self, pnl_series: list) -> float:
        """Calculate maximum drawdown"""
        if not pnl_series:
            return 0
        
        cumulative = np.cumsum(pnl_series)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        
        return abs(min(drawdown)) if len(drawdown) > 0 else 0
    
    def calculate_sharpe_ratio(self, pnl_series: list) -> float:
        """Calculate Sharpe ratio (simplified)"""
        if not pnl_series or len(pnl_series) < 2:
            return 0
        
        returns = np.array(pnl_series)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        return (mean_return / std_return) if std_return != 0 else 0

def main():
    """Main validation function"""
    print("🔍 RIGOROUS BACKTEST VALIDATION")
    print("=" * 60)
    print("Ensuring results are realistic and accurate...")
    
    backtest = RigorousBacktest()
    
    # Test the "optimal" configuration from previous backtest
    optimal_config = {
        'CONFIDENCE_THRESHOLD': 0.55,
        'TREND_RSI_LONG_MIN': 50,
        'TREND_RSI_SHORT_MAX': 50,
        'RSI_OVERSOLD': 35,
        'RSI_OVERBOUGHT': 65
    }
    
    # Also test current default for comparison
    current_config = {
        'CONFIDENCE_THRESHOLD': 0.65,
        'TREND_RSI_LONG_MIN': 53,
        'TREND_RSI_SHORT_MAX': 47,
        'RSI_OVERSOLD': 30,
        'RSI_OVERBOUGHT': 70
    }
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    days = 14  # 2 weeks of data
    
    configs_to_test = {
        'Optimal (Previous Result)': optimal_config,
        'Current Default': current_config
    }
    
    results = {}
    
    for config_name, config in configs_to_test.items():
        print(f"\n🧪 Testing: {config_name}")
        print("-" * 40)
        
        try:
            result = backtest.run_realistic_backtest(config, symbols, days)
            
            if 'error' not in result:
                results[config_name] = result
                
                print(f"📊 Results for {config_name}:")
                print(f"   Total Signals: {result['total_signals']}")
                print(f"   Win Rate: {result['win_rate']}%")
                print(f"   Signals/Day: {result['signals_per_day']}")
                print(f"   Total PnL: {result['total_pnl']}%")
                print(f"   Avg Win: {result['avg_win']}%")
                print(f"   Avg Loss: {result['avg_loss']}%")
                print(f"   Profit Factor: {result['profit_factor']}")
                print(f"   Max Drawdown: {result['max_drawdown']}%")
                print(f"   Sharpe Ratio: {result['sharpe_ratio']}")
                print(f"   Avg Duration: {result['avg_duration_minutes']:.1f} minutes")
                
                print(f"\n📈 Strategy Breakdown:")
                for strategy, stats in result['strategy_breakdown'].items():
                    print(f"   {strategy}: {stats['win_rate']}% WR, {stats['signals']} signals, {stats['total_pnl']}% PnL")
                
                print(f"\n🚪 Exit Reasons:")
                for reason, count in result['exit_reasons'].items():
                    print(f"   {reason}: {count}")
                
            else:
                print(f"❌ Error: {result['error']}")
                
        except Exception as e:
            print(f"❌ Failed to test {config_name}: {e}")
    
    # Compare results
    if len(results) >= 2:
        print(f"\n📊 COMPARISON:")
        print("=" * 50)
        
        config_names = list(results.keys())
        metrics = ['win_rate', 'signals_per_day', 'total_pnl', 'profit_factor', 'max_drawdown']
        
        for metric in metrics:
            print(f"\n{metric.replace('_', ' ').title()}:")
            for name in config_names:
                value = results[name][metric]
                print(f"   {name}: {value}")
    
    # Reality check
    print(f"\n🎯 REALITY CHECK:")
    print("=" * 30)
    
    for config_name, result in results.items():
        print(f"\n{config_name}:")
        
        # Check if results are realistic
        realistic_checks = []
        
        # Win rate should be reasonable (30-80%)
        if 30 <= result['win_rate'] <= 80:
            realistic_checks.append("✅ Win rate is realistic")
        else:
            realistic_checks.append(f"⚠️  Win rate seems unrealistic: {result['win_rate']}%")
        
        # Signals per day should be reasonable (0.1-20)
        if 0.1 <= result['signals_per_day'] <= 20:
            realistic_checks.append("✅ Signal frequency is realistic")
        else:
            realistic_checks.append(f"⚠️  Signal frequency seems unrealistic: {result['signals_per_day']}/day")
        
        # Profit factor should be reasonable (0.5-3.0)
        if 0.5 <= result['profit_factor'] <= 3.0:
            realistic_checks.append("✅ Profit factor is realistic")
        else:
            realistic_checks.append(f"⚠️  Profit factor seems unrealistic: {result['profit_factor']}")
        
        # Max drawdown should be reasonable (< 20%)
        if result['max_drawdown'] < 20:
            realistic_checks.append("✅ Max drawdown is acceptable")
        else:
            realistic_checks.append(f"⚠️  Max drawdown is high: {result['max_drawdown']}%")
        
        for check in realistic_checks:
            print(f"   {check}")
    
    # Save validation results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'validation_results_{timestamp}.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Validation results saved to: validation_results_{timestamp}.json")
    
    # Final verdict
    print(f"\n🏁 FINAL VERDICT:")
    print("=" * 30)
    
    if results:
        best_config = max(results.items(), key=lambda x: x[1]['win_rate'] * x[1]['profit_factor'])
        best_name, best_result = best_config
        
        print(f"🥇 Best Configuration: {best_name}")
        print(f"   Win Rate: {best_result['win_rate']}%")
        print(f"   Signals/Day: {best_result['signals_per_day']}")
        print(f"   Profit Factor: {best_result['profit_factor']}")
        
        if (30 <= best_result['win_rate'] <= 75 and 
            0.5 <= best_result['signals_per_day'] <= 10 and
            1.0 <= best_result['profit_factor'] <= 2.5):
            print("✅ RESULTS ARE REALISTIC AND TRUSTWORTHY")
        else:
            print("⚠️  RESULTS NEED FURTHER VALIDATION")
    
    return results

if __name__ == "__main__":
    main()
