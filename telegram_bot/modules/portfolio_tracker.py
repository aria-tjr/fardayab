from __future__ import annotations

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

import httpx
from telegram_bot.config.settings import Settings

log = logging.getLogger(__name__)


@dataclass
class Position:
    """Trading position data structure"""
    symbol: str
    side: str  # 'long' or 'short'
    quantity: float
    entry_price: float
    current_price: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: str = ""
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L"""
        if self.side == "long":
            return (self.current_price - self.entry_price) * self.quantity
        else:  # short
            return (self.entry_price - self.current_price) * self.quantity
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """Calculate unrealized P&L percentage"""
        if self.side == "long":
            return ((self.current_price - self.entry_price) / self.entry_price) * 100
        else:  # short
            return ((self.entry_price - self.current_price) / self.entry_price) * 100
    
    @property
    def is_profitable(self) -> bool:
        """Check if position is profitable"""
        return self.unrealized_pnl > 0
    
    @property
    def risk_reward_ratio(self) -> Optional[float]:
        """Calculate risk-reward ratio"""
        if not self.stop_loss or not self.take_profit:
            return None
        
        if self.side == "long":
            risk = self.entry_price - self.stop_loss
            reward = self.take_profit - self.entry_price
        else:  # short
            risk = self.stop_loss - self.entry_price
            reward = self.entry_price - self.take_profit
        
        if risk <= 0:
            return None
        
        return reward / risk


@dataclass
class Trade:
    """Completed trade data structure"""
    symbol: str
    side: str  # 'long' or 'short'
    quantity: float
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    pnl_percent: float
    fees: float = 0.0
    notes: str = ""


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""
    total_value: float
    total_pnl: float
    total_pnl_percent: float
    daily_pnl: float
    daily_pnl_percent: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float


class AdvancedPortfolioTracker:
    """Advanced portfolio tracking and analysis"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.timeout = settings.HTTP_TIMEOUT
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.portfolio_history: List[Dict[str, Any]] = []
        
    async def add_position(self, symbol: str, side: str, quantity: float, 
                          entry_price: float, stop_loss: Optional[float] = None,
                          take_profit: Optional[float] = None, notes: str = "") -> bool:
        """Add a new position to the portfolio"""
        try:
            # Get current price
            current_price = await self._get_current_price(symbol)
            if not current_price:
                log.error(f"Could not get current price for {symbol}")
                return False
            
            position_id = f"{symbol}_{side}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            position = Position(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                current_price=current_price,
                entry_time=datetime.now(),
                stop_loss=stop_loss,
                take_profit=take_profit,
                notes=notes
            )
            
            self.positions[position_id] = position
            await self._save_portfolio()
            
            log.info(f"Added position: {symbol} {side} {quantity} @ {entry_price}")
            return True
            
        except Exception as e:
            log.error(f"Failed to add position: {e}")
            return False
    
    async def close_position(self, position_id: str, exit_price: Optional[float] = None, 
                           notes: str = "") -> bool:
        """Close a position and record the trade"""
        try:
            if position_id not in self.positions:
                log.error(f"Position {position_id} not found")
                return False
            
            position = self.positions[position_id]
            
            # Get current price if not provided
            if exit_price is None:
                exit_price = await self._get_current_price(position.symbol)
                if not exit_price:
                    log.error(f"Could not get current price for {position.symbol}")
                    return False
            
            # Calculate P&L
            if position.side == "long":
                pnl = (exit_price - position.entry_price) * position.quantity
            else:  # short
                pnl = (position.entry_price - exit_price) * position.quantity
            
            pnl_percent = (pnl / (position.entry_price * position.quantity)) * 100
            
            # Create trade record
            trade = Trade(
                symbol=position.symbol,
                side=position.side,
                quantity=position.quantity,
                entry_price=position.entry_price,
                exit_price=exit_price,
                entry_time=position.entry_time,
                exit_time=datetime.now(),
                pnl=pnl,
                pnl_percent=pnl_percent,
                notes=notes
            )
            
            self.trades.append(trade)
            del self.positions[position_id]
            await self._save_portfolio()
            
            log.info(f"Closed position: {position.symbol} P&L: {pnl:.2f} ({pnl_percent:.2f}%)")
            return True
            
        except Exception as e:
            log.error(f"Failed to close position: {e}")
            return False
    
    async def update_positions(self) -> Dict[str, Any]:
        """Update all positions with current prices"""
        try:
            updated_count = 0
            total_unrealized_pnl = 0.0
            total_value = 0.0
        
            for position_id, position in self.positions.items():
                current_price = await self._get_current_price(position.symbol)
                if current_price:
                    position.current_price = current_price
                    updated_count += 1
                    
                    # Calculate portfolio metrics
                    position_value = position.current_price * position.quantity
                    total_value += position_value
                    total_unrealized_pnl += position.unrealized_pnl
            
            await self._save_portfolio()
            
            return {
                "updated_positions": updated_count,
                "total_positions": len(self.positions),
                "total_value": total_value,
                "total_unrealized_pnl": total_unrealized_pnl,
                "unrealized_pnl_percent": (total_unrealized_pnl / total_value * 100) if total_value > 0 else 0
            }
            
        except Exception as e:
            log.error(f"Failed to update positions: {e}")
            return {"error": str(e)}
    
    def calculate_portfolio_metrics(self) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics"""
        try:
            # Current positions metrics
            total_value = sum(pos.current_price * pos.quantity for pos in self.positions.values())
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            
            # Trade history metrics
            if not self.trades:
                return PortfolioMetrics(
                    total_value=total_value,
                    total_pnl=total_unrealized_pnl,
                    total_pnl_percent=0,
                    daily_pnl=0,
                    daily_pnl_percent=0,
                    win_rate=0,
                    profit_factor=0,
                    sharpe_ratio=0,
                    max_drawdown=0,
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    avg_win=0,
                    avg_loss=0,
                    largest_win=0,
                    largest_loss=0
                )
            
            # Calculate realized P&L
            realized_pnl = sum(trade.pnl for trade in self.trades)
            total_pnl = realized_pnl + total_unrealized_pnl
            
            # Win rate
            winning_trades = [trade for trade in self.trades if trade.pnl > 0]
            losing_trades = [trade for trade in self.trades if trade.pnl < 0]
            win_rate = (len(winning_trades) / len(self.trades)) * 100 if self.trades else 0
            
            # Profit factor
            total_wins = sum(trade.pnl for trade in winning_trades)
            total_losses = abs(sum(trade.pnl for trade in losing_trades))
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            # Average win/loss
            avg_win = total_wins / len(winning_trades) if winning_trades else 0
            avg_loss = total_losses / len(losing_trades) if losing_trades else 0
            
            # Largest win/loss
            largest_win = max(trade.pnl for trade in winning_trades) if winning_trades else 0
            largest_loss = min(trade.pnl for trade in losing_trades) if losing_trades else 0
            
            # Daily P&L (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            recent_trades = [trade for trade in self.trades if trade.exit_time >= yesterday]
            daily_pnl = sum(trade.pnl for trade in recent_trades)
            
            # Sharpe ratio (simplified)
            if len(self.trades) > 1:
                returns = [trade.pnl_percent for trade in self.trades]
                avg_return = sum(returns) / len(returns)
                variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
                std_dev = variance ** 0.5
                sharpe_ratio = avg_return / std_dev if std_dev > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Max drawdown (simplified)
            cumulative_pnl = 0
            max_pnl = 0
            max_drawdown = 0
            
            for trade in self.trades:
                cumulative_pnl += trade.pnl
                max_pnl = max(max_pnl, cumulative_pnl)
                drawdown = max_pnl - cumulative_pnl
                max_drawdown = max(max_drawdown, drawdown)
            
            return PortfolioMetrics(
                total_value=total_value,
                total_pnl=total_pnl,
                total_pnl_percent=(total_pnl / total_value * 100) if total_value > 0 else 0,
                daily_pnl=daily_pnl,
                daily_pnl_percent=(daily_pnl / total_value * 100) if total_value > 0 else 0,
                win_rate=win_rate,
                profit_factor=profit_factor,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                total_trades=len(self.trades),
                winning_trades=len(winning_trades),
                losing_trades=len(losing_trades),
                avg_win=avg_win,
                avg_loss=avg_loss,
                largest_win=largest_win,
                largest_loss=largest_loss
            )
            
        except Exception as e:
            log.error(f"Failed to calculate portfolio metrics: {e}")
            return PortfolioMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        try:
            # Update positions first
            await self.update_positions()
            
            # Calculate metrics
            metrics = self.calculate_portfolio_metrics()
            
            # Position details
            position_details = []
            for position_id, position in self.positions.items():
                position_details.append({
                    "id": position_id,
                    "symbol": position.symbol,
                    "side": position.side,
                    "quantity": position.quantity,
                    "entry_price": position.entry_price,
                    "current_price": position.current_price,
                    "unrealized_pnl": position.unrealized_pnl,
                    "unrealized_pnl_percent": position.unrealized_pnl_percent,
                    "is_profitable": position.is_profitable,
                    "risk_reward_ratio": position.risk_reward_ratio,
                    "entry_time": position.entry_time.isoformat(),
                    "notes": position.notes
                })
            
            # Recent trades
            recent_trades = sorted(self.trades, key=lambda x: x.exit_time, reverse=True)[:10]
            trade_details = []
            for trade in recent_trades:
                trade_details.append({
                    "symbol": trade.symbol,
                    "side": trade.side,
                    "quantity": trade.quantity,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "pnl": trade.pnl,
                    "pnl_percent": trade.pnl_percent,
                    "entry_time": trade.entry_time.isoformat(),
                    "exit_time": trade.exit_time.isoformat(),
                    "notes": trade.notes
                })
            
            return {
                "summary_timestamp": datetime.now().isoformat(),
                "metrics": asdict(metrics),
                "positions": position_details,
                "recent_trades": trade_details,
                "portfolio_health": self._assess_portfolio_health(metrics)
            }
            
        except Exception as e:
            log.error(f"Failed to get portfolio summary: {e}")
            return {"error": str(e)}
    
    def _assess_portfolio_health(self, metrics: PortfolioMetrics) -> Dict[str, Any]:
        """Assess overall portfolio health"""
        health_score = 0
        issues = []
        recommendations = []
        
        # Win rate assessment
        if metrics.win_rate >= 60:
            health_score += 25
        elif metrics.win_rate >= 40:
            health_score += 15
        else:
            health_score += 5
            issues.append("Low win rate")
            recommendations.append("Review trading strategy and risk management")
        
        # Profit factor assessment
        if metrics.profit_factor >= 2.0:
            health_score += 25
        elif metrics.profit_factor >= 1.5:
            health_score += 20
        elif metrics.profit_factor >= 1.0:
            health_score += 10
        else:
            health_score += 0
            issues.append("Low profit factor")
            recommendations.append("Improve trade selection and exit strategies")
        
        # Drawdown assessment
        if metrics.max_drawdown < metrics.total_value * 0.1:  # Less than 10%
            health_score += 25
        elif metrics.max_drawdown < metrics.total_value * 0.2:  # Less than 20%
            health_score += 15
        else:
            health_score += 5
            issues.append("High drawdown")
            recommendations.append("Implement better risk management and position sizing")
        
        # Sharpe ratio assessment
        if metrics.sharpe_ratio >= 1.0:
            health_score += 25
        elif metrics.sharpe_ratio >= 0.5:
            health_score += 15
        else:
            health_score += 5
            issues.append("Low risk-adjusted returns")
            recommendations.append("Optimize risk-reward ratios")
        
        # Overall health status
        if health_score >= 80:
            status = "Excellent"
        elif health_score >= 60:
            status = "Good"
        elif health_score >= 40:
            status = "Fair"
        else:
            status = "Poor"
        
        return {
            "health_score": health_score,
            "status": status,
            "issues": issues,
            "recommendations": recommendations
        }
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if symbol.upper() in ['BTC', 'ETH', 'ADA', 'SOL', 'MATIC', 'DOT', 'LINK', 'UNI', 'AAVE', 'COMP']:
                    # Crypto price from CoinGecko
                    coin_id = self._get_coin_id(symbol)
                    response = await client.get(
                        f"https://api.coingecko.com/api/v3/simple/price",
                        params={"ids": coin_id, "vs_currencies": "usd"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return data.get(coin_id, {}).get("usd")
                else:
                    # Forex price from ExchangeRate.host
                    base = symbol[:3]
                    quote = symbol[3:]
                    response = await client.get(
                        "https://api.exchangerate.host/latest",
                        params={"base": base, "symbols": quote}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return data.get("rates", {}).get(quote)
                        
        except Exception as e:
            log.warning(f"Failed to get price for {symbol}: {e}")
        
        return None
    
    def _get_coin_id(self, symbol: str) -> str:
        """Convert symbol to CoinGecko coin ID"""
        symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'ADA': 'cardano',
            'SOL': 'solana',
            'MATIC': 'matic-network',
            'DOT': 'polkadot',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'AAVE': 'aave',
            'COMP': 'compound-governance-token'
        }
        return symbol_map.get(symbol.upper(), 'bitcoin')
    
    async def _save_portfolio(self):
        """Save portfolio data to file"""
        try:
            portfolio_data = {
                "positions": {k: asdict(v) for k, v in self.positions.items()},
                "trades": [asdict(trade) for trade in self.trades],
                "last_updated": datetime.now().isoformat()
            }
            
            # Convert datetime objects to strings
            for position_data in portfolio_data["positions"].values():
                position_data["entry_time"] = position_data["entry_time"].isoformat()
            
            for trade_data in portfolio_data["trades"]:
                trade_data["entry_time"] = trade_data["entry_time"].isoformat()
                trade_data["exit_time"] = trade_data["exit_time"].isoformat()
            
            with open("data/portfolio.json", "w") as f:
                json.dump(portfolio_data, f, indent=2)
                
        except Exception as e:
            log.error(f"Failed to save portfolio: {e}")
    
    async def load_portfolio(self):
        """Load portfolio data from file"""
        try:
            with open("data/portfolio.json", "r") as f:
                portfolio_data = json.load(f)
            
            # Load positions
            self.positions = {}
            for position_id, position_data in portfolio_data.get("positions", {}).items():
                position_data["entry_time"] = datetime.fromisoformat(position_data["entry_time"])
                self.positions[position_id] = Position(**position_data)
            
            # Load trades
            self.trades = []
            for trade_data in portfolio_data.get("trades", []):
                trade_data["entry_time"] = datetime.fromisoformat(trade_data["entry_time"])
                trade_data["exit_time"] = datetime.fromisoformat(trade_data["exit_time"])
                self.trades.append(Trade(**trade_data))
                
        except FileNotFoundError:
            log.info("No existing portfolio file found, starting fresh")
        except Exception as e:
            log.error(f"Failed to load portfolio: {e}")
