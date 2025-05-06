import pandas as pd
from .base_filter import BaseFilter
from .filter_factory import FilterFactory
import logging

logger = logging.getLogger(__name__)

class KlinePatternFilter(BaseFilter):
    """K线形态筛选器"""
    
    PATTERNS = {
        "所有": None,
        "V型底": "v_bottom",
        "W底（双重底）": "double_bottom",
        "启明之星": "morning_star",
        "圆弧底": "rounding_bottom",
        "头肩底": "head_shoulders_bottom",
        "平底": "flat_bottom",
        "旭日东升": "rising_sun",
        "看涨吞没": "bullish_engulfing",
        "红三兵": "three_white_soldiers",
        "锤头线": "hammer"
    }
    
    def __init__(self, pattern: str):
        self.pattern = pattern
        logger.info(f"初始化K线形态筛选器，模式: {pattern}")
    
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行K线形态筛选"""
        if self.pattern == "所有":
            return stocks_df
            
        logger.info(f"开始执行K线形态筛选: {self.pattern}")
        filter_type = self.PATTERNS[self.pattern]
        pattern_filter = FilterFactory.create_filter(filter_type)
        return pattern_filter.filter(stocks_df) 