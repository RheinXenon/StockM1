# Agent股票交易模拟系统

## 项目简介

使用大模型Agent（Qwen3-30B-A3B）模拟股票交易，验证AI在金融决策中的表现。

## MVP版本配置

- **Agent**: Qwen3-30B-A3B (公益API)
- **初始资金**: 100万人民币
- **模拟时间**: 2020年全年
- **股票池**: 贵州茅台(600519)、招商银行(600036)、万科A(000002)
- **交易规则**: T+1，真实佣金和印花税

## 快速开始

### 1. 配置API密钥
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入真实的API密钥
# QWEN_API_KEY=sk-your_actual_api_key_here
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行MVP测试
```bash
cd Agents_Experience
python run_mvp.py
```

或者使用一键启动脚本（Windows）：
```bash
快速开始.bat
```

## 项目结构

```
Agents_Experience/
├── agents/
│   ├── base_agent.py      # Agent基类
│   └── qwen_agent.py      # Qwen Agent实现
├── core/
│   ├── simulator.py       # 交易模拟引擎
│   ├── tools.py          # Agent交易工具
│   └── data_provider.py  # 数据提供接口
├── prompts/
│   └── system_prompt.py  # 系统提示词
├── utils/
│   ├── logger.py         # 日志工具
│   └── analyzer.py       # 性能分析
├── results/              # 结果输出
├── logs/                # 运行日志
├── config.py            # 配置文件
└── run_mvp.py          # MVP启动脚本
```

## 功能特性

### Agent能力
- ✅ 查询股票历史K线数据
- ✅ 获取技术指标（MA、MACD、RSI等）
- ✅ 查看当前持仓和资金
- ✅ 执行买入/卖出操作
- ✅ 严格防止未来信息泄露

### 模拟引擎
- ✅ 逐日推进时间循环
- ✅ 只提供历史数据
- ✅ 真实交易成本计算
- ✅ 完整交易记录
- ✅ 性能统计分析

## 输出结果

1. **交易日志**: `logs/agent_qwen_YYYYMMDD_HHMMSS.log`
2. **性能报告**: `results/performance_report_YYYYMMDD_HHMMSS.json`
3. **决策记录**: 每次Agent的思考过程和决策依据

## 注意事项

⚠️ **免责声明**: 本系统仅用于学习和研究，不构成任何投资建议。
