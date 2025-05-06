import pandas as pd
import numpy as np
from .base_kline_filter import BaseKlineFilter
import logging

logger = logging.getLogger(__name__)

class ThreeWhiteSoldiersFilter(BaseKlineFilter):
    """红三兵筛选器"""
    
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行红三兵筛选"""
        logger.info("开始执行红三兵筛选，传入的股票数量：%d", len(stocks_df))
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
                kline_data['body_size'] = abs(kline_data['body'])
                kline_data['upper_shadow'] = kline_data['high'] - kline_data[['open', 'close']].max(axis=1)
                kline_data['lower_shadow'] = kline_data[['open', 'close']].min(axis=1) - kline_data['low']
                
                # 寻找红三兵形态
                for i in range(2, len(kline_data)):
                    # 检查连续三根阳线（收盘价必须高于开盘价）
                    if not all(kline_data['close'].iloc[i-2:i+1] > kline_data['open'].iloc[i-2:i+1]):
                        continue
                    
                    # 检查每根阳线的实体大小（过滤掉十字星等微小实体）
                    avg_body = kline_data['body_size'].iloc[i-2:i+1].mean()
                    if not all(kline_data['body_size'].iloc[i-2:i+1] > avg_body * 0.5):
                        continue
                        
                    # 检查每根阳线的开盘价是否高于前一根阳线的开盘价
                    if not (kline_data['open'].iloc[i] > kline_data['open'].iloc[i-1] > kline_data['open'].iloc[i-2]):
                        continue
                        
                    # 检查每根阳线的收盘价是否高于前一根阳线的收盘价
                    if not (kline_data['close'].iloc[i] > kline_data['close'].iloc[i-1] > kline_data['close'].iloc[i-2]):
                        continue
                        
                    # 检查上影线不能过长（不超过实体的50%）
                    if not all(kline_data['upper_shadow'].iloc[i-2:i+1] < kline_data['body_size'].iloc[i-2:i+1] * 0.5):
                        continue
                        
                    # 检查成交量是否递增
                    if (kline_data['volume'].iloc[i] > kline_data['volume'].iloc[i-1] and
                        kline_data['volume'].iloc[i-1] > kline_data['volume'].iloc[i-2]):
                        
                        result_stocks.append(stock)
                        logger.info("股票 %s 形成红三兵形态，成交量递增：%.2f%%", 
                                  stock['ts_code'],
                                  (kline_data['volume'].iloc[i] / kline_data['volume'].iloc[i-2] - 1) * 100)
                        break
                
            except Exception as e:
                logger.error("处理股票 %s 时出错: %s", stock['ts_code'], str(e))
                continue
        
        logger.info("红三兵筛选完成，找到的股票数量：%d", len(result_stocks))
        return pd.DataFrame(result_stocks) 