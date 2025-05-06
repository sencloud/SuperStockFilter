from typing import Optional, Dict, Type
from .base_filter import BaseFilter
from .kline_patterns.v_bottom_filter import VBottomFilter
from .kline_patterns.double_bottom_filter import DoubleBottomFilter
from .kline_patterns.morning_star_filter import MorningStarFilter
from .kline_patterns.rounding_bottom_filter import RoundingBottomFilter
from .kline_patterns.head_shoulders_bottom_filter import HeadShouldersBottomFilter
from .kline_patterns.flat_bottom_filter import FlatBottomFilter
from .kline_patterns.rising_sun_filter import RisingSunFilter
from .kline_patterns.bullish_engulfing_filter import BullishEngulfingFilter
from .kline_patterns.three_white_soldiers_filter import ThreeWhiteSoldiersFilter
from .kline_patterns.hammer_filter import HammerFilter
from .price_patterns.limit_up_filter import LimitUpFilter

class FilterFactory:
    """筛选器工厂类"""
    
    # 注册筛选器
    _filters: Dict[str, Type[BaseFilter]] = {
        'V型底': VBottomFilter,
        'W底': DoubleBottomFilter,
        '启明之星': MorningStarFilter,
        '圆弧底': RoundingBottomFilter,
        '头肩底': HeadShouldersBottomFilter,
        '平底': FlatBottomFilter,
        '旭日东升': RisingSunFilter,
        '看涨吞没': BullishEngulfingFilter,
        '红三兵': ThreeWhiteSoldiersFilter,
        '锤头线': HammerFilter,
        '涨停': LimitUpFilter
    }
    
    @classmethod
    def create_filter(cls, filter_type: str, **kwargs) -> Optional[BaseFilter]:
        """创建筛选器实例"""
        if filter_type == '所有':
            return None
            
        filter_class = cls._filters.get(filter_type)
        if filter_class is None:
            raise ValueError(f"未知的筛选器类型: {filter_type}")
            
        return filter_class(**kwargs) 