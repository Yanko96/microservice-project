from fastapi import APIRouter

from app.api.endpoints import auth, users, health

# 创建主路由
api_router = APIRouter()

# 包含各端点路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(health.router, tags=["健康检查"])  # 不要给健康检查加前缀