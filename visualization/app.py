"""
股票数据可视化主应用
使用Streamlit构建交互式界面
"""
import warnings
warnings.filterwarnings('ignore')

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# 禁用Streamlit的弃用警告
import logging
logging.getLogger('streamlit').setLevel(logging.ERROR)

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualization.data_loader import StockDataLoader
from visualization.indicators import calculate_all_indicators, calculate_returns, calculate_volatility
from visualization.charts import (
    create_candlestick_chart, create_volume_chart, create_macd_chart,
    create_rsi_chart, create_kdj_chart, create_bollinger_chart,
    create_combined_chart, create_comparison_chart, create_returns_chart,
    create_comparison_with_index
)
from visualization.agent_data_loader import AgentDataLoader
from visualization.agent_charts import (
    create_portfolio_value_chart, create_return_rate_chart,
    create_cash_position_chart, create_combined_overview_chart,
    create_transactions_timeline, create_holdings_pie_chart,
    create_daily_return_distribution, create_portfolio_value_chart_with_index
)
from src.stock_app.data_downloader import DataDownloader
from src.stock_app.database import Database
import time

# 常用指数定义（使用SH/SZ前缀区分市场，避免与股票代码冲突）
COMMON_INDICES = {
    'sh.000001': '上证指数',
    'sz.399001': '深证成指',
    'sz.399006': '创业板指',
    'sh.000300': '沪深300',
    'sh.000016': '上证50',
    'sh.000905': '中证500',
    'sz.399673': '创业板50'
}

# Plotly配置（避免警告）
PLOTLY_CONFIG = {
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['select2d', 'lasso2d']
}

# 页面配置
st.set_page_config(
    page_title="A股数据可视化分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化数据加载器（使用缓存）
@st.cache_resource
def get_data_loader():
    return StockDataLoader()

data_loader = get_data_loader()

# 添加缓存装饰器优化数据查询
@st.cache_data(ttl=300)  # 5分钟缓存
def get_cached_stocks_list(limit=None, offset=0):
    """\u7f13\u5b58\u80a1\u7968\u5217\u8868\u67e5\u8be2"""
    return data_loader.get_all_stocks(limit=limit, offset=offset)

@st.cache_data(ttl=300)
def get_cached_stock_info(symbol):
    """\u7f13\u5b58\u80a1\u7968\u4fe1\u606f\u67e5\u8be2"""
    return data_loader.get_stock_info(symbol)

@st.cache_data(ttl=300)
def get_cached_stock_data(symbol, start_date, end_date):
    """\u7f13\u5b58\u80a1\u7968\u6570\u636e\u67e5\u8be2"""
    return data_loader.get_stock_daily_data(symbol, start_date, end_date)

@st.cache_data(ttl=300)
def get_cached_search_results(keyword):
    """\u7f13\u5b58\u641c\u7d22\u7ed3\u679c"""
    return data_loader.search_stocks(keyword)

@st.cache_data(ttl=300)
def get_cached_latest_price(symbol):
    """\u7f13\u5b58\u6700\u65b0\u4ef7\u683c"""
    return data_loader.get_latest_price(symbol)

@st.cache_data(ttl=300)
def get_cached_multiple_stocks(symbols, start_date, end_date):
    """\u7f13\u5b58\u591a\u80a1\u7968\u6570\u636e"""
    return data_loader.get_multiple_stocks_data(symbols, start_date, end_date)

@st.cache_data(ttl=300)
def get_cached_statistics(symbol, days):
    """\u7f13\u5b58\u7edf\u8ba1\u6570\u636e"""
    return data_loader.get_stock_statistics(symbol, days)

@st.cache_data(ttl=300)
def get_cached_indicators(df, symbol, start_date, end_date):
    """\u7f13\u5b58\u6280\u672f\u6307\u6807\u8ba1\u7b97\u7ed3\u679c"""
    df_copy = df.copy()
    df_copy = calculate_all_indicators(df_copy)
    df_copy = calculate_returns(df_copy)
    df_copy = calculate_volatility(df_copy)
    return df_copy

@st.cache_data(ttl=300)
def get_cached_index_data(index_symbol, start_date, end_date):
    """\u7f13\u5b58\u6307\u6570\u6570\u636e\u67e5\u8be2"""
    # 将sh.000001格式转换为000001，因为数据库中只存储纯代码
    pure_symbol = index_symbol.split('.')[-1] if '.' in index_symbol else index_symbol
    return data_loader.get_index_data(pure_symbol, start_date, end_date)


def main():
    """主函数"""
    st.title("📈 A股数据可视化分析系统")
    
    # 侧边栏导航
    st.sidebar.title("导航菜单")
    page = st.sidebar.radio(
        "选择页面",
        ["📊 股票列表", "📈 股票详细分析", "🔍 多股票对比", "📉 技术指标分析", "📊 统计分析", "💻 AI Agent交易结果", "⬇️ 下载股票数据"]
    )
    
    # 根据选择显示不同页面
    if page == "📊 股票列表":
        show_stock_list_page()
    elif page == "📈 股票详细分析":
        show_stock_detail_page()
    elif page == "🔍 多股票对比":
        show_comparison_page()
    elif page == "📉 技术指标分析":
        show_indicators_page()
    elif page == "📊 统计分析":
        show_statistics_page()
    elif page == "💻 AI Agent交易结果":
        show_ai_agent_page()
    elif page == "⬇️ 下载股票数据":
        show_download_page()


def show_stock_list_page():
    """显示股票列表页面（优化版本）"""
    st.header("股票列表")
    
    # 搜索栏
    col1, col2 = st.columns([3, 1])
    with col1:
        search_keyword = st.text_input("🔍 搜索股票（代码或名称）", "")
    
    # 获取股票列表（使用缓存）
    with st.spinner('加载数据中...'):
        if search_keyword:
            stocks_df = get_cached_search_results(search_keyword)
        else:
            # 分页加载，默认加载前500只
            stocks_df = get_cached_stocks_list(limit=500, offset=0)
    
    if stocks_df.empty:
        st.warning("暂无股票数据，请先使用命令行工具下载数据。")
        st.code("python main.py download-stocks --limit 10", language="bash")
        return
    
    # 显示统计信息
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("股票总数", f"{len(stocks_df):,}")
    with col2:
        total_records = stocks_df['data_count'].sum()
        st.metric("数据总条数", f"{total_records:,}")
    with col3:
        avg_records = stocks_df['data_count'].mean()
        st.metric("平均数据量", f"{avg_records:.0f}")
    with col4:
        max_records = stocks_df['data_count'].max()
        st.metric("最大数据量", f"{max_records:,}")
    
    st.divider()
    
    # 显示股票表格
    st.subheader("股票列表")
    
    # 数据表格配置
    display_df = stocks_df.copy()
    display_df = display_df.rename(columns={
        'symbol': '股票代码',
        'name': '股票名称',
        'market': '市场',
        'data_count': '数据条数',
        'start_date': '起始日期',
        'end_date': '结束日期'
    })
    
    # 使用分页显示
    page_size = 50
    total_pages = (len(display_df) - 1) // page_size + 1
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        current_page = st.number_input(
            f"页码（共 {total_pages} 页）",
            min_value=1,
            max_value=total_pages,
            value=1
        )
    
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, len(display_df))
    
    st.dataframe(
        display_df.iloc[start_idx:end_idx],
        width='stretch',
        hide_index=True
    )
    
    st.info(f"显示 {start_idx + 1} - {end_idx} 条，共 {len(display_df)} 条记录")


def show_stock_detail_page():
    """显示股票详细分析页面（优化版本）"""
    st.header("股票详细分析")
    
    # 股票选择
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 搜索股票
        search_keyword = st.text_input("🔍 搜索股票", "", key="detail_search")
        
        with st.spinner('搜索中...'):
            if search_keyword:
                stocks_df = get_cached_search_results(search_keyword)
            else:
                # 限制加载100只股票，避免加载过多
                stocks_df = get_cached_stocks_list(limit=100, offset=0)
        
        if stocks_df.empty:
            st.warning("未找到股票数据")
            return
        
        # 股票选择下拉框
        stock_options = {f"{row['symbol']} - {row['name']}": row['symbol'] 
                        for _, row in stocks_df.iterrows()}
        
        selected_stock = st.selectbox(
            "选择股票",
            options=list(stock_options.keys())
        )
        
        if not selected_stock:
            return
        
        symbol = stock_options[selected_stock]
    
    with col2:
        # 日期范围选择
        date_range = st.selectbox(
            "时间范围",
            ["近1个月", "近3个月", "近6个月", "近1年", "近3年", "全部", "自定义"],
            index=3
        )
    
    # 获取股票信息（使用缓存）
    stock_info = get_cached_stock_info(symbol)
    if not stock_info:
        st.error(f"未找到股票 {symbol} 的信息")
        return
    
    # 计算日期范围
    end_date = datetime.now()
    if date_range == "近1个月":
        start_date = end_date - timedelta(days=30)
    elif date_range == "近3个月":
        start_date = end_date - timedelta(days=90)
    elif date_range == "近6个月":
        start_date = end_date - timedelta(days=180)
    elif date_range == "近1年":
        start_date = end_date - timedelta(days=365)
    elif date_range == "近3年":
        start_date = end_date - timedelta(days=365*3)
    elif date_range == "自定义":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期", end_date - timedelta(days=365))
        with col2:
            end_date = st.date_input("结束日期", end_date)
    else:
        start_date = None
    
    # 转换日期格式
    start_date_str = start_date.strftime('%Y-%m-%d') if start_date else None
    end_date_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime) else end_date.strftime('%Y-%m-%d')
    
    # 获取股票数据（使用缓存）
    with st.spinner(f'加载 {symbol} 数据中...'):
        df = get_cached_stock_data(symbol, start_date_str, end_date_str)
    
    if df.empty:
        st.warning(f"股票 {symbol} 暂无数据")
        return
    
    # 计算技术指标（缓存计算结果）
    df = get_cached_indicators(df, symbol, start_date_str, end_date_str)
    
    # 显示股票基本信息
    st.subheader(f"{symbol} - {stock_info['name']}")
    
    # 最新价格信息（使用缓存）
    latest = get_cached_latest_price(symbol)
    if latest:
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        pct_change = latest['pct_change'] if latest['pct_change'] else 0
        change_color = "normal" if pct_change == 0 else ("inverse" if pct_change > 0 else "off")
        
        with col1:
            st.metric("最新价", f"¥{latest['close']:.2f}")
        with col2:
            st.metric("涨跌幅", f"{pct_change:.2f}%", delta=f"{pct_change:.2f}%", delta_color=change_color)
        with col3:
            st.metric("开盘价", f"¥{latest['open']:.2f}")
        with col4:
            st.metric("最高价", f"¥{latest['high']:.2f}")
        with col5:
            st.metric("最低价", f"¥{latest['low']:.2f}")
        with col6:
            st.metric("成交量", f"{latest['volume']/10000:.2f}万")
        
        st.caption(f"更新时间: {latest['date']}")
    
    st.divider()
    
    # 指数选择
    with st.expander("📊 添加指数对比（可选）", expanded=False):
        selected_indices = st.multiselect(
            "选择要对比的指数",
            options=list(COMMON_INDICES.keys()),
            format_func=lambda x: f"{x} - {COMMON_INDICES[x]}",
            default=[],
            help="在收益率分析中显示指数对比",
            key="detail_indices"
        )
    
    # 图表选项
    chart_type = st.radio(
        "选择图表类型",
        ["组合图表", "K线图", "成交量", "MACD", "RSI", "KDJ", "布林带", "收益率分析"],
        horizontal=True
    )
    
    # 显示图表
    if chart_type == "组合图表":
        fig = create_combined_chart(df, symbol, stock_info['name'])
        st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
    elif chart_type == "K线图":
        fig = create_candlestick_chart(df, f"{symbol} - {stock_info['name']} K线图")
        st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
    elif chart_type == "成交量":
        fig = create_volume_chart(df)
        st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
    elif chart_type == "MACD":
        fig = create_macd_chart(df)
        st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
    elif chart_type == "RSI":
        fig = create_rsi_chart(df)
        st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
    elif chart_type == "KDJ":
        fig = create_kdj_chart(df)
        st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
    elif chart_type == "布林带":
        fig = create_bollinger_chart(df)
        st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
    elif chart_type == "收益率分析":
        # 如果选择了指数，创建对比图
        if selected_indices:
            # 获取指数数据
            index_data_dict = {}
            with st.spinner(f'加载 {len(selected_indices)} 个指数数据...'):
                for index_symbol in selected_indices:
                    index_df = get_cached_index_data(index_symbol, start_date_str, end_date_str)
                    if not index_df.empty:
                        index_data_dict[index_symbol] = index_df
            
            # 创建对比图（归一化）
            st.subheader("收益率对比（归一化）")
            data_dict = {symbol: df}
            if index_data_dict:
                fig = create_comparison_with_index(data_dict, index_data_dict, COMMON_INDICES, f"{symbol} vs 指数对比")
            else:
                fig = create_comparison_chart(data_dict, f"{symbol} 收益率")
            st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
        else:
            fig = create_returns_chart(df)
            st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
    
    # 数据表格
    with st.expander("📊 查看原始数据"):
        st.dataframe(df.tail(100), width='stretch')


def show_comparison_page():
    """显示多股票对比页面（优化版本）"""
    st.header("多股票对比分析")
    
    st.info("💡 选择多只股票进行对比分析，可以查看相对表现和收益率对比。")
    
    # 股票选择（限制加载数量）
    with st.spinner('加载股票列表...'):
        stocks_df = get_cached_stocks_list(limit=500, offset=0)
    
    if stocks_df.empty:
        st.warning("暂无股票数据")
        return
    
    # 创建股票选项
    stock_options = {f"{row['symbol']} - {row['name']}": row['symbol'] 
                    for _, row in stocks_df.iterrows()}
    
    # 多选
    selected_stocks = st.multiselect(
        "选择要对比的股票（最多10只）",
        options=list(stock_options.keys()),
        max_selections=10
    )
    
    if not selected_stocks:
        st.warning("请至少选择一只股票")
        return
    
    symbols = [stock_options[s] for s in selected_stocks]
    
    # 日期范围和指数选择
    col1, col2 = st.columns(2)
    with col1:
        date_range = st.selectbox(
            "时间范围",
            ["近1个月", "近3个月", "近6个月", "近1年", "近3年"],
            index=2
        )
    
    # 指数选择
    st.subheader("📊 添加指数对比")
    selected_indices = st.multiselect(
        "选择要对比的指数（可选）",
        options=list(COMMON_INDICES.keys()),
        format_func=lambda x: f"{x} - {COMMON_INDICES[x]}",
        default=[],
        help="选择指数与股票进行对比分析"
    )
    
    # 计算日期
    end_date = datetime.now()
    if date_range == "近1个月":
        start_date = end_date - timedelta(days=30)
    elif date_range == "近3个月":
        start_date = end_date - timedelta(days=90)
    elif date_range == "近6个月":
        start_date = end_date - timedelta(days=180)
    elif date_range == "近1年":
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=365*3)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # 获取股票数据（使用缓存）
    with st.spinner(f'加载 {len(symbols)} 只股票数据...'):
        data_dict = get_cached_multiple_stocks(tuple(symbols), start_date_str, end_date_str)
    
    if not data_dict:
        st.warning("未找到数据")
        return
    
    # 获取指数数据
    index_data_dict = {}
    if selected_indices:
        with st.spinner(f'加载 {len(selected_indices)} 个指数数据...'):
            for index_symbol in selected_indices:
                index_df = get_cached_index_data(index_symbol, start_date_str, end_date_str)
                if not index_df.empty:
                    index_data_dict[index_symbol] = index_df
    
    # 对比图表
    st.subheader("价格走势对比（归一化）")
    if index_data_dict:
        fig = create_comparison_with_index(data_dict, index_data_dict, COMMON_INDICES, "股票与指数对比")
    else:
        fig = create_comparison_chart(data_dict, "股票价格对比")
    st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
    
    # 统计对比表
    st.subheader("统计数据对比")
    
    stats_data = []
    for symbol, df in data_dict.items():
        if not df.empty:
            stock_info = get_cached_stock_info(symbol)
            name = stock_info['name'] if stock_info else symbol
            
            # 计算统计数据
            total_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
            volatility = df['close'].pct_change().std() * (252 ** 0.5) * 100
            max_price = df['high'].max()
            min_price = df['low'].min()
            avg_volume = df['volume'].mean()
            
            stats_data.append({
                '股票代码': symbol,
                '股票名称': name,
                '总收益率(%)': f"{total_return:.2f}",
                '年化波动率(%)': f"{volatility:.2f}",
                '最高价': f"{max_price:.2f}",
                '最低价': f"{min_price:.2f}",
                '平均成交量': f"{avg_volume/10000:.2f}万"
            })
    
    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, width='stretch', hide_index=True)


def show_indicators_page():
    """显示技术指标分析页面（优化版本）"""
    st.header("技术指标分析")
    
    # 股票选择（使用缓存）
    with st.spinner('加载股票列表...'):
        stocks_df = get_cached_stocks_list(limit=100, offset=0)
    
    if stocks_df.empty:
        st.warning("暂无股票数据")
        return
    
    stock_options = {f"{row['symbol']} - {row['name']}": row['symbol'] 
                    for _, row in stocks_df.iterrows()}
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_stock = st.selectbox("选择股票", options=list(stock_options.keys()))
        if not selected_stock:
            return
        symbol = stock_options[selected_stock]
    
    with col2:
        days = st.selectbox("数据天数", [60, 120, 250, 500], index=2)
    
    # 获取数据（使用缓存）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    with st.spinner(f'加载 {symbol} 数据中...'):
        df = get_cached_stock_data(symbol, start_date, end_date)
    
    if df.empty:
        st.warning(f"股票 {symbol} 暂无数据")
        return
    
    # 计算指标（使用缓存）
    df = get_cached_indicators(df, symbol, start_date, end_date)
    
    # 显示不同指标
    tab1, tab2, tab3, tab4 = st.tabs(["移动平均线", "MACD", "RSI", "KDJ"])
    
    with tab1:
        st.subheader("移动平均线 (MA)")
        st.write("移动平均线是最常用的技术指标，用于判断趋势方向。")
        fig = create_candlestick_chart(df, f"{symbol} K线与MA", show_ma=True)
        st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
        
        # 最新MA值
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if 'MA5' in df.columns:
                st.metric("MA5", f"¥{df['MA5'].iloc[-1]:.2f}")
        with col2:
            if 'MA10' in df.columns:
                st.metric("MA10", f"¥{df['MA10'].iloc[-1]:.2f}")
        with col3:
            if 'MA20' in df.columns:
                st.metric("MA20", f"¥{df['MA20'].iloc[-1]:.2f}")
        with col4:
            if 'MA60' in df.columns:
                st.metric("MA60", f"¥{df['MA60'].iloc[-1]:.2f}")
    
    with tab2:
        st.subheader("MACD指标")
        st.write("MACD是趋势跟踪动量指标，用于判断买卖时机。")
        fig = create_macd_chart(df)
        st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
        
        # 最新MACD值
        if 'MACD' in df.columns:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("MACD", f"{df['MACD'].iloc[-1]:.4f}")
            with col2:
                st.metric("信号线", f"{df['MACD_signal'].iloc[-1]:.4f}")
            with col3:
                st.metric("MACD柱", f"{df['MACD_hist'].iloc[-1]:.4f}")
    
    with tab3:
        st.subheader("RSI指标")
        st.write("RSI用于衡量市场超买超卖状态，取值0-100。")
        fig = create_rsi_chart(df)
        st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
        
        # RSI分析
        if 'RSI' in df.columns:
            rsi_value = df['RSI'].iloc[-1]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("当前RSI", f"{rsi_value:.2f}")
            with col2:
                if rsi_value > 70:
                    st.error("⚠️ 超买区域")
                elif rsi_value < 30:
                    st.success("⚠️ 超卖区域")
                else:
                    st.info("✓ 正常区域")
    
    with tab4:
        st.subheader("KDJ指标")
        st.write("KDJ是随机指标，用于判断超买超卖。")
        fig = create_kdj_chart(df)
        st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
        
        # KDJ值
        if 'K' in df.columns:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("K值", f"{df['K'].iloc[-1]:.2f}")
            with col2:
                st.metric("D值", f"{df['D'].iloc[-1]:.2f}")
            with col3:
                st.metric("J值", f"{df['J'].iloc[-1]:.2f}")


def show_statistics_page():
    """显示统计分析页面（优化版本）"""
    st.header("统计分析")
    
    # 股票选择（使用缓存）
    with st.spinner('加载股票列表...'):
        stocks_df = get_cached_stocks_list(limit=100, offset=0)
    
    if stocks_df.empty:
        st.warning("暂无股票数据")
        return
    
    stock_options = {f"{row['symbol']} - {row['name']}": row['symbol'] 
                    for _, row in stocks_df.iterrows()}
    
    selected_stock = st.selectbox("选择股票", options=list(stock_options.keys()))
    if not selected_stock:
        return
    
    symbol = stock_options[selected_stock]
    
    # 统计周期选择
    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox("统计周期", [30, 60, 90, 180, 365], index=2)
    
    # 获取统计数据（使用缓存）
    with st.spinner('计算统计数据...'):
        stats = get_cached_statistics(symbol, period)
    
    if not stats:
        st.warning("暂无统计数据")
        return
    
    # 显示统计指标
    st.subheader(f"近{period}天统计数据")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("平均收盘价", f"¥{stats['avg_close']:.2f}")
    with col2:
        st.metric("最高价", f"¥{stats['max_high']:.2f}")
    with col3:
        st.metric("最低价", f"¥{stats['min_low']:.2f}")
    with col4:
        price_range = ((stats['max_high'] - stats['min_low']) / stats['min_low'] * 100)
        st.metric("价格波动幅度", f"{price_range:.2f}%")
    
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("平均成交量", f"{stats['avg_volume']/10000:.2f}万")
    with col2:
        st.metric("总成交量", f"{stats['total_volume']/100000000:.2f}亿")
    with col3:
        st.metric("平均涨跌幅", f"{stats['avg_pct_change']:.2f}%")
    with col4:
        st.metric("最大单日涨幅", f"{stats['max_pct_change']:.2f}%")
    
    # 获取详细数据绘制分布图（使用缓存）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=period)).strftime('%Y-%m-%d')
    df = get_cached_stock_data(symbol, start_date, end_date)
    
    if not df.empty:
        st.divider()
        st.subheader("收益率分布")
        
        # 计算收益率
        df = calculate_returns(df)
        
        # 收益率直方图
        import plotly.express as px
        
        fig = px.histogram(
            df,
            x='daily_return',
            nbins=50,
            title='日收益率分布',
            labels={'daily_return': '日收益率', 'count': '频数'}
        )
        fig.update_traces(marker_color='lightblue', marker_line_color='darkblue', marker_line_width=1)
        st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)


def get_cached_stock_list(db, downloader, force_refresh=False):
    """获取股票列表（优先从数据库缓存，支持强制刷新）"""
    if force_refresh:
        # 强制从网络刷新
        with st.spinner("正在从网络获取最新股票列表..."):
            stock_list = downloader.get_stock_list()
            if not stock_list.empty:
                db.save_stock_info(stock_list)
                st.success(f"✅ 成功刷新股票列表，共 {len(stock_list)} 只股票")
            return stock_list
    else:
        # 优先从数据库获取
        stock_list = db.get_stock_list_for_download()
        if stock_list.empty:
            # 数据库为空，从网络获取
            with st.spinner("首次获取股票列表..."):
                stock_list = downloader.get_stock_list()
                if not stock_list.empty:
                    db.save_stock_info(stock_list)
        return stock_list


def show_download_page():
    """显示股票下载页面"""
    st.header("⬇️ 下载股票数据")
    
    st.info("💡 从数据源下载股票历史数据并保存到本地数据库。支持单个下载、批量下载和搜索下载。")
    
    # 初始化下载器和数据库
    @st.cache_resource
    def get_downloader_and_db():
        return DataDownloader(), Database()
    
    downloader, db = get_downloader_and_db()
    
    # 显示股票列表状态和刷新按钮
    stock_count = db.get_stock_list_count()
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if stock_count > 0:
            st.info(f"📊 本地已缓存 {stock_count} 只股票信息")
        else:
            st.warning("⚠️ 本地暂无股票列表缓存，将在搜索或批量下载时自动获取")
    with col2:
        if st.button("🔄 刷新股票列表", help="从网络重新获取最新的股票列表"):
            get_cached_stock_list(db, downloader, force_refresh=True)
            st.rerun()
    with col3:
        pass  # 预留空间
    
    # 下载模式选择
    download_mode = st.radio(
        "选择下载模式",
        ["📋 单个股票", "🔍 搜索并下载", "📦 批量下载"],
        horizontal=True
    )
    
    st.divider()
    
    # 时间范围设置（通用）
    st.subheader("⏰ 时间范围设置")
    col1, col2 = st.columns(2)
    
    with col1:
        use_default_range = st.checkbox("使用默认时间范围（从2010-01-01至今）", value=True)
    
    if not use_default_range:
        with col1:
            start_date = st.date_input(
                "开始日期",
                value=datetime(2020, 1, 1),
                min_value=datetime(2000, 1, 1),
                max_value=datetime.now()
            )
        with col2:
            end_date = st.date_input(
                "结束日期",
                value=datetime.now(),
                min_value=datetime(2000, 1, 1),
                max_value=datetime.now()
            )
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
    else:
        start_date_str = '20100101'
        end_date_str = datetime.now().strftime('%Y%m%d')
        st.caption(f"将下载从 2010-01-01 到 {datetime.now().strftime('%Y-%m-%d')} 的数据")
    
    # 请求间隔设置（通用）
    st.subheader("⚙️ 请求设置")
    request_interval = st.slider(
        "请求间隔（秒）- 避免请求过快被限制",
        min_value=0.5,
        max_value=10.0,
        value=2.0,
        step=0.5,
        help="设置每次请求之间的等待时间，建议2-3秒"
    )
    
    st.divider()
    
    # 根据不同模式显示不同的下载界面
    if download_mode == "📋 单个股票":
        show_single_download_section(downloader, db, start_date_str, end_date_str, request_interval)
    elif download_mode == "🔍 搜索并下载":
        show_search_download_section(downloader, db, start_date_str, end_date_str, request_interval)
    elif download_mode == "📦 批量下载":
        show_batch_download_section(downloader, db, start_date_str, end_date_str, request_interval)


def show_single_download_section(downloader, db, start_date, end_date, interval):
    """单个股票下载部分"""
    st.subheader("📋 单个股票下载")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        stock_symbol = st.text_input(
            "输入股票代码",
            placeholder="例如: 000001, 600000",
            help="输入6位数字股票代码"
        )
    
    with col2:
        st.write("")
        st.write("")
        if st.button("🚀 开始下载", type="primary", width='stretch'):
            if not stock_symbol:
                st.error("❌ 请输入股票代码")
            else:
                download_single_stock(downloader, db, stock_symbol.strip(), start_date, end_date)


def show_search_download_section(downloader, db, start_date, end_date, interval):
    """搜索并下载部分"""
    st.subheader("🔍 搜索并下载")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_keyword = st.text_input(
            "搜索股票（代码或名称）",
            placeholder="例如: 平安银行, 000001",
            help="输入股票代码或名称进行搜索"
        )
    
    if search_keyword:
        with st.spinner("正在搜索股票列表..."):
            try:
                stock_list = get_cached_stock_list(db, downloader)
                if not stock_list.empty:
                    # 搜索匹配
                    matched = stock_list[
                        stock_list['code'].str.contains(search_keyword, na=False) |
                        stock_list['name'].str.contains(search_keyword, na=False)
                    ]
                    
                    if not matched.empty:
                        st.success(f"✅ 找到 {len(matched)} 只匹配的股票")
                        
                        # 显示匹配结果
                        display_df = matched[['code', 'name']].rename(columns={
                            'code': '股票代码',
                            'name': '股票名称'
                        })
                        st.dataframe(display_df, width='stretch', hide_index=True)
                        
                        # 下载选项
                        col1, col2 = st.columns(2)
                        with col1:
                            download_all = st.checkbox("下载所有搜索结果", value=False)
                        
                        if download_all:
                            if st.button("🚀 下载所有搜索到的股票", type="primary"):
                                download_multiple_stocks(
                                    downloader, db, matched['code'].tolist(),
                                    start_date, end_date, interval
                                )
                        else:
                            selected_codes = st.multiselect(
                                "选择要下载的股票",
                                options=matched['code'].tolist(),
                                format_func=lambda x: f"{x} - {matched[matched['code']==x]['name'].values[0]}"
                            )
                            
                            if selected_codes and st.button("🚀 下载选中的股票", type="primary"):
                                download_multiple_stocks(
                                    downloader, db, selected_codes,
                                    start_date, end_date, interval
                                )
                    else:
                        st.warning("⚠️ 未找到匹配的股票")
                else:
                    st.error("❌ 获取股票列表失败")
            except Exception as e:
                st.error(f"❌ 搜索失败: {str(e)}")


def show_batch_download_section(downloader, db, start_date, end_date, interval):
    """批量下载部分"""
    st.subheader("📦 批量下载")
    
    st.warning("⚠️ 批量下载会消耗较长时间，请合理设置下载数量和请求间隔")
    
    # 批量下载选项
    batch_mode = st.radio(
        "批量模式",
        ["按数量下载", "按股票代码范围下载"],
        horizontal=True
    )
    
    if batch_mode == "按数量下载":
        col1, col2 = st.columns(2)
        
        with col1:
            limit = st.number_input(
                "下载数量",
                min_value=1,
                max_value=5000,
                value=10,
                step=10,
                help="限制下载的股票数量"
            )
        
        with col2:
            skip = st.number_input(
                "跳过前N只",
                min_value=0,
                max_value=5000,
                value=0,
                step=10,
                help="跳过列表前面的股票"
            )
        
        if st.button("🚀 开始批量下载", type="primary"):
            download_batch_by_limit(downloader, db, start_date, end_date, interval, limit, skip)
    
    else:  # 按股票代码范围
        col1, col2 = st.columns(2)
        
        with col1:
            start_code = st.text_input(
                "起始代码",
                value="000001",
                help="输入起始股票代码"
            )
        
        with col2:
            end_code = st.text_input(
                "结束代码",
                value="000100",
                help="输入结束股票代码"
            )
        
        if st.button("🚀 开始范围下载", type="primary"):
            download_batch_by_range(downloader, db, start_date, end_date, interval, start_code, end_code)


def download_single_stock(downloader, db, symbol, start_date, end_date):
    """下载单个股票"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text(f"正在下载 {symbol}...")
        progress_bar.progress(30)
        
        df = downloader.get_stock_daily_data(symbol, start_date, end_date)
        progress_bar.progress(70)
        
        if not df.empty:
            # 保存到数据库
            db.save_stock_daily_data(symbol, df)
            progress_bar.progress(100)
            status_text.empty()
            st.success(f"✅ 成功下载 {symbol}，共 {len(df)} 条数据")
            
            # 显示数据预览
            with st.expander("查看数据预览"):
                st.dataframe(df.head(10), width='stretch')
        else:
            progress_bar.progress(100)
            status_text.empty()
            st.warning(f"⚠️ 股票 {symbol} 无数据或下载失败")
    
    except Exception as e:
        progress_bar.progress(100)
        status_text.empty()
        st.error(f"❌ 下载失败: {str(e)}")


def download_multiple_stocks(downloader, db, symbols, start_date, end_date, interval):
    """下载多个股票"""
    total = len(symbols)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    success_count = 0
    failed_count = 0
    
    for idx, symbol in enumerate(symbols):
        try:
            status_text.text(f"正在下载 {symbol} ({idx + 1}/{total})...")
            
            df = downloader.get_stock_daily_data(symbol, start_date, end_date)
            
            if not df.empty:
                db.save_stock_daily_data(symbol, df)
                success_count += 1
            else:
                failed_count += 1
            
            # 更新进度
            progress_bar.progress((idx + 1) / total)
            
            # 等待间隔
            if idx < total - 1:  # 最后一个不需要等待
                time.sleep(interval)
        
        except Exception as e:
            failed_count += 1
            st.error(f"下载 {symbol} 失败: {str(e)}")
    
    progress_bar.progress(1.0)
    status_text.empty()
    
    # 显示结果
    col1, col2 = st.columns(2)
    with col1:
        st.metric("成功", success_count, delta=success_count)
    with col2:
        st.metric("失败", failed_count, delta=-failed_count if failed_count > 0 else 0)
    
    if success_count > 0:
        st.success(f"✅ 批量下载完成！成功 {success_count} 只，失败 {failed_count} 只")
    else:
        st.error("❌ 所有股票下载失败")


def download_batch_by_limit(downloader, db, start_date, end_date, interval, limit, skip):
    """按数量批量下载"""
    status_text = st.empty()
    
    try:
        status_text.text("正在获取股票列表...")
        stock_list = get_cached_stock_list(db, downloader)
        
        if stock_list.empty:
            st.error("❌ 获取股票列表失败")
            return
        
        # 应用跳过和限制
        stock_list = stock_list.iloc[skip:skip + limit]
        symbols = stock_list['code'].tolist()
        
        status_text.empty()
        st.info(f"📊 将下载 {len(symbols)} 只股票")
        
        # 调用多股票下载
        download_multiple_stocks(downloader, db, symbols, start_date, end_date, interval)
        
        # 同时保存股票信息
        db.save_stock_info(stock_list)
    
    except Exception as e:
        status_text.empty()
        st.error(f"❌ 批量下载失败: {str(e)}")


def download_batch_by_range(downloader, db, start_date, end_date, interval, start_code, end_code):
    """按代码范围批量下载"""
    status_text = st.empty()
    
    try:
        status_text.text("正在获取股票列表...")
        stock_list = get_cached_stock_list(db, downloader)
        
        if stock_list.empty:
            st.error("❌ 获取股票列表失败")
            return
        
        # 过滤代码范围
        filtered = stock_list[
            (stock_list['code'] >= start_code) & 
            (stock_list['code'] <= end_code)
        ]
        
        if filtered.empty:
            status_text.empty()
            st.warning(f"⚠️ 在代码范围 {start_code} - {end_code} 内未找到股票")
            return
        
        symbols = filtered['code'].tolist()
        status_text.empty()
        st.info(f"📊 在范围内找到 {len(symbols)} 只股票")
        
        # 调用多股票下载
        download_multiple_stocks(downloader, db, symbols, start_date, end_date, interval)
        
        # 同时保存股票信息
        db.save_stock_info(filtered)
    
    except Exception as e:
        status_text.empty()
        st.error(f"❌ 范围下载失败: {str(e)}")


def show_ai_agent_page():
    """显示AI Agent交易结果页面"""
    st.header("💻 AI Agent交易结果分析")
    
    st.info("💡 展示AI Agents的炒股操作结果，包括资产曲线、收益率变化和每日交易操作。")
    
    # 初始化数据加载器
    @st.cache_resource
    def get_agent_loader():
        return AgentDataLoader()
    
    agent_loader = get_agent_loader()
    
    # 获取可用的日志文件
    available_logs = agent_loader.get_available_logs()
    
    if not available_logs:
        st.warning("⚠️ 暂无AI Agent交易日志数据")
        st.info("请先运行AI Agent进行交易模拟，日志文件将保存在 `Agents_Experience/logs` 目录中。")
        return
    
    # 选择日志文件
    st.subheader("📂 选择交易日志")
    
    log_options = {log['display_name']: log for log in available_logs}
    selected_log_name = st.selectbox(
        "选择Agent和时间",
        options=list(log_options.keys())
    )
    
    selected_log = log_options[selected_log_name]
    
    # 加载数据
    with st.spinner('加载交易数据中...'):
        portfolio_df = agent_loader.load_portfolio_data(selected_log['portfolio_file'])
        transactions_df = agent_loader.load_daily_transactions(selected_log['portfolio_file'])
        statistics = agent_loader.get_portfolio_statistics(selected_log['portfolio_file'])
    
    if portfolio_df.empty:
        st.error("❌ 无法加载投资组合数据")
        return
    
    st.divider()
    
    # 显示统计概览
    st.subheader("📊 投资组合统计概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "初始资金",
            f"¥{statistics.get('初始资金', 0):,.0f}"
        )
    with col2:
        final_value = statistics.get('最终资产', 0)
        initial_value = statistics.get('初始资金', 1)
        total_return = statistics.get('总收益率', 0)
        st.metric(
            "最终资产",
            f"¥{final_value:,.0f}",
            delta=f"{total_return:.2f}%",
            delta_color="normal" if total_return >= 0 else "inverse"
        )
    with col3:
        st.metric(
            "总收益",
            f"¥{statistics.get('总收益', 0):,.0f}"
        )
    with col4:
        st.metric(
            "交易天数",
            f"{statistics.get('交易天数', 0)} 天"
        )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "最大资产",
            f"¥{statistics.get('最大资产', 0):,.0f}"
        )
    with col2:
        st.metric(
            "最大回撤",
            f"{statistics.get('最大回撤', 0):.2f}%"
        )
    with col3:
        st.metric(
            "收益波动率",
            f"{statistics.get('收益波动率', 0):.2f}%"
        )
    with col4:
        sharpe = statistics.get('夏普比率', 0)
        st.metric(
            "夏普比率",
            f"{sharpe:.2f}"
        )
    
    st.divider()
    
    # 指数选择（在侧边栏）
    with st.sidebar:
        st.subheader("📊 指数对比设置")
        selected_indices = st.multiselect(
            "选择指数进行对比",
            options=list(COMMON_INDICES.keys()),
            format_func=lambda x: f"{COMMON_INDICES[x]}",
            default=[],
            help="在资产曲线图中显示指数走势对比",
            key="agent_indices"
        )
    
    # 图表展示选项
    chart_view = st.radio(
        "选择视图",
        ["📈 综合概览", "💰 资产曲线", "📊 收益率变化", "💼 资产配置", "🔄 交易操作", "📋 持仓分布", "📉 收益率分布"],
        horizontal=True
    )
    
    st.divider()
    
    # 根据选择显示不同图表
    if chart_view == "📈 综合概览":
        st.subheader("综合概览")
        
        # 获取指数数据（如果已选择）
        index_data_dict = {}
        if selected_indices:
            start_date_str = portfolio_df['日期'].min().strftime('%Y-%m-%d')
            end_date_str = portfolio_df['日期'].max().strftime('%Y-%m-%d')
            
            with st.spinner(f'加载 {len(selected_indices)} 个指数数据...'):
                for index_symbol in selected_indices:
                    index_df = get_cached_index_data(index_symbol, start_date_str, end_date_str)
                    if not index_df.empty:
                        index_data_dict[index_symbol] = index_df
        
        # 创建图表
        if index_data_dict:
            fig = create_combined_overview_chart(
                portfolio_df, 
                selected_log['agent_name'],
                index_data_dict,
                COMMON_INDICES
            )
        else:
            fig = create_combined_overview_chart(portfolio_df, selected_log['agent_name'])
        
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        
    elif chart_view == "💰 资产曲线":
        st.subheader("总资产变化曲线")
        
        # 获取指数数据
        index_data_dict = {}
        if selected_indices:
            # 获取日期范围
            start_date_str = portfolio_df['日期'].min().strftime('%Y-%m-%d')
            end_date_str = portfolio_df['日期'].max().strftime('%Y-%m-%d')
            
            with st.spinner(f'加载 {len(selected_indices)} 个指数数据...'):
                for index_symbol in selected_indices:
                    index_df = get_cached_index_data(index_symbol, start_date_str, end_date_str)
                    if not index_df.empty:
                        index_data_dict[index_symbol] = index_df
        
        # 根据是否有指数数据选择不同的图表
        if index_data_dict:
            fig = create_portfolio_value_chart_with_index(
                portfolio_df, 
                index_data_dict, 
                COMMON_INDICES,
                "投资组合 vs 指数对比"
            )
        else:
            fig = create_portfolio_value_chart(portfolio_df)
        
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        
    elif chart_view == "📊 收益率变化":
        st.subheader("收益率变化")
        fig = create_return_rate_chart(portfolio_df)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        
    elif chart_view == "💼 资产配置":
        st.subheader("现金与持仓市值分布")
        fig = create_cash_position_chart(portfolio_df)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        
    elif chart_view == "🔄 交易操作":
        st.subheader("交易操作时间线")
        fig = create_transactions_timeline(transactions_df)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        
        # 显示交易记录表格
        if not transactions_df.empty:
            st.subheader("📋 交易记录详情")
            
            # 添加筛选选项
            col1, col2 = st.columns(2)
            with col1:
                operation_filter = st.multiselect(
                    "筛选操作类型",
                    options=transactions_df['操作'].unique().tolist(),
                    default=transactions_df['操作'].unique().tolist()
                )
            
            filtered_transactions = transactions_df[transactions_df['操作'].isin(operation_filter)]
            
            # 格式化显示
            display_df = filtered_transactions.copy()
            display_df['日期'] = display_df['日期'].dt.strftime('%Y-%m-%d')
            display_df['金额'] = display_df['金额'].apply(lambda x: f"¥{x:,.2f}")
            display_df['价格'] = display_df['价格'].apply(lambda x: f"¥{x:.2f}")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # 统计信息
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总交易次数", len(filtered_transactions))
            with col2:
                buy_count = len(filtered_transactions[filtered_transactions['操作'].isin(['买入', '加仓'])])
                st.metric("买入次数", buy_count)
            with col3:
                sell_count = len(filtered_transactions[filtered_transactions['操作'].isin(['卖出', '减仓'])])
                st.metric("卖出次数", sell_count)
            with col4:
                unique_stocks = filtered_transactions['股票代码'].nunique()
                st.metric("交易股票数", unique_stocks)
    
    elif chart_view == "📋 持仓分布":
        st.subheader("持仓分布")
        
        # 选择日期查看持仓
        selected_date = st.select_slider(
            "选择日期",
            options=portfolio_df['日期'].dt.strftime('%Y-%m-%d').tolist(),
            value=portfolio_df['日期'].iloc[-1].strftime('%Y-%m-%d')
        )
        
        # 获取该日期的持仓详情
        date_data = portfolio_df[portfolio_df['日期'].dt.strftime('%Y-%m-%d') == selected_date].iloc[0]
        holdings_str = date_data['持仓详情']
        
        fig = create_holdings_pie_chart(holdings_str, selected_date)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        
        # 显示详细持仓信息
        if pd.notna(holdings_str) and holdings_str:
            st.subheader("持仓明细")
            holdings = agent_loader.parse_holdings_detail(holdings_str)
            
            if holdings:
                holdings_display = []
                for h in holdings:
                    holdings_display.append({
                        '股票代码': h['symbol'],
                        '持仓数量': f"{h['shares']} 股",
                        '成本价格': f"¥{h['price']:.2f}",
                        '市值': f"¥{h['shares'] * h['price']:,.2f}",
                        '持仓收益率': f"{h['return_rate']:.2f}%"
                    })
                
                st.dataframe(
                    pd.DataFrame(holdings_display),
                    use_container_width=True,
                    hide_index=True
                )
    
    elif chart_view == "📉 收益率分布":
        st.subheader("日收益率分布")
        fig = create_daily_return_distribution(portfolio_df)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        
        # 显示收益率统计
        daily_returns = portfolio_df['收益率'].diff().dropna()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("平均日收益率", f"{daily_returns.mean():.3f}%")
        with col2:
            st.metric("收益率标准差", f"{daily_returns.std():.3f}%")
        with col3:
            st.metric("最大单日收益", f"{daily_returns.max():.2f}%")
        with col4:
            st.metric("最大单日亏损", f"{daily_returns.min():.2f}%")
    
    # 决策日志查看（如果存在）
    if selected_log['decision_file']:
        st.divider()
        with st.expander("📝 查看AI决策日志"):
            decisions = agent_loader.load_decision_log(selected_log['decision_file'])
            
            if decisions:
                # 选择日期查看决策
                decision_dates = [d['trade_date'] for d in decisions]
                selected_decision_date = st.selectbox(
                    "选择日期查看决策分析",
                    options=decision_dates
                )
                
                # 显示该日期的决策
                decision = next((d for d in decisions if d['trade_date'] == selected_decision_date), None)
                
                if decision:
                    st.markdown(f"**交易日期：** {decision['trade_date']}")
                    st.markdown(f"**记录时间：** {decision['timestamp']}")
                    
                    if decision['market_analysis']:
                        st.markdown("**市场分析：**")
                        st.text(decision['market_analysis'])
                    
                    if decision['decision_reason']:
                        st.markdown("**决策理由：**")
                        st.text(decision['decision_reason'])
            else:
                st.info("暂无决策日志内容")


if __name__ == "__main__":
    main()
