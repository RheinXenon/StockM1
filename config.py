"""
配置文件
"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# 数据库文件
DATABASE_PATH = os.path.join(DATA_DIR, 'stock_data.db')

# 模拟交易配置
INITIAL_CAPITAL = 1000000  # 初始资金：100万元
COMMISSION_RATE = 0.0003   # 佣金费率：万分之三
STAMP_TAX_RATE = 0.001     # 印花税：千分之一（仅卖出时收取）
MIN_COMMISSION = 5         # 最低佣金：5元

# 数据下载配置
DEFAULT_START_DATE = '20100101'  # 默认起始日期
