# A股数据可视化与模拟交易系统

一个功能完善的A股数据分析系统，支持历史数据下载、交互式可视化分析、技术指标计算和模拟交易。

## 主要功能

- 📊 **数据下载**：下载A股股票和主要指数的历史数据（基于akshare）
- 📈 **可视化分析**：交互式Web界面，支持K线图、技术指标、多股对比
- 📉 **技术指标**：MACD、RSI、KDJ、布林带、移动平均线等
- 🔍 **多股对比**：同时对比最多10只股票的走势和收益率
- 📊 **统计分析**：价格统计、成交量分析、收益率分布
- 💰 **模拟交易**：支持任意历史时间点的模拟买卖（可选功能）

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载数据

```bash
# 下载10只股票数据（推荐新手测试）
python main.py download-stocks --limit 10

# 下载所有股票数据（需要较长时间）
python main.py download-stocks

# 下载指数数据（可选）
python main.py download-indices
```

### 3. 启动可视化界面

```bash
python run_visualization.py
```

浏览器会自动打开，或手动访问：http://localhost:8501

### 4. 开始使用

- **📊 股票列表**：查看所有已下载的股票，支持搜索和分页
- **📈 股票详细分析**：查看K线图、技术指标（组合图、K线、MACD、RSI、KDJ、布林带、收益率）
- **🔍 多股票对比**：对比多只股票的归一化走势和统计数据
- **📉 技术指标分析**：查看MA、MACD、RSI、KDJ的最新数值和建议
- **📊 统计分析**：查看指定周期的价格、成交量、收益率统计

## 常用命令

### 数据管理
```bash
# 下载股票数据
python main.py download-stocks --limit 50

# 下载指数数据
python main.py download-indices

# 查看已下载股票列表
python main.py list-stocks
```

### 可视化分析
```bash
# 启动Web界面（推荐）
python run_visualization.py

# 直接运行Streamlit
streamlit run visualization/app.py

# 指定端口
streamlit run visualization/app.py --server.port 8502
```

### 模拟交易（可选）
```bash
# 创建账户（默认100万初始资金）
python main.py create-account 我的账户

# 加载账户进行交易
python main.py load-account 我的账户
>>> date 2020-01-02        # 设置模拟日期
>>> buy 000001 1000        # 买入1000股
>>> portfolio              # 查看持仓
>>> sell 000001 500        # 卖出500股
>>> transactions           # 查看交易记录
>>> exit                   # 退出
```

## 可视化功能详解

### 1. 股票列表
- 显示所有已下载股票的代码、名称、数据条数、起始/结束日期
- 支持按股票代码或名称搜索
- 分页显示，每页50条

### 2. 股票详细分析
- **时间范围**：1个月、3个月、6个月、1年、3年、全部、自定义
- **8种图表类型**：
  - 组合图表（K线+成交量+MACD+RSI）
  - K线图（含MA5/10/20/60移动平均线）
  - 成交量图（带成交量均线）
  - MACD图（MACD线、信号线、MACD柱）
  - RSI图（相对强弱指标，超买超卖提示）
  - KDJ图（随机指标）
  - 布林带图（上轨、中轨、下轨）
  - 收益率分析（日收益率、累计收益率）

### 3. 多股票对比
- 同时对比最多10只股票
- 归一化价格走势对比
- 统计数据对比表（总收益率、年化波动率、最高/最低价、平均成交量）

### 4. 技术指标分析
- 显示MA、MACD、RSI、KDJ的最新数值
- 提供参考建议（如超买、超卖、金叉、死叉等）

### 5. 统计分析
- 指定周期统计（30/60/90/180/365天）
- 价格统计（平均价、最高价、最低价、波动幅度）
- 成交量统计（平均成交量、总成交量）
- 收益率统计（平均涨跌幅、最大单日涨跌幅）
- 日收益率分布直方图

## 技术指标说明

### 移动平均线（MA）
- 股价在MA上方为强势，下方为弱势
- 短期MA上穿长期MA为金叉（买入信号）
- 短期MA下穿长期MA为死叉（卖出信号）

### MACD（异同移动平均线）
- MACD线上穿信号线为买入信号
- MACD线下穿信号线为卖出信号
- MACD柱由负转正为看涨，由正转负为看跌

### RSI（相对强弱指数）
- RSI > 70 为超买区域
- RSI < 30 为超卖区域
- RSI在50附近为均衡状态

### KDJ（随机指标）
- K线和D线在20以下为超卖，80以上为超买
- K线上穿D线为买入信号，下穿为卖出信号
- J线可提前K、D线反映趋势变化

### 布林带（Bollinger Bands）
- 价格触及上轨可能回落（超买）
- 价格触及下轨可能反弹（超卖）
- 带宽收窄表示波动率降低，可能酝酿突破

## 项目结构

```
Stock/
├── src/stock_app/          # 核心模块
│   ├── data_downloader.py  # 数据下载
│   ├── database.py         # 数据库管理
│   ├── trading_engine.py   # 交易引擎
│   └── portfolio.py        # 持仓管理
├── visualization/          # 可视化模块（~1650行代码）
│   ├── app.py             # Streamlit主应用（5个页面）
│   ├── data_loader.py     # 数据加载模块
│   ├── indicators.py      # 技术指标计算（11个指标）
│   └── charts.py          # 图表组件（9种图表）
├── main.py                # 主程序入口
├── run_visualization.py   # 可视化启动脚本
└── requirements.txt       # 项目依赖
```

## 常见问题

### 界面显示"暂无股票数据"
需要先下载数据：
```bash
python main.py download-stocks --limit 10
```

### ModuleNotFoundError: No module named 'streamlit'
未安装可视化依赖：
```bash
pip install streamlit plotly
```

### 端口8501已被占用
使用其他端口：
```bash
streamlit run visualization/app.py --server.port 8502
```

### pip安装速度慢
使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 图表加载缓慢
- 缩小时间范围
- 减少同时对比的股票数量

### 某些技术指标显示不全
某些指标需要足够的历史数据才能计算，建议选择较长的时间范围

## 主要指数代码

- `000001`：上证指数
- `399001`：深证成指
- `399006`：创业板指
- `000300`：沪深300

## 技术栈

- **数据源**：akshare
- **数据库**：SQLite3
- **数据处理**：pandas, numpy
- **Web框架**：streamlit
- **图表库**：plotly
- **命令行**：click, rich

## 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。技术指标仅供参考，股市有风险，投资需谨慎。

## 许可证

MIT License
