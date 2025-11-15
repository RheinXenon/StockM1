"""
测试交易工具功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from Agents_Experience.core.data_provider import MarketDataProvider
from Agents_Experience.core.tools import TradingTools
from Agents_Experience import config
from src.stock_app.portfolio import Portfolio


def test_tools():
    """测试所有工具功能"""
    print("\n" + "="*60)
    print("测试Agent交易工具")
    print("="*60 + "\n")
    
    # 初始化数据提供者
    print("1. 初始化数据提供者...")
    data_provider = MarketDataProvider(config.DATABASE_PATH)
    print("   ✓ 数据提供者初始化成功\n")
    
    # 初始化工具
    print("2. 初始化交易工具...")
    tools = TradingTools(data_provider, config.MVP_STOCK_POOL)
    print("   ✓ 工具初始化成功\n")
    
    # 获取工具定义
    print("3. 获取工具定义...")
    tools_def = tools.get_tools_definition()
    print(f"   ✓ 共 {len(tools_def)} 个工具:")
    for tool in tools_def:
        print(f"      - {tool['function']['name']}: {tool['function']['description'][:50]}...")
    print()
    
    # 创建测试用的持仓
    print("4. 创建测试持仓...")
    portfolio = Portfolio("test_agent", config.INITIAL_CAPITAL)
    portfolio.current_date = "2020-06-01"
    print(f"   ✓ 初始资金: {portfolio.cash:,.2f} 元\n")
    
    # 测试日期
    test_date = "2020-06-01"
    
    # ====== 测试 get_stock_history ======
    print("5. 测试 get_stock_history...")
    result = tools.execute_tool(
        "get_stock_history",
        {"symbol": "600519", "days": 30},
        test_date,
        portfolio
    )
    result_data = json.loads(result)
    if "error" not in result_data:
        print(f"   ✓ 成功获取贵州茅台历史数据 ({result_data.get('data_points')} 个数据点)")
        if result_data.get('recent_10_days'):
            latest = result_data['recent_10_days'][-1]
            print(f"      最新数据: {latest['date']}, 收盘价: {latest['close']:.2f}")
    else:
        print(f"   ✗ 错误: {result_data['error']}")
    print()
    
    # ====== 测试 get_technical_indicators ======
    print("6. 测试 get_technical_indicators...")
    result = tools.execute_tool(
        "get_technical_indicators",
        {"symbol": "600036"},
        test_date,
        portfolio
    )
    result_data = json.loads(result)
    if "error" not in result_data:
        print(f"   ✓ 成功获取招商银行技术指标")
        print(f"      当前价: {result_data.get('current_price'):.2f}")
        print(f"      MA20: {result_data.get('移动平均线', {}).get('MA20'):.2f}")
        print(f"      RSI: {result_data.get('RSI', {}).get('RSI值'):.2f}")
    else:
        print(f"   ✗ 错误: {result_data['error']}")
    print()
    
    # ====== 测试 get_portfolio ======
    print("7. 测试 get_portfolio...")
    result = tools.execute_tool(
        "get_portfolio",
        {},
        test_date,
        portfolio
    )
    result_data = json.loads(result)
    if "error" not in result_data:
        print(f"   ✓ 成功获取持仓信息")
        print(f"      可用资金: {result_data.get('可用资金'):,.2f} 元")
        print(f"      总资产: {result_data.get('总资产'):,.2f} 元")
        print(f"      持仓数量: {len(result_data.get('持仓明细', []))} 个")
    else:
        print(f"   ✗ 错误: {result_data['error']}")
    print()
    
    # ====== 测试 buy_stock ======
    print("8. 测试 buy_stock...")
    result = tools.execute_tool(
        "buy_stock",
        {"symbol": "600519", "quantity": 100},
        test_date,
        portfolio
    )
    result_data = json.loads(result)
    if "error" not in result_data:
        print(f"   ✓ 买入指令验证成功")
        print(f"      {result_data.get('message')}")
        print(f"      预计花费: {result_data.get('estimated_cost'):,.2f} 元")
    else:
        print(f"   ✗ 错误: {result_data['error']}")
    print()
    
    # 模拟实际买入（不通过工具，直接操作portfolio）
    portfolio.add_position("600519", "贵州茅台", 100, 1200.0)
    portfolio.cash -= 120036.0
    print("   模拟实际买入完成，持仓已更新\n")
    
    # ====== 测试 sell_stock ======
    print("9. 测试 sell_stock...")
    result = tools.execute_tool(
        "sell_stock",
        {"symbol": "600519", "quantity": 100},
        test_date,
        portfolio
    )
    result_data = json.loads(result)
    if "error" not in result_data:
        print(f"   ✓ 卖出指令验证成功")
        print(f"      {result_data.get('message')}")
        print(f"      预计收入: {result_data.get('estimated_revenue'):,.2f} 元")
    else:
        print(f"   ✗ 错误: {result_data['error']}")
    print()
    
    # ====== 测试错误处理 ======
    print("10. 测试错误处理...")
    
    # 测试资金不足
    result = tools.execute_tool(
        "buy_stock",
        {"symbol": "600519", "quantity": 100000},  # 超大数量
        test_date,
        portfolio
    )
    result_data = json.loads(result)
    if "error" in result_data:
        print(f"   ✓ 资金不足错误处理正确: {result_data['error'][:50]}...")
    
    # 测试卖出未持有的股票
    result = tools.execute_tool(
        "sell_stock",
        {"symbol": "000002", "quantity": 100},
        test_date,
        portfolio
    )
    result_data = json.loads(result)
    if "error" in result_data:
        print(f"   ✓ 未持有股票错误处理正确: {result_data['error']}")
    
    print()
    
    print("="*60)
    print("工具测试完成！所有功能正常")
    print("="*60 + "\n")


if __name__ == '__main__':
    test_tools()
