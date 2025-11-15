"""
CSV数据导入模块 - 从两个时间段的文件夹中导入股票数据
"""
import pandas as pd
import sqlite3
import os
import glob
from typing import List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
import config

console = Console()


class CSVImporter:
    """CSV数据导入器"""
    
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.base_dir = config.BASE_DIR
        
        # 定义两个数据文件夹
        self.data_folders = [
            '日个股回报率文件2015-11-15 至 2020-11-14(仅供浙江工商大学使用)',
            '日个股回报率文件2020-11-15 至 2025-11-14(仅供浙江工商大学使用)'
        ]
        
        # CSV字段映射（从原始字段名到数据库字段名）
        self.column_mapping = {
            'Stkcd': 'symbol',
            'Trddt': 'trade_date',
            'Opnprc': 'open_price',
            'Hiprc': 'high_price',
            'Loprc': 'low_price',
            'Clsprc': 'close_price',
            'Dnshrtrd': 'volume',
            'Dnvaltrd': 'amount',
            'Dsmvosd': 'market_cap_float',
            'Dsmvtll': 'market_cap_total',
            'Dretwd': 'return_with_dividend',
            'Dretnd': 'return_no_dividend',
            'Adjprcwd': 'adj_price_with_dividend',
            'Adjprcnd': 'adj_price_no_dividend',
            'Markettype': 'market_type',
            'Capchgdt': 'cap_change_date',
            'Trdsta': 'trade_status',
            'Ahshrtrd_D': 'after_hours_volume',
            'Ahvaltrd_D': 'after_hours_amount',
            'PreClosePrice': 'pre_close_price',
            'ChangeRatio': 'change_ratio',
            'LimitDown': 'limit_down',
            'LimitUp': 'limit_up',
            'LimitStatus': 'limit_status'
        }
    
    def get_csv_files(self, folder_name: str) -> List[str]:
        """获取指定文件夹中的所有CSV文件"""
        folder_path = os.path.join(self.base_dir, folder_name)
        
        if not os.path.exists(folder_path):
            console.print(f"[red]文件夹不存在: {folder_path}[/red]")
            return []
        
        # 查找所有TRD_Dalyr开头的CSV文件，排除描述文件
        csv_files = glob.glob(os.path.join(folder_path, 'TRD_Dalyr*.csv'))
        
        console.print(f"[cyan]在文件夹 {folder_name} 中找到 {len(csv_files)} 个CSV文件[/cyan]")
        return csv_files
    
    def read_csv_file(self, file_path: str, encoding: str = 'gbk', chunksize: int = None) -> pd.DataFrame:
        """
        读取CSV文件
        
        Args:
            file_path: CSV文件路径
            encoding: 文件编码，默认gbk（中文CSV常用编码）
            chunksize: 分块读取大小，默认None（一次性读取）
        """
        try:
            # 尝试不同的编码
            encodings = [encoding, 'utf-8', 'gb2312', 'gb18030']
            
            for enc in encodings:
                try:
                    # 只读取需要的列
                    usecols = list(self.column_mapping.keys())
                    
                    df = pd.read_csv(
                        file_path, 
                        encoding=enc, 
                        low_memory=False,
                        usecols=lambda x: x in usecols  # 只读取需要的列
                    )
                    
                    # 重命名列
                    df = df.rename(columns=self.column_mapping)
                    
                    # 处理日期格式：从YYYY-MM-DD转换为标准格式
                    if 'trade_date' in df.columns:
                        df['trade_date'] = pd.to_datetime(df['trade_date'], errors='coerce').dt.strftime('%Y-%m-%d')
                    
                    if 'cap_change_date' in df.columns:
                        # cap_change_date可能有缺失值
                        df['cap_change_date'] = pd.to_datetime(
                            df['cap_change_date'], 
                            errors='coerce'
                        ).dt.strftime('%Y-%m-%d')
                    
                    # 将NaN替换为None以便SQLite处理
                    df = df.where(pd.notnull(df), None)
                    
                    return df
                    
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    # 如果usecols失败，尝试不使用usecols
                    try:
                        df = pd.read_csv(file_path, encoding=enc, low_memory=False)
                        df = df.rename(columns=self.column_mapping)
                        
                        if 'trade_date' in df.columns:
                            df['trade_date'] = pd.to_datetime(df['trade_date'], errors='coerce').dt.strftime('%Y-%m-%d')
                        
                        if 'cap_change_date' in df.columns:
                            df['cap_change_date'] = pd.to_datetime(
                                df['cap_change_date'], 
                                errors='coerce'
                            ).dt.strftime('%Y-%m-%d')
                        
                        df = df.where(pd.notnull(df), None)
                        return df
                    except:
                        continue
            
            console.print(f"[red]无法读取文件（编码错误）: {file_path}[/red]")
            return pd.DataFrame()
            
        except Exception as e:
            console.print(f"[red]读取文件失败 {file_path}: {e}[/red]")
            return pd.DataFrame()
    
    def insert_stock_data(self, df: pd.DataFrame, conn: sqlite3.Connection, batch_size: int = 10000):
        """
        批量插入股票数据到数据库（分批处理）
        
        Args:
            df: 数据DataFrame
            conn: 数据库连接
            batch_size: 每批插入的记录数，默认10000
        """
        cursor = conn.cursor()
        
        # 准备插入数据
        insert_query = '''
            INSERT OR REPLACE INTO stock_daily (
                symbol, trade_date, open_price, high_price, low_price, close_price,
                volume, amount, market_cap_float, market_cap_total,
                return_with_dividend, return_no_dividend,
                adj_price_with_dividend, adj_price_no_dividend,
                market_type, cap_change_date, trade_status,
                after_hours_volume, after_hours_amount,
                pre_close_price, change_ratio,
                limit_down, limit_up, limit_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        total_rows = len(df)
        batch_data = []
        inserted_count = 0
        
        # 分批处理数据
        for idx, row in df.iterrows():
            batch_data.append((
                row.get('symbol'),
                row.get('trade_date'),
                row.get('open_price'),
                row.get('high_price'),
                row.get('low_price'),
                row.get('close_price'),
                row.get('volume'),
                row.get('amount'),
                row.get('market_cap_float'),
                row.get('market_cap_total'),
                row.get('return_with_dividend'),
                row.get('return_no_dividend'),
                row.get('adj_price_with_dividend'),
                row.get('adj_price_no_dividend'),
                row.get('market_type'),
                row.get('cap_change_date'),
                row.get('trade_status'),
                row.get('after_hours_volume'),
                row.get('after_hours_amount'),
                row.get('pre_close_price'),
                row.get('change_ratio'),
                row.get('limit_down'),
                row.get('limit_up'),
                row.get('limit_status')
            ))
            
            # 达到批次大小时执行插入
            if len(batch_data) >= batch_size:
                cursor.executemany(insert_query, batch_data)
                conn.commit()
                inserted_count += len(batch_data)
                batch_data = []
                
                # 显示进度（每批）
                progress_pct = (inserted_count / total_rows) * 100
                if inserted_count % (batch_size * 5) == 0:  # 每5批显示一次
                    console.print(f"  [cyan]已插入 {inserted_count:,}/{total_rows:,} 条记录 ({progress_pct:.1f}%)[/cyan]")
        
        # 插入剩余数据
        if batch_data:
            cursor.executemany(insert_query, batch_data)
            conn.commit()
            inserted_count += len(batch_data)
        
        return inserted_count
    
    def update_stock_info(self, df: pd.DataFrame, conn: sqlite3.Connection):
        """
        更新股票基本信息表
        
        Args:
            df: 数据DataFrame
            conn: 数据库连接
        """
        from datetime import datetime
        
        cursor = conn.cursor()
        
        # 获取唯一的股票代码和市场类型
        stocks = df[['symbol', 'market_type', 'trade_date']].copy()
        stocks = stocks.groupby('symbol').agg({
            'market_type': 'first',
            'trade_date': 'min'
        }).reset_index()
        
        update_time = datetime.now().isoformat()
        
        for _, row in stocks.iterrows():
            cursor.execute('''
                INSERT OR REPLACE INTO stock_info 
                (symbol, market_type, first_seen_date, last_updated)
                VALUES (?, ?, ?, ?)
            ''', (
                row['symbol'],
                row['market_type'],
                row['trade_date'],
                update_time
            ))
        
        conn.commit()
    
    def import_all_data(self):
        """导入所有CSV文件的数据"""
        console.print("\n[bold cyan]开始导入CSV数据...[/bold cyan]\n")
        
        conn = sqlite3.connect(self.db_path)
        
        total_records = 0
        total_files = 0
        
        # 遍历两个时间段的文件夹
        for folder in self.data_folders:
            console.print(f"\n[bold yellow]处理文件夹: {folder}[/bold yellow]")
            
            csv_files = self.get_csv_files(folder)
            
            if not csv_files:
                console.print(f"[yellow]跳过空文件夹[/yellow]")
                continue
            
            # 使用进度条
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task(
                    f"[cyan]导入CSV文件...",
                    total=len(csv_files)
                )
                
                for csv_file in csv_files:
                    file_name = os.path.basename(csv_file)
                    progress.update(task, description=f"[cyan]导入 {file_name}...")
                    
                    # 读取CSV
                    df = self.read_csv_file(csv_file)
                    
                    if df.empty:
                        console.print(f"[yellow]⚠ 文件为空或读取失败: {file_name}[/yellow]")
                        progress.advance(task)
                        continue
                    
                    # 插入数据
                    try:
                        console.print(f"[cyan]正在处理 {file_name} ({len(df):,} 条记录)...[/cyan]")
                        
                        inserted = self.insert_stock_data(df, conn)
                        self.update_stock_info(df, conn)
                        
                        total_records += inserted
                        total_files += 1
                        
                        console.print(
                            f"[green]✓ {file_name}: 成功插入 {inserted:,} 条记录[/green]"
                        )
                    except Exception as e:
                        console.print(f"[red]✗ 导入失败 {file_name}: {e}[/red]")
                        import traceback
                        console.print(f"[red]{traceback.format_exc()}[/red]")
                    
                    progress.advance(task)
        
        conn.close()
        
        # 显示统计信息
        console.print(f"\n[bold green]导入完成！[/bold green]")
        console.print(f"[cyan]成功导入文件数: {total_files}[/cyan]")
        console.print(f"[cyan]总记录数: {total_records:,}[/cyan]")
        
        # 查询数据库统计
        self.print_database_stats()
    
    def print_database_stats(self):
        """打印数据库统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        console.print("\n[bold cyan]数据库统计信息：[/bold cyan]")
        
        # 股票数量
        cursor.execute('SELECT COUNT(DISTINCT symbol) FROM stock_daily')
        stock_count = cursor.fetchone()[0]
        console.print(f"[cyan]股票数量: {stock_count}[/cyan]")
        
        # 总记录数
        cursor.execute('SELECT COUNT(*) FROM stock_daily')
        record_count = cursor.fetchone()[0]
        console.print(f"[cyan]总记录数: {record_count:,}[/cyan]")
        
        # 日期范围
        cursor.execute('SELECT MIN(trade_date), MAX(trade_date) FROM stock_daily')
        date_range = cursor.fetchone()
        console.print(f"[cyan]日期范围: {date_range[0]} 至 {date_range[1]}[/cyan]")
        
        # 市场类型分布
        cursor.execute('''
            SELECT market_type, COUNT(DISTINCT symbol) as count
            FROM stock_info
            GROUP BY market_type
            ORDER BY count DESC
        ''')
        
        console.print("\n[bold cyan]市场类型分布：[/bold cyan]")
        market_types = {
            1: '上证A股',
            2: '上证B股',
            4: '深证A股',
            8: '深证B股',
            16: '创业板',
            32: '科创板',
            64: '北证A股'
        }
        
        for row in cursor.fetchall():
            market_type, count = row
            type_name = market_types.get(market_type, f'未知({market_type})')
            console.print(f"  {type_name}: {count} 只股票")
        
        conn.close()


def main():
    """主函数"""
    importer = CSVImporter()
    importer.import_all_data()


if __name__ == '__main__':
    main()
