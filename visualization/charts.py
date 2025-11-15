"""
图表组件模块 - 使用plotly生成交互式图表
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, List, Dict


def create_candlestick_chart(df: pd.DataFrame, 
                             title: str = "K线图",
                             show_ma: bool = True,
                             ma_periods: List[int] = [5, 10, 20, 60]) -> go.Figure:
    """
    创建K线图
    
    Args:
        df: 包含OHLC数据的DataFrame
        title: 图表标题
        show_ma: 是否显示移动平均线
        ma_periods: MA周期列表
    """
    fig = go.Figure()
    
    # K线图
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='K线',
        increasing_line_color='red',
        decreasing_line_color='green'
    ))
    
    # 添加移动平均线
    if show_ma:
        colors = ['orange', 'blue', 'purple', 'brown']
        for i, period in enumerate(ma_periods):
            if f'MA{period}' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df[f'MA{period}'],
                    mode='lines',
                    name=f'MA{period}',
                    line=dict(color=colors[i % len(colors)], width=1)
                ))
    
    fig.update_layout(
        title=title,
        yaxis_title='价格',
        xaxis_title='日期',
        template='plotly_white',
        height=600,
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )
    
    return fig


def create_volume_chart(df: pd.DataFrame, title: str = "成交量") -> go.Figure:
    """
    创建成交量图
    
    Args:
        df: 包含volume数据的DataFrame
        title: 图表标题
    """
    # 判断涨跌颜色
    colors = ['red' if row['close'] >= row['open'] else 'green' 
              for _, row in df.iterrows()]
    
    fig = go.Figure()
    
    # 成交量柱状图
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        name='成交量',
        marker_color=colors,
        opacity=0.7
    ))
    
    # 添加成交量MA
    if 'VOL_MA5' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['VOL_MA5'],
            mode='lines',
            name='VOL_MA5',
            line=dict(color='orange', width=1)
        ))
    
    if 'VOL_MA10' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['VOL_MA10'],
            mode='lines',
            name='VOL_MA10',
            line=dict(color='blue', width=1)
        ))
    
    fig.update_layout(
        title=title,
        yaxis_title='成交量',
        xaxis_title='日期',
        template='plotly_white',
        height=300,
        hovermode='x unified'
    )
    
    return fig


def create_macd_chart(df: pd.DataFrame, title: str = "MACD") -> go.Figure:
    """
    创建MACD图
    
    Args:
        df: 包含MACD数据的DataFrame
        title: 图表标题
    """
    fig = go.Figure()
    
    # MACD柱状图
    if 'MACD_hist' in df.columns:
        colors = ['red' if val >= 0 else 'green' for val in df['MACD_hist']]
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['MACD_hist'],
            name='MACD柱',
            marker_color=colors,
            opacity=0.7
        ))
    
    # MACD线
    if 'MACD' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['MACD'],
            mode='lines',
            name='MACD',
            line=dict(color='blue', width=1.5)
        ))
    
    # 信号线
    if 'MACD_signal' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['MACD_signal'],
            mode='lines',
            name='信号线',
            line=dict(color='orange', width=1.5)
        ))
    
    # 添加零轴
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        title=title,
        yaxis_title='MACD',
        xaxis_title='日期',
        template='plotly_white',
        height=300,
        hovermode='x unified'
    )
    
    return fig


def create_rsi_chart(df: pd.DataFrame, title: str = "RSI") -> go.Figure:
    """
    创建RSI图
    
    Args:
        df: 包含RSI数据的DataFrame
        title: 图表标题
    """
    fig = go.Figure()
    
    # RSI线
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['RSI'],
            mode='lines',
            name='RSI',
            line=dict(color='purple', width=2)
        ))
    
    # 添加超买超卖线
    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, annotation_text="超买")
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, annotation_text="超卖")
    fig.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.3)
    
    fig.update_layout(
        title=title,
        yaxis_title='RSI',
        xaxis_title='日期',
        template='plotly_white',
        height=300,
        yaxis=dict(range=[0, 100]),
        hovermode='x unified'
    )
    
    return fig


def create_kdj_chart(df: pd.DataFrame, title: str = "KDJ") -> go.Figure:
    """
    创建KDJ图
    
    Args:
        df: 包含KDJ数据的DataFrame
        title: 图表标题
    """
    fig = go.Figure()
    
    # K线
    if 'K' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['K'],
            mode='lines',
            name='K',
            line=dict(color='blue', width=1.5)
        ))
    
    # D线
    if 'D' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['D'],
            mode='lines',
            name='D',
            line=dict(color='orange', width=1.5)
        ))
    
    # J线
    if 'J' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['J'],
            mode='lines',
            name='J',
            line=dict(color='purple', width=1.5)
        ))
    
    # 添加参考线
    fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.5)
    fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.5)
    
    fig.update_layout(
        title=title,
        yaxis_title='KDJ',
        xaxis_title='日期',
        template='plotly_white',
        height=300,
        hovermode='x unified'
    )
    
    return fig


def create_bollinger_chart(df: pd.DataFrame, title: str = "布林带") -> go.Figure:
    """
    创建布林带图
    
    Args:
        df: 包含布林带数据的DataFrame
        title: 图表标题
    """
    fig = go.Figure()
    
    # 上轨
    if 'BB_upper' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['BB_upper'],
            mode='lines',
            name='上轨',
            line=dict(color='red', width=1, dash='dash')
        ))
    
    # 中轨
    if 'BB_middle' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['BB_middle'],
            mode='lines',
            name='中轨',
            line=dict(color='blue', width=1.5)
        ))
    
    # 下轨
    if 'BB_lower' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['BB_lower'],
            mode='lines',
            name='下轨',
            line=dict(color='green', width=1, dash='dash'),
            fill='tonexty',
            fillcolor='rgba(173, 216, 230, 0.2)'
        ))
    
    # 收盘价
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['close'],
        mode='lines',
        name='收盘价',
        line=dict(color='black', width=2)
    ))
    
    fig.update_layout(
        title=title,
        yaxis_title='价格',
        xaxis_title='日期',
        template='plotly_white',
        height=500,
        hovermode='x unified'
    )
    
    return fig


def create_combined_chart(df: pd.DataFrame, symbol: str, name: str = "") -> go.Figure:
    """
    创建组合图表（K线 + 成交量 + MACD + RSI）
    
    Args:
        df: 包含所有数据的DataFrame
        symbol: 股票代码
        name: 股票名称
    """
    # 创建子图
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.2, 0.15, 0.15],
        subplot_titles=(f'{symbol} {name} K线图', '成交量', 'MACD', 'RSI')
    )
    
    # K线图
    fig.add_trace(go.Candlestick(
        x=df['date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='K线',
        increasing_line_color='red',
        decreasing_line_color='green'
    ), row=1, col=1)
    
    # 添加MA线
    ma_colors = {'MA5': 'orange', 'MA10': 'blue', 'MA20': 'purple', 'MA60': 'brown'}
    for ma, color in ma_colors.items():
        if ma in df.columns:
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df[ma],
                mode='lines',
                name=ma,
                line=dict(color=color, width=1)
            ), row=1, col=1)
    
    # 成交量
    colors = ['red' if row['close'] >= row['open'] else 'green' 
              for _, row in df.iterrows()]
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['volume'],
        name='成交量',
        marker_color=colors,
        opacity=0.7,
        showlegend=False
    ), row=2, col=1)
    
    # MACD
    if 'MACD_hist' in df.columns:
        colors = ['red' if val >= 0 else 'green' for val in df['MACD_hist']]
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['MACD_hist'],
            name='MACD柱',
            marker_color=colors,
            opacity=0.7,
            showlegend=False
        ), row=3, col=1)
    
    if 'MACD' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['MACD'],
            mode='lines',
            name='MACD',
            line=dict(color='blue', width=1),
            showlegend=False
        ), row=3, col=1)
    
    if 'MACD_signal' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['MACD_signal'],
            mode='lines',
            name='信号线',
            line=dict(color='orange', width=1),
            showlegend=False
        ), row=3, col=1)
    
    # RSI
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['RSI'],
            mode='lines',
            name='RSI',
            line=dict(color='purple', width=1.5),
            showlegend=False
        ), row=4, col=1)
        
        # RSI参考线
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.3, row=4, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.3, row=4, col=1)
    
    # 更新布局
    fig.update_layout(
        height=1000,
        template='plotly_white',
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        showlegend=True
    )
    
    # 更新y轴标题
    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    fig.update_yaxes(title_text="RSI", row=4, col=1)
    
    return fig


def create_comparison_chart(data_dict: dict, title: str = "股票对比") -> go.Figure:
    """
    创建多股票对比图（归一化）
    
    Args:
        data_dict: {symbol: df} 字典
        title: 图表标题
    """
    fig = go.Figure()
    
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
    
    for i, (symbol, df) in enumerate(data_dict.items()):
        if not df.empty and 'close' in df.columns:
            # 归一化（以第一个值为基准）
            normalized = (df['close'] / df['close'].iloc[0] - 1) * 100
            
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=normalized,
                mode='lines',
                name=symbol,
                line=dict(color=colors[i % len(colors)], width=2)
            ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        title=title,
        yaxis_title='涨跌幅 (%)',
        xaxis_title='日期',
        template='plotly_white',
        height=600,
        hovermode='x unified'
    )
    
    return fig


def create_returns_chart(df: pd.DataFrame, title: str = "收益率分析") -> go.Figure:
    """
    创建收益率分析图
    
    Args:
        df: 包含收益率数据的DataFrame
        title: 图表标题
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('日收益率', '累计收益率')
    )
    
    # 日收益率
    if 'daily_return' in df.columns:
        colors = ['red' if val >= 0 else 'green' for val in df['daily_return']]
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['daily_return'] * 100,
            name='日收益率',
            marker_color=colors,
            opacity=0.7
        ), row=1, col=1)
    
    # 累计收益率
    if 'cumulative_return' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['cumulative_return'] * 100,
            mode='lines',
            name='累计收益率',
            line=dict(color='blue', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 100, 255, 0.2)'
        ), row=2, col=1)
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=2, col=1)
    
    fig.update_layout(
        title=title,
        template='plotly_white',
        height=700,
        hovermode='x unified'
    )
    
    fig.update_yaxes(title_text="收益率 (%)", row=1, col=1)
    fig.update_yaxes(title_text="累计收益率 (%)", row=2, col=1)
    
    return fig


def add_index_to_comparison(fig: go.Figure, 
                           index_data_dict: Dict[str, pd.DataFrame],
                           index_names: Dict[str, str] = None) -> go.Figure:
    """
    向对比图表中添加指数曲线
    
    Args:
        fig: 现有的图表对象
        index_data_dict: {index_symbol: df} 指数数据字典
        index_names: {index_symbol: display_name} 指数显示名称映射
    
    Returns:
        添加了指数曲线的图表对象
    """
    if index_names is None:
        index_names = {}
    
    # 指数专用颜色（虚线样式）
    index_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    for i, (symbol, df) in enumerate(index_data_dict.items()):
        if not df.empty and 'close' in df.columns:
            # 归一化（以第一个值为基准）
            normalized = (df['close'] / df['close'].iloc[0] - 1) * 100
            
            display_name = index_names.get(symbol, symbol)
            
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=normalized,
                mode='lines',
                name=f"{display_name} (指数)",
                line=dict(
                    color=index_colors[i % len(index_colors)], 
                    width=2.5,
                    dash='dash'  # 虚线样式
                ),
                opacity=0.8
            ))
    
    return fig


def create_comparison_with_index(data_dict: dict, 
                                index_data_dict: dict = None,
                                index_names: dict = None,
                                title: str = "股票对比") -> go.Figure:
    """
    创建包含指数的多股票对比图（归一化）
    
    Args:
        data_dict: {symbol: df} 股票数据字典
        index_data_dict: {index_symbol: df} 指数数据字典
        index_names: {index_symbol: display_name} 指数显示名称映射
        title: 图表标题
    """
    fig = create_comparison_chart(data_dict, title)
    
    # 添加指数曲线
    if index_data_dict:
        fig = add_index_to_comparison(fig, index_data_dict, index_names)
    
    return fig
