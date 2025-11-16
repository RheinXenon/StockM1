"""
AI Agent配置管理模块
处理user_setting.ini的读写和.env的加载
"""
import os
import configparser
from typing import Dict, Any, List
from dotenv import load_dotenv


class AgentConfigManager:
    """Agent配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        # 配置文件路径
        self.agents_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'Agents_Experience'
        )
        self.config_file = os.path.join(self.agents_dir, 'user_setting.ini')
        self.env_file = os.path.join(self.agents_dir, '.env')
        
        # 加载.env文件
        load_dotenv(self.env_file)
        
        # 初始化配置解析器（使用RawConfigParser避免插值语法问题）
        self.config = configparser.RawConfigParser()
        
    def get_default_config(self) -> Dict[str, Any]:
        """
        从.env文件获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            # API配置
            'api_base': os.getenv('QWEN_API_BASE', 'https://api.suanli.cn/v1'),
            'api_key': os.getenv('QWEN_API_KEY', ''),
            'model': os.getenv('QWEN_MODEL', 'free:Qwen3-30B-A3B'),
            'api_call_interval': float(os.getenv('API_CALL_INTERVAL', '2')),
            
            # 模型参数
            'temperature': 1.0,
            'max_tokens': 2000,
            
            # 系统提示词
            'system_prompt': self._get_default_prompt(),
            
            # 交易配置
            'initial_capital': 1000000,
            'stock_pool': ['600519', '600036', '000002', '601318', '000858', 
                          '600276', '300750', '002594', '600887', '002475'],
            
            # 时间配置
            'start_date': '2020-01-02',
            'end_date': '2020-12-31',
            
            # 历史窗口
            'history_window_days': 60
        }
    
    def _get_default_prompt(self) -> str:
        """获取默认系统提示词（与system_prompt.py一致）"""
        return """你是一位专业的股票投资顾问AI助手，负责管理一个100万人民币的股票账户。

## 你的角色
- 你需要基于市场数据和技术分析做出买入/卖出决策
- 你的目标是在控制风险的前提下，获得稳定的投资收益
- 你必须遵守T+1交易规则（今天买入的股票明天才能卖出）

## 工作流程（必须严格遵守！）

### 步骤1：查看持仓
**强制要求**：必须调用 `get_portfolio` 工具查看当前持仓

### 步骤2：数据收集
对股票池中多只股票（建议至少分析5-6只），必须调用：
- `get_stock_history`: 查看K线走势
- `get_technical_indicators`: 查看技术指标

⚠️ 注意：不要只关注固定的几只股票，应该分析股票池中的多只股票以发现最佳机会

### 步骤3：执行交易（必须调用工具！）

⚠️⚠️⚠️ 严重警告 - 常见错误示例：
```
❌ 错误做法：只在文字中说"已买入某股票"
✅ 正确做法：先调用 buy_stock 工具，然后在文字中说"已买入"
```

**如果你决定买入某股票1000股，正确步骤是：**
1. 先调用工具：buy_stock(symbol="股票代码", quantity=1000)
2. 等待工具返回结果
3. 然后在文字总结中说："已通过工具买入XXX股票1000股"

**选项A：买入股票（资金充足且看好时）**
- 条件：技术指标良好（RSI<70, MACD>0且上穿信号线，价格在MA5/MA10上方）
- 行动：**必须调用 buy_stock(symbol="代码", quantity=数量)**
- 数量：100-3000股（总资产的10-30%），必须是100的整数倍
- 示例：buy_stock(symbol="600036", quantity=1000)

**选项B：卖出股票（持仓且出现卖出信号时）** ⚠️重要：不要只会买不会卖！
- **强制卖出条件（满足任一即卖）**：
  * 亏损达到 -8% 或以上（止损）
  * 盈利达到 15% 或以上（止盈）
  * RSI > 75（极度超买）
  * MACD死叉（MACD线下穿信号线）
  * 价格跌破MA5和MA10均线
- 行动：**必须调用 sell_stock(symbol="代码", quantity=数量)**
- 数量：可以全部卖出或部分卖出（100的整数倍）
- 示例：sell_stock(symbol="600036", quantity=1000)

**选项C：持有观望（谨慎情况）**
- 条件：无明确买入或卖出信号
- 行动：不调用交易工具，直接进入步骤4

🚨 关键提醒：
- **买卖要平衡**：不要只会买不会卖，该卖的时候必须果断卖出
- **止损止盈是铁律**：达到止损/止盈线必须执行，不要犹豫
- **禁止在文字中说"已买入"或"已卖出"而不调用工具 - 这是欺骗行为！**

### 步骤4：文字总结
在调用完交易工具后（或确认不交易），用文字总结。

## 决策原则
1. **风险控制优先**: 单只股票仓位不超过总资产的40%
2. **基于数据分析**: 结合K线形态、技术指标和市场趋势
3. **严格止损止盈**: 亏损达到-8%**必须**止损，盈利达到15%**必须**止盈（非"考虑"，是强制执行）
4. **买卖平衡**: 既要敢于买入优质股票，也要果断卖出弱势股票，不要只买不卖
5. **分散投资**: 适当配置不同板块的股票
6. **理性交易**: 不要频繁交易，关注中长期趋势

## 技术指标参考
- **MA均线**: 价格在均线上方为强势，下方为弱势；金叉看涨，死叉看跌
- **MACD**: MACD线上穿信号线为买入信号，下穿为**卖出信号**
- **RSI**: >75超买（**必须卖出**），<25超卖（考虑买入），70-75警戒区，25-30机会区
- **卖出优先级**: 止损/止盈 > RSI超买 > MACD死叉 > 跌破均线

## 输出格式
完成工具调用后，请按以下格式总结：

**分析**：
[简要分析市场情况、技术指标、持仓状态]

**决策**：
[说明今天的操作：已买入XXX/已卖出XXX/持有观望]

**理由**：
[解释决策依据，包括技术指标、市场趋势等]

## 重要提醒
- 你只能看到今天及之前的数据，无法预知未来
- 每次决策都会产生真实的交易成本（佣金约万分之三，卖出时还有千分之一印花税）
- 买入数量必须是100的整数倍（1手=100股）
- **必须通过调用buy_stock/sell_stock工具来执行交易，不能只在文本中说明**"""
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载用户配置，如果不存在则返回默认配置
        
        Returns:
            配置字典
        """
        # 先获取默认配置
        config = self.get_default_config()
        
        # 如果配置文件存在，则加载覆盖
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file, encoding='utf-8')
                
                # API配置
                if self.config.has_section('API'):
                    config['api_base'] = self.config.get('API', 'api_base', fallback=config['api_base'])
                    config['api_key'] = self.config.get('API', 'api_key', fallback=config['api_key'])
                    config['model'] = self.config.get('API', 'model', fallback=config['model'])
                    config['api_call_interval'] = self.config.getfloat('API', 'api_call_interval', 
                                                                       fallback=config['api_call_interval'])
                
                # 模型参数
                if self.config.has_section('Model'):
                    config['temperature'] = self.config.getfloat('Model', 'temperature', 
                                                                 fallback=config['temperature'])
                    config['max_tokens'] = self.config.getint('Model', 'max_tokens', 
                                                             fallback=config['max_tokens'])
                
                # 系统提示词
                if self.config.has_section('Prompt'):
                    config['system_prompt'] = self.config.get('Prompt', 'system_prompt', 
                                                             fallback=config['system_prompt'])
                
                # 交易配置
                if self.config.has_section('Trading'):
                    config['initial_capital'] = self.config.getfloat('Trading', 'initial_capital', 
                                                                     fallback=config['initial_capital'])
                    stock_pool_str = self.config.get('Trading', 'stock_pool', fallback='')
                    if stock_pool_str:
                        config['stock_pool'] = [s.strip() for s in stock_pool_str.split(',')]
                    config['history_window_days'] = self.config.getint('Trading', 'history_window_days',
                                                                       fallback=config['history_window_days'])
                
                # 时间配置
                if self.config.has_section('Time'):
                    config['start_date'] = self.config.get('Time', 'start_date', 
                                                          fallback=config['start_date'])
                    config['end_date'] = self.config.get('Time', 'end_date', 
                                                        fallback=config['end_date'])
                    
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                # 出错时使用默认配置
                pass
        
        return config
    
    def save_config(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """
        保存配置到文件
        
        Args:
            config: 配置字典
            
        Returns:
            (是否保存成功, 错误信息)
        """
        try:
            # 创建新的配置对象（使用RawConfigParser避免插值语法问题）
            new_config = configparser.RawConfigParser()
            
            # API配置
            new_config.add_section('API')
            new_config.set('API', 'api_base', str(config.get('api_base', '')))
            new_config.set('API', 'api_key', str(config.get('api_key', '')))
            new_config.set('API', 'model', str(config.get('model', '')))
            new_config.set('API', 'api_call_interval', str(config.get('api_call_interval', 2)))
            
            # 模型参数
            new_config.add_section('Model')
            new_config.set('Model', 'temperature', str(config.get('temperature', 1.0)))
            new_config.set('Model', 'max_tokens', str(config.get('max_tokens', 2000)))
            
            # 系统提示词
            new_config.add_section('Prompt')
            new_config.set('Prompt', 'system_prompt', str(config.get('system_prompt', '')))
            
            # 交易配置
            new_config.add_section('Trading')
            new_config.set('Trading', 'initial_capital', str(config.get('initial_capital', 1000000)))
            stock_pool = config.get('stock_pool', [])
            if isinstance(stock_pool, list):
                new_config.set('Trading', 'stock_pool', ','.join(stock_pool))
            else:
                new_config.set('Trading', 'stock_pool', str(stock_pool))
            new_config.set('Trading', 'history_window_days', str(config.get('history_window_days', 60)))
            
            # 时间配置
            new_config.add_section('Time')
            new_config.set('Time', 'start_date', str(config.get('start_date', '')))
            new_config.set('Time', 'end_date', str(config.get('end_date', '')))
            
            # 确保目录存在
            os.makedirs(self.agents_dir, exist_ok=True)
            
            # 写入文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                new_config.write(f)
            
            print(f"配置已成功保存到: {self.config_file}")
            return True, ""
            
        except Exception as e:
            error_msg = f"保存配置失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return False, error_msg
    
    def get_available_stock_pool(self) -> List[str]:
        """
        获取可用的股票池（从数据库或默认配置）
        
        Returns:
            股票代码列表
        """
        # 这里可以从数据库查询，目前返回默认股票池
        return [
            '600519',  # 贵州茅台
            '600036',  # 招商银行
            '000002',  # 万科A
            '601318',  # 中国平安
            '000858',  # 五粮液
            '600276',  # 恒瑞医药
            '300750',  # 宁德时代
            '002594',  # 比亚迪
            '600887',  # 伊利股份
            '002475',  # 立讯精密
            '000001',  # 平安银行
            '000333',  # 美的集团
            '600031',  # 三一重工
            '601166',  # 兴业银行
            '600900',  # 长江电力
        ]
