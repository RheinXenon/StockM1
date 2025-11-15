"""
数据加载模块 - 从数据库加载股票数据
"""
import sys
import os
import pandas as pd
import sqlite3
from typing import Optional, List, Dict
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class StockDataLoader:
    """股票数据加载器"""
    
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def get_all_stocks(self) -> pd.DataFrame:
        """获取所有股票列表"""
        with self.get_connection() as conn:
            query = '''
                SELECT si.symbol, si.name, si.market_type as market,
                       COUNT(sd.id) as data_count,
                       MIN(sd.trade_date) as start_date,
                       MAX(sd.trade_date) as end_date
                FROM stock_info si
                LEFT JOIN stock_daily sd ON si.symbol = sd.symbol
                GROUP BY si.symbol, si.name, si.market_type
                HAVING data_count > 0
                ORDER BY si.symbol
            '''
            df = pd.read_sql_query(query, conn)
            return df
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """获取股票基本信息"""
        with self.get_connection() as conn:
            query = '''
                SELECT si.symbol, si.name, si.market_type as market,
                       COUNT(sd.id) as data_count,
                       MIN(sd.trade_date) as start_date,
                       MAX(sd.trade_date) as end_date,
                       AVG(sd.volume) as avg_volume,
                       AVG(sd.amount) as avg_amount
                FROM stock_info si
                LEFT JOIN stock_daily sd ON si.symbol = sd.symbol
                WHERE si.symbol = ?
                GROUP BY si.symbol, si.name, si.market_type
            '''
            cursor = conn.cursor()
            cursor.execute(query, (symbol,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'symbol': result[0],
                    'name': result[1] or symbol,
                    'market': result[2],
                    'data_count': result[3],
                    'start_date': result[4],
                    'end_date': result[5],
                    'avg_volume': result[6],
                    'avg_amount': result[7]
                }
            return None
    
    def get_stock_daily_data(self, 
                            symbol: str, 
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取股票日线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
        """
        with self.get_connection() as conn:
            query = '''
                SELECT 
                    trade_date as date,
                    open_price as open,
                    high_price as high,
                    low_price as low,
                    close_price as close,
                    volume,
                    amount,
                    return_with_dividend as pct_change
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
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
            
            return df
    
    def get_latest_price(self, symbol: str) -> Optional[Dict]:
        """获取股票最新价格"""
        with self.get_connection() as conn:
            query = '''
                SELECT trade_date, open_price, close_price, high_price, low_price, 
                       volume, return_with_dividend
                FROM stock_daily
                WHERE symbol = ?
                ORDER BY trade_date DESC
                LIMIT 1
            '''
            cursor = conn.cursor()
            cursor.execute(query, (symbol,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'date': result[0],
                    'open': result[1],
                    'close': result[2],
                    'high': result[3],
                    'low': result[4],
                    'volume': result[5],
                    'pct_change': result[6]
                }
            return None
    
    def get_multiple_stocks_data(self, 
                                symbols: List[str],
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """获取多只股票的数据"""
        result = {}
        for symbol in symbols:
            df = self.get_stock_daily_data(symbol, start_date, end_date)
            if not df.empty:
                result[symbol] = df
        return result
    
    def get_stock_statistics(self, symbol: str, days: int = 30) -> Optional[Dict]:
        """
        获取股票统计信息
        
        Args:
            symbol: 股票代码
            days: 统计天数
        """
        with self.get_connection() as conn:
            query = '''
                SELECT 
                    AVG(close_price) as avg_close,
                    MAX(high_price) as max_high,
                    MIN(low_price) as min_low,
                    AVG(volume) as avg_volume,
                    SUM(volume) as total_volume,
                    AVG(return_with_dividend) as avg_pct_change,
                    MAX(return_with_dividend) as max_pct_change,
                    MIN(return_with_dividend) as min_pct_change
                FROM (
                    SELECT * FROM stock_daily
                    WHERE symbol = ?
                    ORDER BY trade_date DESC
                    LIMIT ?
                )
            '''
            cursor = conn.cursor()
            cursor.execute(query, (symbol, days))
            result = cursor.fetchone()
            
            if result:
                return {
                    'avg_close': result[0],
                    'max_high': result[1],
                    'min_low': result[2],
                    'avg_volume': result[3],
                    'total_volume': result[4],
                    'avg_pct_change': result[5],
                    'max_pct_change': result[6],
                    'min_pct_change': result[7]
                }
            return None
    
    def search_stocks(self, keyword: str) -> pd.DataFrame:
        """搜索股票（按代码或名称）"""
        with self.get_connection() as conn:
            query = '''
                SELECT si.symbol, si.name, si.market_type as market,
                       COUNT(sd.id) as data_count
                FROM stock_info si
                LEFT JOIN stock_daily sd ON si.symbol = sd.symbol
                WHERE si.symbol LIKE ? OR si.name LIKE ?
                GROUP BY si.symbol, si.name, si.market_type
                HAVING data_count > 0
                ORDER BY si.symbol
                LIMIT 50
            '''
            search_pattern = f'%{keyword}%'
            df = pd.read_sql_query(query, conn, params=[search_pattern, search_pattern])
            return df
    
    def get_index_data(self, symbol: str,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> pd.DataFrame:
        """获取指数数据"""
        with self.get_connection() as conn:
            query = 'SELECT * FROM index_daily WHERE symbol = ?'
            params = [symbol]
            
            if start_date:
                query += ' AND date >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND date <= ?'
                params.append(end_date)
            
            query += ' ORDER BY date'
            
            df = pd.read_sql_query(query, conn, params=params)
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
            
            return df
