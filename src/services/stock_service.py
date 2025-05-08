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
    price_prediction: str = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, any]:
    """筛选股票"""
    try:
        logger.info(f"开始筛选股票，参数：market_types={market_types}, industries={industries}, "
                   f"index_components={index_components}, kline_pattern={kline_pattern}, "
                   f"price_prediction={price_prediction}, page={page}, page_size={page_size}")
        
        # 获取股票列表
        df = ts_api.stock_basic(exchange='', list_status='L')
        logger.info(f"获取到原始股票列表: type={type(df)}, shape={df.shape if isinstance(df, pd.DataFrame) else 'not DataFrame'}")
        
        if not isinstance(df, pd.DataFrame):
            logger.error(f"获取股票列表返回类型错误: {type(df)}")
            logger.error(f"返回内容: {df}")
            return {
                'data': [],
                'total': 0,
                'page': page,
                'page_size': page_size
            }
        
        if df.empty:
            logger.warning("获取到的股票列表为空")
            return {
                'data': [],
                'total': 0,
                'page': page,
                'page_size': page_size
            }
        
        # 市场类型筛选
        if market_types:
            logger.info(f"进行市场类型筛选，条件: {market_types}")
            df = df[df['market'].isin(market_types)]
            logger.info(f"市场类型筛选后剩余股票数: {len(df)}")
            
        # 行业筛选
        if industries:
            logger.info(f"进行行业筛选，条件: {industries}")
            df = df[df['industry'].isin(industries)]
            logger.info(f"行业筛选后剩余股票数: {len(df)}")
            
        # 指数成分股筛选
        if index_components:
            logger.info(f"进行指数成分股筛选，条件: {index_components}")
            index_stocks = set()
            for index_code in index_components:
                try:
                    logger.info(f"获取指数 {index_code} 的成分股")
                    index_df = ts_api.index_weight(index_code=index_code)
                    logger.info(f"指数 {index_code} 返回数据类型: {type(index_df)}")
                    if isinstance(index_df, pd.DataFrame) and not index_df.empty:
                        current_stocks = index_df['con_code'].tolist()
                        logger.info(f"指数 {index_code} 包含成分股数量: {len(current_stocks)}")
                        index_stocks.update(current_stocks)
                except Exception as e:
                    logger.error(f"获取指数 {index_code} 成分股失败: {str(e)}", exc_info=True)
            if index_stocks:
                logger.info(f"总成分股数量: {len(index_stocks)}")
                df = df[df['ts_code'].isin(index_stocks)]
                logger.info(f"指数成分股筛选后剩余股票数: {len(df)}")
                
        # K线形态筛选
        if kline_pattern and kline_pattern != '所有':
            logger.info(f"进行K线形态筛选，条件: {kline_pattern}")
            filter_instance = FilterFactory.create_filter(kline_pattern)
            if filter_instance:
                df = filter_instance.filter(df)
                logger.info(f"K线形态筛选后剩余股票数: {len(df)}")
                
        # 价格预测筛选
        if price_prediction:
            logger.info(f"进行价格预测筛选，条件: {price_prediction}")
            filter_instance = FilterFactory.create_filter(price_prediction)
            if filter_instance:
                df = filter_instance.filter(df)
                logger.info(f"价格预测筛选后剩余股票数: {len(df)}")
        
        # 计算总数
        total = len(df)
        logger.info(f"筛选后总股票数: {total}")
        
        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        logger.info(f"进行分页，范围: {start_idx} - {end_idx}")
        df_page = df.iloc[start_idx:end_idx].copy()
        logger.info(f"当前页股票数: {len(df_page)}")
        
        # 获取最新行情数据
        if not df_page.empty:
            stock_codes = ','.join(df_page['ts_code'].tolist())
            logger.info(f"获取行情数据，股票代码: {stock_codes}")
            try:
                # 获取日线数据
                logger.info("开始获取日线数据")
                daily = ts_api.daily(ts_code=stock_codes)
                logger.info(f"日线数据类型: {type(daily)}, 是否为空: {daily.empty if isinstance(daily, pd.DataFrame) else 'not DataFrame'}")
                
                if isinstance(daily, pd.DataFrame) and not daily.empty:
                    daily = daily.sort_values('trade_date').groupby('ts_code').last()
                    logger.info(f"处理后的日线数据列: {daily.columns.tolist()}")
                    df_page = df_page.merge(daily[['close', 'pct_chg', 'vol', 'amount']], 
                                    left_on='ts_code', right_index=True, how='left')
                    df_page = df_page.rename(columns={
                        'close': 'price',
                        'vol': 'volume'
                    })
                    logger.info("日线数据合并完成")
                
                # 获取每日指标
                logger.info("开始获取每日指标")
                daily_basic = ts_api.daily_basic(ts_code=stock_codes)
                logger.info(f"每日指标数据类型: {type(daily_basic)}, 是否为空: {daily_basic.empty if isinstance(daily_basic, pd.DataFrame) else 'not DataFrame'}")
                
                if isinstance(daily_basic, pd.DataFrame) and not daily_basic.empty:
                    daily_basic = daily_basic.sort_values('trade_date').groupby('ts_code').last()
                    logger.info(f"处理后的每日指标列: {daily_basic.columns.tolist()}")
                    df_page = df_page.merge(daily_basic[['pe', 'pb', 'total_mv']], 
                                    left_on='ts_code', right_index=True, how='left')
                    logger.info("每日指标合并完成")
            except Exception as e:
                logger.error(f"获取行情数据失败: {str(e)}", exc_info=True)
        
        # 处理数据，确保JSON序列化不会出错
        logger.info("开始处理数据进行JSON序列化")
        result = []
        for idx, row in df_page.iterrows():
            try:
                logger.debug(f"处理第 {idx} 行数据")
                # 先转换为字典
                row_dict = row.to_dict() if hasattr(row, 'to_dict') else dict(row)
                logger.debug(f"行数据转换为字典: {row_dict}")
                
                stock_data = {
                    'ts_code': str(row_dict.get('ts_code', '')),
                    'name': str(row_dict.get('name', '')),
                    'industry': str(row_dict.get('industry', '')),
                    'market': str(row_dict.get('market', '')),
                    'area': str(row_dict.get('area', '')),
                    'list_date': str(row_dict.get('list_date', '')),
                    'price': float(row_dict['price']) if pd.notna(row_dict.get('price')) else None,
                    'change': float(row_dict['pct_chg']) if pd.notna(row_dict.get('pct_chg')) else None,
                    'volume': float(row_dict['volume']) if pd.notna(row_dict.get('volume')) else None,
                    'amount': float(row_dict['amount']) if pd.notna(row_dict.get('amount')) else None,
                    'pe': float(row_dict['pe']) if pd.notna(row_dict.get('pe')) else None,
                    'pb': float(row_dict['pb']) if pd.notna(row_dict.get('pb')) else None,
                    'total_mv': float(row_dict['total_mv']) if pd.notna(row_dict.get('total_mv')) else None
                }
                result.append(stock_data)
            except Exception as e:
                logger.error(f"处理股票数据失败: {str(e)}, row: {row}", exc_info=True)
                continue
        
        logger.info(f"数据处理完成，返回 {len(result)} 条记录")
        return {
            'data': result,
            'total': total,
            'page': page,
            'page_size': page_size
        }
        
    except Exception as e:
        logger.error(f"筛选股票失败: {str(e)}", exc_info=True)
        return {
            'data': [],
            'total': 0,
            'page': page,
            'page_size': page_size
        }

def get_stock_basic_info(stock_code: str) -> dict:
    """获取股票基础信息"""
    logger.info(f"获取股票{stock_code}的基础信息")
    try:
        # 获取基本信息
        basic_info = ts_api.stock_basic(ts_code=stock_code, fields='ts_code,name,area,industry,market,list_date')
        
        # 获取实时行情
        daily = ts_api.daily(ts_code=stock_code)
        
        # 获取每日指标
        daily_basic = ts_api.daily_basic(ts_code=stock_code)
        
        if basic_info.empty:
            raise ValueError(f"股票不存在: {stock_code}")
            
        # 转换DataFrame为字典
        result = basic_info.iloc[0].to_dict() if isinstance(basic_info, pd.DataFrame) else basic_info
        
        # 添加行情数据
        if not daily.empty and isinstance(daily, pd.DataFrame):
            daily_latest = daily.iloc[0].to_dict()
            result.update({
                'price': float(daily_latest.get('close')) if pd.notna(daily_latest.get('close')) else None,
                'change': float(daily_latest.get('pct_chg')) if pd.notna(daily_latest.get('pct_chg')) else None,
                'volume': float(daily_latest.get('vol')) if pd.notna(daily_latest.get('vol')) else None,
                'amount': float(daily_latest.get('amount')) if pd.notna(daily_latest.get('amount')) else None
            })
            
        # 添加指标数据
        if not daily_basic.empty and isinstance(daily_basic, pd.DataFrame):
            daily_basic_latest = daily_basic.iloc[0].to_dict()
            result.update({
                'pe': float(daily_basic_latest.get('pe')) if pd.notna(daily_basic_latest.get('pe')) else None,
                'pb': float(daily_basic_latest.get('pb')) if pd.notna(daily_basic_latest.get('pb')) else None,
                'total_mv': float(daily_basic_latest.get('total_mv')) if pd.notna(daily_basic_latest.get('total_mv')) else None
            })
            
        return result
    except Exception as e:
        logger.error(f"获取股票{stock_code}基础信息时发生错误: {str(e)}", exc_info=True)
        raise

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
- 公司名称：{basic_info.get('name', '未知')}
- 所属行业：{basic_info.get('industry', '未知')}
- 上市日期：{basic_info.get('list_date', '未知')}
- 所在地区：{basic_info.get('area', '未知')}
- 市场类型：{basic_info.get('market', '未知')}

最新交易数据：
- 最新价：{basic_info.get('price', '未知')}元
- 涨跌幅：{basic_info.get('change', '未知')}%
- 成交量：{basic_info.get('volume', '未知')}手
- 成交额：{basic_info.get('amount', '未知')}千元

主要指标：
- 市盈率：{basic_info.get('pe', '未知')}
- 市净率：{basic_info.get('pb', '未知')}
- 总市值：{basic_info.get('total_mv', '未知')}元

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