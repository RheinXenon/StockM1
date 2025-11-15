# 工具调用问题修复说明

## 问题描述

在运行 Agent 交易模拟时，发现以下问题：
1. **Agent 没有执行交易**：账户资金始终保持初始状态（1,000,000 元），没有任何买卖操作
2. **工具调用失败**：Agent 报告"技术指标工具出现错误"
3. **只有分析没有行动**：Agent 只是在做市场分析，但没有实际调用交易工具

## 根本原因

### 主要问题：提示词不明确

原系统提示词存在以下问题：
1. **没有明确指示 Agent 必须通过调用工具来执行交易**
2. Agent 误以为只需要在文本中说明"买入XXX"或"卖出XXX"
3. 缺少清晰的工作流程指导

### 代码逻辑

`_parse_decision` 方法的设计：
```python
# 只从工具调用记录中提取交易动作
for tool_call in tool_calls:
    if tool_name == 'buy_stock' and 'action' in result_data:
        actions.append(...)
    elif tool_name == 'sell_stock' and 'action' in result_data:
        actions.append(...)
```

这意味着：**只有当 Agent 实际调用了 `buy_stock` 或 `sell_stock` 工具时，才会生成交易动作**。

## 解决方案

### 1. 优化系统提示词 ✅

**修改内容**：
- 添加明确的 4 步工作流程
- 在"第三步：执行交易"中强调**必须调用工具**
- 添加警告：⚠️ 仅在文本中说明是无效的
- 在多处重复强调必须通过工具执行交易

**关键改动**：
```markdown
### 第三步：执行交易（关键！）
**如果决定买入或卖出，必须调用相应的交易工具来执行**：
- 要买入股票：**必须调用 buy_stock 工具**
- 要卖出股票：**必须调用 sell_stock 工具**

⚠️ 注意：仅在文本中说明"买入XXX"是无效的，必须实际调用工具！
```

### 2. 修复技术指标工具 JSON 序列化 bug ✅

**问题**：MACD 的金叉/死叉布尔值导致 JSON 序列化失败

**修复**：
```python
# 修改前
"金叉": indicators['MACD_golden_cross'],  # numpy.bool_ 类型
"死叉": indicators['MACD_death_cross']

# 修改后
"金叉": bool(indicators['MACD_golden_cross']),  # 转换为 Python bool
"死叉": bool(indicators['MACD_death_cross'])
```

### 3. 更新每日决策提示词 ✅

添加明确的操作步骤：
```
请按以下步骤操作：
1. 使用 get_portfolio 查看详细持仓
2. 使用 get_stock_history 和 get_technical_indicators 查询数据
3. 基于分析，**务必调用 buy_stock 或 sell_stock 工具执行**
4. 最后用文本总结

记住：必须通过调用工具来执行交易，不能只在文本中说明！
```

## 测试验证

### 1. 工具功能测试
运行测试脚本：
```bash
cd Agents_Experience
python test_tools.py
```

预期输出：
- ✓ 所有 5 个工具正常工作
- ✓ get_technical_indicators 不再报错
- ✓ 买入/卖出指令验证成功

### 2. Agent 决策测试
运行诊断脚本（需要 API key）：
```bash
python diagnose_tools.py
```

预期结果：
- Agent 会调用多个工具收集数据
- 如果决定交易，会调用 buy_stock 或 sell_stock
- tool_calls 列表中包含交易工具

### 3. 完整模拟测试
运行完整模拟：
```bash
python run_mvp.py
```

预期行为：
- Agent 每天会查询数据
- 做出交易决策后，**实际调用工具执行**
- 账户资金和持仓会发生变化
- 交易次数 > 0

## 文件修改列表

1. **prompts/system_prompt.py** ✅
   - 重写 SYSTEM_PROMPT
   - 更新 DAILY_DECISION_PROMPT

2. **core/tools.py** ✅
   - 修复 get_technical_indicators 的 JSON 序列化

3. **新增测试文件**：
   - test_tools.py - 工具功能测试
   - diagnose_tools.py - Agent 决策诊断

## 预期改进效果

修复后，Agent 应该：
1. ✅ 能够正常调用所有工具（包括技术指标工具）
2. ✅ 在做出买入/卖出决策时，实际调用相应的交易工具
3. ✅ 账户资金和持仓会随着交易发生变化
4. ✅ 交易记录中会有实际的买卖操作

## 下一步建议

1. **运行测试**：先运行 test_tools.py 确认工具正常
2. **小规模测试**：修改 config.py，先测试几天（如 2020-01-02 到 2020-01-10）
3. **观察日志**：检查 Agent 是否真的在调用交易工具
4. **调整参数**：如果交易过于频繁或保守，可以调整提示词中的决策原则

## 注意事项

1. **API 费用**：每次决策可能调用多次 API，注意控制成本
2. **调试模式**：可以在 qwen_agent.py 中添加打印语句，查看工具调用详情
3. **提示词迭代**：如果 Agent 仍然不按预期行为，需要继续优化提示词

## 总结

问题的核心是 **提示词工程**：
- Agent 没有明确的指令去调用交易工具
- 只是将工具列举出来，但没有说明何时、如何使用

修复后，通过明确的工作流程和多次强调，Agent 应该能够理解：
**要执行交易，必须调用 buy_stock/sell_stock 工具，而不是只在文本中描述**。
