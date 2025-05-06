import pandas as pd
import numpy as np
from .base_kline_filter import BaseKlineFilter
import logging

logger = logging.getLogger(__name__)

class MorningStarFilter(BaseKlineFilter):
    """启明之星筛选器"""
    
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行启明之星筛选"""
        logger.info("开始执行启明之星筛选，传入的股票数量：%d", len(stocks_df))
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
                
                # 寻找启明之星形态
                for i in range(2, len(kline_data)):
                    # 第一根K线：大阴线
                    if (kline_data['body'].iloc[i-2] < 0 and 
                        abs(kline_data['body'].iloc[i-2]) > kline_data['close'].iloc[i-2] * 0.02):
                        
                        # 第二根K线：小实体
                        if (abs(kline_data['body'].iloc[i-1]) < kline_data['close'].iloc[i-1] * 0.01 and
                            kline_data['lower_shadow'].iloc[i-1] > kline_data['body'].iloc[i-1] * 2):
                            
                            # 第三根K线：大阳线
                            if (kline_data['body'].iloc[i] > 0 and
                                kline_data['body'].iloc[i] > kline_data['close'].iloc[i] * 0.02 and
                                kline_data['close'].iloc[i] > kline_data['open'].iloc[i-2]):
                                
                                result_stocks.append(stock)
                                logger.info("股票 %s 形成启明之星形态", stock['ts_code'])
                                break
                
            except Exception as e:
                logger.error("处理股票 %s 时出错: %s", stock['ts_code'], str(e))
                continue
        
        logger.info("启明之星筛选完成，找到的股票数量：%d", len(result_stocks))
        return pd.DataFrame(result_stocks) 