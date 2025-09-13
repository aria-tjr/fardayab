from __future__ import annotations

import asyncio
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

import httpx
from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level enumeration"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"


@dataclass
class PositionSize:
    """Position sizing calculation result"""
    symbol: str
    account_balance: float
    risk_per_trade: float
    entry_price: float
    stop_loss: float
    position_size: float
    position_value: float
    risk_amount: float
    risk_percentage: float
    max_loss: float
    max_gain: float
    risk_reward_ratio: float
    recommended_size: float
    risk_level: RiskLevel


@dataclass
class RiskMetrics:
    """Risk management metrics"""
    portfolio_value: float
    total_risk: float
    max_drawdown: float
    current_drawdown: float
    sharpe_ratio: float
    var_95: float  # Value at Risk 95%
    var_99: float  # Value at Risk 99%
    max_position_size: float
    correlation_risk: float
    concentration_risk: float
    liquidity_risk: float


class AdvancedRiskManager:
    """Advanced risk management and position sizing system"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        
        # Risk parameters
        self.risk_parameters = {
            RiskLevel.CONSERVATIVE: {
                "max_risk_per_trade": 0.01,  # 1%
                "max_portfolio_risk": 0.05,  # 5%
                "max_correlation": 0.7,
                "max_position_size": 0.1,  # 10%
                "min_risk_reward": 2.0
            },
            RiskLevel.MODERATE: {
                "max_risk_per_trade": 0.02,  # 2%
                "max_portfolio_risk": 0.10,  # 10%
                "max_correlation": 0.8,
                "max_position_size": 0.15,  # 15%
                "min_risk_reward": 1.5
            },
            RiskLevel.AGGRESSIVE: {
                "max_risk_per_trade": 0.03,  # 3%
                "max_portfolio_risk": 0.15,  # 15%
                "max_correlation": 0.9,
                "max_position_size": 0.25,  # 25%
                "min_risk_reward": 1.2
            },
            RiskLevel.VERY_AGGRESSIVE: {
                "max_risk_per_trade": 0.05,  # 5%
                "max_portfolio_risk": 0.25,  # 25%
                "max_correlation": 1.0,
                "max_position_size": 0.40,  # 40%
                "min_risk_reward": 1.0
            }
        }
    
    def calculate_position_size(self, symbol: str, account_balance: float, 
                              entry_price: float, stop_loss: float, 
                              risk_level: RiskLevel = RiskLevel.MODERATE,
                              take_profit: Optional[float] = None) -> PositionSize:
        """Calculate optimal position size based on risk management rules"""
        try:
            # Get risk parameters
            risk_params = self.risk_parameters[risk_level]
            max_risk_per_trade = risk_params["max_risk_per_trade"]
            max_position_size = risk_params["max_position_size"]
            min_risk_reward = risk_params["min_risk_reward"]
            
            # Calculate risk per trade
            risk_per_trade = account_balance * max_risk_per_trade
            
            # Calculate position size based on stop loss
            price_risk = abs(entry_price - stop_loss)
            if price_risk <= 0:
                raise ValueError("Invalid stop loss price")
            
            position_size = risk_per_trade / price_risk
            
            # Calculate position value
            position_value = position_size * entry_price
            
            # Check maximum position size
            max_position_value = account_balance * max_position_size
            if position_value > max_position_value:
                position_size = max_position_value / entry_price
                position_value = max_position_value
                risk_per_trade = position_size * price_risk
            
            # Calculate risk metrics
            risk_amount = position_size * price_risk
            risk_percentage = (risk_amount / account_balance) * 100
            
            # Calculate potential gains/losses
            max_loss = risk_amount
            if take_profit:
                max_gain = position_size * abs(take_profit - entry_price)
                risk_reward_ratio = max_gain / max_loss if max_loss > 0 else 0
            else:
                max_gain = 0
                risk_reward_ratio = 0
            
            # Check minimum risk-reward ratio
            if take_profit and risk_reward_ratio < min_risk_reward:
                # Adjust position size to meet minimum risk-reward ratio
                adjusted_gain = max_loss * min_risk_reward
                adjusted_take_profit = entry_price + (adjusted_gain / position_size)
                max_gain = adjusted_gain
                risk_reward_ratio = min_risk_reward
            
            # Calculate recommended size (conservative approach)
            recommended_size = position_size * 0.8  # 80% of calculated size
            
            return PositionSize(
                symbol=symbol,
                account_balance=account_balance,
                risk_per_trade=risk_per_trade,
                entry_price=entry_price,
                stop_loss=stop_loss,
                position_size=position_size,
                position_value=position_value,
                risk_amount=risk_amount,
                risk_percentage=risk_percentage,
                max_loss=max_loss,
                max_gain=max_gain,
                risk_reward_ratio=risk_reward_ratio,
                recommended_size=recommended_size,
                risk_level=risk_level
            )
            
        except Exception as e:
            log.error(f"Position size calculation failed: {e}")
            return None
    
    def calculate_kelly_criterion(self, win_rate: float, avg_win: float, 
                                avg_loss: float, account_balance: float) -> float:
        """Calculate Kelly Criterion for optimal position sizing"""
        try:
            if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
                return 0
            
            # Kelly formula: f = (bp - q) / b
            # where b = avg_win/avg_loss, p = win_rate, q = 1 - win_rate
            b = avg_win / avg_loss
            p = win_rate
            q = 1 - win_rate
            
            kelly_fraction = (b * p - q) / b
            
            # Apply Kelly fraction with safety factor (typically 0.25 of Kelly)
            safe_kelly = kelly_fraction * 0.25
            
            # Convert to position size
            position_size = account_balance * safe_kelly
            
            return max(0, min(position_size, account_balance * 0.1))  # Cap at 10%
            
        except Exception as e:
            log.error(f"Kelly Criterion calculation failed: {e}")
            return 0
    
    def calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk (VaR)"""
        try:
            if not returns:
                return 0
            
            # Sort returns
            sorted_returns = sorted(returns)
            
            # Calculate VaR
            index = int((1 - confidence_level) * len(sorted_returns))
            var = -sorted_returns[index] if index < len(sorted_returns) else 0
            
            return var
            
        except Exception as e:
            log.error(f"VaR calculation failed: {e}")
            return 0
    
    def calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calculate maximum drawdown"""
        try:
            if not portfolio_values:
                return 0
            
            max_drawdown = 0
            peak = portfolio_values[0]
            
            for value in portfolio_values:
                if value > peak:
                    peak = value
                else:
                    drawdown = (peak - value) / peak
                    max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
            
        except Exception as e:
            log.error(f"Max drawdown calculation failed: {e}")
            return 0
    
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        try:
            if not returns or len(returns) < 2:
                return 0
            
            # Calculate average return
            avg_return = sum(returns) / len(returns)
            
            # Calculate standard deviation
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_dev = math.sqrt(variance)
            
            if std_dev == 0:
                return 0
            
            # Calculate Sharpe ratio
            sharpe_ratio = (avg_return - risk_free_rate) / std_dev
            
            return sharpe_ratio
            
        except Exception as e:
            log.error(f"Sharpe ratio calculation failed: {e}")
            return 0
    
    def calculate_correlation_risk(self, positions: List[Dict[str, Any]]) -> float:
        """Calculate correlation risk between positions"""
        try:
            if len(positions) < 2:
                return 0
            
            # Simplified correlation calculation
            # In practice, this would use actual price correlation data
            symbols = [pos.get("symbol", "") for pos in positions]
            
            # Check for same asset class (crypto vs forex)
            crypto_count = sum(1 for s in symbols if s.upper() in ['BTC', 'ETH', 'ADA', 'SOL', 'MATIC'])
            forex_count = len(symbols) - crypto_count
            
            # High correlation if all same asset class
            if crypto_count == len(symbols) or forex_count == len(symbols):
                return 0.8
            elif crypto_count > 0 and forex_count > 0:
                return 0.3
            else:
                return 0.5
                
        except Exception as e:
            log.error(f"Correlation risk calculation failed: {e}")
            return 0
    
    def calculate_concentration_risk(self, positions: List[Dict[str, Any]], 
                                   total_portfolio_value: float) -> float:
        """Calculate concentration risk"""
        try:
            if not positions or total_portfolio_value <= 0:
                return 0
            
            # Calculate concentration risk based on position sizes
            position_values = [pos.get("value", 0) for pos in positions]
            max_position_value = max(position_values) if position_values else 0
            
            concentration_risk = max_position_value / total_portfolio_value
            
            return concentration_risk
            
        except Exception as e:
            log.error(f"Concentration risk calculation failed: {e}")
            return 0
    
    def calculate_liquidity_risk(self, symbol: str, position_size: float) -> float:
        """Calculate liquidity risk for a position"""
        try:
            # Simplified liquidity risk calculation
            # In practice, this would use actual market depth data
            
            # Large positions in smaller market cap assets have higher liquidity risk
            if symbol.upper() in ['BTC', 'ETH']:
                # High liquidity
                if position_size < 1000000:  # < $1M
                    return 0.1
                elif position_size < 10000000:  # < $10M
                    return 0.3
                else:
                    return 0.5
            elif symbol.upper() in ['ADA', 'SOL', 'MATIC']:
                # Medium liquidity
                if position_size < 500000:  # < $500K
                    return 0.2
                elif position_size < 5000000:  # < $5M
                    return 0.4
                else:
                    return 0.7
            else:
                # Lower liquidity
                if position_size < 100000:  # < $100K
                    return 0.3
                elif position_size < 1000000:  # < $1M
                    return 0.6
                else:
                    return 0.9
                    
        except Exception as e:
            log.error(f"Liquidity risk calculation failed: {e}")
            return 0.5
    
    async def calculate_portfolio_risk_metrics(self, positions: List[Dict[str, Any]], 
                                             portfolio_value: float) -> RiskMetrics:
        """Calculate comprehensive portfolio risk metrics"""
        try:
            # Calculate individual risk metrics
            total_risk = sum(pos.get("risk_amount", 0) for pos in positions)
            max_drawdown = self.calculate_max_drawdown([pos.get("value", 0) for pos in positions])
            
            # Calculate VaR
            returns = [pos.get("return", 0) for pos in positions if pos.get("return") is not None]
            var_95 = self.calculate_var(returns, 0.95)
            var_99 = self.calculate_var(returns, 0.99)
            
            # Calculate Sharpe ratio
            sharpe_ratio = self.calculate_sharpe_ratio(returns)
            
            # Calculate correlation risk
            correlation_risk = self.calculate_correlation_risk(positions)
            
            # Calculate concentration risk
            concentration_risk = self.calculate_concentration_risk(positions, portfolio_value)
            
            # Calculate liquidity risk
            liquidity_risks = []
            for pos in positions:
                symbol = pos.get("symbol", "")
                position_size = pos.get("value", 0)
                liquidity_risk = self.calculate_liquidity_risk(symbol, position_size)
                liquidity_risks.append(liquidity_risk)
            
            avg_liquidity_risk = sum(liquidity_risks) / len(liquidity_risks) if liquidity_risks else 0
            
            # Calculate current drawdown
            current_value = sum(pos.get("value", 0) for pos in positions)
            peak_value = max([pos.get("peak_value", current_value) for pos in positions])
            current_drawdown = (peak_value - current_value) / peak_value if peak_value > 0 else 0
            
            # Calculate maximum position size
            max_position_size = max([pos.get("value", 0) for pos in positions]) if positions else 0
            
            return RiskMetrics(
                portfolio_value=portfolio_value,
                total_risk=total_risk,
                max_drawdown=max_drawdown,
                current_drawdown=current_drawdown,
                sharpe_ratio=sharpe_ratio,
                var_95=var_95,
                var_99=var_99,
                max_position_size=max_position_size,
                correlation_risk=correlation_risk,
                concentration_risk=concentration_risk,
                liquidity_risk=avg_liquidity_risk
            )
            
        except Exception as e:
            log.error(f"Portfolio risk metrics calculation failed: {e}")
            return None
    
    def generate_risk_report(self, risk_metrics: RiskMetrics, 
                           risk_level: RiskLevel = RiskLevel.MODERATE) -> Dict[str, Any]:
        """Generate comprehensive risk report"""
        try:
            if not risk_metrics:
                return {"error": "No risk metrics available"}
            
            # Get risk parameters
            risk_params = self.risk_parameters[risk_level]
            
            # Risk assessment
            risk_assessment = self._assess_risk_level(risk_metrics, risk_params)
            
            # Generate recommendations
            recommendations = self._generate_risk_recommendations(risk_metrics, risk_params)
            
            # Calculate risk score (0-100, lower is better)
            risk_score = self._calculate_risk_score(risk_metrics, risk_params)
            
            return {
                "risk_score": risk_score,
                "risk_level": risk_level.value,
                "risk_assessment": risk_assessment,
                "recommendations": recommendations,
                "metrics": {
                    "portfolio_value": risk_metrics.portfolio_value,
                    "total_risk": risk_metrics.total_risk,
                    "max_drawdown": risk_metrics.max_drawdown,
                    "current_drawdown": risk_metrics.current_drawdown,
                    "sharpe_ratio": risk_metrics.sharpe_ratio,
                    "var_95": risk_metrics.var_95,
                    "var_99": risk_metrics.var_99,
                    "correlation_risk": risk_metrics.correlation_risk,
                    "concentration_risk": risk_metrics.concentration_risk,
                    "liquidity_risk": risk_metrics.liquidity_risk
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            log.error(f"Risk report generation failed: {e}")
            return {"error": str(e)}
    
    def _assess_risk_level(self, risk_metrics: RiskMetrics, risk_params: Dict[str, float]) -> Dict[str, Any]:
        """Assess current risk level"""
        try:
            issues = []
            warnings = []
            
            # Check drawdown
            if risk_metrics.max_drawdown > 0.2:  # 20%
                issues.append("High maximum drawdown detected")
            elif risk_metrics.max_drawdown > 0.1:  # 10%
                warnings.append("Moderate drawdown level")
            
            # Check current drawdown
            if risk_metrics.current_drawdown > 0.15:  # 15%
                issues.append("High current drawdown")
            elif risk_metrics.current_drawdown > 0.05:  # 5%
                warnings.append("Moderate current drawdown")
            
            # Check concentration risk
            if risk_metrics.concentration_risk > 0.3:  # 30%
                issues.append("High concentration risk")
            elif risk_metrics.concentration_risk > 0.2:  # 20%
                warnings.append("Moderate concentration risk")
            
            # Check correlation risk
            if risk_metrics.correlation_risk > 0.8:
                issues.append("High correlation risk")
            elif risk_metrics.correlation_risk > 0.6:
                warnings.append("Moderate correlation risk")
            
            # Check liquidity risk
            if risk_metrics.liquidity_risk > 0.7:
                issues.append("High liquidity risk")
            elif risk_metrics.liquidity_risk > 0.5:
                warnings.append("Moderate liquidity risk")
            
            # Check Sharpe ratio
            if risk_metrics.sharpe_ratio < 0:
                issues.append("Negative Sharpe ratio - poor risk-adjusted returns")
            elif risk_metrics.sharpe_ratio < 1:
                warnings.append("Low Sharpe ratio - consider improving risk-adjusted returns")
            
            return {
                "status": "Critical" if issues else "Warning" if warnings else "Good",
                "issues": issues,
                "warnings": warnings
            }
            
        except Exception as e:
            log.error(f"Risk assessment failed: {e}")
            return {"status": "Unknown", "issues": [], "warnings": []}
    
    def _generate_risk_recommendations(self, risk_metrics: RiskMetrics, 
                                     risk_params: Dict[str, float]) -> List[str]:
        """Generate risk management recommendations"""
        try:
            recommendations = []
            
            # Drawdown recommendations
            if risk_metrics.max_drawdown > 0.2:
                recommendations.append("Reduce position sizes to limit maximum drawdown")
                recommendations.append("Implement stricter stop-loss levels")
            
            # Concentration recommendations
            if risk_metrics.concentration_risk > 0.3:
                recommendations.append("Diversify portfolio across more assets")
                recommendations.append("Reduce largest position size")
            
            # Correlation recommendations
            if risk_metrics.correlation_risk > 0.8:
                recommendations.append("Add uncorrelated assets to portfolio")
                recommendations.append("Consider different asset classes")
            
            # Liquidity recommendations
            if risk_metrics.liquidity_risk > 0.7:
                recommendations.append("Reduce position sizes in illiquid assets")
                recommendations.append("Focus on more liquid markets")
            
            # Sharpe ratio recommendations
            if risk_metrics.sharpe_ratio < 1:
                recommendations.append("Improve risk-adjusted returns")
                recommendations.append("Review position sizing methodology")
            
            # General recommendations
            if not recommendations:
                recommendations.append("Portfolio risk levels are acceptable")
                recommendations.append("Continue monitoring risk metrics")
            
            return recommendations
            
        except Exception as e:
            log.error(f"Recommendation generation failed: {e}")
            return ["Unable to generate recommendations"]
    
    def _calculate_risk_score(self, risk_metrics: RiskMetrics, 
                            risk_params: Dict[str, float]) -> float:
        """Calculate overall risk score (0-100, lower is better)"""
        try:
            score = 0
            
            # Drawdown score (0-30 points)
            drawdown_score = min(risk_metrics.max_drawdown * 150, 30)
            score += drawdown_score
            
            # Current drawdown score (0-20 points)
            current_drawdown_score = min(risk_metrics.current_drawdown * 200, 20)
            score += current_drawdown_score
            
            # Concentration risk score (0-20 points)
            concentration_score = min(risk_metrics.concentration_risk * 50, 20)
            score += concentration_score
            
            # Correlation risk score (0-15 points)
            correlation_score = min(risk_metrics.correlation_risk * 20, 15)
            score += correlation_score
            
            # Liquidity risk score (0-15 points)
            liquidity_score = min(risk_metrics.liquidity_risk * 20, 15)
            score += liquidity_score
            
            return min(score, 100)
            
        except Exception as e:
            log.error(f"Risk score calculation failed: {e}")
            return 50  # Default moderate risk score
