import pandas as pd
import numpy as np
from .base_kline_filter import BaseKlineFilter
import logging

logger = logging.getLogger(__name__)

class FlatBottomFilter(BaseKlineFilter):
    """平底筛选器"""
    
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行平底筛选"""
        logger.info("开始执行平底筛选，传入的股票数量：%d", len(stocks_df))
        result_stocks = []
        
        for _, stock in stocks_df.iterrows():
            try:
                # 获取K线数据
                kline_data = self.get_kline_data(stock['ts_code'])
                logger.info("获取股票 %s 的K线数据成功，K线数据长度：%d", stock['ts_code'], len(kline_data))
                if kline_data is None or len(kline_data) < self.lookback_period:
                    continue
                    
                # 计算价格波动率
                kline_data['volatility'] = (kline_data['high'] - kline_data['low']) / kline_data['close']
                
                # 寻找平底形态
                for i in range(10, len(kline_data)):
                    # 获取最近10天的数据
                    recent_data = kline_data.iloc[i-10:i+1]
                    
                    # 计算价格标准差
                    price_std = recent_data['close'].std()
                    price_mean = recent_data['close'].mean()
                    
                    # 检查价格是否在窄幅区间内波动
                    if price_std / price_mean < 0.02:  # 价格波动小于2%
                        # 检查成交量是否放大
                        volume_ma = recent_data['vol'].mean()
                        recent_volume = recent_data['vol'].iloc[-3:].mean()
                        
                        if recent_volume > volume_ma * 1.5:  # 成交量放大50%
                            result_stocks.append(stock)
                            logger.info("股票 %s 形成平底形态，价格波动率：%.2f%%，成交量放大：%.2f%%", 
                                      stock['ts_code'], 
                                      (price_std / price_mean) * 100,
                                      (recent_volume / volume_ma - 1) * 100)
                            break
                
            except Exception as e:
                logger.error("处理股票 %s 时出错: %s", stock['ts_code'], str(e))
                continue
        
        logger.info("平底筛选完成，找到的股票数量：%d", len(result_stocks))
        return pd.DataFrame(result_stocks) 