"""
日志工具
"""
import logging
import os
import csv
from datetime import datetime


def setup_logger(name: str, log_dir: str = None) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志名称
        log_dir: 日志目录
    
    Returns:
        Logger实例
    """
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 文件handler
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加handler
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


class DualLogger:
    """
    双日志系统：同时维护AI决策日志和资产记录日志
    """
    
    def __init__(self, agent_name: str, log_dir: str = None):
        """
        初始化双日志系统
        
        Args:
            agent_name: Agent名称
            log_dir: 日志目录
        """
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        
        os.makedirs(log_dir, exist_ok=True)
        
        # 生成时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 决策日志文件（记录AI完整决策过程）
        self.decision_log_path = os.path.join(log_dir, f"{agent_name}_decision_{timestamp}.log")
        
        # 资产日志文件（记录每日资产情况）
        self.portfolio_log_path = os.path.join(log_dir, f"{agent_name}_portfolio_{timestamp}.csv")
        
        # 创建决策日志文件
        self.decision_file = open(self.decision_log_path, 'w', encoding='utf-8')
        
        # 创建资产日志CSV
        self.portfolio_file = open(self.portfolio_log_path, 'w', encoding='utf-8', newline='')
        self.portfolio_writer = csv.writer(self.portfolio_file)
        
        # 写入CSV表头
        self.portfolio_writer.writerow([
            '日期', '现金', '市值', '总资产', '收益率(%)', '持仓详情'
        ])
        self.portfolio_file.flush()
        
        print(f"\n日志文件已创建:")
        print(f"  决策日志: {self.decision_log_path}")
        print(f"  资产日志: {self.portfolio_log_path}\n")
    
    def log_decision(self, date: str, decision_info: dict):
        """
        记录AI决策过程
        
        Args:
            date: 日期
            decision_info: 决策信息
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 写入决策日志
        self.decision_file.write(f"{'='*80}\n")
        self.decision_file.write(f"[{timestamp}] 交易日期: {date}\n")
        self.decision_file.write(f"{'='*80}\n\n")
        
        # 记录市场分析
        if 'analysis' in decision_info:
            self.decision_file.write(f"【市场分析】\n{decision_info['analysis']}\n\n")
        
        # 记录决策理由
        if 'reasoning' in decision_info:
            self.decision_file.write(f"【决策理由】\n{decision_info['reasoning']}\n\n")
        
        # 记录工具调用
        if 'tool_calls' in decision_info and decision_info['tool_calls']:
            self.decision_file.write(f"【工具调用记录】\n")
            for i, tool_call in enumerate(decision_info['tool_calls'], 1):
                self.decision_file.write(f"  {i}. {tool_call['tool']}\n")
                self.decision_file.write(f"     参数: {tool_call['arguments']}\n")
                self.decision_file.write(f"     结果: {tool_call['result']}\n\n")
        
        # 记录交易动作
        if 'actions' in decision_info and decision_info['actions']:
            self.decision_file.write(f"【交易决策】\n")
            for action in decision_info['actions']:
                action_type = action['type']
                symbol = action['symbol']
                quantity = action['quantity']
                self.decision_file.write(f"  {action_type.upper()}: {symbol} x {quantity}股\n")
        else:
            self.decision_file.write(f"【交易决策】\n  保持持仓，不进行交易\n")
        
        # 记录原始响应
        if 'raw_response' in decision_info:
            self.decision_file.write(f"\n【AI原始回复】\n{decision_info['raw_response']}\n")
        
        self.decision_file.write(f"\n\n")
        self.decision_file.flush()
    
    def log_portfolio(self, date: str, portfolio_summary: dict, positions: dict):
        """
        记录每日资产情况
        
        Args:
            date: 日期
            portfolio_summary: 账户摘要
            positions: 持仓详情
        """
        # 格式化持仓详情
        position_details = []
        for symbol, pos in positions.items():
            position_details.append(
                f"{symbol}:{pos.quantity}股@{pos.current_price:.2f}元(收益率{pos.profit_rate:.2f}%)"
            )
        
        positions_str = '; '.join(position_details) if position_details else '无持仓'
        
        # 写入CSV
        self.portfolio_writer.writerow([
            date,
            f"{portfolio_summary['cash']:.2f}",
            f"{portfolio_summary['market_value']:.2f}",
            f"{portfolio_summary['total_asset']:.2f}",
            f"{portfolio_summary['total_profit_rate']:.2f}",
            positions_str
        ])
        self.portfolio_file.flush()
    
    def close(self):
        """关闭日志文件"""
        self.decision_file.close()
        self.portfolio_file.close()
        print(f"\n日志文件已保存:")
        print(f"  决策日志: {self.decision_log_path}")
        print(f"  资产日志: {self.portfolio_log_path}")
