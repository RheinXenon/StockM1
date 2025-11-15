"""
AI Agent交易结果可视化图表组件
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List


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


def create_combined_overview_chart(df: pd.DataFrame, agent_name: str = "") -> go.Figure:
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
