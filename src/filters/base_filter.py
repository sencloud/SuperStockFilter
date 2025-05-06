from abc import ABC, abstractmethod
import pandas as pd

class BaseFilter(ABC):
    """基础筛选器类"""
    
    @abstractmethod
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行筛选"""
        pass 