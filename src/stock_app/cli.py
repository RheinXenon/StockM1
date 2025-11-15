"""
命令行界面模块
"""
import os

import click
import pandas as pd
from rich.console import Console
from rich.table import Table

import config
from src.stock_app.database import Database
from src.stock_app.data_downloader import DataDownloader
from src.stock_app.trading_engine import TradingEngine


console = Console()


@click.group()
def cli():
    """A股模拟炒股系统"""
    pass


@cli.command()
@click.option('--start-date', default=config.DEFAULT_START_DATE, help='开始日期 (YYYYMMDD)')
@click.option('--end-date', default=None, help='结束日期 (YYYYMMDD)')
@click.option('--limit', default=None, type=int, help='限制下载数量（测试用）')
def download_stocks(start_date, end_date, limit):
    """下载A股股票历史数据"""
    console.print("[bold cyan]开始下载A股股票数据...[/bold cyan]")
    
    db = Database()
    downloader = DataDownloader()
    
    # 获取并保存股票列表
    stock_list = downloader.get_stock_list()
    if not stock_list.empty:
        db.save_stock_info(stock_list)
        console.print(f"[green]股票列表已保存到数据库[/green]")
    
    # 下载股票数据
    result = downloader.download_all_stocks(start_date, end_date, limit)
    
    # 保存到数据库
    if result['data']:
        console.print("\n[cyan]正在保存数据到数据库...[/cyan]")
        for symbol, df in result['data'].items():
            db.save_stock_daily_data(symbol, df)
        console.print("[green]数据已保存到数据库[/green]")
    
    db.close()


@cli.command()
@click.option('--start-date', default=config.DEFAULT_START_DATE, help='开始日期 (YYYYMMDD)')
@click.option('--end-date', default=None, help='结束日期 (YYYYMMDD)')
def download_indices(start_date, end_date):
    """下载A股指数历史数据"""
    console.print("[bold cyan]开始下载A股指数数据...[/bold cyan]")
    
    db = Database()
    downloader = DataDownloader()
    
    # 下载指数数据
    result = downloader.download_all_indices(start_date, end_date)
    
    # 保存到数据库
    if result:
        console.print("\n[cyan]正在保存数据到数据库...[/cyan]")
        for symbol, df in result.items():
            db.save_index_daily_data(symbol, df)
        console.print("[green]指数数据已保存到数据库[/green]")
    
    db.close()


@cli.command()
@click.argument('symbol')
@click.option('--start-date', default=None, help='开始日期 (YYYY-MM-DD)')
@click.option('--end-date', default=None, help='结束日期 (YYYY-MM-DD)')
def query_stock(symbol, start_date, end_date):
    """查询股票历史数据"""
    db = Database()
    
    df = db.get_stock_data(symbol, start_date, end_date)
    
    if df.empty:
        console.print(f"[red]未找到股票 {symbol} 的数据[/red]")
    else:
        console.print(f"\n[bold cyan]股票 {symbol} 历史数据（共 {len(df)} 条）[/bold cyan]")
        
        # 显示前10条和后10条
        display_df = df if len(df) <= 20 else pd.concat([df.head(10), df.tail(10)])
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("日期")
        table.add_column("开盘", justify="right")
        table.add_column("收盘", justify="right")
        table.add_column("最高", justify="right")
        table.add_column("最低", justify="right")
        table.add_column("成交量", justify="right")
        
        for _, row in display_df.iterrows():
            table.add_row(
                row['date'],
                f"{row['open']:.2f}",
                f"{row['close']:.2f}",
                f"{row['high']:.2f}",
                f"{row['low']:.2f}",
                f"{row['volume']:,.0f}"
            )
        
        console.print(table)
    
    db.close()


@cli.command()
def list_stocks():
    """列出所有已下载的股票"""
    db = Database()
    
    df = db.get_stocks_with_data_count()
    
    if df.empty:
        console.print("[yellow]数据库中暂无股票数据[/yellow]")
    else:
        console.print(f"\n[bold cyan]已下载股票列表（共 {len(df)} 只）[/bold cyan]")
        
        # 只显示有数据的股票
        df = df[df['data_count'] > 0]
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("股票代码", style="cyan")
        table.add_column("股票名称", style="cyan")
        table.add_column("数据条数", justify="right")
        
        for _, row in df.head(50).iterrows():
            table.add_row(
                row['symbol'],
                row['name'],
                str(row['data_count'])
            )
        
        console.print(table)
        
        if len(df) > 50:
            console.print(f"\n[yellow]... 还有 {len(df) - 50} 只股票未显示[/yellow]")
    
    db.close()


@cli.command()
@click.option(
    '--output',
    default=os.path.join(config.DATA_DIR, 'all_stock_data.csv'),
    show_default=True,
    help='导出CSV路径'
)
def export_stock_data(output):
    """导出所有股票日线数据到CSV"""
    db = Database()
    df = db.get_all_stock_daily()
    
    if df.empty:
        console.print('[yellow]数据库中暂无股票日线数据[/yellow]')
        db.close()
        return
    
    output_dir = os.path.dirname(os.path.abspath(output))
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(output, index=False)
    console.print(f"[green]已导出 {len(df)} 条记录到 {output}[/green]")
    db.close()


@cli.command()
@click.argument('account_name')
@click.option('--capital', default=config.INITIAL_CAPITAL, type=float, help='初始资金')
def create_account(account_name, capital):
    """创建模拟账户"""
    db = Database()
    engine = TradingEngine(db)
    
    engine.create_account(account_name, capital)
    
    db.close()


@cli.command()
@click.argument('account_name')
def load_account(account_name):
    """加载模拟账户（进入交易模式）"""
    db = Database()
    engine = TradingEngine(db)
    
    if not engine.load_account(account_name):
        db.close()
        return
    
    # 进入交互模式
    console.print("\n[bold green]欢迎使用模拟炒股系统！[/bold green]")
    console.print("输入 'help' 查看帮助\n")
    
    while True:
        try:
            cmd = console.input("[bold cyan]>>> [/bold cyan]").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split()
            command = parts[0].lower()
            
            if command == 'help':
                show_trading_help()
            
            elif command == 'date':
                if len(parts) < 2:
                    console.print("[red]用法: date YYYY-MM-DD[/red]")
                else:
                    engine.set_date(parts[1])
            
            elif command == 'buy':
                if len(parts) < 3:
                    console.print("[red]用法: buy 股票代码 数量 [价格][/red]")
                else:
                    symbol = parts[1]
                    quantity = int(parts[2])
                    price = float(parts[3]) if len(parts) > 3 else None
                    engine.buy(symbol, quantity, price)
            
            elif command == 'sell':
                if len(parts) < 3:
                    console.print("[red]用法: sell 股票代码 数量 [价格][/red]")
                else:
                    symbol = parts[1]
                    quantity = int(parts[2])
                    price = float(parts[3]) if len(parts) > 3 else None
                    engine.sell(symbol, quantity, price)
            
            elif command == 'portfolio' or command == 'p':
                engine.show_portfolio()
            
            elif command == 'transactions' or command == 'trans':
                limit = int(parts[1]) if len(parts) > 1 else 20
                engine.show_transactions(limit)
            
            elif command == 'price':
                if len(parts) < 2:
                    console.print("[red]用法: price 股票代码[/red]")
                else:
                    show_price(db, parts[1], engine.portfolio.current_date)
            
            elif command == 'exit' or command == 'quit':
                console.print("[green]再见！[/green]")
                break
            
            else:
                console.print(f"[red]未知命令: {command}[/red]")
                console.print("输入 'help' 查看帮助")
        
        except KeyboardInterrupt:
            console.print("\n[green]再见！[/green]")
            break
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
    
    db.close()


def show_trading_help():
    """显示交易帮助"""
    help_text = """
[bold cyan]可用命令：[/bold cyan]

[yellow]账户管理：[/yellow]
  date YYYY-MM-DD          设置模拟日期
  portfolio (p)            查看持仓
  transactions (trans) [N] 查看最近N笔交易记录

[yellow]交易操作：[/yellow]
  buy 代码 数量 [价格]     买入股票（不指定价格则使用当日收盘价）
  sell 代码 数量 [价格]    卖出股票（不指定价格则使用当日收盘价）

[yellow]信息查询：[/yellow]
  price 代码               查询股票当前价格

[yellow]其他：[/yellow]
  help                     显示帮助
  exit/quit                退出

[bold cyan]示例：[/bold cyan]
  date 2020-01-02
  buy 000001 1000
  sell 000001 500
"""
    console.print(help_text)


def show_price(db: Database, symbol: str, date: str):
    """显示股票价格"""
    price_info = db.get_stock_price_on_date(symbol, date)
    
    if not price_info:
        console.print(f"[red]无法获取股票 {symbol} 在 {date} 的价格[/red]")
    else:
        console.print(f"\n[bold cyan]股票 {symbol} - {date}[/bold cyan]")
        console.print(f"开盘: {price_info['open']:.2f}")
        console.print(f"收盘: {price_info['close']:.2f}")
        console.print(f"最高: {price_info['high']:.2f}")
        console.print(f"最低: {price_info['low']:.2f}")
        console.print(f"成交量: {price_info['volume']:,.0f}")


if __name__ == '__main__':
    cli()
