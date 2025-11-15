"""
数据库管理模块
"""
import sqlite3
import pandas as pd
from typing import Optional, List
from datetime import datetime
import threading
import config


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self._local = threading.local()
        self.init_database()
    
    def connect(self):
        """连接数据库 - 每个线程使用独立的连接"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
        return self._local.conn
    
    def close(self):
        """关闭当前线程的数据库连接"""
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # 股票基本信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_info (
                symbol TEXT PRIMARY KEY,
                name TEXT,
                market TEXT,
                updated_at TEXT
            )
        ''')
        
        # 股票日线数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                close REAL,
                high REAL,
                low REAL,
                volume REAL,
                amount REAL,
                pct_change REAL,
                UNIQUE(symbol, date)
            )
        ''')
        
        # 指数日线数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS index_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                close REAL,
                high REAL,
                low REAL,
                volume REAL,
                UNIQUE(symbol, date)
            )
        ''')
        
        # 模拟账户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS account (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                initial_capital REAL NOT NULL,
                current_capital REAL NOT NULL,
                current_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 持仓表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                avg_cost REAL NOT NULL,
                current_price REAL,
                updated_at TEXT,
                FOREIGN KEY (account_id) REFERENCES account(id),
                UNIQUE(account_id, symbol)
            )
        ''')
        
        # 交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                trade_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                commission REAL NOT NULL,
                stamp_tax REAL NOT NULL,
                total_amount REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (account_id) REFERENCES account(id)
            )
        ''')
        
        # 创建索引（优化性能）
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_daily_symbol ON stock_daily(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_daily_date ON stock_daily(date)')
        # 添加复合索引用于快速查询
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_daily_symbol_date ON stock_daily(symbol, date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_info_name ON stock_info(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_index_daily_symbol ON index_daily(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_index_daily_date ON index_daily(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)')
        
        conn.commit()
    
    def save_stock_info(self, stock_list: pd.DataFrame):
        """保存股票基本信息"""
        conn = self.connect()
        
        for _, row in stock_list.iterrows():
            conn.execute('''
                INSERT OR REPLACE INTO stock_info (symbol, name, market, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (row['code'], row['name'], 'A股', datetime.now().isoformat()))
        
        conn.commit()
    
    def save_stock_daily_data(self, symbol: str, df: pd.DataFrame):
        """保存股票日线数据"""
        if df.empty:
            return
        
        conn = self.connect()
        
        for _, row in df.iterrows():
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO stock_daily 
                    (symbol, date, open, close, high, low, volume, amount, pct_change)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    row.get('date', ''),
                    float(row.get('open', 0)),
                    float(row.get('close', 0)),
                    float(row.get('high', 0)),
                    float(row.get('low', 0)),
                    float(row.get('volume', 0)),
                    float(row.get('amount', 0)),
                    float(row.get('pct_change', 0))
                ))
            except Exception as e:
                print(f"保存数据失败 {symbol} {row.get('date')}: {e}")
                continue
        
        conn.commit()
    
    def save_index_daily_data(self, symbol: str, df: pd.DataFrame):
        """
        保存指数日线数据
        注意：为避免与股票代码冲突，指数代码会自动添加99前缀
        例如：000001 -> 99000001, 399001 -> 99399001
        """
        if df.empty:
            return
        
        conn = self.connect()
        
        # 添加99前缀避免与股票代码冲突
        index_symbol = f"99{symbol}"
        
        for _, row in df.iterrows():
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO index_daily 
                    (symbol, date, open, close, high, low, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    index_symbol,  # 使用添加前缀后的代码
                    row.get('date', ''),
                    float(row.get('open', 0)),
                    float(row.get('close', 0)),
                    float(row.get('high', 0)),
                    float(row.get('low', 0)),
                    float(row.get('volume', 0))
                ))
            except Exception as e:
                print(f"保存指数数据失败 {index_symbol} {row.get('date')}: {e}")
                continue
        
        conn.commit()
    
    def get_stock_data(self, 
                       symbol: str, 
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取股票历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume, amount, etc.
        """
        conn = self.connect()
        
        # 使用新的字段名，并重命名为兼容的格式
        query = '''
            SELECT 
                trade_date as date,
                open_price as open,
                high_price as high,
                low_price as low,
                close_price as close,
                volume,
                amount,
                return_with_dividend as pct_change,
                market_cap_float,
                market_cap_total,
                adj_price_with_dividend,
                market_type,
                trade_status,
                change_ratio,
                limit_status
            FROM stock_daily 
            WHERE symbol = ?
        '''
        params = [symbol]
        
        if start_date:
            query += ' AND trade_date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND trade_date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY trade_date'
        
        df = pd.read_sql_query(query, conn, params=params)
        return df
    
    def get_stock_price_on_date(self, symbol: str, date: str) -> Optional[dict]:
        """获取某只股票在特定日期的价格信息"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT open_price, close_price, high_price, low_price, volume
            FROM stock_daily
            WHERE symbol = ? AND trade_date = ?
        ''', (symbol, date))
        
        result = cursor.fetchone()
        if result:
            return {
                'open': result[0],
                'close': result[1],
                'high': result[2],
                'low': result[3],
                'volume': result[4]
            }
        return None
    
    def get_available_dates(self, symbol: str) -> List[str]:
        """获取某只股票的所有可用交易日期"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT trade_date FROM stock_daily
            WHERE symbol = ?
            ORDER BY trade_date
        ''', (symbol,))
        
        return [row[0] for row in cursor.fetchall()]
    
    def get_all_stocks(self) -> pd.DataFrame:
        """获取所有股票列表"""
        conn = self.connect()
        return pd.read_sql_query('SELECT * FROM stock_info', conn)
    
    def get_stock_list_for_download(self) -> pd.DataFrame:
        """获取股票列表（用于下载页面，格式与API一致：code, name）"""
        conn = self.connect()
        df = pd.read_sql_query('SELECT symbol as code, name FROM stock_info ORDER BY symbol', conn)
        return df
    
    def get_stock_list_count(self) -> int:
        """获取股票列表数量"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM stock_info')
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def get_stocks_with_data_count(self) -> pd.DataFrame:
        """获取股票列表及其数据条数"""
        conn = self.connect()
        query = '''
            SELECT si.symbol, si.name, COUNT(sd.id) as data_count
            FROM stock_info si
            LEFT JOIN stock_daily sd ON si.symbol = sd.symbol
            GROUP BY si.symbol, si.name
            ORDER BY data_count DESC
        '''
        return pd.read_sql_query(query, conn)

    def get_all_stock_daily(self) -> pd.DataFrame:
        """获取所有股票的日线数据（包含名称）"""
        conn = self.connect()
        query = '''
            SELECT 
                sd.symbol,
                COALESCE(si.name, sd.symbol) AS name,
                sd.trade_date as date,
                sd.open_price as open,
                sd.close_price as close,
                sd.high_price as high,
                sd.low_price as low,
                sd.volume,
                sd.amount,
                sd.return_with_dividend as pct_change
            FROM stock_daily sd
            LEFT JOIN stock_info si ON sd.symbol = si.symbol
            ORDER BY sd.symbol, sd.trade_date
        '''
        return pd.read_sql_query(query, conn)
    
    def get_index_data(self,
                      symbol: str,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取指数历史数据
        
        Args:
            symbol: 指数原始代码（如：000001, 399001），会自动添加99前缀查询
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        conn = self.connect()
        
        # 添加99前缀以匹配数据库中的存储格式
        index_symbol = f"99{symbol}"
        
        query = '''
            SELECT 
                date,
                open,
                close,
                high,
                low,
                volume
            FROM index_daily
            WHERE symbol = ?
        '''
        params = [index_symbol]
        
        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY date'
        
        df = pd.read_sql_query(query, conn, params=params)
        return df
