import pandas as pd
import logging
import asyncio
from typing import List, Dict, Optional
from src.utils.config import ts_api
from src.filters.filter_factory import FilterFactory
from src.services.deepseek_client import DeepSeekClient
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_market_types() -> List[str]:
    """获取市场类型列表"""
    try:
        # 获取股票列表
        df = ts_api.stock_basic(exchange='', list_status='L')
        # 获取唯一市场类型
        market_types = df['market'].unique().tolist()
        return market_types
    except Exception as e:
        logger.error(f"获取市场类型失败: {str(e)}")
        return []

def get_industries() -> List[str]:
    """获取行业分类列表"""
    try:
        # 获取股票列表
        df = ts_api.stock_basic(exchange='', list_status='L')
        # 获取唯一行业分类
        industries = df['industry'].unique().tolist()
        return industries
    except Exception as e:
        logger.error(f"获取行业分类失败: {str(e)}")
        return []

def get_index_components() -> List[str]:
    """获取指数成分股列表"""
    try:
        # 获取主要指数列表
        indices = ['000300.SH', '000016.SH', '000905.SH', '000852.SH', '000922.CSI']
        index_names = ['沪深300', '上证50', '中证500', '中证1000', '中证红利']
        return list(zip(indices, index_names))
    except Exception as e:
        logger.error(f"获取指数成分股失败: {str(e)}")
        return []

def filter_stocks(
    market_types: List[str] = None,
    industries: List[str] = None,
    index_components: List[str] = None,
    kline_pattern: str = None,
    price_prediction: str = None
) -> Optional[pd.DataFrame]:
    """筛选股票"""
    try:
        # 获取股票列表
        df = ts_api.stock_basic(exchange='', list_status='L')
        
        # 市场类型筛选
        if market_types:
            df = df[df['market'].isin(market_types)]
            
        # 行业筛选
        if industries:
            df = df[df['industry'].isin(industries)]
            
        # 指数成分股筛选
        if index_components:
            index_stocks = set()
            for index_code in index_components:
                try:
                    index_df = ts_api.index_weight(index_code=index_code)
                    if index_df is not None and not index_df.empty:
                        index_stocks.update(index_df['con_code'].tolist())
                except Exception as e:
                    logger.error(f"获取指数 {index_code} 成分股失败: {str(e)}")
            if index_stocks:
                df = df[df['ts_code'].isin(index_stocks)]
                
        # K线形态筛选
        if kline_pattern and kline_pattern != '所有':
            filter_instance = FilterFactory.create_filter(kline_pattern)
            if filter_instance:
                df = filter_instance.filter(df)
                
        # 价格预测筛选
        if price_prediction:
            filter_instance = FilterFactory.create_filter(price_prediction)
            if filter_instance:
                df = filter_instance.filter(df)
                
        return df
        
    except Exception as e:
        logger.error(f"筛选股票失败: {str(e)}")
        return None

def get_stock_basic_info(stock_code: str) -> dict:
    """获取股票基础信息"""
    logger.info(f"获取股票{stock_code}的基础信息")
    try:
        # 获取基本信息
        basic_info = ts_api.stock_basic(ts_code=stock_code, fields='ts_code,name,area,industry,market,list_date')
        
        # 获取实时行情
        daily_info = ts_api.daily(ts_code=stock_code)
        
        # 获取财务指标
        financial_info = ts_api.fina_indicator(ts_code=stock_code)
        
        # 合并信息
        info = {
            '基本信息': basic_info.to_dict('records')[0] if not basic_info.empty else {},
            '实时行情': daily_info.to_dict('records')[0] if not daily_info.empty else {},
            '财务指标': financial_info.to_dict('records')[0] if not financial_info.empty else {}
        }
        
        logger.info(f"获取到的股票信息:\n{info}")
        return info
    except Exception as e:
        logger.error(f"获取股票{stock_code}基础信息时发生错误: {str(e)}", exc_info=True)
        return {"error": str(e)}

async def get_deepseek_analysis(stock_code: str) -> dict:
    """获取DeepSeek分析结果
    
    Args:
        stock_code: 股票代码
        
    Returns:
        分析结果字典
    """
    logger.info(f"开始获取股票{stock_code}的DeepSeek分析")
    try:
        # 获取股票基础信息
        basic_info = get_stock_basic_info(stock_code)
        logger.info(f"获取到的基础信息: {basic_info}")
        
        # 获取最近的交易数据
        daily_data = ts_api.daily(ts_code=stock_code, start_date=(pd.Timestamp.now() - pd.Timedelta(days=30)).strftime('%Y%m%d'))
        logger.info(f"获取到的交易数据: \n{daily_data.head() if not daily_data.empty else '无数据'}")
        
        # 构建分析提示词
        prompt = f"""如何分析一只股票，以{stock_code}为例，我对这只股票一无所知，如何尽可能全面的分析它，并给出初步的趋势预判。
        请务必结合最近7天的资讯以及我手上的如下信息：

基本面信息：
- 公司名称：{basic_info.get('基本信息', {}).get('name', '未知')}
- 所属行业：{basic_info.get('基本信息', {}).get('industry', '未知')}
- 上市日期：{basic_info.get('基本信息', {}).get('list_date', '未知')}

最新财务指标：
{str(basic_info.get('财务指标', {}))}

最近交易数据：
{daily_data.head().to_string() if not daily_data.empty else '无数据'}

请严格按照以下格式进行分析，每个部分必须以对应的标题开头：

1. 基本面分析：
[在这里详细分析公司基础信息与行业定位、业务与成长性分析、财务状况等]

2. 技术面与资金动向分析：
[在这里详细分析价格趋势、成交量、主要技术指标等]

3. 风险评估：
[在这里详细分析市场风险、行业风险、公司特定风险等]

4. 投资建议：
[在这里给出明确的趋势预判与策略建议]

请用中文回答，每个部分至少200字。请确保严格按照上述格式回复，包含所有标题，移除所有无关内容如参考文献。
"""
        logger.info(f"构建的提示词: {prompt}")
        
        # 初始化DeepSeek客户端
        deepseek = DeepSeekClient()
        logger.info("已初始化DeepSeek客户端")
        
        # 调用DeepSeek API获取分析结果
        response = await deepseek.chat_completion([
            {"role": "system", "content": "你是一个专业的股票分析师。请严格按照用户提供的格式进行分析，确保包含所有指定的标题。"},
            {"role": "user", "content": prompt}
        ])
        
        # 获取原始分析结果
        analysis = response.choices[0].message.content
        logger.info(f"DeepSeek返回的分析结果: {analysis}")
        
        return {
            "content": analysis,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"获取股票{stock_code}的DeepSeek分析失败: {str(e)}", exc_info=True)
        return {
            "content": None,
            "error": str(e)
        } 