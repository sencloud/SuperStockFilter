import pandas as pd
import numpy as np
from .base_kline_filter import BaseKlineFilter
import logging

logger = logging.getLogger(__name__)

class HammerFilter(BaseKlineFilter):
    """锤头线筛选器"""
    
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行锤头线筛选"""
        logger.info("开始执行锤头线筛选，传入的股票数量：%d", len(stocks_df))
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
                
                # 寻找锤头线形态
                for i in range(1, len(kline_data)):
                    # 检查下影线长度是否至少是实体的2倍
                    if kline_data['lower_shadow'].iloc[i] > abs(kline_data['body'].iloc[i]) * 2:
                        # 检查上影线是否较短
                        if kline_data['upper_shadow'].iloc[i] < abs(kline_data['body'].iloc[i]) * 0.5:
                            # 检查实体是否较小
                            if abs(kline_data['body'].iloc[i]) < kline_data['close'].iloc[i] * 0.02:
                                # 检查成交量是否放大
                                if kline_data['vol'].iloc[i] > kline_data['vol'].iloc[i-1] * 1.5:
                                    result_stocks.append(stock)
                                    logger.info("股票 %s 形成锤头线形态，成交量放大：%.2f%%", 
                                              stock['ts_code'],
                                              (kline_data['vol'].iloc[i] / kline_data['vol'].iloc[i-1] - 1) * 100)
                                    break
                
            except Exception as e:
                logger.error("处理股票 %s 时出错: %s", stock['ts_code'], str(e))
                continue
        
        logger.info("锤头线筛选完成，找到的股票数量：%d", len(result_stocks))
        return pd.DataFrame(result_stocks) 