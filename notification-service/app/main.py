import asyncio
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import time
import logging

from app.api import api_router
from app.core.config import settings
from app.events.kafka_consumer import kafka_consumer
from app.websockets.broadcaster import init_redis, close_redis, subscribe_to_channel

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# 设置 CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 请求处理计时中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # 记录请求信息
    logger.debug(
        f"请求处理完成: {request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s"
    )
    
    return response

# 包含 API 路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 健康检查路由
@app.get("/health")
def health_check():
    return {"status": "UP"}

@app.get("/")
def root():
    return {"message": "欢迎使用社交平台通知服务 API"}

# 启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("服务启动中...")
    
    # 初始化Redis连接
    await init_redis()
    
    # 订阅Redis通知频道
    await subscribe_to_channel(settings.REDIS_CHANNEL)
    
    # 启动Kafka消费者
    await kafka_consumer.start()

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("服务关闭中...")
    
    # 关闭Redis连接
    await close_redis()
    
    # 停止Kafka消费者
    await kafka_consumer.stop()

# 如果直接运行此脚本，则启动应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)