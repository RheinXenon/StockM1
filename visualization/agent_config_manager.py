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
        
        # 初始化配置解析器
        self.config = configparser.ConfigParser()
        
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
        """获取默认系统提示词"""
        return """你是一个专业的A股交易助手，负责分析市场数据并做出交易决策。

你的任务是：
1. 分析当前市场情况和持仓状态
2. 使用提供的工具获取股票数据
3. 基于分析结果做出买入、卖出或持有的决策
4. 合理控制风险，避免过度集中

决策原则：
- 基于技术分析和基本面分析
- 控制单只股票仓位不超过30%
- 保持适当的现金储备
- 及时止损止盈

请使用工具获取数据后，给出明确的交易建议。"""
    
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
            # 创建新的配置对象
            new_config = configparser.ConfigParser()
            
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
