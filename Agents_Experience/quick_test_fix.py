"""
快速测试修复效果 - 运行1天模拟
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Agents_Experience import config
from Agents_Experience.agents.qwen_agent import QwenAgent
from Agents_Experience.core.simulator import TradingSimulator


def quick_test():
    """快速测试1天的模拟"""
    print("\n" + "="*60)
    print("快速测试 - 验证工具调用修复")
    print("="*60 + "\n")
    
    print("测试配置：")
    print(f"  日期范围: 2020-01-02 (仅1天)")
    print(f"  初始资金: {config.INITIAL_CAPITAL:,.2f} 元")
    print(f"  股票池: {', '.join(config.MVP_STOCK_POOL)}\n")
    
    # 创建 Agent
    agent = QwenAgent(
        agent_id="quick_test",
        name="测试Agent",
        api_base=config.QWEN_API_BASE,
        api_key=config.QWEN_API_KEY,
        model=config.QWEN_MODEL,
        temperature=0.7
    )
    
    # 创建模拟器（只测试1天）
    simulator = TradingSimulator(
        agent=agent,
        stock_pool=config.MVP_STOCK_POOL,
        initial_capital=config.INITIAL_CAPITAL,
        start_date="2020-01-02",  # 只测试第一天
        end_date="2020-01-02",
        db_path=config.DATABASE_PATH
    )
    
    print("开始运行...\n")
    
    try:
        report = simulator.run()
        
        print("\n" + "="*60)
        print("测试结果分析")
        print("="*60)
        
        if report:
            print(f"\n✓ 模拟成功完成")
            print(f"\n关键指标：")
            print(f"  交易次数: {report['total_trades']}")
            print(f"  买入次数: {report['buy_trades']}")
            print(f"  卖出次数: {report['sell_trades']}")
            print(f"  最终资金: {report['final_asset']:,.2f} 元")
            print(f"  收益率: {report['total_return']:.2f}%")
            
            if report['total_trades'] > 0:
                print(f"\n✅ 成功！Agent 执行了交易操作")
                print(f"\n交易记录：")
                for trade in report['trade_log']:
                    print(f"  - {trade['type'].upper()}: {trade['symbol']} "
                          f"{trade['quantity']}股 @ {trade['price']:.2f}元")
            else:
                print(f"\n⚠️ Agent 没有执行任何交易")
                print(f"  这可能是因为：")
                print(f"  1. Agent 分析后认为当天不适合交易（持有观望）")
                print(f"  2. Agent 仍然没有调用交易工具（需要进一步优化提示词）")
                print(f"\n建议：检查控制台输出，看 Agent 是否提到要买入/卖出")
            
            if report['final_positions']:
                print(f"\n最终持仓：")
                for pos in report['final_positions']:
                    print(f"  {pos['symbol']} {pos['name']}: {pos['quantity']}股")
        else:
            print(f"\n✗ 模拟失败")
        
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    quick_test()
