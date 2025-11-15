"""
Qwen Agent实现
"""
import json
from openai import OpenAI
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts.system_prompt import SYSTEM_PROMPT, DAILY_DECISION_PROMPT


class QwenAgent(BaseAgent):
    """基于Qwen3-30B-A3B的交易Agent"""
    
    def __init__(self, 
                 agent_id: str = "qwen",
                 name: str = "Qwen交易助手",
                 api_base: str = "https://api.suanli.cn/v1",
                 api_key: str = "",
                 model: str = "free:Qwen3-30B-A3B",
                 temperature: float = 0.7):
        super().__init__(agent_id, name)
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.conversation_history = []  # 对话历史
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=api_base,
            api_key=api_key
        )
        
        # 初始化系统提示词
        self.system_prompt = SYSTEM_PROMPT
    
    def _call_api(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> Dict:
        """
        调用Qwen API
        
        Args:
            messages: 消息列表
            tools: 工具定义列表（OpenAI格式）
        
        Returns:
            API响应
        """
        try:
            # 设置extra_body参数
            extra_body = {
                "enable_thinking": False,  # 交易决策不需要thinking输出
            }
            
            # 构造API调用参数
            api_params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": 2000,
                "extra_body": extra_body
            }
            
            # 如果提供了工具定义，添加到请求中
            if tools:
                api_params["tools"] = tools
                api_params["tool_choice"] = "auto"
            
            # 调用API（非流式）
            response = self.client.chat.completions.create(**api_params)
            
            # 转换为字典格式
            return response.model_dump()
            
        except Exception as e:
            return {"error": f"API调用失败: {str(e)}"}
    
    def make_decision(self, 
                     current_date: str,
                     portfolio_info: Dict,
                     tools: Any,
                     context: Optional[Dict] = None) -> Dict:
        """
        使用Qwen模型做出交易决策
        
        Args:
            current_date: 当前日期
            portfolio_info: 账户信息
            tools: TradingTools实例
            context: 额外上下文
        
        Returns:
            决策结果
        """
        # 准备每日决策提示
        daily_prompt = DAILY_DECISION_PROMPT.format(
            current_date=current_date,
            cash=portfolio_info['cash'],
            market_value=portfolio_info['market_value'],
            total_asset=portfolio_info['total_asset'],
            total_return=portfolio_info['total_profit_rate']
        )
        
        # 构建消息
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": daily_prompt}
        ]
        
        # 获取工具定义
        tools_def = tools.get_tools_definition()
        
        # 开始对话循环（支持多轮工具调用）
        max_iterations = 10  # 最多10轮对话
        iteration = 0
        final_decision = None
        tool_call_results = []
        
        while iteration < max_iterations:
            iteration += 1
            
            # 调用API
            response = self._call_api(messages, tools_def)
            
            if "error" in response:
                return {
                    'actions': [],
                    'reasoning': f"API调用失败: {response['error']}",
                    'analysis': '',
                    'success': False
                }
            
            # 解析响应
            if "choices" not in response or len(response["choices"]) == 0:
                return {
                    'actions': [],
                    'reasoning': "API返回格式错误",
                    'analysis': '',
                    'success': False
                }
            
            choice = response["choices"][0]
            message = choice["message"]
            
            # 添加助手回复到消息历史
            messages.append(message)
            
            # 检查是否有工具调用
            if message.get("tool_calls"):
                # 处理工具调用
                for tool_call in message["tool_calls"]:
                    function = tool_call["function"]
                    tool_name = function["name"]
                    
                    try:
                        arguments = json.loads(function["arguments"])
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    # 执行工具
                    tool_result = tools.execute_tool(
                        tool_name, 
                        arguments, 
                        current_date, 
                        context['portfolio'] if context else None
                    )
                    
                    # 记录工具调用
                    tool_call_results.append({
                        'tool': tool_name,
                        'arguments': arguments,
                        'result': tool_result
                    })
                    
                    # 添加工具结果到消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
                        "content": tool_result
                    })
                
                # 继续下一轮对话
                continue
            
            # 如果没有工具调用，说明Agent已经完成决策
            final_response = message.get("content", "")
            
            # 解析决策
            decision = self._parse_decision(final_response, tool_call_results)
            decision['raw_response'] = final_response
            decision['tool_calls'] = tool_call_results
            decision['success'] = True
            
            final_decision = decision
            break
        
        # 如果达到最大迭代次数仍未完成
        if not final_decision:
            final_decision = {
                'actions': [],
                'reasoning': '达到最大对话轮数',
                'analysis': '',
                'success': False
            }
        
        # 记录决策
        self.record_decision(current_date, final_decision)
        
        return final_decision
    
    def _parse_decision(self, response_text: str, tool_calls: List[Dict]) -> Dict:
        """
        解析Agent的决策响应
        
        Args:
            response_text: Agent的文本回复
            tool_calls: 工具调用记录
        
        Returns:
            解析后的决策
        """
        actions = []
        
        # 从工具调用中提取交易动作
        for tool_call in tool_calls:
            tool_name = tool_call['tool']
            result = tool_call['result']
            
            # 解析结果
            try:
                result_data = json.loads(result)
                
                if tool_name == 'buy_stock' and 'action' in result_data:
                    actions.append({
                        'type': 'buy',
                        'symbol': result_data['symbol'],
                        'quantity': result_data['quantity']
                    })
                elif tool_name == 'sell_stock' and 'action' in result_data:
                    actions.append({
                        'type': 'sell',
                        'symbol': result_data['symbol'],
                        'quantity': result_data['quantity']
                    })
            except:
                pass
        
        # 提取分析和理由
        analysis = ""
        reasoning = ""
        
        # 简单解析（可以根据实际响应格式优化）
        if "**分析**" in response_text or "分析：" in response_text:
            parts = response_text.split("**决策**")
            if len(parts) > 0:
                analysis = parts[0].replace("**分析**", "").replace("分析：", "").strip()
        
        if "**理由**" in response_text or "理由：" in response_text:
            parts = response_text.split("**理由**")
            if len(parts) > 1:
                reasoning = parts[1].split("**")[0].replace("理由：", "").strip()
            else:
                parts = response_text.split("理由：")
                if len(parts) > 1:
                    reasoning = parts[1].strip()
        
        # 如果没有明确的分析和理由，使用整个响应
        if not analysis and not reasoning:
            analysis = response_text
            reasoning = response_text
        
        return {
            'actions': actions,
            'analysis': analysis[:500],  # 限制长度
            'reasoning': reasoning[:500]
        }
