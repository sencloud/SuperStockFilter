import pandas as pd
import numpy as np
from ...filters.base_filter import BaseFilter
from src.utils.config import ts_api
import talib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BaseKlineFilter(BaseFilter):
    """基础K线形态筛选器"""
    
    def __init__(self, lookback_period: int = 20):
        self.lookback_period = lookback_period
        
    def get_kline_data(self, stock_code: str) -> pd.DataFrame:
        """获取K线数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            DataFrame: 包含K线数据的DataFrame，列包括：
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - vol: 成交量
        """
        try:
            # 计算开始日期（往前推lookback_period个交易日）
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=self.lookback_period * 2)).strftime('%Y%m%d')
            
            # 获取日线数据
            df = ts_api.daily(
                ts_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,open,high,low,close,vol'
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
        """计算技术指标
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            DataFrame: 添加了技术指标的DataFrame
        """
        if df is None or len(df) == 0:
            return df
            
        try:
            # 计算移动平均线
            df['ma5'] = talib.MA(df['close'].values, timeperiod=5)
            df['ma10'] = talib.MA(df['close'].values, timeperiod=10)
            df['ma20'] = talib.MA(df['close'].values, timeperiod=20)
            df['ma60'] = talib.MA(df['close'].values, timeperiod=60)
            
            # 计算MACD
            df['macd'], df['signal'], df['hist'] = talib.MACD(
                df['close'].values,
                fastperiod=12,
                slowperiod=26,
                signalperiod=9
            )
            
            # 计算RSI
            df['rsi'] = talib.RSI(df['close'].values, timeperiod=14)
            
            # 计算布林带
            df['upper'], df['middle'], df['lower'] = talib.BBANDS(
                df['close'].values,
                timeperiod=20,
                nbdevup=2,
                nbdevdn=2,
                matype=0
            )
            
            # 计算KDJ
            df['k'], df['d'] = talib.STOCH(
                df['high'].values,
                df['low'].values,
                df['close'].values,
                fastk_period=9,
                slowk_period=3,
                slowk_matype=0,
                slowd_period=3,
                slowd_matype=0
            )
            df['j'] = 3 * df['k'] - 2 * df['d']
            
            return df
            
        except Exception as e:
            logger.error(f"计算技术指标时出错: {str(e)}")
            return df 