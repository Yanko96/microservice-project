# app/main.py

import asyncio
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import time
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import api_router
from app.core.config import settings
from app.utils.logging import setup_logging
from app.events.kafka_producer import kafka_producer
from app.utils.elasticsearch import es_service

# 设置日志
logger = setup_logging()

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",  # ✅ 显式开启 Swagger UI
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

# 请求处理计时中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # 记录请求信息
    logger.info(
        f"请求处理完成",
        method=request.method,
        url=str(request.url),
        client=request.client.host if request.client else None,
        process_time=process_time,
        status_code=response.status_code
    )
    
    return response

# 健康检查路由 (根路径)
@app.get("/health")
def root_health_check():
    return {"status": "UP"}

@app.get("/")
def root():
    return {"message": "欢迎使用社交平台帖子服务 API"}

# 启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("服务启动中...")
    
    # 启动Kafka生产者
    await kafka_producer.start()
    
    # 连接到Elasticsearch
    await es_service.connect()
    if es_service.is_ready:
        logger.info("Elasticsearch连接成功")
    else:
        logger.warning("无法连接到Elasticsearch，搜索功能将不可用")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("服务关闭中...")
    
    # 停止Kafka生产者
    await kafka_producer.stop()
    
    # 关闭Elasticsearch连接
    await es_service.close()

# 如果直接运行此脚本，则启动应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)