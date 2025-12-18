import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from pathlib import Path

# 设置页面配置
st.set_page_config(
    page_title="数字化转型指数趋势分析工具",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 应用标题和描述
st.title("📈 数字化转型指数趋势分析工具")
st.markdown("通过股票代码查询企业数字化转型指数，并生成多维度趋势图表")

# 文件路径配置
FILE_PATH = "c:\\Users\\86182\\Desktop\\1999-2023年报数\\两版合并后的年报数据_完整版.xlsx"

# 格式化股票代码为6位的辅助函数
def format_stock_code(code):
    """
    将股票代码格式化为6位数字格式
    """
    # 处理空值
    if pd.isna(code) or code is None:
        return ""
    
    # 转换为字符串并去除空格
    code_str = str(code).strip()
    
    # 去除可能的小数点和后面的0
    if '.' in code_str:
        code_str = code_str.split('.')[0]
    
    # 去除非数字字符
    code_str = ''.join(filter(str.isdigit, code_str))
    
    # 格式化为6位数字，不足前面补0
    return code_str.zfill(6)

# 缓存数据加载函数
@st.cache_data(ttl=3600)
def load_data(file_path):
    """
    加载Excel数据文件
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 数据清洗
        # 去除列名中的空格
        df.columns = df.columns.str.strip()
        
        # 确保股票代码列为6位字符串格式
        if '股票代码' in df.columns:
            df['股票代码'] = df['股票代码'].apply(format_stock_code)
        
        # 确保年份列为整数类型
        if '年份' in df.columns:
            df['年份'] = pd.to_numeric(df['年份'], errors='coerce').fillna(0).astype(int)
        
        # 处理企业名称空值
        if '企业名称' in df.columns:
            df['企业名称'] = df['企业名称'].fillna('未知企业')
        
        st.success(f"✅ 数据加载成功，共加载 {len(df)} 条记录")
        return df
    except Exception as e:
        st.error(f"❌ 数据加载失败: {str(e)}")
        return pd.DataFrame()

# 初始化会话状态
if 'selected_stock' not in st.session_state:
    st.session_state['selected_stock'] = ""
if 'selected_company' not in st.session_state:
    st.session_state['selected_company'] = ""
if 'comparison_stocks' not in st.session_state:
    st.session_state['comparison_stocks'] = []

# 加载数据
df = load_data(FILE_PATH)

# 侧边栏配置
with st.sidebar:
    st.header("🔍 查询设置")
    
    # 主股票代码输入
    stock_code = st.text_input(
        "请输入主查询股票代码",
        placeholder="例如: 000001",
        help="输入6位股票代码进行查询",
        value=st.session_state['selected_stock']
    )
    
    # 获取所有股票代码列表（如果数据已加载）
    if not df.empty and '股票代码' in df.columns:
        all_stocks = sorted(df['股票代码'].unique())
        # 过滤掉空字符串
        all_stocks = [stock for stock in all_stocks if stock]
        
        # 创建股票代码和企业名称的映射
        stock_company_map = {}
        for _, row in df.iterrows():
            if pd.notna(row['股票代码']) and pd.notna(row['企业名称']):
                stock_company_map[row['股票代码']] = row['企业名称']
        
        # 创建带企业名称的股票代码选项
        stock_options = [f"{stock} - {stock_company_map.get(stock, '未知企业')}" for stock in all_stocks]
        
        selected_option = st.selectbox(
            "或者从列表中选择",
            options=["请选择股票代码"] + stock_options,
            index=0
        )
        
        # 如果选择了股票代码，自动填充到输入框
        if selected_option != "请选择股票代码":
            # 提取股票代码部分
            stock_code = selected_option.split(' - ')[0]
            st.session_state['selected_stock'] = stock_code
    
    # 年份筛选器
    if not df.empty and '年份' in df.columns:
        min_year = int(df['年份'].min())
        max_year = int(df['年份'].max())
        year_range = st.slider(
            "选择年份范围",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year),
            step=1
        )
    else:
        year_range = (1999, 2023)
    
    # 趋势图类型选择
    st.subheader("📊 趋势图设置")
    chart_type = st.selectbox(
        "选择趋势图类型",
        options=[
            "数字化转型指数趋势",
            "技术维度 vs 应用维度对比",
            "多技术关键词趋势",
            "多维指标雷达图"
        ],
        index=0
    )
    
    # 企业对比分析选项
    enable_comparison = st.checkbox("启用企业对比分析", value=False)
    comparison_stocks = []
    
    if enable_comparison and not df.empty:
        st.subheader("📊 选择对比企业")
        # 提供最多3个对比企业选择
        for i in range(3):
            comparison_stock = st.selectbox(
                f"对比企业 {i+1}",
                options=["请选择"] + stock_options,
                index=0,
                key=f"compare_{i}"
            )
            if comparison_stock != "请选择":
                comp_stock_code = comparison_stock.split(' - ')[0]
                if comp_stock_code != stock_code:  # 避免与主查询相同
                    comparison_stocks.append(comp_stock_code)
    
    # 查询按钮
    search_button = st.button("🔍 生成趋势图", type="primary")
    
    # 数据统计信息
    if not df.empty:
        st.header("📊 数据统计")
        st.info(f"📈 数据覆盖年份: {int(df['年份'].min())} - {int(df['年份'].max())}")
        st.info(f"🏢 企业总数: {df['企业名称'].nunique()}")
        
        # 显示热门股票
        top_stocks_df = df.groupby(['股票代码', '企业名称']).size().reset_index(name='记录数')
        top_stocks_df = top_stocks_df.sort_values('记录数', ascending=False).head(5)
        st.markdown("### 🔥 热门查询")
        for _, row in top_stocks_df.iterrows():
            if st.button(f"{row['股票代码']} - {row['企业名称']}", key=f"quick_{row['股票代码']}", help=f"快速查询该企业"):
                st.session_state['selected_stock'] = row['股票代码']
                st.experimental_rerun()

# 主内容区域
if search_button and stock_code:
    # 验证股票代码格式
    stock_code = stock_code.strip()
    if not all(c.isdigit() or c == '.' for c in stock_code):
        st.error("❌ 请输入有效的数字股票代码")
    else:
        # 格式化为6位股票代码
        formatted_stock_code = format_stock_code(stock_code)
        st.info(f"🔍 正在查询股票代码: {formatted_stock_code}")
        
        # 筛选数据
        main_df = df[df['股票代码'] == formatted_stock_code]
        
        if main_df.empty:
            st.error(f"❌ 未找到股票代码 {formatted_stock_code} 的数据")
        else:
            # 筛选年份范围
            main_df = main_df[(main_df['年份'] >= year_range[0]) & (main_df['年份'] <= year_range[1])]
            
            if main_df.empty:
                st.warning(f"⚠️ 在 {year_range[0]}-{year_range[1]} 年份范围内未找到数据")
            else:
                # 显示企业基本信息
                company_name = main_df['企业名称'].iloc[0]
                st.success(f"✅ 正在分析: {company_name} (股票代码: {formatted_stock_code})")
                st.session_state['selected_company'] = company_name
                
                # 按年份排序数据
                main_df = main_df.sort_values('年份')
                
                # 根据选择的图表类型生成不同的趋势图
                if chart_type == "数字化转型指数趋势":
                    # 检查是否有数字化转型指数列
                    if '数字化转型指数' in main_df.columns:
                        # 创建数字化转型指数趋势图
                        fig = go.Figure()
                        
                        # 添加主企业数据
                        fig.add_trace(go.Scatter(
                            x=main_df['年份'],
                            y=main_df['数字化转型指数'],
                            mode='lines+markers',
                            name=company_name,
                            line=dict(color='#1f77b4', width=4),
                            marker=dict(size=10, symbol='circle'),
                            hovertemplate='<b>年份</b>: %{x}<br><b>数字化转型指数</b>: %{y:.2f}<extra></extra>'
                        ))
                        
                        # 添加对比企业数据
                        for i, comp_stock in enumerate(comparison_stocks):
                            comp_df = df[(df['股票代码'] == comp_stock) & 
                                        (df['年份'] >= year_range[0]) & 
                                        (df['年份'] <= year_range[1])]
                            if not comp_df.empty and '数字化转型指数' in comp_df.columns:
                                comp_df = comp_df.sort_values('年份')
                                comp_name = comp_df['企业名称'].iloc[0]
                                # 使用不同的颜色
                                colors = ['#ff7f0e', '#2ca02c', '#d62728']
                                color_index = i % len(colors)
                                
                                fig.add_trace(go.Scatter(
                                    x=comp_df['年份'],
                                    y=comp_df['数字化转型指数'],
                                    mode='lines+markers',
                                    name=comp_name,
                                    line=dict(color=colors[color_index], width=3, dash='dash'),
                                    marker=dict(size=8),
                                    hovertemplate='<b>年份</b>: %{x}<br><b>数字化转型指数</b>: %{y:.2f}<extra></extra>'
                                ))
                        
                        # 更新图表布局
                        fig.update_layout(
                            title=f"<b>{company_name} 数字化转型指数趋势</b><br>" \
                                  f"<span style='font-size:0.9em;color:gray;'>{year_range[0]}-{year_range[1]}</span>",
                            plot_bgcolor="white",
                            font=dict(family="SimHei, Arial, sans-serif", size=14),
                            margin=dict(l=60, r=20, t=80, b=60),
                            xaxis=dict(
                                gridcolor='#e0e0e0',
                                dtick=1,
                                title="年份",
                                titlefont=dict(size=14, family="SimHei"),
                                tickfont=dict(size=12)
                            ),
                            yaxis=dict(
                                gridcolor='#e0e0e0',
                                title="数字化转型指数",
                                titlefont=dict(size=14, family="SimHei"),
                                tickfont=dict(size=12)
                            ),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="center",
                                x=0.5,
                                font=dict(family="SimHei", size=12)
                            ),
                            hovermode="x unified"
                        )
                        
                        # 显示图表
                        st.plotly_chart(fig, use_container_width=True, height=600)
                        
                        # 添加统计信息
                        if not main_df.empty and '数字化转型指数' in main_df.columns:
                            st.subheader("📊 趋势分析统计")
                            col1, col2, col3, col4 = st.columns(4)
                            
                            avg_index = main_df['数字化转型指数'].mean()
                            max_index = main_df['数字化转型指数'].max()
                            min_index = main_df['数字化转型指数'].min()
                            
                            # 计算增长率
                            if len(main_df) > 1:
                                first_val = main_df['数字化转型指数'].iloc[0]
                                last_val = main_df['数字化转型指数'].iloc[-1]
                                growth_rate = ((last_val - first_val) / max(first_val, 1)) * 100
                            else:
                                growth_rate = 0
                            
                            with col1:
                                st.metric("📊 平均指数", f"{avg_index:.2f}")
                            with col2:
                                st.metric("🏆 最高指数", f"{max_index:.2f}")
                            with col3:
                                st.metric("📉 最低指数", f"{min_index:.2f}")
                            with col4:
                                st.metric("📈 增长率", f"{growth_rate:.2f}%", 
                                         delta=f"{growth_rate:.2f}%" if growth_rate != 0 else "N/A")
                    else:
                        st.warning("⚠️ 数据集不包含数字化转型指数列")
                
                elif chart_type == "技术维度 vs 应用维度对比":
                    # 检查必要的维度列
                    if '技术维度' in main_df.columns and '应用维度' in main_df.columns:
                        # 创建维度对比图
                        fig = go.Figure()
                        
                        # 添加技术维度
                        fig.add_trace(go.Scatter(
                            x=main_df['年份'],
                            y=main_df['技术维度'],
                            mode='lines+markers',
                            name='技术维度',
                            line=dict(color='#1f77b4', width=4),
                            marker=dict(size=10, symbol='circle'),
                            hovertemplate='<b>年份</b>: %{x}<br><b>技术维度</b>: %{y:.2f}<extra></extra>'
                        ))
                        
                        # 添加应用维度
                        fig.add_trace(go.Scatter(
                            x=main_df['年份'],
                            y=main_df['应用维度'],
                            mode='lines+markers',
                            name='应用维度',
                            line=dict(color='#ff7f0e', width=4),
                            marker=dict(size=10, symbol='diamond'),
                            hovertemplate='<b>年份</b>: %{x}<br><b>应用维度</b>: %{y:.2f}<extra></extra>'
                        ))
                        
                        # 更新布局
                        fig.update_layout(
                            title=f"<b>{company_name} 技术维度与应用维度对比</b><br>" \
                                  f"<span style='font-size:0.9em;color:gray;'>{year_range[0]}-{year_range[1]}</span>",
                            plot_bgcolor="white",
                            font=dict(family="SimHei, Arial, sans-serif", size=14),
                            margin=dict(l=60, r=20, t=80, b=60),
                            xaxis=dict(
                                gridcolor='#e0e0e0',
                                dtick=1,
                                title="年份",
                                titlefont=dict(size=14, family="SimHei"),
                                tickfont=dict(size=12)
                            ),
                            yaxis=dict(
                                gridcolor='#e0e0e0',
                                title="指数值",
                                titlefont=dict(size=14, family="SimHei"),
                                tickfont=dict(size=12)
                            ),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="center",
                                x=0.5,
                                font=dict(family="SimHei", size=12)
                            ),
                            hovermode="x unified"
                        )
                        
                        # 显示图表
                        st.plotly_chart(fig, use_container_width=True, height=600)
                        
                        # 添加维度分析
                        st.subheader("📊 维度平衡分析")
                        tech_avg = main_df['技术维度'].mean()
                        app_avg = main_df['应用维度'].mean()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("💻 平均技术维度", f"{tech_avg:.2f}")
                        with col2:
                            st.metric("🚀 平均应用维度", f"{app_avg:.2f}")
                        
                        # 维度平衡建议
                        st.markdown("### 💡 维度平衡洞察")
                        if tech_avg > app_avg * 1.5:
                            st.info("🔍 该企业技术投入较高，但应用转化相对不足，建议加强技术成果转化")
                        elif app_avg > tech_avg * 1.5:
                            st.info("🔍 该企业应用需求旺盛，但技术支撑相对薄弱，建议加强技术研发投入")
                        else:
                            st.success("✅ 该企业技术与应用维度较为平衡，数字化发展较为协调")
                    else:
                        st.warning("⚠️ 数据集不包含完整的维度信息")
                
                elif chart_type == "多技术关键词趋势":
                    # 定义技术关键词列
                    tech_keywords = {
                        '人工智能词频数': '人工智能',
                        '大数据词频数': '大数据',
                        '云计算词频数': '云计算',
                        '区块链词频数': '区块链'
                    }
                    
                    # 检查数据中是否包含这些关键词列
                    available_keywords = {k: v for k, v in tech_keywords.items() if k in main_df.columns}
                    
                    if available_keywords:
                        # 创建多技术关键词趋势图
                        fig = go.Figure()
                        
                        # 定义颜色映射
                        keyword_colors = {
                            '人工智能': '#1f77b4',
                            '大数据': '#ff7f0e',
                            '云计算': '#2ca02c',
                            '区块链': '#d62728'
                        }
                        
                        # 添加每个关键词的趋势线
                        for col_name, display_name in available_keywords.items():
                            fig.add_trace(go.Scatter(
                                x=main_df['年份'],
                                y=main_df[col_name],
                                mode='lines+markers',
                                name=display_name,
                                line=dict(color=keyword_colors.get(display_name, '#9467bd'), width=3),
                                marker=dict(size=8),
                                hovertemplate=f'<b>年份</b>: %{{x}}<br><b>{display_name}词频</b>: %{{y:.0f}}<extra></extra>'
                            ))
                        
                        # 更新布局
                        fig.update_layout(
                            title=f"<b>{company_name} 技术关键词使用趋势</b><br>" \
                                  f"<span style='font-size:0.9em;color:gray;'>{year_range[0]}-{year_range[1]}</span>",
                            plot_bgcolor="white",
                            font=dict(family="SimHei, Arial, sans-serif", size=14),
                            margin=dict(l=60, r=20, t=80, b=60),
                            xaxis=dict(
                                gridcolor='#e0e0e0',
                                dtick=1,
                                title="年份",
                                titlefont=dict(size=14, family="SimHei"),
                                tickfont=dict(size=12)
                            ),
                            yaxis=dict(
                                gridcolor='#e0e0e0',
                                title="词频数量",
                                titlefont=dict(size=14, family="SimHei"),
                                tickfont=dict(size=12)
                            ),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="center",
                                x=0.5,
                                font=dict(family="SimHei", size=12)
                            ),
                            hovermode="x unified"
                        )
                        
                        # 显示图表
                        st.plotly_chart(fig, use_container_width=True, height=600)
                        
                        # 添加关键词分析
                        st.subheader("📊 技术关键词分析")
                        keyword_summary = []
                        
                        for col_name, display_name in available_keywords.items():
                            total_count = main_df[col_name].sum()
                            max_count = main_df[col_name].max()
                            latest_count = main_df[col_name].iloc[-1] if not main_df.empty else 0
                            
                            # 计算增长率
                            if len(main_df) > 1:
                                first_count = main_df[col_name].iloc[0]
                                keyword_growth = ((latest_count - first_count) / max(first_count, 1)) * 100
                            else:
                                keyword_growth = 0
                            
                            keyword_summary.append({
                                '关键词': display_name,
                                '总频次': total_count,
                                '最高频次': max_count,
                                '最新频次': latest_count,
                                '增长率': f"{keyword_growth:.2f}%"
                            })
                        
                        # 显示关键词汇总表格
                        summary_df = pd.DataFrame(keyword_summary)
                        st.dataframe(summary_df, use_container_width=True)
                    else:
                        st.warning("⚠️ 数据集中未找到技术关键词列")
                
                elif chart_type == "多维指标雷达图":
                    # 检查必要的指标列
                    required_columns = ['技术维度', '应用维度']
                    if all(col in main_df.columns for col in required_columns):
                        # 计算最新年份的多维指标
                        latest_year = main_df['年份'].max()
                        latest_data = main_df[main_df['年份'] == latest_year].iloc[0]
                        
                        # 准备雷达图数据
                        categories = ['技术维度', '应用维度']
                        values = [latest_data['技术维度'], latest_data['应用维度']]
                        
                        # 如果有数字化转型指数，也加入雷达图
                        if '数字化转型指数' in main_df.columns:
                            # 对数字化转型指数进行归一化，使其在0-100范围
                            max_index = main_df['数字化转型指数'].max()
                            normalized_index = min(100, (latest_data['数字化转型指数'] / max_index) * 100)
                            categories.append('数字化转型指数(归一化)')
                            values.append(normalized_index)
                        
                        # 创建雷达图
                        fig = go.Figure()
                        
                        # 添加主企业数据
                        fig.add_trace(go.Scatterpolar(
                            r=values,
                            theta=categories,
                            fill='toself',
                            name=company_name,
                            line=dict(color='#1f77b4', width=3),
                            fillcolor='rgba(31, 119, 180, 0.2)'
                        ))
                        
                        # 添加对比企业数据
                        for i, comp_stock in enumerate(comparison_stocks):
                            comp_df = df[(df['股票代码'] == comp_stock) & (df['年份'] == latest_year)]
                            if not comp_df.empty:
                                comp_data = comp_df.iloc[0]
                                comp_name = comp_data['企业名称']
                                
                                # 准备对比企业数据
                                comp_values = []
                                if '技术维度' in comp_data:
                                    comp_values.append(comp_data['技术维度'])
                                if '应用维度' in comp_data:
                                    comp_values.append(comp_data['应用维度'])
                                if '数字化转型指数' in comp_data and '数字化转型指数' in main_df.columns:
                                    comp_normalized_index = min(100, (comp_data['数字化转型指数'] / max_index) * 100)
                                    comp_values.append(comp_normalized_index)
                                
                                # 确保对比数据与主企业数据长度一致
                                if len(comp_values) == len(values):
                                    # 使用不同的颜色
                                    colors = ['#ff7f0e', '#2ca02c', '#d62728']
                                    color_index = i % len(colors)
                                    
                                    fig.add_trace(go.Scatterpolar(
                                        r=comp_values,
                                        theta=categories,
                                        fill='toself',
                                        name=comp_name,
                                        line=dict(color=colors[color_index], width=2, dash='dash'),
                                        fillcolor=f'rgba{tuple(int(colors[color_index].lstrip("#").slice(i,i+2), 16) for i in (0,2,4)) + (0.1,)}'
                                    ))
                        
                        # 更新布局
                        fig.update_layout(
                            title=f"<b>{company_name} 多维指标雷达图</b><br>" \
                                  f"<span style='font-size:0.9em;color:gray;'>年份: {latest_year}</span>",
                            font=dict(family="SimHei, Arial, sans-serif", size=14),
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    gridcolor='#e0e0e0',
                                    titlefont=dict(family="SimHei")
                                ),
                                angularaxis=dict(
                                    tickfont=dict(family="SimHei", size=12)
                                )
                            ),
                            legend=dict(
                                font=dict(family="SimHei", size=12)
                            )
                        )
                        
                        # 显示图表
                        st.plotly_chart(fig, use_container_width=True, height=600)
                        
                        # 添加雷达图分析
                        st.subheader("📊 多维指标分析")
                        st.markdown(f"**分析年份**: {latest_year}")
                        
                        # 显示各维度具体数值
                        for i, (cat, val) in enumerate(zip(categories, values)):
                            st.metric(cat, f"{val:.2f}")
                    else:
                        st.warning("⚠️ 数据集不包含生成雷达图所需的完整指标")
                
                # 数据下载功能
                st.subheader("💾 数据下载")
                csv_data = main_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label=f"下载 {company_name} 趋势数据",
                    data=csv_data,
                    file_name=f"{formatted_stock_code}_{company_name}_趋势数据_{year_range[0]}-{year_range[1]}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

# 如果没有搜索，显示使用说明和数据预览
if not search_button:
    st.info("💡 使用说明")
    st.markdown("""
    1. 在左侧输入框中输入**6位股票代码**，或从下拉列表中选择企业
    2. 选择要查询的年份范围
    3. 选择您需要的趋势图类型（数字化转型指数、技术维度vs应用维度、多技术关键词、多维指标雷达图）
    4. 可选：启用企业对比分析，选择最多3家企业进行对比
    5. 点击"生成趋势图"按钮查看分析结果
    """)
    
    # 显示数据样例
    if not df.empty:
        st.subheader("📊 数据样例")
        # 显示前5行数据作为样例，只显示关键列
        sample_df = df.head(5).copy()
        # 如果列数太多，只显示关键列
        key_columns = ['股票代码', '企业名称', '年份']
        # 查找数字化转型相关列
        for col in df.columns:
            if any(keyword in col for keyword in ['数字化转型', '技术维度', '应用维度']):
                key_columns.append(col)
        # 确保只显示存在的列
        key_columns = [col for col in key_columns if col in sample_df.columns]
        # 如果关键列不足，显示所有列
        if len(key_columns) < 5:
            key_columns = sample_df.columns.tolist()[:10]  # 最多显示10列
        st.dataframe(sample_df[key_columns], use_container_width=True)

# 页脚
st.markdown("---")
st.markdown("© 2024 数字化转型指数趋势分析工具 | 基于Streamlit和Plotly构建")