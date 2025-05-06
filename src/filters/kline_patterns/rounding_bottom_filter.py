import pandas as pd
import numpy as np
from .base_kline_filter import BaseKlineFilter
import logging

logger = logging.getLogger(__name__)

class RoundingBottomFilter(BaseKlineFilter):
    """圆弧底筛选器"""
    
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行圆弧底筛选"""
        logger.info("开始执行圆弧底筛选，传入的股票数量：%d", len(stocks_df))
        result_stocks = []
        
        for _, stock in stocks_df.iterrows():
            try:
                # 获取K线数据
                kline_data = self.get_kline_data(stock['ts_code'])
                logger.info("获取股票 %s 的K线数据成功，K线数据长度：%d", stock['ts_code'], len(kline_data))
                if kline_data is None or len(kline_data) < self.lookback_period:
                    continue
                    
                # 计算移动平均线
                kline_data['MA20'] = kline_data['close'].rolling(window=20).mean()
                kline_data['MA60'] = kline_data['close'].rolling(window=60).mean()
                
                # 寻找圆弧底形态
                for i in range(60, len(kline_data)):
                    # 获取最近60天的数据
                    recent_data = kline_data.iloc[i-60:i+1]
                    
                    # 计算价格变化率
                    price_changes = recent_data['close'].pct_change()
                    
                    # 检查是否形成圆弧底
                    if (price_changes.iloc[:30].mean() < 0 and  # 前半段下跌
                        price_changes.iloc[30:].mean() > 0 and  # 后半段上涨
                        abs(price_changes.iloc[:30].mean()) > 0.001 and  # 确保有足够的波动
                        abs(price_changes.iloc[30:].mean()) > 0.001):
                        
                        # 计算价格曲线的拟合度
                        x = np.arange(len(recent_data))
                        y = recent_data['close'].values
                        z = np.polyfit(x, y, 2)
                        p = np.poly1d(z)
                        r2 = 1 - (np.sum((y - p(x))**2) / np.sum((y - np.mean(y))**2))
                        
                        if r2 > 0.8:  # 拟合度大于0.8
                            result_stocks.append(stock)
                            logger.info("股票 %s 形成圆弧底形态，拟合度：%.2f", stock['ts_code'], r2)
                            break
                
            except Exception as e:
                logger.error("处理股票 %s 时出错: %s", stock['ts_code'], str(e))
                continue
        
        logger.info("圆弧底筛选完成，找到的股票数量：%d", len(result_stocks))
        return pd.DataFrame(result_stocks) 