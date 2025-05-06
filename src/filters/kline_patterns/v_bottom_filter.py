import pandas as pd
import numpy as np
from .base_kline_filter import BaseKlineFilter
import logging

logger = logging.getLogger(__name__)

class VBottomFilter(BaseKlineFilter):
    """V型底筛选器"""
    
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行V型底筛选"""
        logger.info("开始执行V型底筛选，传入的股票数量：%d", len(stocks_df))
        result_stocks = []
        
        for _, stock in stocks_df.iterrows():
            try:
                # 获取K线数据
                kline_data = self.get_kline_data(stock['ts_code'])
                logger.info("获取K线数据成功，K线数据长度：%d", len(kline_data))
                if kline_data is None or len(kline_data) < self.lookback_period:
                    continue
                    
                # 计算价格变化率
                price_changes = kline_data['close'].pct_change()
                
                # 寻找急速下跌
                rapid_decline = price_changes.rolling(5).sum() < -0.1
                
                # 寻找快速反弹
                rapid_rebound = price_changes.rolling(5).sum() > 0.1
                
                # 判断V型底形态
                for i in range(self.lookback_period - 10, len(kline_data) - 5):
                    if rapid_decline.iloc[i] and rapid_rebound.iloc[i + 5]:
                        # 计算V型底的角度
                        decline_angle = np.arctan2(
                            kline_data['close'].iloc[i] - kline_data['close'].iloc[i-5],
                            5
                        )
                        rebound_angle = np.arctan2(
                            kline_data['close'].iloc[i+5] - kline_data['close'].iloc[i],
                            5
                        )
                        
                        # 判断角度是否接近对称
                        if abs(decline_angle + rebound_angle) < 0.2:
                            result_stocks.append(stock)
                            break
                
            except Exception as e:
                logger.error(f"处理股票 {stock['ts_code']} 时出错: {str(e)}")
                continue
        
        logger.info("V型底筛选完成，找到的股票数量：%d", len(result_stocks))

        return pd.DataFrame(result_stocks) 