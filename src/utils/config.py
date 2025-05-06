import streamlit as st
import tushare as ts
import os
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE = "https://ark.cn-beijing.volces.com/api/v3/bots"

# 获取Tushare API token
TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN')

if not TUSHARE_TOKEN:
    raise ValueError("请在.env文件中设置TUSHARE_TOKEN环境变量")

# 初始化Tushare API
ts_api = ts.pro_api(TUSHARE_TOKEN)

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