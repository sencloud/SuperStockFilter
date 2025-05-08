import uvicorn
from src.api.config import settings

def run_api():
    """启动 API 服务"""
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

if __name__ == "__main__":
    run_api() 