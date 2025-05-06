import pandas as pd
import numpy as np
from .base_kline_filter import BaseKlineFilter
import logging

logger = logging.getLogger(__name__)

class HeadShouldersBottomFilter(BaseKlineFilter):
    """头肩底筛选器"""
    
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行头肩底筛选"""
        logger.info("开始执行头肩底筛选，传入的股票数量：%d", len(stocks_df))
        result_stocks = []
        
        for _, stock in stocks_df.iterrows():
            try:
                # 获取K线数据
                kline_data = self.get_kline_data(stock['ts_code'])
                logger.info("获取股票 %s 的K线数据成功，K线数据长度：%d", stock['ts_code'], len(kline_data))
                if kline_data is None or len(kline_data) < self.lookback_period:
                    continue
                    
                # 寻找局部最低点
                window = 5
                local_minima = []
                for i in range(window, len(kline_data) - window):
                    if all(kline_data['low'].iloc[i] <= kline_data['low'].iloc[i-window:i]) and \
                       all(kline_data['low'].iloc[i] <= kline_data['low'].iloc[i+1:i+window+1]):
                        local_minima.append(i)
                
                logger.info("股票 %s 找到 %d 个局部最低点", stock['ts_code'], len(local_minima))
                
                # 寻找头肩底形态
                for i in range(2, len(local_minima) - 2):
                    left_shoulder = local_minima[i-1]
                    head = local_minima[i]
                    right_shoulder = local_minima[i+1]
                    
                    # 检查时间间隔
                    if (head - left_shoulder < 10 or right_shoulder - head < 10 or
                        right_shoulder - left_shoulder > 60):
                        continue
                    
                    # 检查价格关系
                    if (kline_data['low'].iloc[left_shoulder] > kline_data['low'].iloc[head] and
                        kline_data['low'].iloc[right_shoulder] > kline_data['low'].iloc[head]):
                        
                        # 计算颈线
                        neckline = max(kline_data['high'].iloc[left_shoulder:right_shoulder+1])
                        
                        # 检查是否突破颈线
                        if kline_data['close'].iloc[-1] > neckline:
                            result_stocks.append(stock)
                            logger.info("股票 %s 形成头肩底形态，突破颈线", stock['ts_code'])
                            break
                
            except Exception as e:
                logger.error("处理股票 %s 时出错: %s", stock['ts_code'], str(e))
                continue
        
        logger.info("头肩底筛选完成，找到的股票数量：%d", len(result_stocks))
        return pd.DataFrame(result_stocks) 