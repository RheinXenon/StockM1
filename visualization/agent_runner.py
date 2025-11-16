"""
AI Agent实时运行控制器
支持运行、暂停、终止，并提供实时状态更新
"""
import sys
import os
import threading
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from queue import Queue

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Agents_Experience.agents.qwen_agent import QwenAgent
from Agents_Experience.core.simulator import TradingSimulator
from Agents_Experience.core.data_provider import MarketDataProvider
from Agents_Experience.core.tools import TradingTools
from src.stock_app.portfolio import Portfolio


class AgentRunner:
    """Agent运行控制器"""
    
    def __init__(self, config: Dict[str, Any], db_path: str):
        """
        初始化运行器
        
        Args:
            config: 配置字典
            db_path: 数据库路径
        """
        self.config = config
        self.db_path = db_path
        
        # 运行状态
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
        
        # Agent和模拟器
        self.agent = None
        self.portfolio = None
        self.data_provider = None
        self.tools = None
        
        # 交易日列表
        self.trading_dates = []
        self.current_date_index = 0
        
        # 实时数据
        self.status_queue = Queue()  # 状态更新队列
        self.log_messages = []  # 日志消息
        self.daily_snapshots = []  # 每日快照
        self.trade_log = []  # 交易记录
        
        # 运行线程
        self.run_thread = None
        
    def initialize(self) -> bool:
        """
        初始化Agent和相关组件
        
        Returns:
            是否初始化成功
        """
        try:
            # 创建Agent
            self.agent = QwenAgent(
                agent_id="realtime_agent",
                name="实时交易Agent",
                api_base=self.config['api_base'],
                api_key=self.config['api_key'],
                model=self.config['model'],
                temperature=self.config['temperature'],
                stock_pool=self.config['stock_pool'],
                stock_names={},  # 可以添加股票名称映射
                api_call_interval=self.config['api_call_interval']
            )
            
            # 自定义系统提示词
            self.agent.system_prompt = self.config['system_prompt']
            
            # 初始化数据提供者和工具
            self.data_provider = MarketDataProvider(self.db_path)
            self.tools = TradingTools(self.data_provider, self.config['stock_pool'])
            
            # 初始化投资组合
            self.portfolio = Portfolio(
                f"Agent_{self.agent.agent_id}", 
                self.config['initial_capital']
            )
            self.portfolio.current_date = self.config['start_date']
            
            # 获取交易日列表
            self.trading_dates = self._get_trading_dates()
            
            if not self.trading_dates:
                self.add_log("错误：未找到交易日数据", "error")
                return False
            
            self.add_log(f"初始化成功，共 {len(self.trading_dates)} 个交易日", "success")
            return True
            
        except Exception as e:
            self.add_log(f"初始化失败: {e}", "error")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_trading_dates(self) -> List[str]:
        """获取交易日列表"""
        try:
            # 使用股票池中的第一只股票获取交易日
            dates = self.data_provider.db.get_available_dates(self.config['stock_pool'][0])
            
            # 过滤日期范围
            from datetime import datetime
            start_dt = datetime.strptime(self.config['start_date'], '%Y-%m-%d')
            end_dt = datetime.strptime(self.config['end_date'], '%Y-%m-%d')
            
            trading_dates = []
            for date_str in dates:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                if start_dt <= dt <= end_dt:
                    trading_dates.append(date_str)
            
            return trading_dates
        except Exception as e:
            self.add_log(f"获取交易日失败: {e}", "error")
            return []
    
    def start(self):
        """启动Agent运行"""
        if self.is_running:
            self.add_log("Agent已在运行中", "warning")
            return
        
        self.is_running = True
        self.should_stop = False
        self.is_paused = False
        
        # 在新线程中运行
        self.run_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.run_thread.start()
        
        self.add_log("Agent开始运行", "info")
    
    def pause(self):
        """暂停运行"""
        if not self.is_running:
            return
        
        self.is_paused = True
        self.add_log("Agent已暂停", "info")
    
    def resume(self):
        """继续运行"""
        if not self.is_running or not self.is_paused:
            return
        
        self.is_paused = False
        self.add_log("Agent继续运行", "info")
    
    def stop(self):
        """终止运行"""
        self.should_stop = True
        self.is_running = False
        self.is_paused = False
        self.add_log("Agent已终止", "info")
    
    def _run_loop(self):
        """运行循环（在独立线程中）"""
        try:
            while self.current_date_index < len(self.trading_dates) and not self.should_stop:
                # 检查是否暂停
                while self.is_paused and not self.should_stop:
                    time.sleep(0.5)
                
                if self.should_stop:
                    break
                
                current_date = self.trading_dates[self.current_date_index]
                
                # 更新进度
                progress = (self.current_date_index + 1) / len(self.trading_dates) * 100
                self.update_status('progress', progress)
                self.update_status('current_date', current_date)
                self.update_status('current_index', self.current_date_index + 1)
                
                self.add_log(f"[{self.current_date_index + 1}/{len(self.trading_dates)}] {current_date}", "info")
                
                # 执行一天的交易
                self._execute_day(current_date)
                
                # 更新索引
                self.current_date_index += 1
                
                # 短暂延迟，避免UI更新过快
                time.sleep(0.5)
            
            # 运行完成
            if not self.should_stop:
                self.is_running = False
                self.add_log("模拟完成！", "success")
                self.update_status('completed', True)
            
        except Exception as e:
            self.add_log(f"运行错误: {e}", "error")
            import traceback
            traceback.print_exc()
            self.is_running = False
    
    def _execute_day(self, current_date: str):
        """执行一天的交易"""
        try:
            # 更新持仓价格
            self._update_portfolio_prices(current_date)
            
            # Agent做决策
            decision = self._agent_decide(current_date)
            
            # 处理决策
            if decision and decision.get('success'):
                # 记录决策
                decision_info = {
                    'date': current_date,
                    'analysis': decision.get('analysis', ''),
                    'reasoning': decision.get('reasoning', ''),
                    'actions': decision.get('actions', [])
                }
                self.update_status('last_decision', decision_info)
                
                # 执行交易
                self._execute_actions(current_date, decision['actions'])
                
                self.add_log(f"决策: {len(decision['actions'])}个操作", "info")
            else:
                self.add_log(f"决策失败: {decision.get('reasoning', '未知错误')}", "warning")
            
            # 记录快照
            self._take_snapshot(current_date)
            
            # 更新状态
            summary = self.portfolio.get_summary()
            self.update_status('portfolio', {
                'cash': summary['cash'],
                'market_value': summary['market_value'],
                'total_asset': summary['total_asset'],
                'profit_rate': summary['total_profit_rate']
            })
            
        except Exception as e:
            self.add_log(f"执行交易失败: {e}", "error")
    
    def _update_portfolio_prices(self, current_date: str):
        """更新持仓价格"""
        for symbol in list(self.portfolio.positions.keys()):
            price_info = self.data_provider.get_stock_price_on_date(symbol, current_date)
            if price_info:
                self.portfolio.update_price(symbol, price_info['close'])
        
        self.portfolio.current_date = current_date
    
    def _agent_decide(self, current_date: str) -> Dict:
        """Agent做决策"""
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
        
        try:
            decision = self.agent.make_decision(
                current_date=current_date,
                portfolio_info=portfolio_info,
                tools=self.tools,
                context={'portfolio': self.portfolio}
            )
            return decision
        except Exception as e:
            self.add_log(f"决策异常: {e}", "error")
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
                    self.add_log(f"✓ 买入: {symbol} {quantity}股", "success")
                else:
                    self.add_log(f"✗ 买入失败: {symbol}", "warning")
            
            elif action_type == 'sell':
                success = self._execute_sell(current_date, symbol, quantity)
                if success:
                    self.add_log(f"✓ 卖出: {symbol} {quantity}股", "success")
                else:
                    self.add_log(f"✗ 卖出失败: {symbol}", "warning")
    
    def _execute_buy(self, date: str, symbol: str, quantity: int) -> bool:
        """执行买入"""
        try:
            price_info = self.data_provider.get_stock_price_on_date(symbol, date)
            if not price_info:
                return False
            
            price = price_info['close']
            stock_info = self.data_provider.get_stock_info(symbol)
            stock_name = stock_info['name'] if stock_info else symbol
            
            # 计算成本
            trade_amount = price * quantity
            commission = max(trade_amount * 0.0003, 5)
            total_cost = trade_amount + commission
            
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
            return False
    
    def _execute_sell(self, date: str, symbol: str, quantity: int) -> bool:
        """执行卖出"""
        try:
            position = self.portfolio.get_position(symbol)
            if not position or position.quantity < quantity:
                return False
            
            price_info = self.data_provider.get_stock_price_on_date(symbol, date)
            if not price_info:
                return False
            
            price = price_info['close']
            
            # 计算收入
            trade_amount = price * quantity
            commission = max(trade_amount * 0.0003, 5)
            stamp_tax = trade_amount * 0.001
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
    
    def add_log(self, message: str, level: str = "info"):
        """添加日志消息"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'level': level
        }
        self.log_messages.append(log_entry)
        
        # 限制日志数量
        if len(self.log_messages) > 1000:
            self.log_messages = self.log_messages[-500:]
    
    def update_status(self, key: str, value: Any):
        """更新状态"""
        self.status_queue.put({'key': key, 'value': value})
    
    def get_status_updates(self) -> List[Dict]:
        """获取所有待处理的状态更新"""
        updates = []
        while not self.status_queue.empty():
            updates.append(self.status_queue.get())
        return updates
    
    def get_current_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        summary = self.portfolio.get_summary() if self.portfolio else {}
        
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'current_date': self.trading_dates[self.current_date_index] if self.current_date_index < len(self.trading_dates) else None,
            'progress': (self.current_date_index / len(self.trading_dates) * 100) if self.trading_dates else 0,
            'total_days': len(self.trading_dates),
            'current_day': self.current_date_index + 1,
            'portfolio': {
                'cash': summary.get('cash', 0),
                'market_value': summary.get('market_value', 0),
                'total_asset': summary.get('total_asset', 0),
                'profit_rate': summary.get('total_profit_rate', 0)
            },
            'daily_snapshots': self.daily_snapshots,
            'trade_log': self.trade_log,
            'log_messages': self.log_messages[-50:]  # 最近50条日志
        }
