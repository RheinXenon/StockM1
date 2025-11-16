"""
Qwen Agent实现
"""
import json
import time
from openai import OpenAI
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts.system_prompt import generate_system_prompt, DAILY_DECISION_PROMPT


class QwenAgent(BaseAgent):
    """基于Qwen3-30B-A3B的交易Agent"""
    
    def __init__(self, 
                 agent_id: str = "qwen",
                 name: str = "Qwen交易助手",
                 api_base: str = "https://api.suanli.cn/v1",
                 api_key: str = "",
                 model: str = "free:Qwen3-30B-A3B",
                 temperature: float = 0.7,
                 stock_pool: List[str] = None,
                 stock_names: Dict[str, str] = None,
                 api_call_interval: float = 2.0):
        super().__init__(agent_id, name)
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.conversation_history = []  # 对话历史
        self.api_call_interval = api_call_interval  # API调用间隔（秒）
        self.last_api_call_time = 0  # 上次API调用时间
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=api_base,
            api_key=api_key
        )
        
        # 动态生成系统提示词
        if stock_pool and stock_names:
            self.system_prompt = generate_system_prompt(stock_pool, stock_names)
        else:
            # 如果没有提供股票池，使用默认配置
            from Agents_Experience import config
            self.system_prompt = generate_system_prompt(
                config.MVP_STOCK_POOL, 
                config.STOCK_NAMES
            )
    
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
            # 速率限制：确保两次API调用之间有足够间隔
            if self.api_call_interval > 0:
                current_time = time.time()
                time_since_last_call = current_time - self.last_api_call_time
                if time_since_last_call < self.api_call_interval:
                    sleep_time = self.api_call_interval - time_since_last_call
                    print(f"  [速率限制] 等待 {sleep_time:.1f} 秒...")
                    time.sleep(sleep_time)
                self.last_api_call_time = time.time()
            
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
        from Agents_Experience import config
        max_iterations = config.MAX_CONVERSATION_ITERATIONS  # 从配置读取最大对话轮数
        iteration = 0
        final_decision = None
        tool_call_results = []
        
        while iteration < max_iterations:
            iteration += 1
            print(f"  [对话轮次 {iteration}/{max_iterations}] 调用API...")
            
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
                tool_count = len(message["tool_calls"])
                print(f"  [工具调用] 本轮调用 {tool_count} 个工具")
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
            print(f"  [决策完成] 在第 {iteration} 轮完成决策，共调用 {len(tool_call_results)} 个工具")
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
            print(f"  ⚠️ 达到最大对话轮数限制（{max_iterations}轮），共调用了 {len(tool_call_results)} 个工具")
            final_decision = {
                'actions': [],
                'reasoning': f'达到最大对话轮数（{max_iterations}轮，调用了{len(tool_call_results)}个工具）',
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
        import re
        
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
        
        # 提取分析、决策和理由 - 使用更健壮的正则表达式
        analysis = ""
        decision = ""
        reasoning = ""
        
        # 尝试多种格式的标题匹配
        # 匹配 **分析**、**分析**：、分析：、【分析】等格式
        analysis_pattern = r'(?:\*{0,2}分析\*{0,2}|【分析】)[:：]?\s*(.*?)(?=(?:\*{0,2}决策\*{0,2}|【决策】|$))'
        decision_pattern = r'(?:\*{0,2}决策\*{0,2}|【决策】)[:：]?\s*(.*?)(?=(?:\*{0,2}理由\*{0,2}|【理由】|$))'
        reasoning_pattern = r'(?:\*{0,2}理由\*{0,2}|【理由】)[:：]?\s*(.*)'
        
        # 提取分析
        analysis_match = re.search(analysis_pattern, response_text, re.DOTALL | re.IGNORECASE)
        if analysis_match:
            analysis = analysis_match.group(1).strip()
        
        # 提取决策
        decision_match = re.search(decision_pattern, response_text, re.DOTALL | re.IGNORECASE)
        if decision_match:
            decision = decision_match.group(1).strip()
        
        # 提取理由
        reasoning_match = re.search(reasoning_pattern, response_text, re.DOTALL | re.IGNORECASE)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        
        # 如果没有找到结构化内容，使用整个响应
        if not analysis and not decision and not reasoning:
            analysis = response_text
            reasoning = response_text
        
        # 合并分析和决策作为完整的分析内容
        full_analysis = analysis
        if decision:
            full_analysis = f"{analysis}\n\n决策: {decision}" if analysis else decision
        
        return {
            'actions': actions,
            'analysis': full_analysis,  # 不再限制长度
            'reasoning': reasoning
        }
