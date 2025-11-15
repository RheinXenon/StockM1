"""
下载A股常用指数数据到数据库

A股指数代码说明：
- 上证指数系列：000001, 000016, 000300, 000905, 000688 等（市场代码：sh）
- 深证指数系列：399001, 399006, 399005 等（市场代码：sz）

注意：为避免与股票代码冲突，指数在数据库中存储时会自动添加99前缀
例如：000001 -> 99000001, 399001 -> 99399001
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到系统路径，使其能够在hand_tools文件夹中正常运行
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table
from src.stock_app.data_downloader import DataDownloader
from src.stock_app.database import Database
import config

console = Console()


def main():
    """下载A股常用指数数据"""
    
    console.print("\n[bold cyan]========== A股指数数据下载工具 ==========[/bold cyan]\n")
    
    # 初始化下载器和数据库
    downloader = DataDownloader()
    db = Database()
    
    # 获取指数列表
    indices = downloader.get_index_list()
    
    # 显示将要下载的指数
    table = Table(title="将下载以下A股指数", show_header=True, header_style="bold magenta")
    table.add_column("序号", style="dim", width=6)
    table.add_column("指数代码", style="cyan", width=12)
    table.add_column("存储代码", style="yellow", width=12)
    table.add_column("指数名称", style="green", width=12)
    table.add_column("市场", style="blue", width=8)
    
    for idx, index_info in enumerate(indices, 1):
        original_code = index_info['symbol']
        storage_code = f"99{original_code}"
        table.add_row(
            str(idx),
            original_code,
            storage_code,
            index_info['name'],
            index_info['market'].upper()
        )
    
    console.print(table)
    console.print()
    console.print("[yellow]注意：为避免与股票代码冲突，指数存储时会自动添加99前缀[/yellow]")
    console.print()
    
    # 询问用户确认
    console.print("[yellow]即将下载以上指数的历史数据（从2015年至今）[/yellow]")
    response = input("确认开始下载？(Y/n): ").strip().lower()
    
    if response and response != 'y':
        console.print("[yellow]已取消下载[/yellow]")
        return
    
    # 设置日期范围
    start_date = '20150101'  # 从2015年开始，与股票数据一致
    end_date = datetime.now().strftime('%Y%m%d')
    
    console.print(f"\n[cyan]开始下载指数数据...[/cyan]")
    console.print(f"[cyan]日期范围: {start_date} - {end_date}[/cyan]\n")
    
    # 统计信息
    success_count = 0
    failed_count = 0
    total_records = 0
    
    # 下载每个指数
    for index_info in indices:
        symbol = index_info['symbol']
        name = index_info['name']
        storage_symbol = f"99{symbol}"
        
        console.print(f"[cyan]正在下载 {symbol} ({storage_symbol}) - {name}...[/cyan]")
        
        # 下载数据
        df = downloader.get_index_daily_data(symbol, start_date, end_date)
        
        if not df.empty:
            # 保存到数据库（database.py会自动添加99前缀）
            db.save_index_daily_data(symbol, df)
            
            success_count += 1
            total_records += len(df)
            console.print(f"[green]✓ {name}: 成功下载并保存 {len(df)} 条记录（存储为 {storage_symbol}）[/green]")
        else:
            failed_count += 1
            console.print(f"[red]✗ {name}: 下载失败[/red]")
    
    # 显示统计结果
    console.print("\n[bold green]========== 下载完成 ==========[/bold green]")
    console.print(f"[green]成功: {success_count} 个指数[/green]")
    console.print(f"[red]失败: {failed_count} 个指数[/red]")
    console.print(f"[cyan]总记录数: {total_records:,} 条[/cyan]")
    
    # 显示数据库中的指数统计
    console.print("\n[bold cyan]数据库中的指数数据统计：[/bold cyan]")
    print_index_stats(db)


def print_index_stats(db: Database):
    """打印指数统计信息"""
    conn = db.connect()
    cursor = conn.cursor()
    
    # 查询每个指数的记录数
    cursor.execute('''
        SELECT symbol, COUNT(*) as count, MIN(date) as start_date, MAX(date) as end_date
        FROM index_daily
        GROUP BY symbol
        ORDER BY symbol
    ''')
    
    # 创建显示表格
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("存储代码", style="cyan", width=12)
    table.add_column("原始代码", style="yellow", width=12)
    table.add_column("指数名称", style="green", width=12)
    table.add_column("记录数", style="magenta", width=10, justify="right")
    table.add_column("起始日期", style="blue", width=12)
    table.add_column("结束日期", style="blue", width=12)
    
    results = cursor.fetchall()
    
    if not results:
        console.print("[yellow]数据库中暂无指数数据[/yellow]")
        return
    
    # 获取指数名称映射
    downloader = DataDownloader()
    indices = downloader.get_index_list()
    index_names = {idx['symbol']: idx['name'] for idx in indices}
    
    for row in results:
        storage_symbol, count, start_date, end_date = row
        # 移除99前缀获取原始代码
        original_symbol = storage_symbol[2:] if storage_symbol.startswith('99') else storage_symbol
        name = index_names.get(original_symbol, '未知')
        table.add_row(
            storage_symbol,
            original_symbol,
            name,
            f"{count:,}",
            start_date,
            end_date
        )
    
    console.print(table)
    
    # 显示总记录数
    cursor.execute('SELECT COUNT(*) FROM index_daily')
    total = cursor.fetchone()[0]
    console.print(f"\n[bold cyan]指数数据总记录数: {total:,} 条[/bold cyan]")
    
    # 显示使用提示
    console.print("\n[bold yellow]查询指数数据时的代码说明：[/bold yellow]")
    console.print("  - 使用 db.get_index_data('000001') 会自动添加99前缀查询")
    console.print("  - 直接SQL查询时需要使用存储代码，如：WHERE symbol = '99000001'")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]已中断下载[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]错误: {e}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
        sys.exit(1)
