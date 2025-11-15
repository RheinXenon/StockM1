"""
Agent交易工具定义
"""
import json
from typing import Dict, Any, List
from .data_provider import MarketDataProvider


class TradingTools:
    """为Agent提供的交易工具集"""
    
    def __init__(self, data_provider: MarketDataProvider, stock_pool: List[str]):
        self.data_provider = data_provider
        self.stock_pool = stock_pool
    
    def get_tools_definition(self) -> List[Dict[str, Any]]:
        """获取工具定义（OpenAI Function Calling格式）"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_stock_history",
                    "description": "获取股票的历史K线数据，包括开盘价、收盘价、最高价、最低价、成交量等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "股票代码，可选值：600519(贵州茅台)、600036(招商银行)、000002(万科A)",
                                "enum": self.stock_pool
                            },
                            "days": {
                                "type": "integer",
                                "description": "获取最近N天的数据，默认30天",
                                "default": 30
                            }
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_technical_indicators",
                    "description": "获取股票的技术指标，包括MA均线、MACD、RSI等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "股票代码",
                                "enum": self.stock_pool
                            }
                        },
                        "required": ["symbol"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_portfolio",
                    "description": "查看当前账户的持仓情况和可用资金",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "buy_stock",
                    "description": "买入指定数量的股票（注意：需要有足够的可用资金，交易会产生佣金）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "股票代码",
                                "enum": self.stock_pool
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "买入数量（股），必须是100的整数倍（1手=100股）",
                                "minimum": 100
                            }
                        },
                        "required": ["symbol", "quantity"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "sell_stock",
                    "description": "卖出指定数量的股票（注意：只能卖出已持有的股票，T+1规则-今天买入的明天才能卖）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "股票代码",
                                "enum": self.stock_pool
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "卖出数量（股）",
                                "minimum": 100
                            }
                        },
                        "required": ["symbol", "quantity"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], 
                    current_date: str, portfolio: Any) -> str:
        """
        执行工具调用
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            current_date: 当前模拟日期
            portfolio: 当前持仓对象
        
        Returns:
            工具执行结果（JSON字符串）
        """
        try:
            if tool_name == "get_stock_history":
                symbol = arguments.get("symbol")
                days = arguments.get("days", 30)
                
                df = self.data_provider.get_stock_history(symbol, current_date, days)
                
                if df.empty:
                    return json.dumps({"error": f"无法获取股票 {symbol} 的历史数据"}, ensure_ascii=False)
                
                # 转换为简洁格式
                history = []
                for _, row in df.tail(10).iterrows():  # 只返回最近10天
                    history.append({
                        "date": row['date'],
                        "open": round(float(row['open']), 2),
                        "high": round(float(row['high']), 2),
                        "low": round(float(row['low']), 2),
                        "close": round(float(row['close']), 2),
                        "volume": int(row['volume']),
                        "pct_change": round(float(row['pct_change']), 2) if row['pct_change'] else 0
                    })
                
                return json.dumps({
                    "symbol": symbol,
                    "data_points": len(df),
                    "recent_10_days": history
                }, ensure_ascii=False, indent=2)
            
            elif tool_name == "get_technical_indicators":
                symbol = arguments.get("symbol")
                indicators = self.data_provider.get_technical_indicators(symbol, current_date, 60)
                
                if not indicators:
                    return json.dumps({"error": f"无法计算股票 {symbol} 的技术指标"}, ensure_ascii=False)
                
                # 格式化输出
                result = {
                    "symbol": indicators['symbol'],
                    "date": indicators['date'],
                    "current_price": round(indicators['current_price'], 2),
                    "移动平均线": {
                        "MA5": round(indicators['MA5'], 2) if indicators['MA5'] else None,
                        "MA10": round(indicators['MA10'], 2) if indicators['MA10'] else None,
                        "MA20": round(indicators['MA20'], 2) if indicators['MA20'] else None,
                        "价格位置": "上方" if indicators['price_above_MA20'] else "下方" if indicators['price_above_MA20'] is not None else "未知"
                    },
                    "MACD": {
                        "MACD值": round(indicators['MACD'], 4) if indicators['MACD'] else None,
                        "信号线": round(indicators['MACD_Signal'], 4) if indicators['MACD_Signal'] else None,
                        "柱状图": round(indicators['MACD_Hist'], 4) if indicators['MACD_Hist'] else None,
                        "金叉": bool(indicators['MACD_golden_cross']),
                        "死叉": bool(indicators['MACD_death_cross'])
                    },
                    "RSI": {
                        "RSI值": round(indicators['RSI'], 2) if indicators['RSI'] else None,
                        "状态": "超买" if indicators['RSI'] and indicators['RSI'] > 70 
                                else "超卖" if indicators['RSI'] and indicators['RSI'] < 30 
                                else "正常"
                    },
                    "成交量": int(indicators['volume']),
                    "涨跌幅": f"{indicators['pct_change']:.2f}%"
                }
                
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            elif tool_name == "get_portfolio":
                summary = portfolio.get_summary()
                
                positions = []
                for pos in portfolio.positions.values():
                    positions.append({
                        "股票代码": pos.symbol,
                        "股票名称": pos.name,
                        "持仓数量": pos.quantity,
                        "成本价": round(pos.avg_cost, 2),
                        "当前价": round(pos.current_price, 2),
                        "市值": round(pos.market_value, 2),
                        "盈亏": round(pos.profit, 2),
                        "盈亏率": f"{pos.profit_rate:.2f}%"
                    })
                
                result = {
                    "当前日期": summary['current_date'],
                    "可用资金": round(summary['cash'], 2),
                    "持仓市值": round(summary['market_value'], 2),
                    "总资产": round(summary['total_asset'], 2),
                    "初始资金": round(summary['initial_capital'], 2),
                    "总盈亏": round(summary['total_profit'], 2),
                    "收益率": f"{summary['total_profit_rate']:.2f}%",
                    "持仓明细": positions
                }
                
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            elif tool_name == "buy_stock":
                symbol = arguments.get("symbol")
                quantity = arguments.get("quantity")
                
                # 验证数量
                if quantity % 100 != 0:
                    return json.dumps({"error": "买入数量必须是100的整数倍（1手=100股）"}, ensure_ascii=False)
                
                # 获取当前价格
                price_info = self.data_provider.get_stock_price_on_date(symbol, current_date)
                if not price_info:
                    return json.dumps({"error": f"无法获取股票 {symbol} 在 {current_date} 的价格"}, ensure_ascii=False)
                
                price = price_info['close']
                cost = price * quantity * 1.0003  # 加上佣金
                
                if portfolio.cash < cost:
                    return json.dumps({
                        "error": f"资金不足！需要 {cost:,.2f} 元，可用 {portfolio.cash:,.2f} 元"
                    }, ensure_ascii=False)
                
                # 执行买入（这里返回成功，实际执行由simulator处理）
                return json.dumps({
                    "action": "buy",
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": round(price, 2),
                    "estimated_cost": round(cost, 2),
                    "message": f"准备买入 {symbol} {quantity}股，预计花费 {cost:,.2f} 元"
                }, ensure_ascii=False)
            
            elif tool_name == "sell_stock":
                symbol = arguments.get("symbol")
                quantity = arguments.get("quantity")
                
                # 检查持仓
                position = portfolio.get_position(symbol)
                if not position:
                    return json.dumps({"error": f"未持有股票 {symbol}"}, ensure_ascii=False)
                
                if position.quantity < quantity:
                    return json.dumps({
                        "error": f"持仓不足！持有 {position.quantity} 股，卖出 {quantity} 股"
                    }, ensure_ascii=False)
                
                # 获取当前价格
                price_info = self.data_provider.get_stock_price_on_date(symbol, current_date)
                if not price_info:
                    return json.dumps({"error": f"无法获取股票 {symbol} 在 {current_date} 的价格"}, ensure_ascii=False)
                
                price = price_info['close']
                revenue = price * quantity * (1 - 0.0003 - 0.001)  # 扣除佣金和印花税
                
                return json.dumps({
                    "action": "sell",
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": round(price, 2),
                    "estimated_revenue": round(revenue, 2),
                    "message": f"准备卖出 {symbol} {quantity}股，预计收入 {revenue:,.2f} 元"
                }, ensure_ascii=False)
            
            else:
                return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)
                
        except Exception as e:
            return json.dumps({"error": f"工具执行失败: {str(e)}"}, ensure_ascii=False)
