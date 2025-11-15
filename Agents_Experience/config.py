"""
Agent交易系统配置
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ============ Agent API配置 ============
# Qwen API配置（从.env文件读取）
QWEN_API_BASE = os.getenv("QWEN_API_BASE", "https://api.suanli.cn/v1")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_MODEL = os.getenv("QWEN_MODEL", "free:Qwen3-30B-A3B")

# ============ 模拟交易配置 ============
# MVP测试配置
INITIAL_CAPITAL = 1000000  # 初始资金：100万
MVP_START_DATE = "2020-01-02"  # MVP开始日期
MVP_END_DATE = "2020-12-31"    # MVP结束日期

# 股票池（MVP使用3只股票）
MVP_STOCK_POOL = [
    "600519",  # 贵州茅台
    "600036",  # 招商银行
    "000002",  # 万科A
]

# ============ 交易规则 ============
COMMISSION_RATE = 0.0003   # 佣金费率：万分之三
STAMP_TAX_RATE = 0.001     # 印花税：千分之一（仅卖出）
MIN_COMMISSION = 5         # 最低佣金：5元

# 每日最多决策次数
MAX_DECISIONS_PER_DAY = 1

# ============ Agent配置 ============
# LLM参数
TEMPERATURE = 0.7  # 温度参数
MAX_TOKENS = 2000  # 最大输出token数

# 历史数据窗口（Agent可以看到的历史天数）
HISTORY_WINDOW_DAYS = 60

# ============ 数据库配置 ============
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'stock_data.db')

# ============ 日志配置 ============
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# ============ 结果输出配置 ============
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
