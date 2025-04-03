# app/api/deps.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import TokenPayload

def public_endpoint(path: str) -> bool:
    """检查是否是公开端点"""
    public_paths = [
        "/health",
        "/api/v1/users/health",
        "/api/v1/health"
    ]
    return any(path.endswith(public_path) for public_path in public_paths)

# OAuth2 密码流
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# 获取当前用户
def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    # 对健康检查端点不做认证
    if public_endpoint(request.url.path):
        return None
        
    try:
        # 解码 JWT 令牌
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        # 检查令牌是否已过期
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无法验证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 从数据库获取用户
    user = db.query(User).filter(User.id == token_data.sub).first()
    if user is None:
        raise HTTPException(status_code=404, detail="未找到用户")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户不活跃")
        
    return user

# 获取当前活跃用户（可被重用）
def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户不活跃")
    return current_user

# 获取当前超级用户
def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="用户没有足够的权限"
        )
    return current_user

# 验证用户
def authenticate_user(
    db: Session, username: str, password: str
) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user