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
FILE_PATH = "两版合并后的年报数据_完整版.xlsx"

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
    
    参数:
    file_path: str - Excel文件路径
    
    返回:
    pd.DataFrame - 加载并清洗后的数据
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            st.error(f"❌ 数据文件不存在: {file_path}")
            st.info("请确保数据文件位于应用程序同一目录下，文件名正确")
            return pd.DataFrame()
        
        # 检查文件是否为空
        if os.path.getsize(file_path) == 0:
            st.error(f"❌ 数据文件为空: {file_path}")
            return pd.DataFrame()
        
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 检查数据是否为空
        if df.empty:
            st.warning("⚠️ 数据文件为空或无法读取有效数据")
            return pd.DataFrame()
        
        # 数据清洗和验证
        
        # 去除列名中的空格
        df.columns = df.columns.str.strip()
        
        # 数据基本信息（不显示）
        
        # 确保股票代码列为6位字符串格式
        if '股票代码' in df.columns:
            df['股票代码'] = df['股票代码'].apply(format_stock_code)
            # 去除空的股票代码
            df = df[df['股票代码'] != ""]
        else:
            st.warning("⚠️ 数据文件中缺少'股票代码'列")
        
        # 确保年份列为整数类型
        if '年份' in df.columns:
            df['年份'] = pd.to_numeric(df['年份'], errors='coerce')
            # 去除年份为NaN的记录
            df = df.dropna(subset=['年份'])
            df['年份'] = df['年份'].astype(int)
            # 计算年份范围
            min_year = df['年份'].min()
            max_year = df['年份'].max()
        else:
            st.warning("⚠️ 数据文件中缺少'年份'列")
        
        # 处理企业名称空值
        if '企业名称' in df.columns:
            df['企业名称'] = df['企业名称'].fillna('未知企业')
        else:
            st.warning("⚠️ 数据文件中缺少'企业名称'列")
        
        # 数据质量检查
        if '数字化转型指数' in df.columns:
            # 确保指数值为数值类型
            df['数字化转型指数'] = pd.to_numeric(df['数字化转型指数'], errors='coerce')
            # 去除指数为NaN的记录
            df = df.dropna(subset=['数字化转型指数'])
        
        # 不显示加载完成信息
            
        return df
    except Exception as e:
        st.error(f"❌ 数据加载失败: {str(e)}")
        st.info("请检查数据文件格式是否正确，是否为有效的Excel文件")
        return pd.DataFrame()

# 初始化会话状态
if 'selected_stock' not in st.session_state:
    st.session_state['selected_stock'] = ""
if 'selected_company' not in st.session_state:
    st.session_state['selected_company'] = ""

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
        selected_year = st.selectbox(
            "选择年份",
            options=list(range(min_year, max_year + 1)),
            index=list(range(min_year, max_year + 1)).index(max_year)  # 默认选择最新年份
        )
    else:
        selected_year = 2023
    
    # 查询按钮
    search_button = st.button("🔍 生成趋势图", type="primary")

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
            # 显示企业基本信息
            company_name = main_df['企业名称'].iloc[0]
            st.success(f"✅ 正在分析: {company_name} (股票代码: {formatted_stock_code})")
            st.session_state['selected_company'] = company_name
            

            
            # 按年份排序数据以生成历史趋势
            main_df = main_df.sort_values('年份')
            
            # 历史指数折线图（移到最前面）
            st.subheader("📈 历史指数折线图")
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
                
                # 筛选指定年份的数据
                year_df = main_df[main_df['年份'] == selected_year]
                
                # 添加查询年份的太阳标记
                if selected_year in main_df['年份'].values:
                    year_data = main_df[main_df['年份'] == selected_year]
                    if not year_data.empty:
                        fig.add_trace(go.Scatter(
                            x=[selected_year],
                            y=[year_data['数字化转型指数'].iloc[0]],
                            mode='markers',
                            name=f'{selected_year}年 (查询年份)',
                            marker=dict(
                                size=20,
                                symbol='hexagram',  # 使用六芒星替代太阳形状
                                color='orange',  # 太阳颜色
                                line=dict(width=2, color='red')  # 边缘颜色
                            ),
                            hovertemplate=f'<b>查询年份: {selected_year}</b><br><b>数字化转型指数</b>: %{{y:.2f}}<extra></extra>'
                        ))
                
                # 更新图表布局
                fig.update_layout(
                    title=f"<b>{company_name} 数字化转型指数历史趋势</b>",
                    plot_bgcolor="white",
                    font=dict(family="SimHei, Arial, sans-serif", size=14),
                    margin=dict(l=60, r=20, t=80, b=60),
                    xaxis=dict(
                        gridcolor='#e0e0e0',
                        dtick=1,
                        title=dict(
                            text="年份",
                            font=dict(size=14, family="SimHei")
                        ),
                        tickfont=dict(size=12)
                    ),
                    yaxis=dict(
                        gridcolor='#e0e0e0',
                        title=dict(
                            text="数字化转型指数",
                            font=dict(size=14, family="SimHei")
                        ),
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
            
            # 检查所选年份是否有数据
            if year_df.empty:
                st.warning(f"⚠️ 在 {selected_year} 年份未找到数据")
                

                


# 如果没有搜索，显示使用说明和数据预览
if not search_button:
    st.info("💡 使用说明")
    st.markdown("""
    1. 在左侧输入框中输入**6位股票代码**，或从下拉列表中选择企业
    2. 选择要查询的年份
    3. 点击"生成趋势图"按钮查看分析结果
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