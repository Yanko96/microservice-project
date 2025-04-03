# notification-service/app/api/deps.py
from typing import Generator, Dict, Any, Optional
import httpx

from fastapi import Depends, HTTPException, status, Header, Query, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.core.security import verify_token

def public_endpoint(path: str) -> bool:
    """检查是否是公开端点"""
    public_paths = [
        "/health",
        "/api/v1/notifications/health",
        "/api/v1/health"
    ]
    return any(path.endswith(public_path) for public_path in public_paths)

# OAuth2 密码流
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# 获取当前用户
async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> Dict[str, Any]:
    # 对健康检查端点不做认证
    if public_endpoint(request.url.path):
        return None
        
    # 验证令牌
    payload = verify_token(token)
    user_id = int(payload["sub"])
    
    # 从用户服务获取用户信息
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.USER_SERVICE_BASE_URL}/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            user_data = response.json()
            # 添加令牌过期时间
            if 'exp' in payload:
                user_data['token_exp'] = payload['exp']
            return user_data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效或过期的凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif e.response.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        else:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"用户服务错误: {e.response.text}",
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="无法连接到用户服务",
        )

# 分页参数
def get_pagination_params(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(settings.NOTIFICATION_PAGE_SIZE, ge=1, le=100, description="每页数量"),
) -> Dict[str, int]:
    """
    获取分页参数
    """
    return {"page": page, "size": size}

# 获取用户服务客户端
async def get_user_service_client() -> httpx.AsyncClient:
    """
    创建用于调用用户服务的HTTP客户端
    """
    return httpx.AsyncClient(base_url=settings.USER_SERVICE_BASE_URL, timeout=10.0)