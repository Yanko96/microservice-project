from fastapi import APIRouter

from app.api.endpoints import notifications

# 创建主路由
api_router = APIRouter()

# 包含各端点路由
api_router.include_router(notifications.router, prefix="/notifications", tags=["通知"])