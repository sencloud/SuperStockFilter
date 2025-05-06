import pandas as pd
import numpy as np
from .base_kline_filter import BaseKlineFilter
import logging

logger = logging.getLogger(__name__)

class BullishEngulfingFilter(BaseKlineFilter):
    """看涨吞没筛选器"""
    
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行看涨吞没筛选"""
        logger.info("开始执行看涨吞没筛选，传入的股票数量：%d", len(stocks_df))
        result_stocks = []
        
        for _, stock in stocks_df.iterrows():
            try:
                # 获取K线数据
                kline_data = self.get_kline_data(stock['ts_code'])
                logger.info("获取股票 %s 的K线数据成功，K线数据长度：%d", stock['ts_code'], len(kline_data))
                if kline_data is None or len(kline_data) < self.lookback_period:
                    continue
                    
                # 计算K线实体和影线
                kline_data['body'] = kline_data['close'] - kline_data['open']
                kline_data['upper_shadow'] = kline_data['high'] - kline_data[['open', 'close']].max(axis=1)
                kline_data['lower_shadow'] = kline_data[['open', 'close']].min(axis=1) - kline_data['low']
                
                # 寻找看涨吞没形态
                for i in range(1, len(kline_data)):
                    # 第一根K线：阴线
                    if kline_data['body'].iloc[i-1] < 0:
                        # 第二根K线：阳线
                        if (kline_data['body'].iloc[i] > 0 and
                            kline_data['open'].iloc[i] < kline_data['close'].iloc[i-1] and
                            kline_data['close'].iloc[i] > kline_data['open'].iloc[i-1]):
                            
                            # 检查阳线实体是否大于阴线实体
                            if abs(kline_data['body'].iloc[i]) > abs(kline_data['body'].iloc[i-1]):
                                # 检查成交量
                                if kline_data['volume'].iloc[i] > kline_data['volume'].iloc[i-1] * 1.5:
                                    result_stocks.append(stock)
                                    logger.info("股票 %s 形成看涨吞没形态，成交量放大：%.2f%%", 
                                              stock['ts_code'],
                                              (kline_data['volume'].iloc[i] / kline_data['volume'].iloc[i-1] - 1) * 100)
                                    break
                
            except Exception as e:
                logger.error("处理股票 %s 时出错: %s", stock['ts_code'], str(e))
                continue
        
        logger.info("看涨吞没筛选完成，找到的股票数量：%d", len(result_stocks))
        return pd.DataFrame(result_stocks) 