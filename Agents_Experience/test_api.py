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
        
        for chunk in response:
            thinking_chunk = chunk.choices[0].delta.reasoning_content
            answer_chunk = chunk.choices[0].delta.content
            
            if thinking_chunk and thinking_chunk != '':
                print(thinking_chunk, end='', flush=True)
            elif answer_chunk and answer_chunk != '':
                if not done_thinking:
                    print('\n\n=== 模型回复 ===\n')
                    done_thinking = True
                print(answer_chunk, end='', flush=True)
                full_response += answer_chunk
        
        print("\n")
        return True
            
    except Exception as e:
        print(f"✗ API连接失败: {e}")
        return False


if __name__ == '__main__':
    test_api_connection()
