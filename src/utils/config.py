import streamlit as st
import tushare as ts
from src.api.config import get_settings
import logging

# 获取配置
settings = get_settings()

# 初始化Tushare API
ts_api = ts.pro_api(settings.TUSHARE_TOKEN)

# 设置日志级别
logging.basicConfig(level=logging.INFO)

def init_session_state():
    """初始化session state变量"""
    if 'filtered_stocks' not in st.session_state:
        st.session_state.filtered_stocks = None
    
    if 'market_type' not in st.session_state:
        st.session_state.market_type = []
        
    if 'industry' not in st.session_state:
        st.session_state.industry = []
        
    if 'index_component' not in st.session_state:
        st.session_state.index_component = []
        
    if 'kline_pattern' not in st.session_state:
        st.session_state.kline_pattern = None
        
    if 'price_prediction' not in st.session_state:
        st.session_state.price_prediction = None 