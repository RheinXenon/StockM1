"""
交易模拟引擎 - 控制时间循环和交易执行
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

from src.stock_app.portfolio import Portfolio, Position
from .data_provider import MarketDataProvider
from .tools import TradingTools


class TradingSimulator:
    """交易模拟器"""
    
    def __init__(self, 
                 agent: Any,
                 stock_pool: List[str],
                 initial_capital: float,
                 start_date: str,
                 end_date: str,
                 db_path: str = None):
        """
        初始化模拟器
        
        Args:
            agent: 交易Agent实例
            stock_pool: 股票池
            initial_capital: 初始资金
            start_date: 开始日期
            end_date: 结束日期
            db_path: 数据库路径
        """
        self.agent = agent
        self.stock_pool = stock_pool
        self.initial_capital = initial_capital
        self.start_date = start_date
        self.end_date = end_date
        
        # 初始化数据提供者和工具
        self.data_provider = MarketDataProvider(db_path)
        self.tools = TradingTools(self.data_provider, stock_pool)
        
        # 初始化投资组合
        self.portfolio = Portfolio(f"Agent_{agent.agent_id}", initial_capital)
        self.portfolio.current_date = start_date
        
        # 交易记录
        self.trade_log = []
        self.daily_snapshots = []
        
        # 交易成本配置
        self.commission_rate = 0.0003
        self.stamp_tax_rate = 0.001
        self.min_commission = 5
    
    def run(self) -> Dict[str, Any]:
        """
        运行模拟
        
        Returns:
            模拟结果统计
        """
        print(f"\n{'='*60}")
        print(f"开始运行Agent交易模拟")
        print(f"Agent: {self.agent.name}")
        print(f"时间范围: {self.start_date} 至 {self.end_date}")
        print(f"初始资金: {self.initial_capital:,.2f} 元")
        print(f"股票池: {', '.join(self.stock_pool)}")
        print(f"{'='*60}\n")
        
        # 获取所有交易日
        trading_dates = self._get_trading_dates()
        
        if not trading_dates:
            print("错误：未找到交易日数据")
            return {}
        
        print(f"共 {len(trading_dates)} 个交易日\n")
        
        # 逐日模拟
        for i, current_date in enumerate(trading_dates, 1):
            print(f"\n[{i}/{len(trading_dates)}] {current_date}")
            print("-" * 60)
            
            # 更新持仓价格
            self._update_portfolio_prices(current_date)
            
            # Agent做决策
            decision = self._agent_decide(current_date)
            
            if decision and decision.get('success'):
                # 执行交易动作
                self._execute_actions(current_date, decision['actions'])
                
                # 打印决策
                print(f"\n决策分析: {decision.get('analysis', '')[:200]}")
                print(f"决策理由: {decision.get('reasoning', '')[:200]}")
            else:
                print(f"决策失败: {decision.get('reasoning', '未知错误')}")
            
            # 记录每日快照
            self._take_snapshot(current_date)
            
            # 打印账户状态
            self._print_portfolio_summary()
        
        # 生成最终报告
        return self._generate_report()
    
    def _get_trading_dates(self) -> List[str]:
        """获取交易日列表"""
        # 使用股票池中的第一只股票获取交易日
        dates = self.data_provider.db.get_available_dates(self.stock_pool[0])
        
        # 过滤日期范围
        start_dt = datetime.strptime(self.start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(self.end_date, '%Y-%m-%d')
        
        trading_dates = []
        for date_str in dates:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            if start_dt <= dt <= end_dt:
                trading_dates.append(date_str)
        
        return trading_dates
    
    def _update_portfolio_prices(self, current_date: str):
        """更新持仓价格"""
        for symbol in list(self.portfolio.positions.keys()):
            price_info = self.data_provider.get_stock_price_on_date(symbol, current_date)
            if price_info:
                self.portfolio.update_price(symbol, price_info['close'])
        
        self.portfolio.current_date = current_date
    
    def _agent_decide(self, current_date: str) -> Dict:
        """Agent做决策"""
        # 准备账户信息
        summary = self.portfolio.get_summary()
        
        portfolio_info = {
            'cash': summary['cash'],
            'market_value': summary['market_value'],
            'total_asset': summary['total_asset'],
            'total_profit_rate': summary['total_profit_rate'],
            'positions': {symbol: {
                'quantity': pos.quantity,
                'avg_cost': pos.avg_cost,
                'current_price': pos.current_price,
                'profit_rate': pos.profit_rate
            } for symbol, pos in self.portfolio.positions.items()}
        }
        
        # 调用Agent决策
        try:
            decision = self.agent.make_decision(
                current_date=current_date,
                portfolio_info=portfolio_info,
                tools=self.tools,
                context={'portfolio': self.portfolio}
            )
            return decision
        except Exception as e:
            print(f"Agent决策异常: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'reasoning': str(e), 'actions': []}
    
    def _execute_actions(self, current_date: str, actions: List[Dict]):
        """执行交易动作"""
        for action in actions:
            action_type = action.get('type')
            symbol = action.get('symbol')
            quantity = action.get('quantity')
            
            if action_type == 'buy':
                success = self._execute_buy(current_date, symbol, quantity)
                if success:
                    print(f"✓ 买入: {symbol} {quantity}股")
                else:
                    print(f"✗ 买入失败: {symbol}")
            
            elif action_type == 'sell':
                success = self._execute_sell(current_date, symbol, quantity)
                if success:
                    print(f"✓ 卖出: {symbol} {quantity}股")
                else:
                    print(f"✗ 卖出失败: {symbol}")
    
    def _execute_buy(self, date: str, symbol: str, quantity: int) -> bool:
        """执行买入"""
        try:
            # 获取价格
            price_info = self.data_provider.get_stock_price_on_date(symbol, date)
            if not price_info:
                return False
            
            price = price_info['close']
            
            # 获取股票名称
            stock_info = self.data_provider.get_stock_info(symbol)
            stock_name = stock_info['name'] if stock_info else symbol
            
            # 计算成本
            trade_amount = price * quantity
            commission = max(trade_amount * self.commission_rate, self.min_commission)
            total_cost = trade_amount + commission
            
            # 检查资金
            if self.portfolio.cash < total_cost:
                return False
            
            # 执行交易
            self.portfolio.cash -= total_cost
            self.portfolio.add_position(symbol, stock_name, quantity, price)
            
            # 记录交易
            self.trade_log.append({
                'date': date,
                'type': 'buy',
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'commission': commission,
                'total': total_cost
            })
            
            return True
        except Exception as e:
            print(f"买入异常: {e}")
            return False
    
    def _execute_sell(self, date: str, symbol: str, quantity: int) -> bool:
        """执行卖出"""
        try:
            # 检查持仓
            position = self.portfolio.get_position(symbol)
            if not position or position.quantity < quantity:
                return False
            
            # 获取价格
            price_info = self.data_provider.get_stock_price_on_date(symbol, date)
            if not price_info:
                return False
            
            price = price_info['close']
            
            # 计算收入
            trade_amount = price * quantity
            commission = max(trade_amount * self.commission_rate, self.min_commission)
            stamp_tax = trade_amount * self.stamp_tax_rate
            total_revenue = trade_amount - commission - stamp_tax
            
            # 执行交易
            self.portfolio.cash += total_revenue
            self.portfolio.reduce_position(symbol, quantity)
            
            # 记录交易
            self.trade_log.append({
                'date': date,
                'type': 'sell',
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'commission': commission,
                'stamp_tax': stamp_tax,
                'total': total_revenue
            })
            
            return True
        except Exception as e:
            print(f"卖出异常: {e}")
            return False
    
    def _take_snapshot(self, date: str):
        """记录每日快照"""
        summary = self.portfolio.get_summary()
        
        self.daily_snapshots.append({
            'date': date,
            'cash': summary['cash'],
            'market_value': summary['market_value'],
            'total_asset': summary['total_asset'],
            'profit': summary['total_profit'],
            'profit_rate': summary['total_profit_rate']
        })
    
    def _print_portfolio_summary(self):
        """打印账户摘要"""
        summary = self.portfolio.get_summary()
        print(f"\n账户状态: 现金 {summary['cash']:,.2f} | "
              f"市值 {summary['market_value']:,.2f} | "
              f"总资产 {summary['total_asset']:,.2f} | "
              f"收益率 {summary['total_profit_rate']:.2f}%")
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成最终报告"""
        print(f"\n{'='*60}")
        print("模拟完成！生成报告...")
        print(f"{'='*60}\n")
        
        final_summary = self.portfolio.get_summary()
        
        # 计算统计指标
        if self.daily_snapshots:
            profit_rates = [s['profit_rate'] for s in self.daily_snapshots]
            max_profit_rate = max(profit_rates)
            min_profit_rate = min(profit_rates)
            
            # 计算最大回撤
            max_drawdown = 0
            peak = self.daily_snapshots[0]['total_asset']
            for snapshot in self.daily_snapshots:
                asset = snapshot['total_asset']
                if asset > peak:
                    peak = asset
                drawdown = (peak - asset) / peak * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        else:
            max_profit_rate = 0
            min_profit_rate = 0
            max_drawdown = 0
        
        report = {
            'agent_name': self.agent.name,
            'period': f"{self.start_date} 至 {self.end_date}",
            'trading_days': len(self.daily_snapshots),
            'initial_capital': self.initial_capital,
            'final_asset': final_summary['total_asset'],
            'total_profit': final_summary['total_profit'],
            'total_return': final_summary['total_profit_rate'],
            'max_return': max_profit_rate,
            'min_return': min_profit_rate,
            'max_drawdown': max_drawdown,
            'total_trades': len(self.trade_log),
            'buy_trades': len([t for t in self.trade_log if t['type'] == 'buy']),
            'sell_trades': len([t for t in self.trade_log if t['type'] == 'sell']),
            'final_positions': [
                {
                    'symbol': pos.symbol,
                    'name': pos.name,
                    'quantity': pos.quantity,
                    'profit_rate': pos.profit_rate
                } for pos in self.portfolio.positions.values()
            ],
            'daily_snapshots': self.daily_snapshots,
            'trade_log': self.trade_log
        }
        
        # 打印报告
        print("=" * 60)
        print(f"Agent: {report['agent_name']}")
        print(f"时间周期: {report['period']}")
        print(f"交易天数: {report['trading_days']} 天")
        print("-" * 60)
        print(f"初始资金: {report['initial_capital']:,.2f} 元")
        print(f"最终资产: {report['final_asset']:,.2f} 元")
        print(f"总收益: {report['total_profit']:,.2f} 元")
        print(f"收益率: {report['total_return']:.2f}%")
        print(f"最大收益率: {report['max_return']:.2f}%")
        print(f"最大回撤: {report['max_drawdown']:.2f}%")
        print("-" * 60)
        print(f"总交易次数: {report['total_trades']} 次")
        print(f"买入: {report['buy_trades']} 次")
        print(f"卖出: {report['sell_trades']} 次")
        
        if report['final_positions']:
            print("\n最终持仓:")
            for pos in report['final_positions']:
                print(f"  {pos['symbol']} {pos['name']}: {pos['quantity']}股 (收益率: {pos['profit_rate']:.2f}%)")
        
        print("=" * 60)
        
        return report
