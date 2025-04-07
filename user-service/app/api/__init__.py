from fastapi import APIRouter

from app.api.endpoints import auth, users, health, follow

# 创建主路由
api_router = APIRouter()

# 包含各端点路由 - 将健康检查路由放在最前面，确保它不会被其他路由捕获
api_router.include_router(health.router, prefix="/users/health", tags=["健康检查"])  # 不添加前缀
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(follow.router)