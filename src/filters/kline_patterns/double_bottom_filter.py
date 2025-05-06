import pandas as pd
import numpy as np
from .base_kline_filter import BaseKlineFilter
import logging

logger = logging.getLogger(__name__)

class DoubleBottomFilter(BaseKlineFilter):
    """W底筛选器"""
    
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行W底筛选"""
        logger.info("开始执行W底筛选，传入的股票数量：%d", len(stocks_df))
        result_stocks = []
        
        for _, stock in stocks_df.iterrows():
            try:
                # 获取K线数据
                kline_data = self.get_kline_data(stock['ts_code'])
                logger.info("获取股票 %s 的K线数据成功，K线数据长度：%d", stock['ts_code'], len(kline_data))
                if kline_data is None or len(kline_data) < self.lookback_period:
                    continue
                    
                # 计算价格变化率
                price_changes = kline_data['close'].pct_change()
                
                # 寻找两个底部
                bottoms = []
                for i in range(2, len(kline_data) - 2):
                    if (kline_data['close'].iloc[i] < kline_data['close'].iloc[i-1] and 
                        kline_data['close'].iloc[i] < kline_data['close'].iloc[i-2] and
                        kline_data['close'].iloc[i] < kline_data['close'].iloc[i+1] and
                        kline_data['close'].iloc[i] < kline_data['close'].iloc[i+2]):
                        bottoms.append(i)
                
                logger.info("股票 %s 找到 %d 个可能的底部", stock['ts_code'], len(bottoms))
                
                # 检查是否有两个相近的底部
                for i in range(len(bottoms) - 1):
                    if bottoms[i+1] - bottoms[i] >= 5 and bottoms[i+1] - bottoms[i] <= 20:
                        # 检查两个底部的价格是否接近
                        price_diff = abs(kline_data['close'].iloc[bottoms[i]] - kline_data['close'].iloc[bottoms[i+1]])
                        price_avg = (kline_data['close'].iloc[bottoms[i]] + kline_data['close'].iloc[bottoms[i+1]]) / 2
                        
                        if price_diff / price_avg < 0.05:  # 价格差异小于5%
                            result_stocks.append(stock)
                            logger.info("股票 %s 形成W底形态", stock['ts_code'])
                            break
                
            except Exception as e:
                logger.error("处理股票 %s 时出错: %s", stock['ts_code'], str(e))
                continue
        
        logger.info("W底筛选完成，找到的股票数量：%d", len(result_stocks))
        return pd.DataFrame(result_stocks) 