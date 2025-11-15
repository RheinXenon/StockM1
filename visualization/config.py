"""
可视化模块配置文件
"""

# Streamlit页面配置
PAGE_TITLE = "A股数据可视化分析系统"
PAGE_ICON = "📈"
LAYOUT = "wide"

# 图表配置
CHART_TEMPLATE = "plotly_white"
CHART_HEIGHT_MAIN = 600
CHART_HEIGHT_SUB = 300
CHART_HEIGHT_COMBINED = 1000

# 颜色配置
COLOR_UP = "red"        # 上涨颜色（中国股市习惯）
COLOR_DOWN = "green"    # 下跌颜色
COLOR_MA5 = "orange"
COLOR_MA10 = "blue"
COLOR_MA20 = "purple"
COLOR_MA60 = "brown"
COLOR_MA120 = "pink"

# 技术指标参数
MA_PERIODS = [5, 10, 20, 60, 120]
EMA_PERIODS = [12, 26]
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
RSI_PERIOD = 14
KDJ_N = 9
KDJ_M1 = 3
KDJ_M2 = 3
BB_PERIOD = 20
BB_STD = 2.0

# 分页配置
PAGE_SIZE = 50
MAX_SEARCH_RESULTS = 100

# 对比配置
MAX_COMPARISON_STOCKS = 10

# 日期范围配置
DATE_RANGES = {
    "近1个月": 30,
    "近3个月": 90,
    "近6个月": 180,
    "近1年": 365,
    "近3年": 365 * 3,
}

# 统计周期配置
STATISTICS_PERIODS = [30, 60, 90, 180, 365]
