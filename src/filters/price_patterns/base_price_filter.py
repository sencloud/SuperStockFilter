import pandas as pd
import numpy as np
from ...filters.base_filter import BaseFilter
from src.utils.config import ts_api
import talib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BasePriceFilter(BaseFilter):
    """基础价格形态筛选器"""
    
    def __init__(self, lookback_period: int = 20):
        self.lookback_period = lookback_period
        
    def get_kline_data(self, stock_code: str) -> pd.DataFrame:
        """获取K线数据"""
        try:
            # 计算开始日期（往前推lookback_period个交易日）
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=self.lookback_period * 2)).strftime('%Y%m%d')
            
            # 获取日线数据
            df = ts_api.daily(
                ts_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,open,high,low,close,vol,amount'
            )
            
            if df is None or len(df) == 0:
                logger.warning(f"未获取到股票 {stock_code} 的K线数据")
                return None
                
            # 按日期排序
            df = df.sort_values('trade_date')
            
            # 重命名列
            df = df.rename(columns={
                'trade_date': 'date',
                'vol': 'volume'
            })
            
            # 设置日期索引
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 的K线数据时出错: {str(e)}")
            return None
            
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        if df is None or len(df) == 0:
            return df
            
        try:
            # 计算涨跌幅
            df['pct_change'] = df['close'].pct_change()
            
            # 计算振幅
            df['amplitude'] = (df['high'] - df['low']) / df['close'].shift(1)
            
            # 计算换手率
            df['turnover_rate'] = df['volume'] / df['volume'].rolling(window=20).mean()
            
            # 计算量比
            df['volume_ratio'] = df['volume'] / df['volume'].rolling(window=5).mean()
            
            # 计算资金流向
            df['money_flow'] = df['amount'] * (df['close'] - df['open']) / (df['high'] - df['low'])
            
            return df
            
        except Exception as e:
            logger.error(f"计算技术指标时出错: {str(e)}")
            return df 