"""
技术指标计算模块
"""
import pandas as pd
import numpy as np
from typing import Optional


def calculate_ma(df: pd.DataFrame, periods: list = [5, 10, 20, 60]) -> pd.DataFrame:
    """
    计算移动平均线
    
    Args:
        df: 包含close列的DataFrame
        periods: 周期列表
    """
    result = df.copy()
    for period in periods:
        result[f'MA{period}'] = result['close'].rolling(window=period).mean()
    return result


def calculate_ema(df: pd.DataFrame, periods: list = [12, 26]) -> pd.DataFrame:
    """
    计算指数移动平均线
    
    Args:
        df: 包含close列的DataFrame
        periods: 周期列表
    """
    result = df.copy()
    for period in periods:
        result[f'EMA{period}'] = result['close'].ewm(span=period, adjust=False).mean()
    return result


def calculate_macd(df: pd.DataFrame, 
                  fast_period: int = 12,
                  slow_period: int = 26,
                  signal_period: int = 9) -> pd.DataFrame:
    """
    计算MACD指标
    
    Args:
        df: 包含close列的DataFrame
        fast_period: 快线周期
        slow_period: 慢线周期
        signal_period: 信号线周期
    """
    result = df.copy()
    
    # 计算EMA
    ema_fast = result['close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = result['close'].ewm(span=slow_period, adjust=False).mean()
    
    # MACD线 = 快线EMA - 慢线EMA
    result['MACD'] = ema_fast - ema_slow
    
    # 信号线 = MACD的EMA
    result['MACD_signal'] = result['MACD'].ewm(span=signal_period, adjust=False).mean()
    
    # MACD柱 = MACD - 信号线
    result['MACD_hist'] = result['MACD'] - result['MACD_signal']
    
    return result


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    计算RSI指标
    
    Args:
        df: 包含close列的DataFrame
        period: 周期
    """
    result = df.copy()
    
    # 计算价格变化
    delta = result['close'].diff()
    
    # 分离上涨和下跌
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # 计算RS和RSI
    rs = gain / loss
    result['RSI'] = 100 - (100 / (1 + rs))
    
    return result


def calculate_bollinger_bands(df: pd.DataFrame, 
                              period: int = 20,
                              std_dev: float = 2.0) -> pd.DataFrame:
    """
    计算布林带
    
    Args:
        df: 包含close列的DataFrame
        period: 周期
        std_dev: 标准差倍数
    """
    result = df.copy()
    
    # 中轨 = MA
    result['BB_middle'] = result['close'].rolling(window=period).mean()
    
    # 标准差
    rolling_std = result['close'].rolling(window=period).std()
    
    # 上轨 = 中轨 + 标准差 * 倍数
    result['BB_upper'] = result['BB_middle'] + (rolling_std * std_dev)
    
    # 下轨 = 中轨 - 标准差 * 倍数
    result['BB_lower'] = result['BB_middle'] - (rolling_std * std_dev)
    
    return result


def calculate_kdj(df: pd.DataFrame, 
                 n: int = 9,
                 m1: int = 3,
                 m2: int = 3) -> pd.DataFrame:
    """
    计算KDJ指标
    
    Args:
        df: 包含high, low, close列的DataFrame
        n: RSV周期
        m1: K值平滑周期
        m2: D值平滑周期
    """
    result = df.copy()
    
    # 计算RSV
    low_list = result['low'].rolling(window=n, min_periods=1).min()
    high_list = result['high'].rolling(window=n, min_periods=1).max()
    rsv = (result['close'] - low_list) / (high_list - low_list) * 100
    
    # 计算K值
    result['K'] = rsv.ewm(com=m1-1, adjust=False).mean()
    
    # 计算D值
    result['D'] = result['K'].ewm(com=m2-1, adjust=False).mean()
    
    # 计算J值
    result['J'] = 3 * result['K'] - 2 * result['D']
    
    return result


def calculate_volume_ma(df: pd.DataFrame, periods: list = [5, 10]) -> pd.DataFrame:
    """
    计算成交量移动平均
    
    Args:
        df: 包含volume列的DataFrame
        periods: 周期列表
    """
    result = df.copy()
    for period in periods:
        result[f'VOL_MA{period}'] = result['volume'].rolling(window=period).mean()
    return result


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    计算所有技术指标
    
    Args:
        df: 原始数据DataFrame
    """
    if df.empty:
        return df
    
    result = df.copy()
    
    # MA
    result = calculate_ma(result, [5, 10, 20, 60, 120])
    
    # EMA
    result = calculate_ema(result, [12, 26])
    
    # MACD
    result = calculate_macd(result)
    
    # RSI
    result = calculate_rsi(result, 14)
    
    # 布林带
    result = calculate_bollinger_bands(result)
    
    # KDJ
    result = calculate_kdj(result)
    
    # 成交量MA
    result = calculate_volume_ma(result, [5, 10])
    
    return result


def calculate_returns(df: pd.DataFrame) -> pd.DataFrame:
    """计算收益率"""
    result = df.copy()
    
    # 日收益率
    result['daily_return'] = result['close'].pct_change()
    
    # 累计收益率
    result['cumulative_return'] = (1 + result['daily_return']).cumprod() - 1
    
    return result


def calculate_volatility(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """计算波动率"""
    result = df.copy()
    
    # 计算日收益率
    returns = result['close'].pct_change()
    
    # 滚动标准差（波动率）
    result['volatility'] = returns.rolling(window=window).std() * np.sqrt(252)  # 年化波动率
    
    return result
