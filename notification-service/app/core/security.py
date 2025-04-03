from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError

from app.core.config import settings

# 验证 JWT 令牌
def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    验证并解码JWT令牌，返回载荷
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_token(token: str) -> Dict[str, Any]:
    """
    验证令牌并确保未过期
    """
    payload = decode_jwt_token(token)
    
    # 检查令牌是否已过期
    if 'exp' in payload and datetime.fromtimestamp(payload['exp']) < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 确保存在用户ID
    if 'sub' not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌载荷",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload