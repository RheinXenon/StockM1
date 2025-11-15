"""
测试Qwen API连接
"""
import requests
from config import QWEN_API_BASE, QWEN_API_KEY, QWEN_MODEL


def test_api_connection():
    """测试API连接"""
    print("测试Qwen API连接...")
    print(f"API地址: {QWEN_API_BASE}")
    print(f"模型: {QWEN_MODEL}\n")
    
    url = f"{QWEN_API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {
                "role": "user",
                "content": "请用一句话介绍你自己"
            }
        ],
        "max_tokens": 100
    }
    
    try:
        print("发送测试请求...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            message = result["choices"][0]["message"]["content"]
            print("✓ API连接成功！")
            print(f"\n模型回复: {message}\n")
            return True
        else:
            print("✗ API返回格式异常")
            print(result)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ API连接失败: {e}")
        return False


if __name__ == '__main__':
    test_api_connection()
