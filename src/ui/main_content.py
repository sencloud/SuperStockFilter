import streamlit as st
from src.services.stock_service import filter_stocks, get_stock_basic_info, get_deepseek_analysis
from src.ui.stock_table import render_stock_table
from src.filters.filter_factory import FilterFactory

def render_main_content():
    """渲染主要内容区域"""
    tab1, tab2 = st.tabs(["高级筛选", "筛选结果"])
    
    with tab1:
        render_advanced_filter()
    
    with tab2:
        render_filter_results()

def render_advanced_filter():
    """渲染高级筛选界面"""
    st.subheader("高级筛选")
    
    # K线形态选择
    pattern_options = ['所有', 'V型底', 'W底', '启明之星', '圆弧底', '头肩底', '平底', '旭日东升', '看涨吞没', '红三兵', '锤头线']
    pattern = st.radio(
        "K线形态",
        options=pattern_options,
        index=0,
        help="选择要筛选的K线形态"
    )
    
    # 价格预测
    price_prediction = st.radio(
        "价格预测",
        options=['所有', '涨停'],
        index=0,
        help="选择价格预测类型"
    )
    
    if st.button("应用高级筛选"):
        # 获取当前筛选结果
        filtered_stocks = st.session_state.get('filtered_stocks', None)
        if filtered_stocks is not None:
            # 应用K线形态筛选
            if pattern != '所有':
                kline_filter = FilterFactory.create_filter(pattern)
                if kline_filter:
                    filtered_stocks = kline_filter.filter(filtered_stocks)
            
            # 应用价格预测筛选
            if price_prediction != '所有':
                price_filter = FilterFactory.create_filter(price_prediction)
                if price_filter:
                    filtered_stocks = price_filter.filter(filtered_stocks)
            
            # 更新筛选结果
            st.session_state['filtered_stocks'] = filtered_stocks
            st.success(f"高级筛选完成，找到 {len(filtered_stocks)} 只股票")
        else:
            st.warning("请先进行基础筛选")

def render_filter_results():
    """渲染筛选结果tab"""
    if 'filtered_stocks' not in st.session_state or st.session_state.filtered_stocks is None:
        st.info("请先进行筛选")
        return
    
    render_stock_table(st.session_state.filtered_stocks) 