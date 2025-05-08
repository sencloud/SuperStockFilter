import pandas as pd
import numpy as np
from .base_price_filter import BasePriceFilter
import logging
import tushare as ts
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class MoneyFlowFilter(BasePriceFilter):
    """资金持续流入筛选器"""
    
    def __init__(self, lookback_period=60):
        super().__init__(lookback_period)
        self.pro = ts.pro_api()
        self.api_calls = 0  # API调用计数
        self.last_reset = time.time()  # 上次重置计数的时间
        self.rate_limit = 290  # 每分钟API调用限制（留10个余量）
        
    def _check_rate_limit(self):
        """检查并控制API调用频率"""
        current_time = time.time()
        # 如果距离上次重置已经过了60秒，重置计数器
        if current_time - self.last_reset >= 60:
            logger.debug(f"重置API调用计数 - 上一分钟调用次数: {self.api_calls}")
            self.api_calls = 0
            self.last_reset = current_time
            
        # 如果当前分钟内的调用次数已达到限制
        if self.api_calls >= self.rate_limit:
            wait_time = 60 - (current_time - self.last_reset)
            if wait_time > 0:
                logger.warning(f"达到API调用限制，等待{wait_time:.1f}秒")
                time.sleep(wait_time)
                self.api_calls = 0
                self.last_reset = time.time()
        
        self.api_calls += 1
        
    def get_money_flow_data(self, ts_code, start_date, end_date):
        """获取个股资金流向数据"""
        try:
            self._check_rate_limit()  # 检查API调用限制
            df = self.pro.moneyflow(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='trade_date,buy_sm_vol,buy_sm_amount,sell_sm_vol,sell_sm_amount,'
                       'buy_md_vol,buy_md_amount,sell_md_vol,sell_md_amount,'
                       'buy_lg_vol,buy_lg_amount,sell_lg_vol,sell_lg_amount,'
                       'buy_elg_vol,buy_elg_amount,sell_elg_vol,sell_elg_amount,'
                       'net_mf_vol,net_mf_amount'
            )
            return df
        except Exception as e:
            logger.error(f"获取{ts_code}资金流向数据失败: {str(e)}")
            return None

    def analyze_stock_inflow(self, stock_info, start_date, end_date):
        """分析单只股票的资金流入情况"""
        flow_data = self.get_money_flow_data(stock_info['ts_code'], start_date, end_date)
        if flow_data is None or flow_data.empty:
            return None
            
        # 计算大单和超大单的净流入
        flow_data['large_net_inflow'] = (
            (flow_data['buy_lg_amount'] + flow_data['buy_elg_amount']) -
            (flow_data['sell_lg_amount'] + flow_data['sell_elg_amount'])
        )
        
        # 统计指标
        total_days = len(flow_data)
        inflow_days = len(flow_data[flow_data['large_net_inflow'] > 0])
        total_inflow = flow_data['large_net_inflow'].sum()
        
        # 筛选条件
        if (inflow_days / total_days > 0.6) and (total_inflow > 0):
            avg_daily_inflow = total_inflow / total_days
            
            # 保留原始股票信息的所有字段
            result = stock_info.copy()
            # 添加资金流向分析结果
            result.update({
                'inflow_days': inflow_days,
                'total_days': total_days,
                'inflow_ratio': round(inflow_days / total_days * 100, 2),
                'total_inflow': round(total_inflow / 10000, 2),  # 转换为亿元
                'avg_daily_inflow': round(avg_daily_inflow / 10000, 2),  # 转换为亿元
                'reason': f"近{total_days}天资金净流入{inflow_days}天，累计净流入{round(total_inflow/10000, 2)}亿元"
            })
            return result
        return None
        
    def filter(self, stocks_df: pd.DataFrame) -> pd.DataFrame:
        """执行资金持续流入筛选"""
        logger.info("开始执行资金持续流入筛选，传入的股票数量：%d", len(stocks_df))
        result_stocks = []
        
        # 获取当前日期
        today = datetime.now()
        end_date = today.strftime('%Y%m%d')
        start_date = (today - timedelta(days=self.lookback_period)).strftime('%Y%m%d')
        
        total_stocks = len(stocks_df)
        processed_stocks = 0
        start_time = time.time()
        
        for _, stock in stocks_df.iterrows():
            try:
                processed_stocks += 1
                if processed_stocks % 50 == 0:
                    elapsed_time = time.time() - start_time
                    avg_time_per_stock = elapsed_time / processed_stocks
                    remaining_stocks = total_stocks - processed_stocks
                    estimated_remaining_time = remaining_stocks * avg_time_per_stock
                    logger.info(f"进度: {processed_stocks}/{total_stocks} ({processed_stocks/total_stocks*100:.1f}%) "
                              f"预计还需: {estimated_remaining_time/60:.1f}分钟")
                
                result = self.analyze_stock_inflow(
                    stock.to_dict(),
                    start_date,
                    end_date
                )
                
                if result:
                    result_stocks.append(result)
                    logger.info(f"找到符合条件的股票: {result['ts_code']} {result['name']} - "
                              f"净流入{result['inflow_days']}/{result['total_days']}天, "
                              f"累计净流入{result['total_inflow']}亿元")
                    
            except Exception as e:
                logger.error(f"处理股票 {stock['ts_code']} 时出错: {str(e)}")
                continue
        
        total_time = time.time() - start_time
        logger.info(f"资金持续流入筛选完成，耗时{total_time/60:.1f}分钟，找到的股票数量：%d", len(result_stocks))
        return pd.DataFrame(result_stocks) 