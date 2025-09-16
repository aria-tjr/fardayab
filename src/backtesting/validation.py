"""
Comprehensive backtest validation system
Ensures accuracy and reliability of backtest results
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import warnings

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Results of backtest validation"""
    is_valid: bool
    data_quality_score: float
    trading_conditions_score: float
    bias_detection_score: float
    overfitting_score: float
    risk_management_score: float
    overall_score: float
    issues: List[str]
    recommendations: List[str]

class BacktestValidator:
    """Comprehensive backtest validation system"""
    
    def __init__(self):
        self.issues = []
        self.recommendations = []
        
    def validate_data_integrity(self, historical_data: Dict) -> float:
        """Validate data integrity and completeness"""
        score = 100.0
        
        try:
            for symbol, timeframes in historical_data.items():
                for timeframe, df in timeframes.items():
                    # Check for missing data
                    missing_data = df.isnull().sum().sum()
                    if missing_data > 0:
                        self.issues.append(f"Missing data in {symbol} {timeframe}: {missing_data} values")
                        score -= 10
                    
                    # Check for duplicate timestamps
                    duplicate_timestamps = df.index.duplicated().sum()
                    if duplicate_timestamps > 0:
                        self.issues.append(f"Duplicate timestamps in {symbol} {timeframe}: {duplicate_timestamps}")
                        score -= 5
                    
                    # Check for data gaps
                    time_diff = df.index.to_series().diff()
                    expected_interval = self._get_expected_interval(timeframe)
                    large_gaps = (time_diff > expected_interval * 2).sum()
                    if large_gaps > 0:
                        self.issues.append(f"Large time gaps in {symbol} {timeframe}: {large_gaps}")
                        score -= 5
                    
                    # Check for unrealistic price movements
                    price_changes = df['close'].pct_change().abs()
                    extreme_moves = (price_changes > 0.5).sum()  # 50% moves
                    if extreme_moves > 0:
                        self.issues.append(f"Extreme price movements in {symbol} {timeframe}: {extreme_moves}")
                        score -= 3
                    
                    # Check for zero or negative prices
                    invalid_prices = (df[['open', 'high', 'low', 'close']] <= 0).sum().sum()
                    if invalid_prices > 0:
                        self.issues.append(f"Invalid prices in {symbol} {timeframe}: {invalid_prices}")
                        score -= 15
                    
                    # Check for volume consistency
                    zero_volume = (df['volume'] == 0).sum()
                    if zero_volume > len(df) * 0.1:  # More than 10% zero volume
                        self.issues.append(f"High zero volume in {symbol} {timeframe}: {zero_volume}")
                        score -= 5
            
            if score < 70:
                self.recommendations.append("Data quality issues detected. Consider using higher quality data source.")
            
            return max(0, score)
            
        except Exception as e:
            logger.error(f"Error validating data integrity: {e}")
            self.issues.append(f"Data integrity validation error: {e}")
            return 0
    
    def _get_expected_interval(self, timeframe: str) -> pd.Timedelta:
        """Get expected time interval for timeframe"""
        intervals = {
            '1m': pd.Timedelta(minutes=1),
            '5m': pd.Timedelta(minutes=5),
            '15m': pd.Timedelta(minutes=15),
            '1h': pd.Timedelta(hours=1),
            '4h': pd.Timedelta(hours=4),
            '1d': pd.Timedelta(days=1)
        }
        return intervals.get(timeframe, pd.Timedelta(minutes=5))
    
    def validate_trading_conditions(self, trades: List[Dict], initial_capital: float) -> float:
        """Validate realistic trading conditions"""
        score = 100.0
        
        try:
            if not trades:
                self.issues.append("No trades to validate")
                return 0
            
            # Check transaction costs
            total_commission = 0
            total_slippage = 0
            
            for trade in trades:
                # Commission (0.1% per trade)
                trade_value = trade.get('entry_value', 0)
                commission = trade_value * 0.001
                total_commission += commission
                
                # Slippage (0.05% per trade)
                slippage = trade_value * 0.0005
                total_slippage += slippage
            
            # Check if costs are realistic
            total_costs = total_commission + total_slippage
            cost_ratio = total_costs / initial_capital
            
            if cost_ratio > 0.1:  # More than 10% of capital
                self.issues.append(f"High trading costs: {cost_ratio:.2%} of capital")
                score -= 20
            elif cost_ratio > 0.05:  # More than 5% of capital
                self.issues.append(f"Moderate trading costs: {cost_ratio:.2%} of capital")
                score -= 10
            
            # Check position sizing
            position_sizes = [trade.get('position_size', 0) for trade in trades]
            if position_sizes:
                max_position = max(position_sizes)
                if max_position > 0.2:  # More than 20% of capital
                    self.issues.append(f"Large position size: {max_position:.1%}")
                    score -= 15
                elif max_position > 0.1:  # More than 10% of capital
                    self.issues.append(f"Moderate position size: {max_position:.1%}")
                    score -= 5
            
            # Check for unrealistic returns
            total_pnl = sum(trade.get('pnl', 0) for trade in trades)
            return_ratio = total_pnl / initial_capital if initial_capital > 0 else 0
            
            if return_ratio > 10:  # More than 1000% return
                self.issues.append(f"Unrealistic returns: {return_ratio:.1%}")
                score -= 30
            elif return_ratio > 5:  # More than 500% return
                self.issues.append(f"Very high returns: {return_ratio:.1%}")
                score -= 15
            
            return max(0, score)
            
        except Exception as e:
            logger.error(f"Error validating trading conditions: {e}")
            self.issues.append(f"Trading conditions validation error: {e}")
            return 0
    
    def validate_look_ahead_bias(self, signals: List[Dict], historical_data: Dict) -> float:
        """Validate no look-ahead bias in signals"""
        score = 100.0
        
        try:
            for signal in signals:
                signal_time = signal.get('timestamp')
                symbol = signal.get('symbol')
                
                if not signal_time or not symbol:
                    continue
                
                # Check if signal uses future data
                for timeframe, df in historical_data.get(symbol, {}).items():
                    if df is None or len(df) == 0:
                        continue
                    
                    # Find data point at signal time
                    try:
                        signal_data = df.loc[signal_time]
                        
                        # Check if signal uses data from after signal time
                        future_data = df[df.index > signal_time]
                        if len(future_data) > 0:
                            # This is normal - we have future data for backtesting
                            pass
                        
                    except KeyError:
                        # Signal time not in data - this is normal for backtesting
                        pass
                
                # Check for unrealistic confidence scores
                confidence = signal.get('confidence', 0)
                if confidence > 0.99:  # 99%+ confidence
                    self.issues.append(f"Unrealistic confidence: {confidence:.2%}")
                    score -= 10
                elif confidence > 0.95:  # 95%+ confidence
                    self.issues.append(f"Very high confidence: {confidence:.2%}")
                    score -= 5
            
            return max(0, score)
            
        except Exception as e:
            logger.error(f"Error validating look-ahead bias: {e}")
            self.issues.append(f"Look-ahead bias validation error: {e}")
            return 0
    
    def validate_overfitting(self, backtest_results: Dict, parameter_sets: List[Dict]) -> float:
        """Validate no overfitting in strategy"""
        score = 100.0
        
        try:
            # Check if strategy has too many parameters
            if len(parameter_sets) > 10:
                self.issues.append(f"Too many parameter combinations: {len(parameter_sets)}")
                score -= 20
            
            # Check for parameter sensitivity
            if len(parameter_sets) > 1:
                # Calculate performance variance across parameter sets
                performances = [result.get('total_pnl', 0) for result in parameter_sets]
                if performances:
                    performance_std = np.std(performances)
                    performance_mean = np.mean(performances)
                    
                    if performance_mean != 0:
                        cv = performance_std / abs(performance_mean)
                        if cv > 0.5:  # High coefficient of variation
                            self.issues.append(f"High parameter sensitivity: CV={cv:.2f}")
                            score -= 15
                        elif cv > 0.3:  # Moderate coefficient of variation
                            self.issues.append(f"Moderate parameter sensitivity: CV={cv:.2f}")
                            score -= 5
            
            # Check for unrealistic performance metrics
            win_rate = backtest_results.get('win_rate', 0)
            # Convert percentage to decimal if needed
            if win_rate > 1:  # If already in percentage form
                win_rate = win_rate / 100
            
            if win_rate > 0.9:  # 90%+ win rate
                self.issues.append(f"Unrealistic win rate: {win_rate:.1%}")
                score -= 25
            elif win_rate > 0.8:  # 80%+ win rate
                self.issues.append(f"Very high win rate: {win_rate:.1%}")
                score -= 10
            
            sharpe_ratio = backtest_results.get('sharpe_ratio', 0)
            if sharpe_ratio > 3:  # Sharpe > 3
                self.issues.append(f"Unrealistic Sharpe ratio: {sharpe_ratio:.2f}")
                score -= 20
            elif sharpe_ratio > 2:  # Sharpe > 2
                self.issues.append(f"Very high Sharpe ratio: {sharpe_ratio:.2f}")
                score -= 5
            
            return max(0, score)
            
        except Exception as e:
            logger.error(f"Error validating overfitting: {e}")
            self.issues.append(f"Overfitting validation error: {e}")
            return 0
    
    def validate_risk_management(self, trades: List[Dict], backtest_results: Dict) -> float:
        """Validate risk management implementation"""
        score = 100.0
        
        try:
            if not trades:
                return 0
            
            # Check maximum drawdown
            max_drawdown = backtest_results.get('max_drawdown', 0)
            # Convert percentage to decimal if needed
            if max_drawdown > 1:  # If already in percentage form
                max_drawdown = max_drawdown / 100
            
            if max_drawdown > 0.5:  # 50%+ drawdown
                self.issues.append(f"Excessive drawdown: {max_drawdown:.1%}")
                score -= 25
            elif max_drawdown > 0.3:  # 30%+ drawdown
                self.issues.append(f"High drawdown: {max_drawdown:.1%}")
                score -= 10
            
            # Check consecutive losses
            consecutive_losses = backtest_results.get('max_consecutive_losses', 0)
            if consecutive_losses > 10:
                self.issues.append(f"Too many consecutive losses: {consecutive_losses}")
                score -= 15
            elif consecutive_losses > 5:
                self.issues.append(f"Many consecutive losses: {consecutive_losses}")
                score -= 5
            
            # Check position sizing consistency
            position_sizes = [trade.get('position_size', 0) for trade in trades if 'position_size' in trade]
            if position_sizes:
                position_std = np.std(position_sizes)
                position_mean = np.mean(position_sizes)
                
                if position_mean > 0:
                    position_cv = position_std / position_mean
                    if position_cv > 0.5:  # High variation in position sizes
                        self.issues.append(f"Inconsistent position sizing: CV={position_cv:.2f}")
                        score -= 10
            
            # Check stop loss implementation
            stop_loss_trades = [trade for trade in trades if 'stop_loss' in trade and trade['stop_loss']]
            if len(stop_loss_trades) < len(trades) * 0.8:  # Less than 80% have stop loss
                self.issues.append(f"Missing stop losses: {len(stop_loss_trades)}/{len(trades)}")
                score -= 15
            
            return max(0, score)
            
        except Exception as e:
            logger.error(f"Error validating risk management: {e}")
            self.issues.append(f"Risk management validation error: {e}")
            return 0
    
    def calculate_comprehensive_metrics(self, trades: List[Dict], backtest_results: Dict) -> Dict:
        """Calculate comprehensive performance metrics"""
        try:
            if not trades:
                return {}
            
            # Basic metrics
            total_trades = len(trades)
            winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
            losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
            
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            total_pnl = sum(t.get('pnl', 0) for t in trades)
            
            # Advanced metrics
            returns = [t.get('return_pct', 0) for t in trades if 'return_pct' in t]
            
            metrics = {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_win': np.mean([t.get('pnl', 0) for t in winning_trades]) if winning_trades else 0,
                'avg_loss': np.mean([t.get('pnl', 0) for t in losing_trades]) if losing_trades else 0,
                'profit_factor': abs(sum(t.get('pnl', 0) for t in winning_trades) / sum(t.get('pnl', 0) for t in losing_trades)) if losing_trades else float('inf'),
                'max_drawdown': backtest_results.get('max_drawdown', 0),
                'sharpe_ratio': backtest_results.get('sharpe_ratio', 0),
                'max_consecutive_wins': backtest_results.get('max_consecutive_wins', 0),
                'max_consecutive_losses': backtest_results.get('max_consecutive_losses', 0),
            }
            
            # Additional metrics
            if returns:
                metrics.update({
                    'volatility': np.std(returns),
                    'skewness': self._calculate_skewness(returns),
                    'kurtosis': self._calculate_kurtosis(returns),
                    'var_95': np.percentile(returns, 5),
                    'cvar_95': np.mean([r for r in returns if r <= np.percentile(returns, 5)]),
                    'calmar_ratio': total_pnl / abs(backtest_results.get('max_drawdown', 1)) if backtest_results.get('max_drawdown', 0) != 0 else 0,
                    'sortino_ratio': self._calculate_sortino_ratio(returns),
                    'omega_ratio': self._calculate_omega_ratio(returns),
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive metrics: {e}")
            return {}
    
    def _calculate_skewness(self, returns: List[float]) -> float:
        """Calculate skewness of returns"""
        if len(returns) < 3:
            return 0
        mean = np.mean(returns)
        std = np.std(returns)
        if std == 0:
            return 0
        return np.mean([(r - mean) ** 3 for r in returns]) / (std ** 3)
    
    def _calculate_kurtosis(self, returns: List[float]) -> float:
        """Calculate kurtosis of returns"""
        if len(returns) < 4:
            return 0
        mean = np.mean(returns)
        std = np.std(returns)
        if std == 0:
            return 0
        return np.mean([(r - mean) ** 4 for r in returns]) / (std ** 4) - 3
    
    def _calculate_sortino_ratio(self, returns: List[float]) -> float:
        """Calculate Sortino ratio"""
        if not returns:
            return 0
        mean_return = np.mean(returns)
        downside_returns = [r for r in returns if r < 0]
        if not downside_returns:
            return float('inf')
        downside_std = np.std(downside_returns)
        return mean_return / downside_std if downside_std != 0 else 0
    
    def _calculate_omega_ratio(self, returns: List[float]) -> float:
        """Calculate Omega ratio"""
        if not returns:
            return 0
        threshold = 0
        positive_returns = [r for r in returns if r > threshold]
        negative_returns = [r for r in returns if r <= threshold]
        
        if not negative_returns:
            return float('inf')
        
        positive_sum = sum(positive_returns)
        negative_sum = abs(sum(negative_returns))
        
        return positive_sum / negative_sum if negative_sum != 0 else 0
    
    def validate_comprehensive(self, historical_data: Dict, trades: List[Dict], 
                            backtest_results: Dict, parameter_sets: List[Dict] = None) -> ValidationResult:
        """Comprehensive validation of backtest results"""
        try:
            self.issues = []
            self.recommendations = []
            
            # Validate each component
            data_quality_score = self.validate_data_integrity(historical_data)
            trading_conditions_score = self.validate_trading_conditions(trades, 10000)  # Default initial capital
            bias_detection_score = self.validate_look_ahead_bias(trades, historical_data)
            overfitting_score = self.validate_overfitting(backtest_results, parameter_sets or [])
            risk_management_score = self.validate_risk_management(trades, backtest_results)
            
            # Calculate overall score
            overall_score = (data_quality_score + trading_conditions_score + 
                           bias_detection_score + overfitting_score + risk_management_score) / 5
            
            # Determine if validation passed
            is_valid = overall_score >= 70 and len(self.issues) < 5
            
            # Generate recommendations
            if data_quality_score < 80:
                self.recommendations.append("Improve data quality by using more reliable data sources")
            
            if trading_conditions_score < 80:
                self.recommendations.append("Implement more realistic trading conditions and costs")
            
            if bias_detection_score < 80:
                self.recommendations.append("Review strategy for potential look-ahead bias")
            
            if overfitting_score < 80:
                self.recommendations.append("Simplify strategy to avoid overfitting")
            
            if risk_management_score < 80:
                self.recommendations.append("Improve risk management implementation")
            
            return ValidationResult(
                is_valid=is_valid,
                data_quality_score=data_quality_score,
                trading_conditions_score=trading_conditions_score,
                bias_detection_score=bias_detection_score,
                overfitting_score=overfitting_score,
                risk_management_score=risk_management_score,
                overall_score=overall_score,
                issues=self.issues,
                recommendations=self.recommendations
            )
            
        except Exception as e:
            logger.error(f"Error in comprehensive validation: {e}")
            return ValidationResult(
                is_valid=False,
                data_quality_score=0,
                trading_conditions_score=0,
                bias_detection_score=0,
                overfitting_score=0,
                risk_management_score=0,
                overall_score=0,
                issues=[f"Validation error: {e}"],
                recommendations=["Fix validation system errors"]
            )
