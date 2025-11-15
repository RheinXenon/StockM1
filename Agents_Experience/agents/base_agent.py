"""
Agent基类
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseAgent(ABC):
    """交易Agent基类"""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.decision_history = []  # 决策历史
    
    @abstractmethod
    def make_decision(self, 
                     current_date: str,
                     portfolio_info: Dict,
                     tools: Any,
                     context: Optional[Dict] = None) -> Dict:
        """
        做出交易决策
        
        Args:
            current_date: 当前日期
            portfolio_info: 账户信息（可用资金、持仓等）
            tools: 可用工具
            context: 额外上下文信息
        
        Returns:
            决策结果字典，包含：
            {
                'actions': [{'type': 'buy/sell', 'symbol': '...', 'quantity': ...}, ...],
                'reasoning': '决策理由',
                'analysis': '市场分析'
            }
        """
        pass
    
    def record_decision(self, date: str, decision: Dict):
        """记录决策"""
        self.decision_history.append({
            'date': date,
            'decision': decision
        })
    
    def get_decision_history(self) -> List[Dict]:
        """获取决策历史"""
        return self.decision_history
