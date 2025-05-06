import streamlit as st
from src.ui.sidebar import render_sidebar
from src.ui.main_content import render_main_content
from src.utils.config import init_session_state

def main():
    st.set_page_config(
        page_title="超级股票过滤器",
        page_icon="📈",
        layout="wide"
    )
    
    # 初始化session state
    init_session_state()
    
    # 渲染侧边栏
    render_sidebar()
    
    # 渲染主要内容
    render_main_content()

if __name__ == "__main__":
    main() 