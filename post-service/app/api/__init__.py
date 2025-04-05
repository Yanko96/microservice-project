# app/api/__init__.py

from fastapi import APIRouter

from app.api.endpoints import posts, comments, reactions, search, health

# 创建主路由
api_router = APIRouter()

# 包含各端点路由
api_router.include_router(posts.router, prefix="/posts", tags=["帖子"])
api_router.include_router(comments.router, prefix="/comments", tags=["评论"])
api_router.include_router(reactions.router, prefix="/reactions", tags=["反应/点赞"])
api_router.include_router(search.router, prefix="/search", tags=["搜索"])
api_router.include_router(health.router, tags=["监控"])