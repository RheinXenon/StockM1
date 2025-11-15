"""
股票数据可视化主应用
使用Streamlit构建交互式界面
"""
import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualization.data_loader import StockDataLoader
from visualization.indicators import calculate_all_indicators, calculate_returns, calculate_volatility
from visualization.charts import (
    create_candlestick_chart, create_volume_chart, create_macd_chart,
    create_rsi_chart, create_kdj_chart, create_bollinger_chart,
    create_combined_chart, create_comparison_chart, create_returns_chart
)

# 页面配置
st.set_page_config(
    page_title="A股数据可视化分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化数据加载器
@st.cache_resource
def get_data_loader():
    return StockDataLoader()

data_loader = get_data_loader()


def main():
    """主函数"""
    st.title("📈 A股数据可视化分析系统")
    
    # 侧边栏导航
    st.sidebar.title("导航菜单")
    page = st.sidebar.radio(
        "选择页面",
        ["📊 股票列表", "📈 股票详细分析", "🔍 多股票对比", "📉 技术指标分析", "📊 统计分析"]
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


def show_stock_list_page():
    """显示股票列表页面"""
    st.header("股票列表")
    
    # 搜索栏
    col1, col2 = st.columns([3, 1])
    with col1:
        search_keyword = st.text_input("🔍 搜索股票（代码或名称）", "")
    
    # 获取股票列表
    if search_keyword:
        stocks_df = data_loader.search_stocks(search_keyword)
    else:
        stocks_df = data_loader.get_all_stocks()
    
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
        use_container_width=True,
        hide_index=True
    )
    
    st.info(f"显示 {start_idx + 1} - {end_idx} 条，共 {len(display_df)} 条记录")


def show_stock_detail_page():
    """显示股票详细分析页面"""
    st.header("股票详细分析")
    
    # 股票选择
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 搜索股票
        search_keyword = st.text_input("🔍 搜索股票", "", key="detail_search")
        
        if search_keyword:
            stocks_df = data_loader.search_stocks(search_keyword)
        else:
            stocks_df = data_loader.get_all_stocks().head(100)
        
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
    
    # 获取股票信息
    stock_info = data_loader.get_stock_info(symbol)
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
    
    # 获取股票数据
    df = data_loader.get_stock_daily_data(symbol, start_date_str, end_date_str)
    
    if df.empty:
        st.warning(f"股票 {symbol} 暂无数据")
        return
    
    # 计算技术指标
    df = calculate_all_indicators(df)
    df = calculate_returns(df)
    df = calculate_volatility(df)
    
    # 显示股票基本信息
    st.subheader(f"{symbol} - {stock_info['name']}")
    
    # 最新价格信息
    latest = data_loader.get_latest_price(symbol)
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
    
    # 图表选项
    chart_type = st.radio(
        "选择图表类型",
        ["组合图表", "K线图", "成交量", "MACD", "RSI", "KDJ", "布林带", "收益率分析"],
        horizontal=True
    )
    
    # 显示图表
    if chart_type == "组合图表":
        fig = create_combined_chart(df, symbol, stock_info['name'])
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "K线图":
        fig = create_candlestick_chart(df, f"{symbol} - {stock_info['name']} K线图")
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "成交量":
        fig = create_volume_chart(df)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "MACD":
        fig = create_macd_chart(df)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "RSI":
        fig = create_rsi_chart(df)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "KDJ":
        fig = create_kdj_chart(df)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "布林带":
        fig = create_bollinger_chart(df)
        st.plotly_chart(fig, use_container_width=True)
    elif chart_type == "收益率分析":
        fig = create_returns_chart(df)
        st.plotly_chart(fig, use_container_width=True)
    
    # 数据表格
    with st.expander("📊 查看原始数据"):
        st.dataframe(df.tail(100), use_container_width=True)


def show_comparison_page():
    """显示多股票对比页面"""
    st.header("多股票对比分析")
    
    st.info("💡 选择多只股票进行对比分析，可以查看相对表现和收益率对比。")
    
    # 股票选择
    stocks_df = data_loader.get_all_stocks()
    
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
    
    # 日期范围
    col1, col2 = st.columns(2)
    with col1:
        date_range = st.selectbox(
            "时间范围",
            ["近1个月", "近3个月", "近6个月", "近1年", "近3年"],
            index=2
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
    
    # 获取数据
    data_dict = data_loader.get_multiple_stocks_data(symbols, start_date_str, end_date_str)
    
    if not data_dict:
        st.warning("未找到数据")
        return
    
    # 对比图表
    st.subheader("价格走势对比（归一化）")
    fig = create_comparison_chart(data_dict, "股票价格对比")
    st.plotly_chart(fig, use_container_width=True)
    
    # 统计对比表
    st.subheader("统计数据对比")
    
    stats_data = []
    for symbol, df in data_dict.items():
        if not df.empty:
            stock_info = data_loader.get_stock_info(symbol)
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
    st.dataframe(stats_df, use_container_width=True, hide_index=True)


def show_indicators_page():
    """显示技术指标分析页面"""
    st.header("技术指标分析")
    
    # 股票选择
    stocks_df = data_loader.get_all_stocks().head(100)
    
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
    
    # 获取数据
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    df = data_loader.get_stock_daily_data(symbol, start_date, end_date)
    
    if df.empty:
        st.warning(f"股票 {symbol} 暂无数据")
        return
    
    # 计算指标
    df = calculate_all_indicators(df)
    
    # 显示不同指标
    tab1, tab2, tab3, tab4 = st.tabs(["移动平均线", "MACD", "RSI", "KDJ"])
    
    with tab1:
        st.subheader("移动平均线 (MA)")
        st.write("移动平均线是最常用的技术指标，用于判断趋势方向。")
        fig = create_candlestick_chart(df, f"{symbol} K线与MA", show_ma=True)
        st.plotly_chart(fig, use_container_width=True)
        
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
        st.plotly_chart(fig, use_container_width=True)
        
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
        st.plotly_chart(fig, use_container_width=True)
        
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
        st.plotly_chart(fig, use_container_width=True)
        
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
    """显示统计分析页面"""
    st.header("统计分析")
    
    # 股票选择
    stocks_df = data_loader.get_all_stocks().head(100)
    
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
    
    # 获取统计数据
    stats = data_loader.get_stock_statistics(symbol, period)
    
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
    
    # 获取详细数据绘制分布图
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=period)).strftime('%Y-%m-%d')
    df = data_loader.get_stock_daily_data(symbol, start_date, end_date)
    
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
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
