import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 设置页面配置
st.set_page_config(
    page_title="数字化转型指数查询工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 添加标题和描述
st.title("📊 数字化转型指数查询工具")
st.markdown("基于股票代码查询企业的数字化转型指数，支持历史趋势分析")

# 定义文件路径
file_path = "两版合并后的年报数据_完整版.xlsx"

@st.cache_data
# 加载数据的函数
def load_data():
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        # 转换股票代码为字符串，保留前6位
        df['股票代码'] = df['股票代码'].astype(str).str.zfill(6)
        return df
    else:
        st.error(f"文件不存在: {file_path}")
        return None

# 加载数据
df = load_data()

if df is not None:
    # 侧边栏设置
    st.sidebar.header("查询设置")
    
    # 获取所有股票代码
    stock_codes = sorted(df['股票代码'].unique())
    
    # 股票代码输入
    selected_code = st.sidebar.selectbox(
        "选择股票代码",
        options=stock_codes,
        help="从下拉列表中选择股票代码"
    )
    
    # 股票代码搜索框（如果股票代码很多）
    search_code = st.sidebar.text_input(
        "搜索股票代码",
        placeholder="输入股票代码前几位",
        help="快速搜索特定股票代码"
    )
    
    # 年份范围筛选
    years = sorted(df['年份'].unique())
    min_year, max_year = min(years), max(years)
    
    selected_years = st.sidebar.slider(
        "选择年份范围",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1
    )
    
    # 如果有搜索内容，过滤股票代码
    if search_code:
        filtered_codes = [code for code in stock_codes if search_code in code]
        selected_code = st.sidebar.selectbox(
            "筛选后的股票代码",
            options=filtered_codes,
            help="基于搜索条件过滤后的股票代码列表"
        )
    
    # 根据选择的股票代码和年份范围筛选数据
    filtered_df = df[
        (df['股票代码'] == selected_code) & 
        (df['年份'] >= selected_years[0]) & 
        (df['年份'] <= selected_years[1])
    ].sort_values('年份')
    
    # 显示查询结果
    if not filtered_df.empty:
        # 获取企业名称
        company_name = filtered_df['企业名称'].iloc[0]
        
        # 主内容区
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("股票代码", selected_code)
        
        with col2:
            st.metric("企业名称", company_name)
        
        with col3:
            st.metric("数据年份范围", f"{selected_years[0]}-{selected_years[1]}")
        
        # 显示数据表格
        st.subheader("数字化转型指数数据")
        st.dataframe(
            filtered_df[["年份", "数字化转型指数", "技术维度", "应用维度", "数字技术运用词频数"]],
            hide_index=True,
            use_container_width=True
        )
        
        # 绘制趋势图
        st.subheader("数字化转型指数趋势")
        
        # 指数趋势图
        fig1 = px.line(
            filtered_df,
            x="年份",
            y="数字化转型指数",
            title=f"{company_name}({selected_code}) - 数字化转型指数趋势",
            labels={"年份": "年份", "数字化转型指数": "数字化转型指数"},
            markers=True
        )
        
        # 设置图表样式
        fig1.update_layout(
            xaxis_tickformat='%Y',
            xaxis_title_font=dict(size=14),
            yaxis_title_font=dict(size=14),
            title_font=dict(size=16, family='Arial', color='blue'),
            template='plotly_white'
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        
        # 技术维度和应用维度对比图
        fig2 = px.line(
            filtered_df,
            x="年份",
            y=["技术维度", "应用维度"],
            title=f"{company_name}({selected_code}) - 技术维度 vs 应用维度",
            labels={"年份": "年份", "value": "指数值"},
            markers=True
        )
        
        fig2.update_layout(
            xaxis_tickformat='%Y',
            xaxis_title_font=dict(size=14),
            yaxis_title_font=dict(size=14),
            title_font=dict(size=16, family='Arial', color='green'),
            template='plotly_white',
            legend_title="维度类型"
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # 数字技术运用词频数
        st.subheader("数字技术运用情况")
        
        tech_columns = ["人工智能词频数", "大数据词频数", "云计算词频数", "区块链词频数", "数字技术运用词频数"]
        tech_data = filtered_df[tech_columns + ["年份"]].melt(id_vars=["年份"], var_name="技术类型", value_name="词频数")
        
        fig3 = px.bar(
            tech_data,
            x="年份",
            y="词频数",
            color="技术类型",
            title=f"{company_name}({selected_code}) - 数字技术运用词频数",
            labels={"年份": "年份", "词频数": "词频数"},
            barmode='group'
        )
        
        fig3.update_layout(
            xaxis_tickformat='%Y',
            xaxis_title_font=dict(size=14),
            yaxis_title_font=dict(size=14),
            title_font=dict(size=16, family='Arial', color='purple'),
            template='plotly_white',
            legend_title="技术类型"
        )
        
        st.plotly_chart(fig3, use_container_width=True)
        
        # 显示统计信息
        st.subheader("统计信息")
        
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        
        with stats_col1:
            avg_index = filtered_df['数字化转型指数'].mean()
            max_index = filtered_df['数字化转型指数'].max()
            min_index = filtered_df['数字化转型指数'].min()
            
            st.metric("平均指数", f"{avg_index:.4f}")
            st.metric("最高指数", f"{max_index:.4f}")
            st.metric("最低指数", f"{min_index:.4f}")
        
        with stats_col2:
            avg_tech = filtered_df['技术维度'].mean()
            max_tech = filtered_df['技术维度'].max()
            min_tech = filtered_df['技术维度'].min()
            
            st.metric("平均技术维度", f"{avg_tech:.4f}")
            st.metric("最高技术维度", f"{max_tech:.4f}")
            st.metric("最低技术维度", f"{min_tech:.4f}")
        
        with stats_col3:
            avg_app = filtered_df['应用维度'].mean()
            max_app = filtered_df['应用维度'].max()
            min_app = filtered_df['应用维度'].min()
            
            st.metric("平均应用维度", f"{avg_app:.4f}")
            st.metric("最高应用维度", f"{max_app:.4f}")
            st.metric("最低应用维度", f"{min_app:.4f}")
    else:
        st.warning(f"在选择的年份范围内，没有找到股票代码 {selected_code} 的数据")
    
    # 添加数据概览
    st.subheader("数据概览")
    
    overview_col1, overview_col2 = st.columns(2)
    
    with overview_col1:
        st.metric("总企业数", df['股票代码'].nunique())
        st.metric("总年份数", df['年份'].nunique())
        st.metric("总数据条数", len(df))
    
    with overview_col2:
        # 数字化转型指数分布
        st.markdown("### 数字化转型指数分布")
        fig_dist = px.histogram(
            df,
            x="数字化转型指数",
            nbins=30,
            title="数字化转型指数分布",
            labels={"数字化转型指数": "数字化转型指数", "count": "企业数量"}
        )
        
        fig_dist.update_layout(
            xaxis_title_font=dict(size=14),
            yaxis_title_font=dict(size=14),
            title_font=dict(size=14),
            template='plotly_white'
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)

# 添加页脚
st.markdown("---")
st.markdown("### 使用说明")
st.markdown("1. 在左侧选择或搜索股票代码")
st.markdown("2. 选择年份范围")
st.markdown("3. 查看企业数字化转型指数的历史趋势和详细数据")
st.markdown("4. 分析技术维度、应用维度和数字技术运用情况")

# 运行命令提示
st.markdown("---")
st.markdown("### 运行命令")
st.code("python -m streamlit run digital_transformation_query_app.py")
