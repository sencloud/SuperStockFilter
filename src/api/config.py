from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings(BaseSettings):
    """API 配置"""
    # API 版本
    API_VERSION: str = "1.0.0"
    
    # API 前缀
    API_PREFIX: str = "/api"
    
    # 是否开启调试模式
    DEBUG: bool = True
    
    # CORS 配置
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # API Keys
    TUSHARE_TOKEN: str = os.getenv('TUSHARE_TOKEN', '')
    DEEPSEEK_API_KEY: str = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_API_BASE: str = os.getenv('DEEPSEEK_API_BASE', 'https://ark.cn-beijing.volces.com/api/v3/bots')
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()

settings = get_settings() 