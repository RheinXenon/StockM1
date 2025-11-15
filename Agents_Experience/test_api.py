"""
测试Qwen API连接
"""
from openai import OpenAI
from config import QWEN_API_BASE, QWEN_API_KEY, QWEN_MODEL


def test_api_connection():
    """测试API连接"""
    print("测试Qwen API连接...")
    print(f"API地址: {QWEN_API_BASE}")
    print(f"模型: {QWEN_MODEL}\n")
    
    try:
        # 初始化OpenAI客户端
        client = OpenAI(
            base_url=QWEN_API_BASE,
            api_key=QWEN_API_KEY
        )
        
        # 设置extra_body参数以启用thinking功能
        extra_body = {
            "enable_thinking": True,
        }
        
        print("发送测试请求...")
        
        # 使用流式输出
        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {
                    'role': 'user',
                    'content': '请用一句话介绍你自己'
                }
            ],
            stream=True,
            extra_body=extra_body
        )
        
        print("✓ API连接成功！\n")
        
        # 处理流式响应
        done_thinking = False
        full_response = ""
        has_reasoning = None  # 用于检测模型是否支持reasoning
        
        for chunk in response:
            delta = chunk.choices[0].delta
            
            # 首次检测模型是否支持reasoning_content
            if has_reasoning is None:
                has_reasoning = hasattr(delta, 'reasoning_content')
                if has_reasoning:
                    print("检测到模型支持思考功能\n")
                else:
                    print("模型不支持思考功能，使用标准模式\n")
            
            # 根据模型能力处理响应
            if has_reasoning:
                # 支持reasoning的模型
                thinking_chunk = delta.reasoning_content
                answer_chunk = delta.content
                
                if thinking_chunk and thinking_chunk != '':
                    print(thinking_chunk, end='', flush=True)
                elif answer_chunk and answer_chunk != '':
                    if not done_thinking:
                        print('\n\n=== 模型回复 ===\n')
                        done_thinking = True
                    print(answer_chunk, end='', flush=True)
                    full_response += answer_chunk
            else:
                # 不支持reasoning的模型
                answer_chunk = delta.content
                if answer_chunk and answer_chunk != '':
                    print(answer_chunk, end='', flush=True)
                    full_response += answer_chunk
        
        print("\n")
        return True
            
    except Exception as e:
        print(f"✗ API连接失败: {e}")
        return False


if __name__ == '__main__':
    test_api_connection()
