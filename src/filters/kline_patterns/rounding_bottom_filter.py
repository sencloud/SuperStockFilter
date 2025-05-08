import pandas as pd
import numpy as np
from .base_kline_filter import BaseKlineFilter
import logging
from scipy.signal import argrelextrema
from statsmodels.nonparametric.kernel_regression import KernelReg

logger = logging.getLogger(__name__)

class RoundingBottomFilter(BaseKlineFilter):
    """圆弧底筛选器"""
    
    def __init__(self):
        super().__init__(lookback_period=480)
        self.config = {
            'lookback_period': 480,    # 约2年交易日
            'min_formation_days': 40,   # 最小形态形成天数
            'min_r_squared': 0.75,     # 最小拟合优度
            'max_price_volatility': 0.03,  # 价格波动阈值
            'volume_increase_ratio': 1.5,  # 成交量放大倍数
            'ma_periods': [20, 60, 200]    # 均线周期
        }

    def _calculate_moving_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算多周期均线"""
        for period in self.config['ma_periods']:
            data[f'MA{period}'] = data['close'].rolling(window=period).mean()
        return data

    def _check_volume_pattern(self, data: pd.DataFrame) -> bool:
        """验证成交量模式：底部缩量，突破放量"""
        recent_vol = data['volume'].iloc[-20:].mean()
        base_vol = data['volume'].iloc[:20].mean()
        return recent_vol > base_vol * self.config['volume_increase_ratio']

    def _detect_rounding_pattern(self, data: pd.DataFrame) -> tuple:
        """使用核回归检测圆弧底形态"""
        x = np.arange(len(data))
        y = data['close'].values
        
        # 核回归拟合
        kr = KernelReg(y, x[:, np.newaxis], var_type='c', reg_type='ll')
        y_pred, _ = kr.fit(x[:, np.newaxis])
        
        # 计算拟合优度
        r2 = 1 - (np.sum((y - y_pred)**2) / np.sum((y - np.mean(y))**2))
        
        # 寻找极值点
        minima = argrelextrema(y_pred, np.less, order=10)[0]
        maxima = argrelextrema(y_pred, np.greater, order=10)[0]
        
        return r2, minima, maxima

    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行圆弧底筛选"""
        logger.info("开始执行圆弧底筛选，传入的股票数量：%d", len(stocks_df))
        result_stocks = []
        
        for _, stock in stocks_df.iterrows():
            try:
                kline_data = self.get_kline_data(stock['ts_code'])
                if kline_data is None or len(kline_data) < self.config['lookback_period']:
                    continue
                
                logger.info("分析股票 %s 的K线数据，数据长度：%d", stock['ts_code'], len(kline_data))
                
                # 计算技术指标
                kline_data = self._calculate_moving_averages(kline_data)
                
                # 在不同时间窗口中寻找形态
                for window in range(self.config['min_formation_days'], 120, 20):
                    recent_data = kline_data.iloc[-window:]
                    
                    # 检测圆弧底形态
                    r2, minima, maxima = self._detect_rounding_pattern(recent_data)
                    
                    if (r2 > self.config['min_r_squared'] and 
                        len(minima) >= 2 and len(maxima) >= 1):
                        
                        # 验证价格突破
                        price_breakout = (recent_data['close'].iloc[-1] > 
                                        recent_data['MA200'].iloc[-1])
                        
                        # 验证成交量特征
                        volume_valid = self._check_volume_pattern(recent_data)
                        
                        if price_breakout and volume_valid:
                            result_stocks.append({
                                **stock.to_dict(),
                                'r_squared': r2,
                                'formation_days': window
                            })
                            logger.info("股票 %s 形成有效圆弧底形态，拟合度：%.2f，形成周期：%d", 
                                      stock['ts_code'], r2, window)
                            break
                
            except Exception as e:
                logger.error("处理股票 %s 时出错: %s", stock['ts_code'], str(e))
                continue
        
        logger.info("圆弧底筛选完成，找到的股票数量：%d", len(result_stocks))
        return pd.DataFrame(result_stocks) 