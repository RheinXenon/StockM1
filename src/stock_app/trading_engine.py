"""
交易引擎模块
"""
from datetime import datetime
from typing import Optional, List, Tuple
from rich.console import Console
from rich.table import Table

import config
from src.stock_app.database import Database
from src.stock_app.portfolio import Portfolio, Position


console = Console()


class TradingEngine:
    """模拟交易引擎"""
    
    def __init__(self, db: Database):
        self.db = db
        self.portfolio: Optional[Portfolio] = None
        self.account_id: Optional[int] = None
        
    def create_account(self, account_name: str, initial_capital: float = None) -> bool:
        """创建模拟账户"""
        if initial_capital is None:
            initial_capital = config.INITIAL_CAPITAL
        
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            # 检查账户是否已存在
            cursor.execute('SELECT id FROM account WHERE name = ?', (account_name,))
            if cursor.fetchone():
                console.print(f"[red]账户 '{account_name}' 已存在[/red]")
                return False
            
            # 创建账户
            cursor.execute('''
                INSERT INTO account (name, initial_capital, current_capital, current_date, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                account_name,
                initial_capital,
                initial_capital,
                config.DEFAULT_START_DATE,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            console.print(f"[green]账户 '{account_name}' 创建成功！初始资金: {initial_capital:,.2f}元[/green]")
            return True
        except Exception as e:
            console.print(f"[red]创建账户失败: {e}[/red]")
            return False
    
    def load_account(self, account_name: str) -> bool:
        """加载账户"""
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            # 获取账户信息
            cursor.execute('''
                SELECT id, initial_capital, current_capital, current_date
                FROM account WHERE name = ?
            ''', (account_name,))
            
            result = cursor.fetchone()
            if not result:
                console.print(f"[red]账户 '{account_name}' 不存在[/red]")
                return False
            
            account_id, initial_capital, current_capital, current_date = result
            
            # 创建投资组合
            self.portfolio = Portfolio(account_name, initial_capital)
            self.portfolio.cash = current_capital
            self.portfolio.current_date = current_date
            self.account_id = account_id
            
            # 加载持仓
            cursor.execute('''
                SELECT symbol, quantity, avg_cost, current_price
                FROM positions WHERE account_id = ?
            ''', (account_id,))
            
            for symbol, quantity, avg_cost, current_price in cursor.fetchall():
                # 获取股票名称
                cursor.execute('SELECT name FROM stock_info WHERE symbol = ?', (symbol,))
                name_result = cursor.fetchone()
                name = name_result[0] if name_result else symbol
                
                self.portfolio.positions[symbol] = Position(
                    symbol=symbol,
                    name=name,
                    quantity=quantity,
                    avg_cost=avg_cost,
                    current_price=current_price or avg_cost
                )
            
            console.print(f"[green]账户 '{account_name}' 加载成功！[/green]")
            return True
        except Exception as e:
            console.print(f"[red]加载账户失败: {e}[/red]")
            return False
    
    def set_date(self, date: str) -> bool:
        """设置模拟日期"""
        if not self.portfolio:
            console.print("[red]请先加载账户[/red]")
            return False
        
        # 验证日期格式
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            console.print("[red]日期格式错误，应为 YYYY-MM-DD[/red]")
            return False
        
        self.portfolio.current_date = date
        
        # 更新所有持仓的当前价格
        for symbol in self.portfolio.positions.keys():
            price_info = self.db.get_stock_price_on_date(symbol, date)
            if price_info:
                self.portfolio.update_price(symbol, price_info['close'])
        
        # 保存到数据库
        self._save_account_state()
        
        console.print(f"[green]模拟日期已设置为: {date}[/green]")
        return True
    
    def buy(self, symbol: str, quantity: int, price: Optional[float] = None) -> bool:
        """买入股票"""
        if not self.portfolio:
            console.print("[red]请先加载账户[/red]")
            return False
        
        if not self.portfolio.current_date:
            console.print("[red]请先设置模拟日期[/red]")
            return False
        
        # 获取股票信息
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM stock_info WHERE symbol = ?', (symbol,))
        result = cursor.fetchone()
        if not result:
            console.print(f"[red]股票 {symbol} 不存在[/red]")
            return False
        stock_name = result[0]
        
        # 获取当日价格
        if price is None:
            price_info = self.db.get_stock_price_on_date(symbol, self.portfolio.current_date)
            if not price_info:
                console.print(f"[red]无法获取股票 {symbol} 在 {self.portfolio.current_date} 的价格[/red]")
                return False
            price = price_info['close']
        
        # 计算费用
        total_cost, commission, stamp_tax = self._calculate_trade_cost(
            price, quantity, trade_type='buy'
        )
        
        # 检查资金是否足够
        if self.portfolio.cash < total_cost:
            console.print(f"[red]资金不足！需要 {total_cost:,.2f}元，可用 {self.portfolio.cash:,.2f}元[/red]")
            return False
        
        # 执行买入
        self.portfolio.cash -= total_cost
        self.portfolio.add_position(symbol, stock_name, quantity, price)
        
        # 记录交易
        self._record_transaction(
            symbol=symbol,
            trade_type='buy',
            quantity=quantity,
            price=price,
            commission=commission,
            stamp_tax=stamp_tax,
            total_amount=total_cost
        )
        
        # 保存状态
        self._save_account_state()
        self._save_position(symbol)
        
        console.print(f"[green]买入成功！{stock_name}({symbol}) {quantity}股 @ {price:.2f}元[/green]")
        console.print(f"[cyan]成交金额: {quantity * price:,.2f}元, 手续费: {commission:.2f}元, 总计: {total_cost:,.2f}元[/cyan]")
        return True
    
    def sell(self, symbol: str, quantity: int, price: Optional[float] = None) -> bool:
        """卖出股票"""
        if not self.portfolio:
            console.print("[red]请先加载账户[/red]")
            return False
        
        # 检查持仓
        position = self.portfolio.get_position(symbol)
        if not position:
            console.print(f"[red]未持有股票 {symbol}[/red]")
            return False
        
        if position.quantity < quantity:
            console.print(f"[red]持仓不足！持有 {position.quantity}股，卖出 {quantity}股[/red]")
            return False
        
        # 获取当日价格
        if price is None:
            price_info = self.db.get_stock_price_on_date(symbol, self.portfolio.current_date)
            if not price_info:
                console.print(f"[red]无法获取股票 {symbol} 在 {self.portfolio.current_date} 的价格[/red]")
                return False
            price = price_info['close']
        
        # 计算费用
        total_amount, commission, stamp_tax = self._calculate_trade_cost(
            price, quantity, trade_type='sell'
        )
        
        # 执行卖出
        self.portfolio.cash += total_amount
        self.portfolio.reduce_position(symbol, quantity)
        
        # 记录交易
        self._record_transaction(
            symbol=symbol,
            trade_type='sell',
            quantity=quantity,
            price=price,
            commission=commission,
            stamp_tax=stamp_tax,
            total_amount=total_amount
        )
        
        # 保存状态
        self._save_account_state()
        if symbol in self.portfolio.positions:
            self._save_position(symbol)
        else:
            self._delete_position(symbol)
        
        console.print(f"[green]卖出成功！{position.name}({symbol}) {quantity}股 @ {price:.2f}元[/green]")
        console.print(f"[cyan]成交金额: {quantity * price:,.2f}元, 手续费: {commission:.2f}元, 印花税: {stamp_tax:.2f}元, 实收: {total_amount:,.2f}元[/cyan]")
        return True
    
    def _calculate_trade_cost(self, price: float, quantity: int, trade_type: str) -> Tuple[float, float, float]:
        """
        计算交易费用
        
        Returns:
            (总金额, 佣金, 印花税)
        """
        trade_amount = price * quantity
        
        # 佣金
        commission = max(trade_amount * config.COMMISSION_RATE, config.MIN_COMMISSION)
        
        # 印花税（只在卖出时收取）
        stamp_tax = trade_amount * config.STAMP_TAX_RATE if trade_type == 'sell' else 0
        
        if trade_type == 'buy':
            total = trade_amount + commission
        else:  # sell
            total = trade_amount - commission - stamp_tax
        
        return total, commission, stamp_tax
    
    def _record_transaction(self, symbol: str, trade_type: str, quantity: int,
                          price: float, commission: float, stamp_tax: float,
                          total_amount: float):
        """记录交易"""
        conn = self.db.connect()
        conn.execute('''
            INSERT INTO transactions 
            (account_id, symbol, trade_date, trade_type, quantity, price, 
             commission, stamp_tax, total_amount, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.account_id,
            symbol,
            self.portfolio.current_date,
            trade_type,
            quantity,
            price,
            commission,
            stamp_tax,
            total_amount,
            datetime.now().isoformat()
        ))
        conn.commit()
    
    def _save_account_state(self):
        """保存账户状态"""
        conn = self.db.connect()
        conn.execute('''
            UPDATE account 
            SET current_capital = ?, current_date = ?
            WHERE id = ?
        ''', (self.portfolio.cash, self.portfolio.current_date, self.account_id))
        conn.commit()
    
    def _save_position(self, symbol: str):
        """保存持仓"""
        position = self.portfolio.get_position(symbol)
        if not position:
            return
        
        conn = self.db.connect()
        conn.execute('''
            INSERT OR REPLACE INTO positions 
            (account_id, symbol, quantity, avg_cost, current_price, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            self.account_id,
            symbol,
            position.quantity,
            position.avg_cost,
            position.current_price,
            datetime.now().isoformat()
        ))
        conn.commit()
    
    def _delete_position(self, symbol: str):
        """删除持仓"""
        conn = self.db.connect()
        conn.execute('''
            DELETE FROM positions 
            WHERE account_id = ? AND symbol = ?
        ''', (self.account_id, symbol))
        conn.commit()
    
    def show_portfolio(self):
        """显示持仓"""
        if not self.portfolio:
            console.print("[red]请先加载账户[/red]")
            return
        
        summary = self.portfolio.get_summary()
        
        # 账户摘要
        console.print("\n[bold cyan]账户摘要[/bold cyan]")
        console.print(f"账户名称: {summary['account_name']}")
        console.print(f"当前日期: {summary['current_date']}")
        console.print(f"初始资金: {summary['initial_capital']:,.2f}元")
        console.print(f"可用资金: {summary['cash']:,.2f}元")
        console.print(f"持仓市值: {summary['market_value']:,.2f}元")
        console.print(f"总资产: {summary['total_asset']:,.2f}元")
        
        profit_color = "green" if summary['total_profit'] >= 0 else "red"
        console.print(f"总盈亏: [{profit_color}]{summary['total_profit']:,.2f}元 ({summary['total_profit_rate']:.2f}%)[/{profit_color}]")
        
        # 持仓明细
        if self.portfolio.positions:
            console.print("\n[bold cyan]持仓明细[/bold cyan]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("股票代码", style="cyan")
            table.add_column("股票名称", style="cyan")
            table.add_column("持仓数量", justify="right")
            table.add_column("成本价", justify="right")
            table.add_column("当前价", justify="right")
            table.add_column("市值", justify="right")
            table.add_column("盈亏", justify="right")
            table.add_column("盈亏比例", justify="right")
            
            for pos in self.portfolio.positions.values():
                profit_color = "green" if pos.profit >= 0 else "red"
                table.add_row(
                    pos.symbol,
                    pos.name,
                    str(pos.quantity),
                    f"{pos.avg_cost:.2f}",
                    f"{pos.current_price:.2f}",
                    f"{pos.market_value:,.2f}",
                    f"[{profit_color}]{pos.profit:,.2f}[/{profit_color}]",
                    f"[{profit_color}]{pos.profit_rate:.2f}%[/{profit_color}]"
                )
            
            console.print(table)
        else:
            console.print("\n[yellow]暂无持仓[/yellow]")
    
    def show_transactions(self, limit: int = 20):
        """显示交易记录"""
        if not self.account_id:
            console.print("[red]请先加载账户[/red]")
            return
        
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT trade_date, symbol, trade_type, quantity, price, 
                   commission, stamp_tax, total_amount
            FROM transactions
            WHERE account_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (self.account_id, limit))
        
        results = cursor.fetchall()
        
        if not results:
            console.print("[yellow]暂无交易记录[/yellow]")
            return
        
        console.print(f"\n[bold cyan]最近 {len(results)} 笔交易记录[/bold cyan]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("日期")
        table.add_column("股票代码")
        table.add_column("交易类型")
        table.add_column("数量", justify="right")
        table.add_column("价格", justify="right")
        table.add_column("手续费", justify="right")
        table.add_column("印花税", justify="right")
        table.add_column("总金额", justify="right")
        
        for row in results:
            trade_type_text = "[green]买入[/green]" if row[2] == 'buy' else "[red]卖出[/red]"
            table.add_row(
                row[0],
                row[1],
                trade_type_text,
                str(row[3]),
                f"{row[4]:.2f}",
                f"{row[5]:.2f}",
                f"{row[6]:.2f}",
                f"{row[7]:,.2f}"
            )
        
        console.print(table)
