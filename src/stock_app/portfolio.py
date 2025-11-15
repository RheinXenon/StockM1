"""
持仓管理模块
"""
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    name: str
    quantity: int
    avg_cost: float
    current_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        """市值"""
        return self.quantity * self.current_price
    
    @property
    def cost_value(self) -> float:
        """成本"""
        return self.quantity * self.avg_cost
    
    @property
    def profit(self) -> float:
        """盈亏金额"""
        return self.market_value - self.cost_value
    
    @property
    def profit_rate(self) -> float:
        """盈亏比例"""
        if self.cost_value == 0:
            return 0.0
        return (self.profit / self.cost_value) * 100


class Portfolio:
    """投资组合管理"""
    
    def __init__(self, account_name: str, initial_capital: float):
        self.account_name = account_name
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.current_date = None
    
    def add_position(self, symbol: str, name: str, quantity: int, price: float):
        """添加持仓"""
        if symbol in self.positions:
            # 更新持仓
            pos = self.positions[symbol]
            total_cost = pos.cost_value + (quantity * price)
            total_quantity = pos.quantity + quantity
            pos.avg_cost = total_cost / total_quantity
            pos.quantity = total_quantity
        else:
            # 新建持仓
            self.positions[symbol] = Position(
                symbol=symbol,
                name=name,
                quantity=quantity,
                avg_cost=price,
                current_price=price
            )
    
    def reduce_position(self, symbol: str, quantity: int) -> bool:
        """减少持仓"""
        if symbol not in self.positions:
            return False
        
        pos = self.positions[symbol]
        if pos.quantity < quantity:
            return False
        
        pos.quantity -= quantity
        if pos.quantity == 0:
            del self.positions[symbol]
        
        return True
    
    def update_price(self, symbol: str, price: float):
        """更新持仓价格"""
        if symbol in self.positions:
            self.positions[symbol].current_price = price
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(symbol)
    
    @property
    def total_market_value(self) -> float:
        """总市值"""
        return sum(pos.market_value for pos in self.positions.values())
    
    @property
    def total_asset(self) -> float:
        """总资产"""
        return self.cash + self.total_market_value
    
    @property
    def total_profit(self) -> float:
        """总盈亏"""
        return self.total_asset - self.initial_capital
    
    @property
    def total_profit_rate(self) -> float:
        """总盈亏比例"""
        if self.initial_capital == 0:
            return 0.0
        return (self.total_profit / self.initial_capital) * 100
    
    def get_summary(self) -> dict:
        """获取账户摘要"""
        return {
            'account_name': self.account_name,
            'current_date': self.current_date,
            'initial_capital': self.initial_capital,
            'cash': self.cash,
            'market_value': self.total_market_value,
            'total_asset': self.total_asset,
            'total_profit': self.total_profit,
            'total_profit_rate': self.total_profit_rate,
            'position_count': len(self.positions)
        }
