"""
AI Agent模拟炒股页面
提供实时运行、配置和监控功能
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualization.agent_config_manager import AgentConfigManager
from visualization.agent_runner import AgentRunner
from config import DATABASE_PATH


def show_agent_simulator_page():
    """显示AI Agent模拟炒股页面"""
    st.header("💻 AI Agent模拟炒股")
    
    st.info("💡 配置并运行AI Agent进行股票交易模拟，实时观察决策过程和交易结果。")
    
    # 初始化session state
    if 'agent_runner' not in st.session_state:
        st.session_state.agent_runner = None
    if 'agent_initialized' not in st.session_state:
        st.session_state.agent_initialized = False
    
    # 配置管理器
    config_manager = AgentConfigManager()
    
    # 显示配置部分
    with st.expander("⚙️ 配置设置", expanded=not st.session_state.agent_initialized):
        show_configuration_section(config_manager)
    
    st.divider()
    
    # 控制面板
    show_control_panel()
    
    st.divider()
    
    # 实时显示部分
    if st.session_state.agent_initialized and st.session_state.agent_runner:
        show_realtime_display()


def show_configuration_section(config_manager: AgentConfigManager):
    """显示配置部分"""
    st.subheader("配置设置")
    
    # 加载配置
    config = config_manager.load_config()
    
    # 使用tabs组织配置
    tab1, tab2, tab3, tab4 = st.tabs(["🔌 API配置", "🧠 模型参数", "📝 系统提示词", "📊 交易设置"])
    
    # Tab 1: API配置
    with tab1:
        st.markdown("### API配置")
        api_base = st.text_input(
            "API Base URL",
            value=config['api_base'],
            help="API服务地址"
        )
        
        api_key = st.text_input(
            "API Key",
            value=config['api_key'],
            type="password",
            help="API密钥"
        )
        
        model = st.text_input(
            "模型名称",
            value=config['model'],
            help="使用的模型名称，如：qwen3-max, free:Qwen3-30B-A3B"
        )
        
        api_call_interval = st.number_input(
            "API调用间隔（秒）",
            min_value=0.0,
            max_value=10.0,
            value=float(config['api_call_interval']),
            step=0.5,
            help="两次API调用之间的最小间隔时间"
        )
    
    # Tab 2: 模型参数
    with tab2:
        st.markdown("### 模型参数")
        temperature = st.slider(
            "Temperature (温度)",
            min_value=0.0,
            max_value=2.0,
            value=float(config['temperature']),
            step=0.1,
            help="控制输出的随机性，值越高越随机"
        )
        
        max_tokens = st.number_input(
            "Max Tokens (最大输出长度)",
            min_value=500,
            max_value=4000,
            value=int(config['max_tokens']),
            step=100,
            help="每次生成的最大token数"
        )
        
        history_window_days = st.number_input(
            "历史数据窗口（天）",
            min_value=30,
            max_value=250,
            value=int(config['history_window_days']),
            step=10,
            help="Agent可以查看的历史数据天数"
        )
    
    # Tab 3: 系统提示词
    with tab3:
        st.markdown("### 系统提示词")
        system_prompt = st.text_area(
            "自定义系统提示词",
            value=config['system_prompt'],
            height=300,
            help="定义Agent的角色、目标和交易策略"
        )
        
        if st.button("🔄 恢复默认提示词"):
            system_prompt = config_manager._get_default_prompt()
            st.rerun()
    
    # Tab 4: 交易设置
    with tab4:
        st.markdown("### 交易设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            initial_capital = st.number_input(
                "初始资金（元）",
                min_value=100000,
                max_value=100000000,
                value=int(config['initial_capital']),
                step=100000,
                help="模拟交易的初始资金"
            )
        
        with col2:
            # 获取可用股票
            all_stocks = config_manager.get_available_stock_pool()
            
            stock_pool = st.multiselect(
                "股票池",
                options=all_stocks,
                default=config['stock_pool'],
                help="从数据库中选择可交易的股票"
            )
        
        st.markdown("### 模拟时间期间")
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "开始日期",
                value=datetime.strptime(config['start_date'], '%Y-%m-%d'),
                min_value=datetime(2015, 1, 1),
                max_value=datetime.now()
            )
        
        with col2:
            end_date = st.date_input(
                "结束日期",
                value=datetime.strptime(config['end_date'], '%Y-%m-%d'),
                min_value=datetime(2015, 1, 1),
                max_value=datetime.now()
            )
        
        if start_date >= end_date:
            st.error("❌ 结束日期必须晚于开始日期")
    
    # 保存按钮
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 保存配置", type="primary", use_container_width=True):
            # 收集所有配置
            new_config = {
                'api_base': api_base,
                'api_key': api_key,
                'model': model,
                'api_call_interval': api_call_interval,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'system_prompt': system_prompt,
                'initial_capital': initial_capital,
                'stock_pool': stock_pool,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'history_window_days': history_window_days
            }
            
            # 保存到文件
            success, error_msg = config_manager.save_config(new_config)
            if success:
                st.success("✅ 配置已保存到 Agents_Experience/user_setting.ini")
            else:
                st.error(f"❌ 保存配置失败: {error_msg}")
    
    with col2:
        if st.button("🔄 加载配置", use_container_width=True):
            st.rerun()


def show_control_panel():
    """显示控制面板"""
    st.subheader("🎮 运行控制")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🚀 初始化Agent", type="primary", use_container_width=True, 
                    disabled=st.session_state.agent_initialized):
            # 加载配置
            config_manager = AgentConfigManager()
            config = config_manager.load_config()
            
            # 验证配置
            if not config['api_key']:
                st.error("❌ 请先配置API Key")
                return
            
            if not config['stock_pool']:
                st.error("❌ 请至少选择一只股票")
                return
            
            # 创建runner
            with st.spinner("正在初始化Agent..."):
                runner = AgentRunner(config, DATABASE_PATH)
                if runner.initialize():
                    st.session_state.agent_runner = runner
                    st.session_state.agent_initialized = True
                    st.success("✅ Agent初始化成功！")
                    st.rerun()
                else:
                    st.error("❌ Agent初始化失败，请检查配置和数据库")
    
    with col2:
        if st.button("▶️ 开始运行", use_container_width=True,
                    disabled=not st.session_state.agent_initialized or 
                    (st.session_state.agent_runner and st.session_state.agent_runner.is_running)):
            if st.session_state.agent_runner:
                st.session_state.agent_runner.start()
                st.rerun()
    
    with col3:
        if st.button("⏸️ 暂停", use_container_width=True,
                    disabled=not st.session_state.agent_initialized or 
                    not (st.session_state.agent_runner and st.session_state.agent_runner.is_running and 
                         not st.session_state.agent_runner.is_paused)):
            if st.session_state.agent_runner:
                st.session_state.agent_runner.pause()
                st.rerun()
    
    with col4:
        if st.button("▶️ 继续", use_container_width=True,
                    disabled=not st.session_state.agent_initialized or 
                    not (st.session_state.agent_runner and st.session_state.agent_runner.is_paused)):
            if st.session_state.agent_runner:
                st.session_state.agent_runner.resume()
                st.rerun()
    
    with col5:
        if st.button("⏹️ 终止", use_container_width=True,
                    disabled=not st.session_state.agent_initialized):
            if st.session_state.agent_runner:
                st.session_state.agent_runner.stop()
                st.session_state.agent_runner = None
                st.session_state.agent_initialized = False
                st.rerun()


def show_realtime_display():
    """显示实时状态"""
    runner = st.session_state.agent_runner
    
    if not runner:
        return
    
    # 获取当前状态
    state = runner.get_current_state()
    
    # 状态概览
    st.subheader("📊 实时状态")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_text = "🟢 运行中" if state['is_running'] and not state['is_paused'] else \
                     "🟡 已暂停" if state['is_paused'] else "⚪ 已停止"
        st.metric("状态", status_text)
    
    with col2:
        st.metric("当前日期", state['current_date'] or "未开始")
    
    with col3:
        st.metric("进度", f"{state['current_day']}/{state['total_days']}")
    
    with col4:
        st.metric("完成度", f"{state['progress']:.1f}%")
    
    # 进度条
    st.progress(state['progress'] / 100)
    
    st.divider()
    
    # 使用tabs组织实时信息
    tab1, tab2, tab3, tab4 = st.tabs(["💼 账户状态", "📈 资产曲线", "🔄 交易记录", "📝 运行日志"])
    
    # Tab 1: 账户状态
    with tab1:
        portfolio = state['portfolio']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("现金", f"¥{portfolio['cash']:,.0f}")
        
        with col2:
            st.metric("市值", f"¥{portfolio['market_value']:,.0f}")
        
        with col3:
            st.metric("总资产", f"¥{portfolio['total_asset']:,.0f}")
        
        with col4:
            profit_rate = portfolio['profit_rate']
            st.metric(
                "收益率", 
                f"{profit_rate:.2f}%",
                delta=f"{profit_rate:.2f}%",
                delta_color="normal" if profit_rate >= 0 else "inverse"
            )
        
        # 持仓信息
        if runner.portfolio and runner.portfolio.positions:
            st.subheader("持仓详情")
            positions_data = []
            for symbol, pos in runner.portfolio.positions.items():
                positions_data.append({
                    '股票代码': symbol,
                    '股票名称': pos.name,
                    '持仓数量': pos.quantity,
                    '成本价': f"¥{pos.avg_cost:.2f}",
                    '现价': f"¥{pos.current_price:.2f}",
                    '市值': f"¥{pos.market_value:,.0f}",
                    '盈亏': f"¥{pos.profit:,.0f}",
                    '收益率': f"{pos.profit_rate:.2f}%"
                })
            
            if positions_data:
                st.dataframe(pd.DataFrame(positions_data), use_container_width=True, hide_index=True)
        else:
            st.info("当前无持仓")
    
    # Tab 2: 资产曲线
    with tab2:
        if state['daily_snapshots']:
            df = pd.DataFrame(state['daily_snapshots'])
            
            fig = go.Figure()
            
            # 总资产曲线
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['total_asset'],
                mode='lines',
                name='总资产',
                line=dict(color='blue', width=2)
            ))
            
            # 现金曲线
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['cash'],
                mode='lines',
                name='现金',
                line=dict(color='green', width=1, dash='dash')
            ))
            
            # 市值曲线
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['market_value'],
                mode='lines',
                name='市值',
                line=dict(color='orange', width=1, dash='dash')
            ))
            
            fig.update_layout(
                title='资产变化曲线',
                xaxis_title='日期',
                yaxis_title='金额（元）',
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 收益率曲线
            fig2 = go.Figure()
            
            fig2.add_trace(go.Scatter(
                x=df['date'],
                y=df['profit_rate'],
                mode='lines',
                name='收益率',
                line=dict(color='red', width=2),
                fill='tozeroy'
            ))
            
            fig2.update_layout(
                title='收益率变化',
                xaxis_title='日期',
                yaxis_title='收益率（%）',
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("暂无数据，请等待Agent开始运行")
    
    # Tab 3: 交易记录
    with tab3:
        if state['trade_log']:
            trades_df = pd.DataFrame(state['trade_log'])
            
            # 格式化显示
            display_df = trades_df.copy()
            display_df['type'] = display_df['type'].map({'buy': '买入', 'sell': '卖出'})
            display_df = display_df.rename(columns={
                'date': '日期',
                'type': '类型',
                'symbol': '股票代码',
                'quantity': '数量',
                'price': '价格',
                'total': '金额'
            })
            
            # 格式化数值
            display_df['价格'] = display_df['价格'].apply(lambda x: f"¥{x:.2f}")
            display_df['金额'] = display_df['金额'].apply(lambda x: f"¥{x:,.2f}")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # 统计
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总交易次数", len(trades_df))
            with col2:
                buy_count = len(trades_df[trades_df['type'] == '买入'])
                st.metric("买入次数", buy_count)
            with col3:
                sell_count = len(trades_df[trades_df['type'] == '卖出'])
                st.metric("卖出次数", sell_count)
        else:
            st.info("暂无交易记录")
    
    # Tab 4: 运行日志
    with tab4:
        if state['log_messages']:
            st.markdown("### 最近日志")
            
            # 日志级别过滤
            log_level_filter = st.multiselect(
                "过滤日志级别",
                options=['info', 'success', 'warning', 'error'],
                default=['info', 'success', 'warning', 'error']
            )
            
            # 显示日志
            log_container = st.container()
            with log_container:
                for log in reversed(state['log_messages'][-100:]):
                    if log['level'] in log_level_filter:
                        icon = {
                            'info': 'ℹ️',
                            'success': '✅',
                            'warning': '⚠️',
                            'error': '❌'
                        }.get(log['level'], 'ℹ️')
                        
                        st.text(f"{log['timestamp']} {icon} {log['message']}")
        else:
            st.info("暂无日志")
    
    # 自动刷新
    if state['is_running'] and not state['is_paused']:
        time.sleep(1)
        st.rerun()
