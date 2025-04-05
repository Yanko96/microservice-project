# app/api/api_router.py

"""
此文件是API路由的中央定义点，整合所有端点路由
"""

from fastapi import APIRouter

from app.api.endpoints import notifications

# 创建主路由
api_router = APIRouter()

# 包含各端点路由
api_router.include_router(notifications.router, prefix="/notifications", tags=["通知"])