"""
数据库迁移脚本 - 重构数据库以适配新的CSV数据格式
"""
import sqlite3
import config
import os
from datetime import datetime
from rich.console import Console

console = Console()


class DatabaseMigration:
    """数据库迁移类"""
    
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.backup_path = None
        
    def backup_database(self):
        """备份当前数据库"""
        if os.path.exists(self.db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.backup_path = self.db_path.replace('.db', f'_backup_{timestamp}.db')
            
            console.print(f"[cyan]正在备份数据库到: {self.backup_path}[/cyan]")
            
            # 复制数据库文件
            import shutil
            shutil.copy2(self.db_path, self.backup_path)
            
            console.print(f"[green]✓ 数据库备份完成[/green]")
            return True
        else:
            console.print("[yellow]数据库文件不存在，跳过备份[/yellow]")
            return False
    
    def drop_old_tables(self):
        """删除旧的股票数据表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        console.print("[cyan]正在删除旧的数据表...[/cyan]")
        
        # 删除旧的股票相关表
        tables_to_drop = ['stock_daily', 'stock_info']
        
        for table in tables_to_drop:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS {table}')
                console.print(f"[green]✓ 删除表: {table}[/green]")
            except Exception as e:
                console.print(f"[yellow]! 删除表 {table} 时出错: {e}[/yellow]")
        
        # 删除相关索引
        indexes_to_drop = [
            'idx_stock_daily_symbol',
            'idx_stock_daily_date'
        ]
        
        for index in indexes_to_drop:
            try:
                cursor.execute(f'DROP INDEX IF EXISTS {index}')
            except Exception as e:
                pass
        
        conn.commit()
        conn.close()
        
        console.print("[green]✓ 旧表删除完成[/green]")
    
    def create_new_schema(self):
        """创建新的数据库架构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        console.print("[cyan]正在创建新的数据表结构...[/cyan]")
        
        # 创建股票基本信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_info (
                symbol TEXT PRIMARY KEY,
                name TEXT,
                market_type INTEGER,
                first_seen_date TEXT,
                last_updated TEXT
            )
        ''')
        console.print("[green]✓ 创建 stock_info 表[/green]")
        
        # 创建股票日线数据表 - 包含所有CSV字段
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                open_price REAL,
                high_price REAL,
                low_price REAL,
                close_price REAL,
                volume REAL,
                amount REAL,
                market_cap_float REAL,
                market_cap_total REAL,
                return_with_dividend REAL,
                return_no_dividend REAL,
                adj_price_with_dividend REAL,
                adj_price_no_dividend REAL,
                market_type INTEGER,
                cap_change_date TEXT,
                trade_status INTEGER,
                after_hours_volume REAL,
                after_hours_amount REAL,
                pre_close_price REAL,
                change_ratio REAL,
                limit_down REAL,
                limit_up REAL,
                limit_status INTEGER,
                UNIQUE(symbol, trade_date)
            )
        ''')
        console.print("[green]✓ 创建 stock_daily 表[/green]")
        
        # 创建索引以提高查询性能
        console.print("[cyan]正在创建索引...[/cyan]")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stock_daily_symbol 
            ON stock_daily(symbol)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stock_daily_date 
            ON stock_daily(trade_date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stock_daily_symbol_date 
            ON stock_daily(symbol, trade_date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_stock_daily_market_type 
            ON stock_daily(market_type)
        ''')
        
        console.print("[green]✓ 索引创建完成[/green]")
        
        conn.commit()
        conn.close()
        
        console.print("[green]✓ 新数据表结构创建完成[/green]")
    
    def migrate(self):
        """执行完整的迁移流程"""
        console.print("\n[bold cyan]开始数据库迁移...[/bold cyan]\n")
        
        # 1. 备份数据库
        self.backup_database()
        
        # 2. 删除旧表
        self.drop_old_tables()
        
        # 3. 创建新架构
        self.create_new_schema()
        
        console.print("\n[bold green]数据库迁移完成！[/bold green]")
        if self.backup_path:
            console.print(f"[yellow]原数据库已备份至: {self.backup_path}[/yellow]")
        
        return True


def main():
    """主函数"""
    migration = DatabaseMigration()
    migration.migrate()


if __name__ == '__main__':
    main()
