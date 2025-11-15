"""
测试数据库连接和数据可用性
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_PATH, MVP_STOCK_POOL, MVP_START_DATE, MVP_END_DATE
from core.data_provider import MarketDataProvider


def test_database():
    """测试数据库连接和数据"""
    print("测试数据库连接...")
    print(f"数据库路径: {DATABASE_PATH}")
    print(f"股票池: {MVP_STOCK_POOL}")
    print(f"测试日期: {MVP_START_DATE}\n")
    
    try:
        provider = MarketDataProvider(DATABASE_PATH)
        print("✓ 数据库连接成功\n")
        
        # 测试每只股票的数据
        for symbol in MVP_STOCK_POOL:
            print(f"测试股票 {symbol}:")
            
            # 获取股票信息
            info = provider.get_stock_info(symbol)
            if info:
                print(f"  名称: {info['name']}")
            else:
                print(f"  ✗ 未找到股票信息")
                continue
            
            # 获取历史数据
            df = provider.get_stock_history(symbol, MVP_START_DATE, 30)
            if not df.empty:
                print(f"  ✓ 历史数据: {len(df)} 条记录")
                print(f"  日期范围: {df.iloc[0]['date']} 至 {df.iloc[-1]['date']}")
            else:
                print(f"  ✗ 未找到历史数据")
                continue
            
            # 获取技术指标
            indicators = provider.get_technical_indicators(symbol, MVP_START_DATE, 60)
            if indicators:
                print(f"  ✓ 技术指标计算成功")
                print(f"  当前价: {indicators['current_price']:.2f}")
                if indicators['MA20']:
                    print(f"  MA20: {indicators['MA20']:.2f}")
                if indicators['RSI']:
                    print(f"  RSI: {indicators['RSI']:.2f}")
            else:
                print(f"  ✗ 技术指标计算失败")
            
            print()
        
        # 测试交易日数量
        dates = provider.db.get_available_dates(MVP_STOCK_POOL[0])
        from datetime import datetime
        start_dt = datetime.strptime(MVP_START_DATE, '%Y-%m-%d')
        end_dt = datetime.strptime(MVP_END_DATE, '%Y-%m-%d')
        
        trading_dates = [d for d in dates 
                        if start_dt <= datetime.strptime(d, '%Y-%m-%d') <= end_dt]
        
        print(f"交易日数量: {len(trading_dates)} 天")
        print(f"日期范围: {trading_dates[0]} 至 {trading_dates[-1]}")
        
        print("\n✓ 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_database()
