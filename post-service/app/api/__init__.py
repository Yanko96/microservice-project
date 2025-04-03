# app/api/api_router.py or app/api/__init__.py (wherever your main API router is defined)

from fastapi import APIRouter

from app.api.endpoints import posts, comments, reactions, search, health

# Create main router
api_router = APIRouter()

# Include routers in the correct order:
# 1. Global health endpoint (no prefix, will be accessible at /api/v1/health)
api_router.include_router(health.router, prefix="/posts/health", tags=["健康检查"])

# 2. Functional endpoints
api_router.include_router(search.router, prefix="/search", tags=["搜索"])
api_router.include_router(reactions.router, prefix="/reactions", tags=["反应/点赞"])
api_router.include_router(comments.router, prefix="/comments", tags=["评论"])

# 3. Posts router last (since it has a dynamic parameter route that could catch other paths)
api_router.include_router(posts.router, prefix="/posts", tags=["帖子"])