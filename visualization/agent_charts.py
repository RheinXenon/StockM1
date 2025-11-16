"""
AI Agent交易结果可视化图表组件
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional


def create_portfolio_value_chart(df: pd.DataFrame, title: str = "投资组合总资产变化") -> go.Figure:
    """
    创建投资组合总资产变化曲线图
    
    Args:
        df: 包含日期、总资产数据的DataFrame
        title: 图表标题
    """
    fig = go.Figure()
    
    # 总资产曲线
    fig.add_trace(go.Scatter(
        x=df['日期'],
        y=df['总资产'],
        mode='lines+markers',
        name='总资产',
        line=dict(color='blue', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 100, 255, 0.1)'
    ))
    
    # 添加初始资金参考线
    if len(df) > 0:
        initial_value = df['总资产'].iloc[0]
        fig.add_hline(
            y=initial_value,
            line_dash="dash",
            line_color="gray",
            opacity=0.5,
            annotation_text=f"初始资金: ¥{initial_value:,.0f}"
        )
    
    fig.update_layout(
        title=title,
        xaxis_title='日期',
        yaxis_title='总资产（元）',
        template='plotly_white',
        height=500,
        hovermode='x unified',
        yaxis=dict(tickformat=',.0f')
    )
    
    return fig


def create_return_rate_chart(df: pd.DataFrame, title: str = "收益率变化曲线") -> go.Figure:
    """
    创建收益率变化曲线图
    
    Args:
        df: 包含日期、收益率数据的DataFrame
        title: 图表标题
    """
    fig = go.Figure()
    
    # 收益率曲线
    colors = ['red' if val >= 0 else 'green' for val in df['收益率']]
    
    fig.add_trace(go.Scatter(
        x=df['日期'],
        y=df['收益率'],
        mode='lines+markers',
        name='收益率',
        line=dict(color='orange', width=2),
        marker=dict(
            size=6,
            color=df['收益率'],
            colorscale=[[0, 'green'], [0.5, 'yellow'], [1, 'red']],
            showscale=True,
            colorbar=dict(title="收益率(%)")
        ),
        fill='tozeroy',
        fillcolor='rgba(255, 165, 0, 0.1)'
    ))
    
    # 零轴参考线
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        title=title,
        xaxis_title='日期',
        yaxis_title='收益率 (%)',
        template='plotly_white',
        height=400,
        hovermode='x unified'
    )
    
    return fig


def create_cash_position_chart(df: pd.DataFrame, title: str = "现金与持仓市值分布") -> go.Figure:
    """
    创建现金与持仓市值的堆叠面积图
    
    Args:
        df: 包含日期、现金、市值数据的DataFrame
        title: 图表标题
    """
    fig = go.Figure()
    
    # 持仓市值
    fig.add_trace(go.Scatter(
        x=df['日期'],
        y=df['市值'],
        mode='lines',
        name='持仓市值',
        line=dict(width=0.5, color='rgb(184, 247, 212)'),
        stackgroup='one',
        fillcolor='rgb(184, 247, 212)'
    ))
    
    # 现金
    fig.add_trace(go.Scatter(
        x=df['日期'],
        y=df['现金'],
        mode='lines',
        name='现金',
        line=dict(width=0.5, color='rgb(111, 231, 219)'),
        stackgroup='one',
        fillcolor='rgb(111, 231, 219)'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='日期',
        yaxis_title='金额（元）',
        template='plotly_white',
        height=400,
        hovermode='x unified',
        yaxis=dict(tickformat=',.0f')
    )
    
    return fig


def create_combined_overview_chart(df: pd.DataFrame, 
                                   agent_name: str = "",
                                   index_data_dict: Optional[Dict[str, pd.DataFrame]] = None,
                                   index_names: Optional[Dict[str, str]] = None) -> go.Figure:
    """
    创建综合概览图表（资产、收益率、现金持仓分布）
    
    Args:
        df: 包含完整数据的DataFrame
        agent_name: Agent名称
    """
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            f'{agent_name} 总资产变化',
            '收益率变化',
            '资产配置（现金 vs 持仓）'
        ),
        row_heights=[0.4, 0.3, 0.3]
    )
    
    # 1. 总资产曲线
    fig.add_trace(go.Scatter(
        x=df['日期'],
        y=df['总资产'],
        mode='lines+markers',
        name='总资产',
        line=dict(color='blue', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 100, 255, 0.1)',
        marker=dict(size=4)
    ), row=1, col=1)
    
    # 初始资金参考线
    if len(df) > 0:
        initial_value = df['总资产'].iloc[0]
        fig.add_hline(
            y=initial_value,
            line_dash="dash",
            line_color="gray",
            opacity=0.3,
            row=1, col=1
        )
    
    # 2. 收益率曲线
    fig.add_trace(go.Scatter(
        x=df['日期'],
        y=df['收益率'],
        mode='lines+markers',
        name='收益率',
        line=dict(color='orange', width=2),
        marker=dict(
            size=4,
            color=df['收益率'],
            colorscale=[[0, 'green'], [0.5, 'yellow'], [1, 'red']],
            showscale=False
        ),
        fill='tozeroy',
        fillcolor='rgba(255, 165, 0, 0.1)'
    ), row=2, col=1)
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.3, row=2, col=1)
    
    # 添加指数对比（在收益率行）
    if index_data_dict and index_names and len(df) > 0:
        initial_value = df['总资产'].iloc[0]
        index_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        
        for i, (symbol, index_df) in enumerate(index_data_dict.items()):
            if not index_df.empty and 'close' in index_df.columns:
                # 归一化（以第一个值为基准，转换为收益率）
                normalized = (index_df['close'] / index_df['close'].iloc[0] - 1) * 100
                
                display_name = index_names.get(symbol, symbol)
                
                fig.add_trace(go.Scatter(
                    x=index_df['date'],
                    y=normalized,
                    mode='lines',
                    name=f"{display_name}",
                    line=dict(
                        color=index_colors[i % len(index_colors)], 
                        width=1.5,
                        dash='dash'
                    ),
                    opacity=0.7,
                    showlegend=True
                ), row=2, col=1)
    
    # 3. 资产配置堆叠图
    fig.add_trace(go.Scatter(
        x=df['日期'],
        y=df['市值'],
        mode='lines',
        name='持仓市值',
        line=dict(width=0.5),
        stackgroup='assets',
        fillcolor='rgba(184, 247, 212, 0.8)'
    ), row=3, col=1)
    
    fig.add_trace(go.Scatter(
        x=df['日期'],
        y=df['现金'],
        mode='lines',
        name='现金',
        line=dict(width=0.5),
        stackgroup='assets',
        fillcolor='rgba(111, 231, 219, 0.8)'
    ), row=3, col=1)
    
    # 更新布局
    fig.update_layout(
        height=1000,
        template='plotly_white',
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # 更新y轴标签
    fig.update_yaxes(title_text="总资产（元）", tickformat=',.0f', row=1, col=1)
    fig.update_yaxes(title_text="收益率 (%)", row=2, col=1)
    fig.update_yaxes(title_text="金额（元）", tickformat=',.0f', row=3, col=1)
    fig.update_xaxes(title_text="日期", row=3, col=1)
    
    return fig


def create_transactions_timeline(transactions_df: pd.DataFrame, title: str = "交易操作时间线") -> go.Figure:
    """
    创建交易操作时间线图
    
    Args:
        transactions_df: 包含交易记录的DataFrame
        title: 图表标题
    """
    if transactions_df.empty:
        # 返回空图表
        fig = go.Figure()
        fig.add_annotation(
            text="暂无交易记录",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig.update_layout(
            title=title,
            template='plotly_white',
            height=400
        )
        return fig
    
    fig = go.Figure()
    
    # 为不同操作类型设置颜色
    color_map = {
        '买入': 'red',
        '卖出': 'green',
        '加仓': 'orange',
        '减仓': 'blue'
    }
    
    # 按操作类型分组绘制
    for operation in transactions_df['操作'].unique():
        df_op = transactions_df[transactions_df['操作'] == operation]
        
        fig.add_trace(go.Scatter(
            x=df_op['日期'],
            y=df_op['金额'],
            mode='markers',
            name=operation,
            marker=dict(
                size=df_op['数量'] / df_op['数量'].max() * 30 + 5,  # 根据数量调整大小
                color=color_map.get(operation, 'gray'),
                opacity=0.7,
                line=dict(width=1, color='white')
            ),
            text=[f"{row['股票代码']}<br>数量: {row['数量']}<br>价格: ¥{row['价格']:.2f}" 
                  for _, row in df_op.iterrows()],
            hovertemplate='<b>%{text}</b><br>日期: %{x}<br>金额: ¥%{y:,.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title='日期',
        yaxis_title='交易金额（元）',
        template='plotly_white',
        height=500,
        hovermode='closest',
        yaxis=dict(tickformat=',.0f')
    )
    
    return fig


def create_holdings_pie_chart(holdings_str: str, date: str = "", title: str = "持仓分布") -> go.Figure:
    """
    创建持仓分布饼图
    
    Args:
        holdings_str: 持仓详情字符串
        date: 日期
        title: 图表标题
    """
    import re
    
    holdings = []
    if pd.notna(holdings_str) and holdings_str:
        for item in holdings_str.split(';'):
            item = item.strip()
            if not item:
                continue
            
            match = re.match(r'(\d{6}):(\d+)股@([\d.]+)元\(收益率([-\d.]+)%\)', item)
            if match:
                symbol = match.group(1)
                shares = int(match.group(2))
                price = float(match.group(3))
                holdings.append({
                    'symbol': symbol,
                    'value': shares * price
                })
    
    if not holdings:
        fig = go.Figure()
        fig.add_annotation(
            text="暂无持仓",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig.update_layout(
            title=f"{title} ({date})" if date else title,
            template='plotly_white',
            height=400
        )
        return fig
    
    symbols = [h['symbol'] for h in holdings]
    values = [h['value'] for h in holdings]
    
    fig = go.Figure(data=[go.Pie(
        labels=symbols,
        values=values,
        hole=0.3,
        marker=dict(
            colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F'],
            line=dict(color='white', width=2)
        ),
        textinfo='label+percent',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>市值: ¥%{value:,.0f}<br>占比: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=f"{title} ({date})" if date else title,
        template='plotly_white',
        height=400,
        showlegend=True
    )
    
    return fig


def create_stock_profit_pie_chart(stock_profits: Dict[str, float], title: str = "各股票收益贡献占比") -> go.Figure:
    """
    创建各股票收益贡献占比饼图
    处理盈利和亏损的情况
    
    Args:
        stock_profits: {股票代码: 收益金额} 字典
        title: 图表标题
    """
    if not stock_profits:
        fig = go.Figure()
        fig.add_annotation(
            text="暂无收益数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig.update_layout(
            title=title,
            template='plotly_white',
            height=400
        )
        return fig
    
    # 分离盈利和亏损股票
    profit_stocks = {k: v for k, v in stock_profits.items() if v > 0}
    loss_stocks = {k: abs(v) for k, v in stock_profits.items() if v < 0}
    
    # 判断总体是盈利还是亏损
    total_profit = sum(stock_profits.values())
    
    if not profit_stocks and not loss_stocks:
        fig = go.Figure()
        fig.add_annotation(
            text="所有股票收益为0",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig.update_layout(
            title=title,
            template='plotly_white',
            height=400
        )
        return fig
    
    # 根据总收益决定显示方式
    if total_profit >= 0:
        # 总体盈利：显示盈利股票的贡献比例
        if profit_stocks:
            symbols = list(profit_stocks.keys())
            values = list(profit_stocks.values())
            
            # 创建颜色：盈利用绿色系
            colors = ['#00C853', '#69F0AE', '#00E676', '#76FF03', '#B2FF59', '#CCFF90']
            
            # 添加亏损股票的影响（用负值表示）
            if loss_stocks:
                for symbol, loss in loss_stocks.items():
                    symbols.append(f"{symbol}(亏)")
                    values.append(loss)  # 用正值显示，但标记为亏损
                colors.extend(['#FF1744', '#FF5252', '#FF6E40', '#FF9100'])
            
            hover_text = []
            for i, symbol in enumerate(symbols):
                if '(亏)' in symbol:
                    original_profit = -loss_stocks[symbol.replace('(亏)', '')]
                    hover_text.append(f'<b>{symbol}</b><br>亏损: ¥{original_profit:,.0f}<br>占比: %{{percent}}')
                else:
                    hover_text.append(f'<b>{symbol}</b><br>盈利: ¥{profit_stocks[symbol]:,.0f}<br>占比: %{{percent}}')
            
            fig = go.Figure(data=[go.Pie(
                labels=symbols,
                values=values,
                hole=0.3,
                marker=dict(
                    colors=colors[:len(symbols)],
                    line=dict(color='white', width=2)
                ),
                textinfo='label+percent',
                textposition='auto',
                hovertemplate='%{hovertext}<extra></extra>',
                hovertext=hover_text
            )])
            
            subtitle = f"总收益: ¥{total_profit:,.0f}"
        else:
            # 只有亏损股票
            symbols = [f"{k}(亏)" for k in loss_stocks.keys()]
            values = list(loss_stocks.values())
            colors = ['#FF1744', '#FF5252', '#FF6E40', '#FF9100', '#FFAB40', '#FFD740']
            
            fig = go.Figure(data=[go.Pie(
                labels=symbols,
                values=values,
                hole=0.3,
                marker=dict(
                    colors=colors[:len(symbols)],
                    line=dict(color='white', width=2)
                ),
                textinfo='label+percent',
                textposition='auto',
                hovertemplate='<b>%{label}</b><br>亏损: ¥%{value:,.0f}<br>占比: %{percent}<extra></extra>'
            )])
            subtitle = f"总亏损: ¥{total_profit:,.0f}"
    else:
        # 总体亏损：显示亏损股票的占比
        symbols = [f"{k}(亏)" for k in loss_stocks.keys()]
        values = list(loss_stocks.values())
        colors = ['#FF1744', '#FF5252', '#FF6E40', '#FF9100', '#FFAB40', '#FFD740']
        
        # 如果有盈利股票，也显示出来
        if profit_stocks:
            for symbol, profit in profit_stocks.items():
                symbols.append(f"{symbol}(盈)")
                values.append(profit)
            colors.extend(['#00C853', '#69F0AE', '#00E676', '#76FF03'])
        
        fig = go.Figure(data=[go.Pie(
            labels=symbols,
            values=values,
            hole=0.3,
            marker=dict(
                colors=colors[:len(symbols)],
                line=dict(color='white', width=2)
            ),
            textinfo='label+percent',
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>金额: ¥%{value:,.0f}<br>占比: %{percent}<extra></extra>'
        )])
        subtitle = f"总亏损: ¥{total_profit:,.0f}"
    
    fig.update_layout(
        title=dict(
            text=f"{title}<br><sub>{subtitle}</sub>",
            x=0.5,
            xanchor='center'
        ),
        template='plotly_white',
        height=450,
        showlegend=True
    )
    
    return fig


def create_daily_return_distribution(df: pd.DataFrame, title: str = "日收益率分布") -> go.Figure:
    """
    创建日收益率分布直方图
    
    Args:
        df: 包含收益率数据的DataFrame
        title: 图表标题
    """
    # 计算日收益率变化
    daily_returns = df['收益率'].diff().dropna()
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=daily_returns,
        nbinsx=30,
        name='日收益率',
        marker=dict(
            color='lightblue',
            line=dict(color='darkblue', width=1)
        ),
        opacity=0.75
    ))
    
    # 添加均值线
    mean_return = daily_returns.mean()
    fig.add_vline(
        x=mean_return,
        line_dash="dash",
        line_color="red",
        opacity=0.7,
        annotation_text=f"均值: {mean_return:.2f}%"
    )
    
    fig.update_layout(
        title=title,
        xaxis_title='日收益率变化 (%)',
        yaxis_title='频数',
        template='plotly_white',
        height=400,
        showlegend=False
    )
    
    return fig


def create_portfolio_value_chart_with_index(df: pd.DataFrame, 
                                           index_data_dict: Optional[Dict[str, pd.DataFrame]] = None,
                                           index_names: Optional[Dict[str, str]] = None,
                                           title: str = "投资组合总资产变化") -> go.Figure:
    """
    创建带指数对比的投资组合总资产变化曲线图
    
    Args:
        df: 包含日期、总资产数据的DataFrame
        index_data_dict: {index_symbol: df} 指数数据字典
        index_names: {index_symbol: display_name} 指数显示名称映射
        title: 图表标题
    """
    fig = go.Figure()
    
    # 总资产曲线（归一化为收益率）
    if len(df) > 0 and '总资产' in df.columns:
        initial_value = df['总资产'].iloc[0]
        portfolio_return = (df['总资产'] / initial_value - 1) * 100
        
        fig.add_trace(go.Scatter(
            x=df['日期'],
            y=portfolio_return,
            mode='lines+markers',
            name='投资组合',
            line=dict(color='blue', width=3),
            marker=dict(size=4),
            fill='tozeroy',
            fillcolor='rgba(0, 100, 255, 0.1)'
        ))
    
    # 添加指数曲线
    if index_data_dict and index_names:
        index_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        
        for i, (symbol, index_df) in enumerate(index_data_dict.items()):
            if not index_df.empty and 'close' in index_df.columns:
                # 归一化（以第一个值为基准）
                normalized = (index_df['close'] / index_df['close'].iloc[0] - 1) * 100
                
                display_name = index_names.get(symbol, symbol)
                
                fig.add_trace(go.Scatter(
                    x=index_df['date'],
                    y=normalized,
                    mode='lines',
                    name=f"{display_name}",
                    line=dict(
                        color=index_colors[i % len(index_colors)], 
                        width=2,
                        dash='dash'
                    ),
                    opacity=0.8
                ))
    
    # 添加零轴参考线
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        opacity=0.5
    )
    
    fig.update_layout(
        title=title,
        xaxis_title='日期',
        yaxis_title='收益率 (%)',
        template='plotly_white',
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def create_stock_pool_comparison_chart(portfolio_df: pd.DataFrame,
                                       stock_pool_data: Dict[str, pd.DataFrame],
                                       stock_names: Optional[Dict[str, str]] = None,
                                       title: str = "投资组合 vs 股票池对比") -> go.Figure:
    """
    创建投资组合与股票池中所有股票的对比图
    
    Args:
        portfolio_df: 投资组合数据
        stock_pool_data: {股票代码: 价格数据DataFrame} 字典
        stock_names: {股票代码: 股票名称} 映射
        title: 图表标题
    """
    fig = go.Figure()
    
    # 投资组合收益率曲线
    if len(portfolio_df) > 0 and '总资产' in portfolio_df.columns:
        initial_value = portfolio_df['总资产'].iloc[0]
        portfolio_return = (portfolio_df['总资产'] / initial_value - 1) * 100
        
        fig.add_trace(go.Scatter(
            x=portfolio_df['日期'],
            y=portfolio_return,
            mode='lines+markers',
            name='AI投资组合',
            line=dict(color='#FF1744', width=4),
            marker=dict(size=5),
        ))
    
    # 股票池中各股票的收益率曲线
    stock_colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#00BCD4', 
                   '#FFC107', '#E91E63', '#009688', '#795548', '#607D8B']
    
    for i, (symbol, stock_df) in enumerate(stock_pool_data.items()):
        if not stock_df.empty and 'close' in stock_df.columns:
            # 归一化收益率
            normalized = (stock_df['close'] / stock_df['close'].iloc[0] - 1) * 100
            
            # 获取股票名称
            if stock_names and symbol in stock_names:
                display_name = f"{symbol} {stock_names[symbol]}"
            else:
                display_name = symbol
            
            fig.add_trace(go.Scatter(
                x=stock_df['date'],
                y=normalized,
                mode='lines',
                name=display_name,
                line=dict(
                    color=stock_colors[i % len(stock_colors)],
                    width=1.5,
                    dash='dot'
                ),
                opacity=0.6
            ))
    
    # 添加零轴参考线
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        opacity=0.5
    )
    
    fig.update_layout(
        title=title,
        xaxis_title='日期',
        yaxis_title='收益率 (%)',
        template='plotly_white',
        height=600,
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.01,
            bgcolor='rgba(255, 255, 255, 0.8)'
        )
    )
    
    return fig


def create_stock_performance_table(portfolio_df: pd.DataFrame,
                                   stock_pool_data: Dict[str, pd.DataFrame],
                                   stock_names: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """
    创建股票表现对比表格
    
    Args:
        portfolio_df: 投资组合数据
        stock_pool_data: {股票代码: 价格数据DataFrame} 字典
        stock_names: {股票代码: 股票名称} 映射
    
    Returns:
        对比数据表格
    """
    performance_data = []
    
    # 计算投资组合表现
    if len(portfolio_df) > 0 and '总资产' in portfolio_df.columns:
        initial_value = portfolio_df['总资产'].iloc[0]
        final_value = portfolio_df['总资产'].iloc[-1]
        total_return = (final_value / initial_value - 1) * 100
        
        performance_data.append({
            '代码/名称': 'AI投资组合',
            '起始值': f"¥{initial_value:,.0f}",
            '最终值': f"¥{final_value:,.0f}",
            '总收益率(%)': f"{total_return:.2f}%",
            '收益金额': f"¥{final_value - initial_value:,.0f}"
        })
    
    # 计算各股票表现
    for symbol, stock_df in stock_pool_data.items():
        if not stock_df.empty and 'close' in stock_df.columns:
            initial_price = stock_df['close'].iloc[0]
            final_price = stock_df['close'].iloc[-1]
            total_return = (final_price / initial_price - 1) * 100
            
            # 假设同样投资100万
            initial_investment = 1000000
            final_value = initial_investment * (1 + total_return / 100)
            profit = final_value - initial_investment
            
            # 获取股票名称
            if stock_names and symbol in stock_names:
                display_name = f"{symbol} {stock_names[symbol]}"
            else:
                display_name = symbol
            
            performance_data.append({
                '代码/名称': display_name,
                '起始值': f"¥{initial_investment:,.0f}",
                '最终值': f"¥{final_value:,.0f}",
                '总收益率(%)': f"{total_return:.2f}%",
                '收益金额': f"¥{profit:,.0f}"
            })
    
    return pd.DataFrame(performance_data)
