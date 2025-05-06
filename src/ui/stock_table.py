import streamlit as st
import pandas as pd
import asyncio
from src.services.stock_service import get_stock_basic_info, get_deepseek_analysis
from typing import Optional

def render_stock_table(stocks_df: Optional[pd.DataFrame]):
    """渲染股票表格"""
    if stocks_df is None or len(stocks_df) == 0:
        st.info("请先进行筛选")
        return
        
    # 显示股票表格
    st.dataframe(
        stocks_df[['ts_code', 'name', 'industry', 'market']].rename(columns={
            'ts_code': '股票代码',
            'name': '股票名称',
            'industry': '所属行业',
            'market': '市场类型'
        }),
        use_container_width=True
    )
    
    # 创建股票选择下拉框
    stock_options = [f"{row['ts_code']} - {row['name']}" for _, row in stocks_df.iterrows()]
    selected_stock = st.selectbox(
        "选择股票查看详情",
        options=stock_options,
        key="selected_stock"
    )
    
    # 如果选择了股票，显示详细信息
    if selected_stock:
        stock_code = selected_stock.split(' - ')[0]
        stock_info = stocks_df[stocks_df['ts_code'] == stock_code].iloc[0]
        
        # 创建两个标签页
        tab1, tab2 = st.tabs(["基础信息", "DeepSeek分析"])
        
        with tab1:
            st.subheader("基础信息")
            # 显示基本信息
            info_cols = st.columns(2)
            with info_cols[0]:
                st.write(f"**股票代码：** {stock_info['ts_code']}")
                st.write(f"**股票名称：** {stock_info['name']}")
                st.write(f"**所属行业：** {stock_info['industry']}")
            with info_cols[1]:
                st.write(f"**市场类型：** {stock_info['market']}")
                st.write(f"**地区：** {stock_info['area']}")
                st.write(f"**上市日期：** {stock_info['list_date']}")
            
            info = get_stock_basic_info(stock_code)
            # 显示实时行情
            if '实时行情' in info:
                st.subheader("实时行情")
                st.write(pd.DataFrame([info['实时行情']]))
            
            # 显示财务指标
            if '财务指标' in info:
                st.subheader("财务指标")
                st.write(pd.DataFrame([info['财务指标']]))
    
        with tab2:
            st.subheader("DeepSeek分析")
            
            # 添加立即分析按钮
            if st.button("立即分析", key=f"analyze_{stock_code}"):
                with st.spinner("正在进行深度分析..."):
                    try:
                        # 调用异步分析函数
                        analysis = asyncio.run(get_deepseek_analysis(stock_code))
                        
                        if analysis.get("error"):
                            st.error(f"分析失败: {analysis['error']}")
                        else:
                            # 使用 markdown 显示分析结果
                            st.markdown(analysis["content"])
                            
                    except Exception as e:
                        st.error(f"分析过程中发生错误: {str(e)}")
            else:
                st.info("点击立即分析按钮获取 DeepSeek 的专业分析结果") 
   