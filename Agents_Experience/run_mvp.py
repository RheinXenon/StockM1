"""
MVP测试脚本 - 运行Qwen Agent交易模拟
"""
import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Agents_Experience import config
from Agents_Experience.agents.qwen_agent import QwenAgent
from Agents_Experience.core.simulator import TradingSimulator
from Agents_Experience.utils.logger import setup_logger


def main():
    """运行MVP测试"""
    print("\n" + "="*60)
    print("Agent股票交易模拟系统 - MVP版本")
    print("="*60 + "\n")
    
    # 设置日志
    logger = setup_logger('agent_qwen')
    logger.info("开始MVP测试")
    
    # 创建Qwen Agent
    print("初始化Qwen Agent...")
    agent = QwenAgent(
        agent_id="qwen_mvp",
        name="Qwen交易助手",
        api_base=config.QWEN_API_BASE,
        api_key=config.QWEN_API_KEY,
        model=config.QWEN_MODEL,
        temperature=config.TEMPERATURE,
        stock_pool=config.MVP_STOCK_POOL,
        stock_names=config.STOCK_NAMES
    )
    print(f"✓ Agent初始化完成: {agent.name}")
    print(f"  模型: {config.QWEN_MODEL}")
    print(f"  温度: {config.TEMPERATURE}")
    print(f"  股票池: {len(config.MVP_STOCK_POOL)}只股票\n")
    
    # 创建模拟器
    print("初始化交易模拟器...")
    simulator = TradingSimulator(
        agent=agent,
        stock_pool=config.MVP_STOCK_POOL,
        initial_capital=config.INITIAL_CAPITAL,
        start_date=config.MVP_START_DATE,
        end_date=config.MVP_END_DATE,
        db_path=config.DATABASE_PATH
    )
    print("✓ 模拟器初始化完成\n")
    
    # 运行模拟
    try:
        report = simulator.run()
        
        # 保存结果
        if report:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = os.path.join(
                config.RESULTS_DIR,
                f'performance_report_{timestamp}.json'
            )
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n报告已保存至: {report_file}")
            logger.info(f"模拟完成，报告保存至: {report_file}")
            
            # 打印关键指标
            print("\n" + "="*60)
            print("MVP测试完成！")
            print("="*60)
            print(f"收益率: {report['total_return']:.2f}%")
            print(f"最大回撤: {report['max_drawdown']:.2f}%")
            print(f"交易次数: {report['total_trades']}")
            print("="*60 + "\n")
            
            return report
        else:
            print("\n模拟失败，未生成报告")
            logger.error("模拟失败")
            return None
            
    except KeyboardInterrupt:
        print("\n\n用户中断模拟")
        logger.info("用户中断模拟")
        return None
    except Exception as e:
        print(f"\n模拟过程中发生错误: {e}")
        logger.error(f"模拟错误: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    main()
