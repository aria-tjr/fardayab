#!/usr/bin/env python3
"""
Comprehensive Backtesting and Optimization
Focus: High Win Rate + High Signal Frequency
"""

import asyncio
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
import ccxt

# Import our signal generator
from src.strategies.signal_generator import SignalGenerator
from src.strategies.indicators import TechnicalIndicators
from src.exchange.data_fetcher import ExchangeDataFetcher
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktestEngine:
    """Backtesting engine for signal strategies"""
    
    def __init__(self):
        self.signal_generator = SignalGenerator()
        self.indicators = TechnicalIndicators()
        self.results = []
        
    def generate_sample_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Generate realistic sample OHLCV data for backtesting"""
        periods = days * 24 * 12  # 5-minute intervals
        dates = pd.date_range(start=datetime.now() - timedelta(days=days), 
                             periods=periods, freq='5min')
        
        # Start with base price
        base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 100
        
        # Generate realistic price movement with volatility
        returns = np.random.normal(0, 0.002, periods)  # 0.2% std deviation
        prices = [base_price]
        
        for i in range(1, periods):
            # Add some trend and mean reversion
            trend = 0.0001 if i % 1000 < 500 else -0.0001
            mean_reversion = -0.1 * (prices[-1] / base_price - 1)
            
            price_change = returns[i] + trend + mean_reversion * 0.01
            new_price = prices[-1] * (1 + price_change)
            prices.append(max(new_price, base_price * 0.5))  # Floor price
        
        # Generate OHLC from price series
        ohlc_data = []
        for i in range(len(prices)):
            price = prices[i]
            volatility = abs(returns[i]) * price
            
            high = price + np.random.uniform(0, volatility)
            low = price - np.random.uniform(0, volatility)
            open_price = prices[i-1] if i > 0 else price
            close_price = price
            
            # Ensure OHLC logic
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            volume = np.random.uniform(1000000, 10000000)  # 1M-10M volume
            
            ohlc_data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
        
        df = pd.DataFrame(ohlc_data, index=dates)
        return df
    
    def simulate_trade_outcome(self, signal: Dict, df: pd.DataFrame, 
                              start_idx: int) -> Dict:
        """Simulate trade outcome based on subsequent price action"""
        try:
            entry_price = signal['entry_price']
            stop_loss = signal['stop_loss']
            take_profit = signal['take_profit']
            direction = signal['direction']
            
            # Look ahead 24 hours (288 5-minute candles)
            end_idx = min(start_idx + 288, len(df) - 1)
            future_data = df.iloc[start_idx:end_idx]
            
            if len(future_data) < 10:
                return {'result': 'NO_DATA', 'pnl': 0, 'duration': 0}
            
            for i, (timestamp, row) in enumerate(future_data.iterrows()):
                high_price = row['high']
                low_price = row['low']
                
                if direction == 'LONG':
                    # Check stop loss first
                    if low_price <= stop_loss:
                        pnl = (stop_loss - entry_price) / entry_price * 100
                        return {'result': 'LOSS', 'pnl': pnl, 'duration': i * 5}
                    
                    # Check take profit
                    if high_price >= take_profit:
                        pnl = (take_profit - entry_price) / entry_price * 100
                        return {'result': 'WIN', 'pnl': pnl, 'duration': i * 5}
                
                else:  # SHORT
                    # Check stop loss first
                    if high_price >= stop_loss:
                        pnl = (entry_price - stop_loss) / entry_price * 100
                        return {'result': 'LOSS', 'pnl': pnl, 'duration': i * 5}
                    
                    # Check take profit
                    if low_price <= take_profit:
                        pnl = (entry_price - take_profit) / entry_price * 100
                        return {'result': 'WIN', 'pnl': pnl, 'duration': i * 5}
            
            # If no SL/TP hit, close at end with small profit/loss
            final_price = future_data.iloc[-1]['close']
            if direction == 'LONG':
                pnl = (final_price - entry_price) / entry_price * 100
            else:
                pnl = (entry_price - final_price) / entry_price * 100
            
            result = 'WIN' if pnl > 0 else 'LOSS'
            return {'result': result, 'pnl': pnl, 'duration': len(future_data) * 5}
            
        except Exception as e:
            logger.error(f"Error simulating trade: {e}")
            return {'result': 'ERROR', 'pnl': 0, 'duration': 0}
    
    def backtest_symbol(self, symbol: str, df: pd.DataFrame, 
                       config_override: Dict = None) -> List[Dict]:
        """Backtest a single symbol"""
        logger.info(f"Backtesting {symbol}...")
        
        # Override config for testing
        if config_override:
            for key, value in config_override.items():
                setattr(Config, key, value)
        
        signals = []
        
        # Need at least 200 candles for indicators
        start_idx = 200
        
        # Generate signals every 5 minutes (but skip some to avoid overtrading)
        for i in range(start_idx, len(df) - 300, 5):  # Check every 5 candles
            try:
                # Get data up to current point
                current_data = df.iloc[:i+1]
                
                # Generate signal
                signal = self.signal_generator.generate_signal(symbol, current_data)
                
                if signal:
                    # Simulate trade outcome
                    outcome = self.simulate_trade_outcome(signal, df, i)
                    
                    signal_result = {
                        'symbol': symbol,
                        'timestamp': df.index[i],
                        'direction': signal['direction'],
                        'type': signal['type'],
                        'confidence': signal['confidence'],
                        'entry_price': signal['entry_price'],
                        'stop_loss': signal['stop_loss'],
                        'take_profit': signal['take_profit'],
                        'conditions_met': len(signal.get('conditions_met', [])),
                        **outcome
                    }
                    
                    signals.append(signal_result)
                    logger.info(f"{symbol}: {signal['direction']} signal - {outcome['result']} ({outcome['pnl']:.2f}%)")
                
            except Exception as e:
                logger.error(f"Error processing signal at index {i}: {e}")
                continue
        
        return signals
    
    def run_comprehensive_backtest(self, symbols: List[str] = None, 
                                  days: int = 30) -> Dict:
        """Run comprehensive backtest on multiple symbols"""
        if symbols is None:
            symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
        
        all_results = []
        
        for symbol in symbols:
            # Generate sample data
            df = self.generate_sample_data(symbol, days)
            
            # Run backtest
            symbol_results = self.backtest_symbol(symbol, df)
            all_results.extend(symbol_results)
        
        return self.analyze_results(all_results)
    
    def analyze_results(self, results: List[Dict]) -> Dict:
        """Analyze backtest results"""
        if not results:
            return {'error': 'No results to analyze'}
        
        df = pd.DataFrame(results)
        
        # Basic statistics
        total_signals = len(df)
        winning_signals = len(df[df['result'] == 'WIN'])
        losing_signals = len(df[df['result'] == 'LOSS'])
        win_rate = (winning_signals / total_signals * 100) if total_signals > 0 else 0
        
        # PnL statistics
        total_pnl = df['pnl'].sum()
        avg_win = df[df['result'] == 'WIN']['pnl'].mean() if winning_signals > 0 else 0
        avg_loss = df[df['result'] == 'LOSS']['pnl'].mean() if losing_signals > 0 else 0
        
        # Frequency analysis
        signals_per_day = total_signals / 30  # 30 days backtest
        
        # By strategy type
        strategy_stats = df.groupby('type').agg({
            'result': lambda x: (x == 'WIN').sum() / len(x) * 100,
            'pnl': ['sum', 'mean', 'count']
        }).round(2)
        
        # By symbol
        symbol_stats = df.groupby('symbol').agg({
            'result': lambda x: (x == 'WIN').sum() / len(x) * 100,
            'pnl': ['sum', 'mean', 'count']
        }).round(2)
        
        analysis = {
            'summary': {
                'total_signals': total_signals,
                'winning_signals': winning_signals,
                'losing_signals': losing_signals,
                'win_rate': round(win_rate, 2),
                'signals_per_day': round(signals_per_day, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'profit_factor': round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0
            },
            'by_strategy': strategy_stats.to_dict(),
            'by_symbol': symbol_stats.to_dict(),
            'detailed_results': results[-20:]  # Last 20 signals for review
        }
        
        return analysis

class ConfigOptimizer:
    """Optimize configuration for high win rate and signal frequency"""
    
    def __init__(self):
        self.backtest_engine = BacktestEngine()
        self.best_configs = []
    
    def test_configuration(self, config: Dict, symbols: List[str]) -> Dict:
        """Test a specific configuration"""
        logger.info(f"Testing config: {config}")
        
        results = []
        for symbol in symbols:
            df = self.backtest_engine.generate_sample_data(symbol, 15)  # Shorter for optimization
            symbol_results = self.backtest_engine.backtest_symbol(symbol, df, config)
            results.extend(symbol_results)
        
        return self.backtest_engine.analyze_results(results)
    
    def optimize_for_win_rate_and_frequency(self) -> List[Dict]:
        """Optimize configurations for both win rate and signal frequency"""
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        
        # Configuration space to test
        test_configs = [
            # Balanced approach
            {
                'CONFIDENCE_THRESHOLD': 0.60,
                'TREND_RSI_LONG_MIN': 50,
                'TREND_RSI_SHORT_MAX': 50,
                'RSI_OVERSOLD': 35,
                'RSI_OVERBOUGHT': 65
            },
            # High frequency
            {
                'CONFIDENCE_THRESHOLD': 0.55,
                'TREND_RSI_LONG_MIN': 48,
                'TREND_RSI_SHORT_MAX': 52,
                'RSI_OVERSOLD': 40,
                'RSI_OVERBOUGHT': 60
            },
            # High win rate
            {
                'CONFIDENCE_THRESHOLD': 0.75,
                'TREND_RSI_LONG_MIN': 55,
                'TREND_RSI_SHORT_MAX': 45,
                'RSI_OVERSOLD': 25,
                'RSI_OVERBOUGHT': 75
            },
            # Aggressive frequency
            {
                'CONFIDENCE_THRESHOLD': 0.50,
                'TREND_RSI_LONG_MIN': 45,
                'TREND_RSI_SHORT_MAX': 55,
                'RSI_OVERSOLD': 45,
                'RSI_OVERBOUGHT': 55
            },
            # Conservative high win rate
            {
                'CONFIDENCE_THRESHOLD': 0.80,
                'TREND_RSI_LONG_MIN': 58,
                'TREND_RSI_SHORT_MAX': 42,
                'RSI_OVERSOLD': 20,
                'RSI_OVERBOUGHT': 80
            }
        ]
        
        results = []
        
        for i, config in enumerate(test_configs):
            logger.info(f"Testing configuration {i+1}/{len(test_configs)}")
            
            try:
                analysis = self.test_configuration(config, symbols)
                
                if 'summary' in analysis:
                    summary = analysis['summary']
                    
                    # Score based on win rate and signal frequency
                    win_rate_score = summary['win_rate'] / 100  # 0-1
                    frequency_score = min(summary['signals_per_day'] / 5, 1)  # Target 5 per day, max 1
                    
                    # Combined score (60% win rate, 40% frequency)
                    combined_score = (win_rate_score * 0.6) + (frequency_score * 0.4)
                    
                    result = {
                        'config': config,
                        'win_rate': summary['win_rate'],
                        'signals_per_day': summary['signals_per_day'],
                        'total_signals': summary['total_signals'],
                        'total_pnl': summary['total_pnl'],
                        'combined_score': combined_score,
                        'analysis': analysis
                    }
                    
                    results.append(result)
                    logger.info(f"Config {i+1}: Win Rate: {summary['win_rate']:.1f}%, "
                               f"Signals/Day: {summary['signals_per_day']:.1f}, "
                               f"Score: {combined_score:.3f}")
                
            except Exception as e:
                logger.error(f"Error testing config {i+1}: {e}")
                continue
        
        # Sort by combined score
        results.sort(key=lambda x: x['combined_score'], reverse=True)
        return results

async def main():
    """Main backtesting function"""
    print("🚀 Starting Comprehensive Backtest for High Win Rate + High Signal Frequency")
    print("=" * 80)
    
    # 1. Run basic backtest
    print("\n📊 Phase 1: Basic Backtest (30 days)")
    backtest_engine = BacktestEngine()
    
    symbols = Config.TRADING_PAIRS[:5]  # Top 5 symbols
    basic_results = backtest_engine.run_comprehensive_backtest(symbols, days=30)
    
    print("\n📈 BASIC BACKTEST RESULTS:")
    print("-" * 40)
    summary = basic_results['summary']
    print(f"Total Signals: {summary['total_signals']}")
    print(f"Win Rate: {summary['win_rate']:.2f}%")
    print(f"Signals per Day: {summary['signals_per_day']:.2f}")
    print(f"Total PnL: {summary['total_pnl']:.2f}%")
    print(f"Average Win: {summary['avg_win']:.2f}%")
    print(f"Average Loss: {summary['avg_loss']:.2f}%")
    print(f"Profit Factor: {summary['profit_factor']:.2f}")
    
    # 2. Optimization phase
    print("\n🔧 Phase 2: Configuration Optimization")
    optimizer = ConfigOptimizer()
    optimized_configs = optimizer.optimize_for_win_rate_and_frequency()
    
    print("\n🏆 TOP 3 OPTIMIZED CONFIGURATIONS:")
    print("=" * 60)
    
    for i, result in enumerate(optimized_configs[:3], 1):
        print(f"\n#{i} Configuration (Score: {result['combined_score']:.3f})")
        print("-" * 30)
        print(f"Win Rate: {result['win_rate']:.2f}%")
        print(f"Signals per Day: {result['signals_per_day']:.2f}")
        print(f"Total Signals: {result['total_signals']}")
        print(f"Total PnL: {result['total_pnl']:.2f}%")
        print("\nConfiguration:")
        for key, value in result['config'].items():
            print(f"  {key}: {value}")
    
    # 3. Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed results
    with open(f'backtest_results_{timestamp}.json', 'w') as f:
        json.dump({
            'basic_backtest': basic_results,
            'optimized_configs': optimized_configs,
            'timestamp': timestamp
        }, f, indent=2, default=str)
    
    # Generate report
    report = f"""
# 📊 BACKTEST RESULTS REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 🎯 OBJECTIVE
Optimize for HIGH WIN RATE + HIGH SIGNAL FREQUENCY

## 📈 CURRENT PERFORMANCE (30-day backtest)
- **Total Signals**: {summary['total_signals']}
- **Win Rate**: {summary['win_rate']:.2f}%
- **Signals per Day**: {summary['signals_per_day']:.2f}
- **Total PnL**: {summary['total_pnl']:.2f}%
- **Profit Factor**: {summary['profit_factor']:.2f}

## 🏆 BEST OPTIMIZED CONFIGURATION
**Score**: {optimized_configs[0]['combined_score']:.3f}
**Win Rate**: {optimized_configs[0]['win_rate']:.2f}%
**Signals per Day**: {optimized_configs[0]['signals_per_day']:.2f}

### Recommended Settings:
```env
"""
    
    if optimized_configs:
        best_config = optimized_configs[0]['config']
        for key, value in best_config.items():
            report += f"{key}={value}\n"
    
    report += f"""```

## 📊 STRATEGY PERFORMANCE
### By Strategy Type:
"""
    
    if 'by_strategy' in basic_results:
        for strategy, stats in basic_results['by_strategy'].items():
            report += f"- **{strategy}**: {stats}\n"
    
    report += f"""
### By Symbol:
"""
    
    if 'by_symbol' in basic_results:
        for symbol, stats in basic_results['by_symbol'].items():
            report += f"- **{symbol}**: {stats}\n"
    
    report += f"""
## 🎯 RECOMMENDATIONS

1. **For Maximum Win Rate**: Use configuration #{3 if len(optimized_configs) >= 3 else 1}
2. **For Maximum Signal Frequency**: Use configuration #{2 if len(optimized_configs) >= 2 else 1}
3. **For Balanced Approach**: Use configuration #1

## ⚙️ IMPLEMENTATION
Update your `.env` file with the recommended settings above and restart the bot.

---
*Generated by Backtest Optimizer*
"""
    
    with open(f'BACKTEST_REPORT_{timestamp}.md', 'w') as f:
        f.write(report)
    
    print(f"\n💾 Results saved to:")
    print(f"   - backtest_results_{timestamp}.json")
    print(f"   - BACKTEST_REPORT_{timestamp}.md")
    
    print(f"\n🎯 RECOMMENDATION:")
    if optimized_configs:
        best = optimized_configs[0]
        print(f"Use the #{1} configuration for optimal balance:")
        print(f"Win Rate: {best['win_rate']:.2f}% | Signals/Day: {best['signals_per_day']:.2f}")
        print("\nUpdate your .env file with these settings:")
        for key, value in best['config'].items():
            print(f"{key}={value}")
    
    print(f"\n✅ Backtest completed successfully!")
    return optimized_configs[0] if optimized_configs else None

if __name__ == "__main__":
    asyncio.run(main())
