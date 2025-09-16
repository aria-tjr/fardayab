"""
Comprehensive backtesting system for crypto signal bot
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import json

from ..exchange.data_fetcher import ExchangeDataFetcher
from ..strategies.signal_generator import SignalGenerator
from ..storage.models import DatabaseManager
from .validation import BacktestValidator
from ..config import Config

logger = logging.getLogger(__name__)

@dataclass
class BacktestResult:
    """Results of a backtest run"""
    total_signals: int
    winning_signals: int
    losing_signals: int
    win_rate: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    avg_holding_period: float
    signals_by_symbol: Dict[str, Dict]
    performance_by_month: Dict[str, float]
    risk_metrics: Dict[str, float]
    validation_result: Optional[object] = None

class Backtester:
    """Comprehensive backtesting system"""
    
    def __init__(self, start_date: str, end_date: str):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.exchange_fetcher = ExchangeDataFetcher()
        self.signal_generator = SignalGenerator()
        self.db = DatabaseManager()
        self.validator = BacktestValidator()
        
        # Backtest parameters
        self.initial_capital = 10000  # $10,000 starting capital
        self.position_size = 0.1  # 10% of capital per trade
        self.commission_rate = 0.001  # 0.1% commission
        self.slippage_rate = 0.0005  # 0.05% slippage
        
        # Results storage
        self.trades = []
        self.equity_curve = []
        self.daily_returns = []
        self.consecutive_losses = 0
        self.max_consecutive_losses = 3  # Balanced approach
        self.trading_paused_until = None
        self.loss_streak_threshold = 2  # Reduce position size after 2 losses
        self.position_size_reduction = 0.5  # Moderate reduction (50% reduction)
        self.original_position_size = self.position_size
        self.consecutive_wins = 0  # Track consecutive wins for position sizing
        
        # Portfolio diversification settings (configurable)
        self.max_symbols_per_trade = getattr(Config, 'MAX_CONCURRENT_TRADES', 1)
        self.symbol_correlation_threshold = getattr(Config, 'SYMBOL_CORRELATION_THRESHOLD', 0.3)
        self.active_symbols = set()  # Track active trading symbols
        
        # Emotional control mechanisms
        self.min_time_between_trades = getattr(Config, 'MIN_TIME_BETWEEN_TRADES', 3600)  # seconds
        self.last_trade_time = None
        self.max_daily_trades = getattr(Config, 'MAX_DAILY_TRADES', 3)
        self.daily_trade_count = 0
        self.last_trade_date = None
        
    async def run_backtest(self) -> BacktestResult:
        """Run comprehensive backtest"""
        try:
            logger.info(f"Starting backtest from {self.start_date} to {self.end_date}")
            
            # Get historical data
            historical_data = await self._get_historical_data()
            
            # Generate signals for all timeframes
            all_signals = []
            for symbol, timeframes in historical_data.items():
                for timeframe, df in timeframes.items():
                    signals = self._generate_historical_signals(symbol, df, timeframe)
                    all_signals.extend(signals)
            
            # Sort signals by timestamp
            all_signals.sort(key=lambda x: x['timestamp'])
            
            # Simulate trading
            self._simulate_trading(all_signals)
            
            # Calculate performance metrics
            result = self._calculate_performance_metrics()
            
            # Validate backtest results
            validation_result = self.validator.validate_comprehensive(
                historical_data, self.trades, result.__dict__
            )
            
            # Add validation results to backtest result
            result.validation_result = validation_result
            
            logger.info(f"Backtest completed. Total signals: {result.total_signals}")
            logger.info(f"Validation score: {validation_result.overall_score:.1f}/100")
            
            if not validation_result.is_valid:
                logger.warning(f"Backtest validation failed: {len(validation_result.issues)} issues found")
                for issue in validation_result.issues:
                    logger.warning(f"  - {issue}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            raise
    
    async def _get_historical_data(self) -> Dict:
        """Get historical data for backtesting"""
        try:
            # Get data for each symbol and timeframe from configuration
            symbols = getattr(Config, 'TRADING_PAIRS', ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT'])
            timeframes = getattr(Config, 'TIMEFRAMES', ['5m', '15m', '1h'])
            
            historical_data = {}
            
            for symbol in symbols:
                historical_data[symbol] = {}
                for timeframe in timeframes:
                    try:
                        # Get data for the entire period
                        df = await self.exchange_fetcher.get_ohlcv_data(
                            symbol, timeframe, limit=2000
                        )
                        
                        # Filter by date range
                        df = df[(df.index >= self.start_date) & (df.index <= self.end_date)]
                        
                        if len(df) > 100:  # Ensure we have enough data
                            historical_data[symbol][timeframe] = df
                            logger.info(f"Got {len(df)} candles for {symbol} {timeframe}")
                        
                    except Exception as e:
                        logger.warning(f"Could not get data for {symbol} {timeframe}: {e}")
                        continue
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return {}
    
    def _generate_historical_signals(self, symbol: str, df: pd.DataFrame, timeframe: str) -> List[Dict]:
        """Generate signals for historical data using the same path as live mode"""
        signals = []

        try:
            # Precompute indicators once per timeframe for performance
            if Config.ULTRA_HIGH_WINRATE_MODE:
                ultra = self.signal_generator.ultra_high_winrate_generator
                indicators_full = ultra.calculate_indicators(df)
            else:
                indicators_full = self.signal_generator.calculate_indicators(df)

            # Generate signals for each candle (after indicators warmup)
            for i in range(200, len(df)):
                current_data = df.iloc[:i+1]

                if Config.ULTRA_HIGH_WINRATE_MODE:
                    # Slice indicators up to current candle
                    current_indicators = {k: v.iloc[:i+1] for k, v in indicators_full.items()}
                    sig = ultra.generate_signal_from_precomputed(symbol, current_data, current_indicators, exchange_fetcher=None)
                else:
                    current_indicators = {k: v.iloc[:i+1] for k, v in indicators_full.items()}
                    # Use faster path with precomputed indicators
                    sig = self.signal_generator.trend_following_signal(current_data, current_indicators)
                    if (not sig.get('direction')) or sig.get('confidence', 0) < 0.6:
                        sig2 = self.signal_generator.mean_reversion_signal(current_data, current_indicators)
                        sig = sig2 if (sig2.get('direction') and sig2.get('confidence', 0) >= 0.6) else None

                if sig:
                    # Ensure backtest timestamp/entry price are aligned with historical candle
                    sig['symbol'] = symbol
                    sig['timeframe'] = timeframe
                    sig['timestamp'] = df.index[i]
                    sig['entry_price'] = float(current_data['close'].iloc[-1])
                    sig['price_change_24h'] = self._calculate_price_change_24h(df, i)
                    sig['volume_24h'] = self._calculate_volume_24h(df, i)

                    signals.append(sig)

            return signals

        except Exception as e:
            logger.error(f"Error generating signals for {symbol}: {e}")
            return []
    
    def _calculate_price_change_24h(self, df: pd.DataFrame, current_index: int) -> float:
        """Calculate 24-hour price change"""
        if current_index < 24:
            return 0.0
        
        current_price = df.iloc[current_index]['close']
        price_24h_ago = df.iloc[current_index - 24]['close']
        
        return ((current_price - price_24h_ago) / price_24h_ago) * 100
    
    def _calculate_volume_24h(self, df: pd.DataFrame, current_index: int) -> float:
        """Calculate 24-hour volume"""
        if current_index < 24:
            return df.iloc[:current_index + 1]['volume'].sum()
        
        return df.iloc[current_index - 23:current_index + 1]['volume'].sum()
    
    def _simulate_trading(self, signals: List[Dict]):
        """Simulate trading based on signals"""
        capital = self.initial_capital
        position = None
        trade_id = 0
        
        for signal in signals:
            current_time = signal['timestamp']
            current_price = signal['entry_price']
            
            # Close existing position if we have one
            if position:
                exit_price = self._get_exit_price(position, current_time, current_price)
                pnl = self._calculate_pnl(position, exit_price)
                capital += pnl
                
                # Record trade
                trade = {
                    'id': trade_id,
                    'symbol': position['symbol'],
                    'direction': position['direction'],
                    'entry_time': position['entry_time'],
                    'exit_time': current_time,
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price,
                    'quantity': position['quantity'],
                    'pnl': pnl,
                    'return_pct': (pnl / position['entry_value']) * 100,
                    'holding_period': (current_time - position['entry_time']).total_seconds() / 3600  # hours
                }
                
                self.trades.append(trade)
                trade_id += 1
                
                # Ultra-strict consecutive losses management
                if pnl < 0:
                    self.consecutive_losses += 1
                    self.consecutive_wins = 0  # Reset wins counter
                    
                    # Reduce position size after 1 consecutive loss
                    if self.consecutive_losses >= self.loss_streak_threshold:
                        self.position_size = self.original_position_size * self.position_size_reduction
                        logger.warning(f"Position size reduced to {self.position_size:.3f} after {self.consecutive_losses} consecutive losses")
                    
                    # Pause trading after 2 consecutive losses
                    if self.consecutive_losses >= self.max_consecutive_losses:
                        # Pause trading for 72 hours (increased from 48)
                        self.trading_paused_until = current_time + timedelta(hours=72)
                        logger.warning(f"Trading paused for 72 hours due to {self.consecutive_losses} consecutive losses")
                else:
                    # Reset on win
                    self.consecutive_losses = 0
                    self.consecutive_wins += 1
                    self.trading_paused_until = None
                    
                    # Gradually restore position size based on consecutive wins
                    if self.consecutive_wins >= 3 and self.position_size < self.original_position_size:
                        self.position_size = min(self.original_position_size, self.position_size * 1.2)
                        logger.info(f"Position size gradually restored to {self.position_size:.3f} after {self.consecutive_wins} consecutive wins")
                    elif self.consecutive_wins >= 5:
                        self.position_size = self.original_position_size
                        logger.info("Position size fully restored after 5 consecutive wins")
                
                # Remove symbol from active trading list
                if position:
                    self.active_symbols.discard(position['symbol'])
                
                position = None
            
            # Check if trading is paused due to consecutive losses
            if self.trading_paused_until and current_time < self.trading_paused_until:
                continue
            
            # Emotional control: Check minimum time between trades
            if (self.last_trade_time and 
                (current_time - self.last_trade_time).total_seconds() < self.min_time_between_trades):
                continue
            
            # Emotional control: Check daily trade limit
            current_date = current_time.date()
            if self.last_trade_date != current_date:
                self.daily_trade_count = 0
                self.last_trade_date = current_date
            
            if self.daily_trade_count >= self.max_daily_trades:
                continue
            
            # Open new position if signal is strong enough and diversification allows
            if (signal['confidence'] >= Config.CONFIDENCE_THRESHOLD and
                len(self.active_symbols) < self.max_symbols_per_trade and  # Diversification limit
                signal['symbol'] not in self.active_symbols):  # Not already trading this symbol
                
                # Ultra-optimized position sizing for better Sharpe ratio
                base_position_size = self.position_size
                
                # Calculate recent performance metrics
                if len(self.trades) >= 10:
                    recent_returns = [trade['return_pct'] for trade in self.trades[-10:]]
                    recent_volatility = np.std(recent_returns) if recent_returns else 0
                    recent_mean_return = np.mean(recent_returns) if recent_returns else 0
                    
                    # Calculate Sortino ratio (downside deviation only)
                    downside_returns = [r for r in recent_returns if r < 0]
                    downside_deviation = np.std(downside_returns) if downside_returns else 0
                    sortino_ratio = recent_mean_return / downside_deviation if downside_deviation > 0 else 0
                    
                    # Reduce position size if Sortino ratio is poor
                    if sortino_ratio < 1.0:  # Poor risk-adjusted returns
                        base_position_size *= 0.6  # Reduce by 40%
                        logger.debug(f"Position size reduced due to poor Sortino ratio: {sortino_ratio:.2f}")
                    
                    # Reduce position size if recent volatility is high
                    if recent_volatility > 3:  # Lowered threshold for stricter control
                        base_position_size *= 0.5  # Reduce by 50%
                        logger.debug(f"Position size reduced due to high volatility: {recent_volatility:.2f}%")
                
                # Reduce position size if recent performance is poor
                if len(self.trades) >= 3:  # Shorter lookback period
                    recent_pnl = sum([trade['pnl'] for trade in self.trades[-3:]])
                    if recent_pnl < 0:
                        base_position_size *= 0.6  # Reduce by 40%
                        logger.debug(f"Position size reduced due to poor recent performance: {recent_pnl:.2f}")
                
                # Additional reduction based on consecutive losses
                if self.consecutive_losses > 0:
                    base_position_size *= (0.5 ** self.consecutive_losses)  # Exponential reduction
                    logger.debug(f"Position size reduced due to consecutive losses: {self.consecutive_losses}")
                
                position_value = capital * base_position_size
                quantity = position_value / current_price
                
                # Apply commission and slippage
                entry_price = current_price * (1 + self.slippage_rate)
                entry_value = quantity * entry_price
                commission = entry_value * self.commission_rate
                
                if entry_value + commission <= capital:
                    position = {
                        'symbol': signal['symbol'],
                        'direction': signal['direction'],
                        'entry_time': current_time,
                        'entry_price': entry_price,
                        'quantity': quantity,
                        'entry_value': entry_value,
                        'stop_loss': signal['stop_loss'],
                        'take_profit': signal['take_profit'],
                        'confidence': signal['confidence'],
                        'atr': signal.get('atr', 0.01)
                    }
                    
                    capital -= commission
                    
                    # Add symbol to active trading list
                    self.active_symbols.add(signal['symbol'])
                    
                    # Update emotional control tracking
                    self.last_trade_time = current_time
                    self.daily_trade_count += 1
            
            # Update equity curve
            current_equity = capital
            if position:
                current_equity += position['quantity'] * current_price
            
            self.equity_curve.append({
                'timestamp': current_time,
                'equity': current_equity,
                'capital': capital
            })
    
    def _get_exit_price(self, position: Dict, current_time: datetime, current_price: float) -> float:
        """Determine exit price for a position with improved trailing stop"""
        # Check if stop loss or take profit hit
        if position['direction'] == 'LONG':
            if position['stop_loss'] and current_price <= position['stop_loss']:
                return position['stop_loss']
            elif position['take_profit'] and current_price >= position['take_profit']:
                return position['take_profit']
            
            # Improved trailing stop for LONG positions
            profit_pct = (current_price - position['entry_price']) / position['entry_price']
            if profit_pct > 0.3:  # 30% profit, activate trailing stop (reduced from 50%)
                new_stop = current_price - (1.0 * position.get('atr', 0.01))  # Tighter stop
                if new_stop > position['stop_loss']:
                    position['stop_loss'] = new_stop
                    logger.debug(f"Trailing stop updated for LONG: {new_stop:.4f}")
            
            # Break-even stop after 20% profit
            if profit_pct > 0.2 and position['stop_loss'] < position['entry_price']:
                position['stop_loss'] = position['entry_price']
                logger.debug("Stop moved to break-even")
                    
        else:  # SHORT
            if position['stop_loss'] and current_price >= position['stop_loss']:
                return position['stop_loss']
            elif position['take_profit'] and current_price <= position['take_profit']:
                return position['take_profit']
            
            # Improved trailing stop for SHORT positions
            profit_pct = (position['entry_price'] - current_price) / position['entry_price']
            if profit_pct > 0.3:  # 30% profit, activate trailing stop (reduced from 50%)
                new_stop = current_price + (1.0 * position.get('atr', 0.01))  # Tighter stop
                if new_stop < position['stop_loss']:
                    position['stop_loss'] = new_stop
                    logger.debug(f"Trailing stop updated for SHORT: {new_stop:.4f}")
            
            # Break-even stop after 20% profit
            if profit_pct > 0.2 and position['stop_loss'] > position['entry_price']:
                position['stop_loss'] = position['entry_price']
                logger.debug("Stop moved to break-even")
        
        # Check if holding period is too long (12 hours max - reduced from 24)
        holding_hours = (current_time - position['entry_time']).total_seconds() / 3600
        if holding_hours >= 12:
            logger.debug(f"Position closed due to time limit: {holding_hours:.1f} hours")
            return current_price
        
        # Check if confidence drops significantly
        # This would require real-time confidence calculation
        # For now, use current price
        return current_price
    
    def _calculate_pnl(self, position: Dict, exit_price: float) -> float:
        """Calculate P&L for a position"""
        if position['direction'] == 'LONG':
            pnl = (exit_price - position['entry_price']) * position['quantity']
        else:  # SHORT
            pnl = (position['entry_price'] - exit_price) * position['quantity']
        
        # Apply commission
        exit_value = position['quantity'] * exit_price
        commission = exit_value * self.commission_rate
        
        return pnl - commission
    
    def _calculate_performance_metrics(self) -> BacktestResult:
        """Calculate comprehensive performance metrics"""
        if not self.trades:
            return BacktestResult(
                total_signals=0, winning_signals=0, losing_signals=0,
                win_rate=0.0, total_pnl=0.0, max_drawdown=0.0,
                sharpe_ratio=0.0, profit_factor=0.0, avg_win=0.0,
                avg_loss=0.0, max_consecutive_wins=0, max_consecutive_losses=0,
                avg_holding_period=0.0, signals_by_symbol={},
                performance_by_month={}, risk_metrics={}
            )
        
        # Basic metrics
        total_signals = len(self.trades)
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] < 0]
        
        winning_signals = len(winning_trades)
        losing_signals = len(losing_trades)
        win_rate = (winning_signals / total_signals) * 100 if total_signals > 0 else 0
        
        # P&L metrics
        total_pnl = sum(t['pnl'] for t in self.trades)
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        # Profit factor
        total_wins = sum(t['pnl'] for t in winning_trades) if winning_trades else 0
        total_losses = abs(sum(t['pnl'] for t in losing_trades)) if losing_trades else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Drawdown calculation
        equity_values = [e['equity'] for e in self.equity_curve]
        peak = equity_values[0]
        max_drawdown = 0
        
        for equity in equity_values:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        max_drawdown *= 100  # Convert to percentage
        
        # Sharpe ratio
        if len(self.equity_curve) > 1:
            returns = []
            for i in range(1, len(self.equity_curve)):
                ret = (self.equity_curve[i]['equity'] - self.equity_curve[i-1]['equity']) / self.equity_curve[i-1]['equity']
                returns.append(ret)
            
            if returns:
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        # Consecutive wins/losses
        max_consecutive_wins = self._calculate_max_consecutive_wins()
        max_consecutive_losses = self._calculate_max_consecutive_losses()
        
        # Average holding period
        avg_holding_period = np.mean([t['holding_period'] for t in self.trades]) if self.trades else 0
        
        # Performance by symbol
        signals_by_symbol = self._calculate_performance_by_symbol()
        
        # Performance by month
        performance_by_month = self._calculate_performance_by_month()
        
        # Risk metrics
        risk_metrics = self._calculate_risk_metrics()
        
        return BacktestResult(
            total_signals=total_signals,
            winning_signals=winning_signals,
            losing_signals=losing_signals,
            win_rate=win_rate,
            total_pnl=total_pnl,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
            avg_holding_period=avg_holding_period,
            signals_by_symbol=signals_by_symbol,
            performance_by_month=performance_by_month,
            risk_metrics=risk_metrics
        )
    
    def _calculate_max_consecutive_wins(self) -> int:
        """Calculate maximum consecutive wins"""
        if not self.trades:
            return 0
        
        max_wins = 0
        current_wins = 0
        
        for trade in self.trades:
            if trade['pnl'] > 0:
                current_wins += 1
                max_wins = max(max_wins, current_wins)
            else:
                current_wins = 0
        
        return max_wins
    
    def _calculate_max_consecutive_losses(self) -> int:
        """Calculate maximum consecutive losses"""
        if not self.trades:
            return 0
        
        max_losses = 0
        current_losses = 0
        
        for trade in self.trades:
            if trade['pnl'] < 0:
                current_losses += 1
                max_losses = max(max_losses, current_losses)
            else:
                current_losses = 0
        
        return max_losses
    
    def _calculate_performance_by_symbol(self) -> Dict[str, Dict]:
        """Calculate performance metrics by symbol"""
        symbol_performance = {}
        
        for trade in self.trades:
            symbol = trade['symbol']
            if symbol not in symbol_performance:
                symbol_performance[symbol] = {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'total_pnl': 0,
                    'win_rate': 0,
                    'avg_return': 0
                }
            
            symbol_performance[symbol]['total_trades'] += 1
            symbol_performance[symbol]['total_pnl'] += trade['pnl']
            
            if trade['pnl'] > 0:
                symbol_performance[symbol]['winning_trades'] += 1
            else:
                symbol_performance[symbol]['losing_trades'] += 1
        
        # Calculate win rates and average returns
        for symbol, metrics in symbol_performance.items():
            if metrics['total_trades'] > 0:
                metrics['win_rate'] = (metrics['winning_trades'] / metrics['total_trades']) * 100
                metrics['avg_return'] = metrics['total_pnl'] / metrics['total_trades']
        
        return symbol_performance
    
    def _calculate_performance_by_month(self) -> Dict[str, float]:
        """Calculate performance by month"""
        monthly_pnl = {}
        
        for trade in self.trades:
            month_key = trade['exit_time'].strftime('%Y-%m')
            if month_key not in monthly_pnl:
                monthly_pnl[month_key] = 0
            monthly_pnl[month_key] += trade['pnl']
        
        return monthly_pnl
    
    def _calculate_risk_metrics(self) -> Dict[str, float]:
        """Calculate additional risk metrics"""
        if not self.trades:
            return {}
        
        returns = [t['return_pct'] for t in self.trades]
        
        return {
            'volatility': np.std(returns) if returns else 0,
            'skewness': self._calculate_skewness(returns),
            'kurtosis': self._calculate_kurtosis(returns),
            'var_95': np.percentile(returns, 5) if returns else 0,  # 95% VaR
            'cvar_95': np.mean([r for r in returns if r <= np.percentile(returns, 5)]) if returns else 0  # CVaR
        }
    
    def _calculate_skewness(self, returns: List[float]) -> float:
        """Calculate skewness of returns"""
        if len(returns) < 3:
            return 0
        
        mean = np.mean(returns)
        std = np.std(returns)
        
        if std == 0:
            return 0
        
        skewness = np.mean([(r - mean) ** 3 for r in returns]) / (std ** 3)
        return skewness
    
    def _calculate_kurtosis(self, returns: List[float]) -> float:
        """Calculate kurtosis of returns"""
        if len(returns) < 4:
            return 0
        
        mean = np.mean(returns)
        std = np.std(returns)
        
        if std == 0:
            return 0
        
        kurtosis = np.mean([(r - mean) ** 4 for r in returns]) / (std ** 4)
        return kurtosis - 3  # Excess kurtosis
    
    def generate_report(self, result: BacktestResult) -> str:
        """Generate comprehensive backtest report"""
        report = f"""
# 📊 گزارش جامع بک‌تست بات سیگنال کریپتو

## 📈 آمار کلی عملکرد
- **کل سیگنال‌ها**: {result.total_signals}
- **سیگنال‌های برنده**: {result.winning_signals}
- **سیگنال‌های بازنده**: {result.losing_signals}
- **نرخ برد**: {result.win_rate:.2f}%
- **سود/زیان کل**: ${result.total_pnl:.2f}
- **بازده کل**: {(result.total_pnl / self.initial_capital) * 100:.2f}%

## 💰 آمار مالی
- **میانگین سود**: ${result.avg_win:.2f}
- **میانگین زیان**: ${result.avg_loss:.2f}
- **ضریب سود**: {result.profit_factor:.2f}
- **حداکثر افت**: {result.max_drawdown:.2f}%
- **نسبت شارپ**: {result.sharpe_ratio:.2f}

## ⏱️ آمار زمانی
- **میانگین مدت نگهداری**: {result.avg_holding_period:.1f} ساعت
- **بیشترین برد متوالی**: {result.max_consecutive_wins}
- **بیشترین باخت متوالی**: {result.max_consecutive_losses}

## 📊 عملکرد به تفکیک نماد
"""
        
        for symbol, metrics in result.signals_by_symbol.items():
            report += f"""
### {symbol}
- **تعداد معاملات**: {metrics['total_trades']}
- **نرخ برد**: {metrics['win_rate']:.2f}%
- **سود/زیان**: ${metrics['total_pnl']:.2f}
- **بازده میانگین**: {metrics['avg_return']:.2f}%
"""
        
        report += f"""
## 📅 عملکرد ماهانه
"""
        
        for month, pnl in result.performance_by_month.items():
            report += f"- **{month}**: ${pnl:.2f}\n"
        
        report += f"""
## ⚠️ معیارهای ریسک
- **نوسان‌پذیری**: {result.risk_metrics.get('volatility', 0):.2f}%
- **چولگی**: {result.risk_metrics.get('skewness', 0):.2f}
- **کشیدگی**: {result.risk_metrics.get('kurtosis', 0):.2f}
- **VaR 95%**: {result.risk_metrics.get('var_95', 0):.2f}%
- **CVaR 95%**: {result.risk_metrics.get('cvar_95', 0):.2f}%

## 🔍 تحلیل و توصیه‌ها
"""
        
        # Add validation results if available
        if result.validation_result:
            validation = result.validation_result
            report += f"""
## ✅ اعتبارسنجی بک‌تست

### 📊 امتیاز کلی اعتبارسنجی: {validation.overall_score:.1f}/100

#### جزئیات اعتبارسنجی:
- **کیفیت داده**: {validation.data_quality_score:.1f}/100
- **شرایط معاملاتی**: {validation.trading_conditions_score:.1f}/100
- **تشخیص سوگیری**: {validation.bias_detection_score:.1f}/100
- **تشخیص بیش‌برازش**: {validation.overfitting_score:.1f}/100
- **مدیریت ریسک**: {validation.risk_management_score:.1f}/100

### ⚠️ مسائل شناسایی شده:
"""
            
            if validation.issues:
                for issue in validation.issues:
                    report += f"- {issue}\n"
            else:
                report += "- هیچ مسئله‌ای شناسایی نشد ✅\n"
            
            report += f"""
### 💡 توصیه‌های بهبود:
"""
            
            if validation.recommendations:
                for recommendation in validation.recommendations:
                    report += f"- {recommendation}\n"
            else:
                report += "- هیچ توصیه‌ای لازم نیست ✅\n"
            
            if validation.is_valid:
                report += f"""
### ✅ نتیجه اعتبارسنجی: **معتبر** - نتایج بک‌تست قابل اعتماد است
"""
            else:
                report += f"""
### ❌ نتیجه اعتبارسنجی: **نامعتبر** - نتایج بک‌تست نیاز به بررسی دارد
"""
        
        # Add analysis and recommendations
        if result.win_rate < 50:
            report += "- ⚠️ **نرخ برد پایین**: استراتژی نیاز به بهبود دارد\n"
        
        if result.max_drawdown > 20:
            report += "- ⚠️ **حداکثر افت بالا**: مدیریت ریسک نیاز به بهبود دارد\n"
        
        if result.profit_factor < 1.5:
            report += "- ⚠️ **ضریب سود پایین**: نسبت سود به زیان نامطلوب است\n"
        
        if result.sharpe_ratio < 1.0:
            report += "- ⚠️ **نسبت شارپ پایین**: بازده نسبت به ریسک نامطلوب است\n"
        
        if result.avg_holding_period > 12:
            report += "- ⚠️ **مدت نگهداری طولانی**: ممکن است فرصت‌های معاملاتی از دست برود\n"
        
        return report
    
    def close(self):
        """Close backtester resources"""
        if hasattr(self, 'exchange_fetcher'):
            self.exchange_fetcher.close()
        if hasattr(self, 'db'):
            self.db.close()
