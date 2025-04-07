from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import api_router
from app.core.config import settings
from app.utils.logging import setup_logging

# 设置日志
logger = setup_logging()

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs"
)

Instrumentator().instrument(app).expose(app)

# 设置 CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 包含 API 路由
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    """
    根路径请求，用于简单测试服务是否在运行
    """
    return {"message": "欢迎使用社交平台用户服务 API"}

# 在 app/main.py 中添加根级别路由
@app.get("/health")
async def root_health_check():
    """
    根级别健康检查路由，不带 API 前缀
    """
    return {"status": "UP"}

@app.get(f"{settings.API_V1_STR}/health")
async def api_health_check():
    """
    API级别健康检查，带API前缀
    """
    return {"status": "UP", "service": "user-service"}

# 启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("服务启动中...")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("服务关闭中...")

# 如果直接运行此脚本，则启动应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)