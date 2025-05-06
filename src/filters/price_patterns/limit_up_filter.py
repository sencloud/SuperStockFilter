import pandas as pd
import numpy as np
from .base_price_filter import BasePriceFilter
import logging

logger = logging.getLogger(__name__)

class LimitUpFilter(BasePriceFilter):
    """可能涨停筛选器"""
    
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行可能涨停筛选"""
        logger.info("开始执行可能涨停筛选，传入的股票数量：%d", len(stocks_df))
        result_stocks = []
        
        for _, stock in stocks_df.iterrows():
            try:
                # 获取K线数据
                kline_data = self.get_kline_data(stock['ts_code'])
                if kline_data is None or len(kline_data) < self.lookback_period:
                    continue
                    
                # 计算技术指标
                kline_data = self.calculate_indicators(kline_data)
                
                # 获取最新数据
                latest = kline_data.iloc[-1]
                prev = kline_data.iloc[-2]
                
                # 检查是否满足涨停条件
                # 1. 当日涨幅接近涨停（9.5%以上）
                if latest['pct_change'] < 0.095:
                    continue
                    
                # 2. 当日振幅较大（超过5%）
                if latest['amplitude'] < 0.05:
                    continue
                    
                # 3. 成交量放大（量比大于2）
                if latest['volume_ratio'] < 2:
                    continue
                    
                # 4. 换手率较高（超过5%）
                if latest['turnover_rate'] < 0.05:
                    continue
                    
                # 5. 资金流向为正
                if latest['money_flow'] <= 0:
                    continue
                    
                # 6. 开盘价低于收盘价（阳线）
                if latest['open'] >= latest['close']:
                    continue
                    
                # 7. 收盘价接近最高价（上影线短）
                if (latest['high'] - latest['close']) / (latest['high'] - latest['low']) > 0.2:
                    continue
                    
                # 8. 前一日收盘价低于当日开盘价（跳空高开）
                if prev['close'] >= latest['open']:
                    continue
                    
                result_stocks.append(stock)
                
            except Exception as e:
                logger.error(f"处理股票 {stock['ts_code']} 时出错: {str(e)}")
                continue
        
        logger.info("可能涨停筛选完成，找到的股票数量：%d", len(result_stocks))
        return pd.DataFrame(result_stocks) 