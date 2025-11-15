"""
AI Agent交易日志数据加载器
用于加载和解析Agents_Experience/logs目录中的交易日志数据
"""
import pandas as pd
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class AgentDataLoader:
    """AI Agent交易数据加载器"""
    
    def __init__(self, logs_dir: str = None):
        """
        初始化数据加载器
        
        Args:
            logs_dir: 日志文件目录路径，默认为项目的Agents_Experience/logs目录
        """
        if logs_dir is None:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            self.logs_dir = os.path.join(project_root, 'Agents_Experience', 'logs')
        else:
            self.logs_dir = logs_dir
    
    def get_available_logs(self) -> List[Dict[str, str]]:
        """
        获取所有可用的日志文件
        
        Returns:
            日志文件列表，每个元素包含agent_name, timestamp, portfolio_file, decision_file等信息
        """
        if not os.path.exists(self.logs_dir):
            return []
        
        logs = []
        portfolio_files = {}
        
        # 查找所有portfolio CSV文件
        for file in os.listdir(self.logs_dir):
            if '_portfolio_' in file and file.endswith('.csv'):
                match = re.match(r'agent_(.+)_portfolio_(\d{8}_\d{6})\.csv', file)
                if match:
                    agent_name = match.group(1)
                    timestamp = match.group(2)
                    key = f"{agent_name}_{timestamp}"
                    portfolio_files[key] = file
        
        # 为每个portfolio文件查找对应的decision log
        for key, portfolio_file in portfolio_files.items():
            agent_name, timestamp = key.rsplit('_', 1)
            decision_file = f"agent_{agent_name}_decision_{timestamp}.log"
            
            log_info = {
                'agent_name': agent_name,
                'timestamp': timestamp,
                'portfolio_file': os.path.join(self.logs_dir, portfolio_file),
                'decision_file': os.path.join(self.logs_dir, decision_file) if os.path.exists(os.path.join(self.logs_dir, decision_file)) else None,
                'display_name': f"{agent_name} ({self._format_timestamp(timestamp)})"
            }
            logs.append(log_info)
        
        # 按时间戳排序
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return logs
    
    def _format_timestamp(self, timestamp: str) -> str:
        """格式化时间戳显示"""
        try:
            dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp
    
    def load_portfolio_data(self, portfolio_file: str) -> pd.DataFrame:
        """
        加载投资组合数据
        
        Args:
            portfolio_file: portfolio CSV文件路径
            
        Returns:
            DataFrame包含日期、现金、市值、总资产、收益率等信息
        """
        try:
            df = pd.read_csv(portfolio_file, encoding='utf-8')
            
            # 确保日期列存在并转换格式
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'])
            
            # 转换收益率列（去除%符号）
            if '收益率(%)' in df.columns:
                df['收益率'] = df['收益率(%)'].astype(float)
            
            return df
        except Exception as e:
            print(f"加载portfolio数据失败: {e}")
            return pd.DataFrame()
    
    def parse_holdings_detail(self, holdings_str: str) -> List[Dict]:
        """
        解析持仓详情字符串
        
        Args:
            holdings_str: 持仓详情字符串，格式如"601318:2000股@86.12元(收益率0.00%); ..."
            
        Returns:
            持仓列表，每个元素包含symbol, shares, price, return_rate
        """
        if pd.isna(holdings_str) or not holdings_str:
            return []
        
        holdings = []
        # 按分号分割多个持仓
        for item in holdings_str.split(';'):
            item = item.strip()
            if not item:
                continue
            
            # 解析格式：601318:2000股@86.12元(收益率0.00%)
            match = re.match(r'(\d{6}):(\d+)股@([\d.]+)元\(收益率([-\d.]+)%\)', item)
            if match:
                holdings.append({
                    'symbol': match.group(1),
                    'shares': int(match.group(2)),
                    'price': float(match.group(3)),
                    'return_rate': float(match.group(4))
                })
        
        return holdings
    
    def load_daily_transactions(self, portfolio_file: str) -> pd.DataFrame:
        """
        从portfolio数据中提取每日交易操作
        
        Args:
            portfolio_file: portfolio CSV文件路径
            
        Returns:
            DataFrame包含日期、交易类型、股票代码、数量、价格等信息
        """
        df = self.load_portfolio_data(portfolio_file)
        if df.empty or '持仓详情' not in df.columns:
            return pd.DataFrame()
        
        transactions = []
        prev_holdings = {}
        
        for idx, row in df.iterrows():
            date = row['日期']
            current_holdings = {}
            
            # 解析当前持仓
            holdings = self.parse_holdings_detail(row['持仓详情'])
            for holding in holdings:
                symbol = holding['symbol']
                current_holdings[symbol] = holding
            
            # 比较与前一天的变化
            if idx > 0:
                # 查找新增持仓（买入）
                for symbol, holding in current_holdings.items():
                    if symbol not in prev_holdings:
                        transactions.append({
                            '日期': date,
                            '操作': '买入',
                            '股票代码': symbol,
                            '数量': holding['shares'],
                            '价格': holding['price'],
                            '金额': holding['shares'] * holding['price']
                        })
                    elif holding['shares'] > prev_holdings[symbol]['shares']:
                        # 加仓
                        diff_shares = holding['shares'] - prev_holdings[symbol]['shares']
                        transactions.append({
                            '日期': date,
                            '操作': '加仓',
                            '股票代码': symbol,
                            '数量': diff_shares,
                            '价格': holding['price'],
                            '金额': diff_shares * holding['price']
                        })
                
                # 查找减少持仓（卖出）
                for symbol, prev_holding in prev_holdings.items():
                    if symbol not in current_holdings:
                        transactions.append({
                            '日期': date,
                            '操作': '卖出',
                            '股票代码': symbol,
                            '数量': prev_holding['shares'],
                            '价格': row.get('现金', 0),  # 实际价格需要从decision log中获取
                            '金额': 0  # 需要从现金变化中计算
                        })
                    elif current_holdings[symbol]['shares'] < prev_holding['shares']:
                        # 减仓
                        diff_shares = prev_holding['shares'] - current_holdings[symbol]['shares']
                        transactions.append({
                            '日期': date,
                            '操作': '减仓',
                            '股票代码': symbol,
                            '数量': diff_shares,
                            '价格': current_holdings[symbol]['price'],
                            '金额': diff_shares * current_holdings[symbol]['price']
                        })
            
            prev_holdings = current_holdings
        
        return pd.DataFrame(transactions)
    
    def load_decision_log(self, decision_file: str) -> List[Dict]:
        """
        加载决策日志
        
        Args:
            decision_file: decision log文件路径
            
        Returns:
            决策记录列表，每个元素包含日期和决策内容
        """
        if not decision_file or not os.path.exists(decision_file):
            return []
        
        try:
            with open(decision_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 按日期分割决策记录
            decisions = []
            date_pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] 交易日期: (\d{4}-\d{2}-\d{2})'
            
            # 找到所有日期分隔符
            matches = list(re.finditer(date_pattern, content))
            
            for i, match in enumerate(matches):
                timestamp = match.group(1)
                trade_date = match.group(2)
                
                # 提取该日期的决策内容
                start_pos = match.end()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                decision_content = content[start_pos:end_pos].strip()
                
                # 提取关键信息
                decisions.append({
                    'timestamp': timestamp,
                    'trade_date': trade_date,
                    'content': decision_content,
                    'market_analysis': self._extract_section(decision_content, '【市场分析】'),
                    'decision_reason': self._extract_section(decision_content, '【决策理由】')
                })
            
            return decisions
        except Exception as e:
            print(f"加载决策日志失败: {e}")
            return []
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """从决策内容中提取特定章节"""
        pattern = f'{section_name}(.*?)(?=【|$)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def get_portfolio_statistics(self, portfolio_file: str) -> Dict:
        """
        计算投资组合统计数据
        
        Args:
            portfolio_file: portfolio CSV文件路径
            
        Returns:
            统计数据字典
        """
        df = self.load_portfolio_data(portfolio_file)
        if df.empty:
            return {}
        
        try:
            stats = {
                '起始日期': df['日期'].iloc[0].strftime('%Y-%m-%d'),
                '结束日期': df['日期'].iloc[-1].strftime('%Y-%m-%d'),
                '交易天数': len(df),
                '初始资金': df['总资产'].iloc[0],
                '最终资产': df['总资产'].iloc[-1],
                '总收益': df['总资产'].iloc[-1] - df['总资产'].iloc[0],
                '总收益率': df['收益率'].iloc[-1],
                '最大资产': df['总资产'].max(),
                '最小资产': df['总资产'].min(),
                '最大收益率': df['收益率'].max(),
                '最大回撤': (df['总资产'].max() - df['总资产'].min()) / df['总资产'].max() * 100,
                '平均日收益率': df['收益率'].diff().mean(),
            }
            
            # 计算夏普比率等高级指标
            if len(df) > 1:
                daily_returns = df['总资产'].pct_change().dropna()
                if len(daily_returns) > 0 and daily_returns.std() != 0:
                    stats['收益波动率'] = daily_returns.std() * 100
                    # 假设无风险利率为3%年化
                    risk_free_rate = 0.03 / 252  # 日无风险利率
                    stats['夏普比率'] = (daily_returns.mean() - risk_free_rate) / daily_returns.std() * (252 ** 0.5) if daily_returns.std() > 0 else 0
            
            return stats
        except Exception as e:
            print(f"计算统计数据失败: {e}")
            return {}
