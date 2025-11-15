"""
数据提供接口 - 为Agent提供市场数据（严格控制只能访问历史数据）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from src.stock_app.database import Database
import config as main_config


class MarketDataProvider:
    """市场数据提供者 - 确保Agent只能访问历史数据"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = main_config.DATABASE_PATH
        self.db = Database(db_path)
    
    def get_stock_history(self, symbol: str, current_date: str, days: int = 60) -> pd.DataFrame:
        """
        获取股票历史数据
        
        Args:
            symbol: 股票代码
            current_date: 当前模拟日期
            days: 获取最近N天的数据
        
        Returns:
            DataFrame包含：date, open, high, low, close, volume等
        """
        # 计算开始日期
        current_dt = datetime.strptime(current_date, '%Y-%m-%d')
        start_dt = current_dt - timedelta(days=days*2)  # 多取一些，因为有非交易日
        start_date = start_dt.strftime('%Y-%m-%d')
        
        # 获取数据（确保不包含未来数据）
        df = self.db.get_stock_data(
            symbol=symbol,
            start_date=start_date,
            end_date=current_date  # 关键：只到当前日期
        )
        
        if df.empty:
            return df
        
        # 只返回最近的N个交易日
        df = df.tail(days)
        
        return df[['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_change']]
    
    def get_stock_price_on_date(self, symbol: str, date: str) -> Optional[Dict]:
        """获取某日的股票价格"""
        return self.db.get_stock_price_on_date(symbol, date)
    
    def get_technical_indicators(self, symbol: str, current_date: str, days: int = 60) -> Dict:
        """
        计算技术指标
        
        Returns:
            包含MA、MACD、RSI、KDJ等指标的字典
        """
        df = self.get_stock_history(symbol, current_date, days)
        
        if df.empty or len(df) < 20:
            return {}
        
        # 计算移动平均线
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        
        # 计算MACD
        df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']
        
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 获取最新值
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        indicators = {
            'symbol': symbol,
            'date': latest['date'],
            'current_price': float(latest['close']),
            'MA5': float(latest['MA5']) if pd.notna(latest['MA5']) else None,
            'MA10': float(latest['MA10']) if pd.notna(latest['MA10']) else None,
            'MA20': float(latest['MA20']) if pd.notna(latest['MA20']) else None,
            'MACD': float(latest['MACD']) if pd.notna(latest['MACD']) else None,
            'MACD_Signal': float(latest['Signal']) if pd.notna(latest['Signal']) else None,
            'MACD_Hist': float(latest['MACD_Hist']) if pd.notna(latest['MACD_Hist']) else None,
            'RSI': float(latest['RSI']) if pd.notna(latest['RSI']) else None,
            'volume': float(latest['volume']),
            'pct_change': float(latest['pct_change']) if pd.notna(latest['pct_change']) else 0,
            # 趋势判断
            'price_above_MA5': latest['close'] > latest['MA5'] if pd.notna(latest['MA5']) else None,
            'price_above_MA20': latest['close'] > latest['MA20'] if pd.notna(latest['MA20']) else None,
            'MA5_above_MA20': latest['MA5'] > latest['MA20'] if pd.notna(latest['MA5']) and pd.notna(latest['MA20']) else None,
            # MACD金叉死叉
            'MACD_golden_cross': (prev['MACD'] < prev['Signal'] and latest['MACD'] > latest['Signal']) 
                                  if pd.notna(prev['MACD']) and pd.notna(latest['MACD']) else False,
            'MACD_death_cross': (prev['MACD'] > prev['Signal'] and latest['MACD'] < latest['Signal']) 
                                 if pd.notna(prev['MACD']) and pd.notna(latest['MACD']) else False,
        }
        
        return indicators
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """获取股票基本信息"""
        conn = self.db.connect()
        cursor = conn.cursor()
        
        cursor.execute('SELECT symbol, name FROM stock_info WHERE symbol = ?', (symbol,))
        result = cursor.fetchone()
        
        if result:
            return {
                'symbol': result[0],
                'name': result[1]
            }
        return None
    
    def get_available_stocks(self, stock_pool: List[str]) -> List[Dict]:
        """获取可用股票列表信息"""
        stocks = []
        for symbol in stock_pool:
            info = self.get_stock_info(symbol)
            if info:
                stocks.append(info)
        return stocks
    
    def validate_trading_date(self, date: str, symbol: str) -> bool:
        """验证是否为交易日"""
        price_info = self.get_stock_price_on_date(symbol, date)
        return price_info is not None
