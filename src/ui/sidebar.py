import streamlit as st
from src.services.stock_service import get_market_types, get_industries, get_index_components, filter_stocks
from src.utils.config import init_session_state

def render_sidebar():
    """渲染侧边栏"""
    st.sidebar.title("基础筛选")
    
    # 初始化session state
    init_session_state()
    
    # 市场类型筛选
    st.sidebar.subheader("市场类型")
    market_types = get_market_types()
    selected_market_types = st.sidebar.multiselect(
        "选择市场类型",
        options=market_types,
        default=[],
        key="market_types"
    )
    
    # 行业分类筛选
    st.sidebar.subheader("行业分类")
    industries = get_industries()
    selected_industries = st.sidebar.multiselect(
        "选择行业",
        options=industries,
        default=[],
        key="industries"
    )
    
    # 指数成分股筛选
    st.sidebar.subheader("指数成分股")
    index_components = get_index_components()
    selected_indices = st.sidebar.multiselect(
        "选择指数",
        options=[name for _, name in index_components],
        default=[],
        key="index_components"
    )
    
    # 获取选中的指数代码
    selected_index_codes = [
        code for code, name in index_components 
        if name in selected_indices
    ]
    
    # 应用筛选按钮
    if st.sidebar.button("应用筛选"):
        filtered_stocks = filter_stocks(
            market_types=selected_market_types,
            industries=selected_industries,
            index_components=selected_index_codes,
            kline_pattern=st.session_state.get('kline_pattern'),
            price_prediction=st.session_state.get('price_prediction')
        )
        
        if filtered_stocks is not None:
            st.session_state['filtered_stocks'] = filtered_stocks
            st.sidebar.success(f"找到 {len(filtered_stocks)} 只股票")
        else:
            st.sidebar.error("筛选失败，请检查日志") 