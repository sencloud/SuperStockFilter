from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from src.services.stock_service import (
    get_market_types,
    get_industries,
    get_index_components,
    filter_stocks,
    get_stock_basic_info,
    get_deepseek_analysis
)
from src.api.config import Settings, get_settings
from src.utils.config import ts_api

def create_app(settings: Settings) -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="超级股票过滤器 API",
        description="提供股票筛选和分析功能的 API 接口",
        version=settings.API_VERSION
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    
    return app

app = create_app(get_settings())

class FilterRequest(BaseModel):
    market_types: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    index_components: Optional[List[str]] = None
    kline_pattern: Optional[str] = None
    price_prediction: Optional[str] = None

@app.get("/api/market-types")
async def get_market_types_api(settings: Settings = Depends(get_settings)):
    """获取市场类型列表"""
    try:
        return {"data": get_market_types()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/industries")
async def get_industries_api(settings: Settings = Depends(get_settings)):
    """获取行业分类列表"""
    try:
        return {"data": get_industries()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/index-components")
async def get_index_components_api(settings: Settings = Depends(get_settings)):
    """获取指数成分股列表"""
    try:
        return {"data": get_index_components()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/filter")
async def filter_stocks_api(
    filter_request: FilterRequest,
    settings: Settings = Depends(get_settings)
):
    """筛选股票"""
    try:
        result = filter_stocks(
            market_types=filter_request.market_types,
            industries=filter_request.industries,
            index_components=filter_request.index_components,
            kline_pattern=filter_request.kline_pattern,
            price_prediction=filter_request.price_prediction
        )
        
        if result is None:
            return {"data": [], "total": 0}
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{stock_code}")
async def get_stock_info_api(
    stock_code: str,
    settings: Settings = Depends(get_settings)
):
    """获取股票详细信息"""
    try:
        return {"data": get_stock_basic_info(stock_code)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{stock_code}/analysis")
async def get_stock_analysis_api(
    stock_code: str,
    settings: Settings = Depends(get_settings)
):
    """获取股票 DeepSeek 分析"""
    try:
        result = await get_deepseek_analysis(stock_code)
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        return {"data": result["content"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{stock_code}/kline")
async def get_stock_kline_api(
    stock_code: str,
    settings: Settings = Depends(get_settings)
):
    """获取股票K线数据"""
    try:
        # 获取最近60个交易日的K线数据
        df = ts_api.daily(
            ts_code=stock_code,
            start_date=(pd.Timestamp.now() - pd.Timedelta(days=120)).strftime('%Y%m%d')
        )
        
        if df is None or df.empty:
            return {"data": []}
            
        # 按日期排序
        df = df.sort_values('trade_date')
        
        # 转换为前端需要的格式
        kline_data = []
        for _, row in df.iterrows():
            kline_data.append({
                'trade_date': row['trade_date'],
                'open': float(row['open']),
                'close': float(row['close']),
                'high': float(row['high']),
                'low': float(row['low']),
                'volume': float(row['vol']),
                'amount': float(row['amount'])
            })
            
        return {"data": kline_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 