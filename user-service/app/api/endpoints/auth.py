from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import authenticate_user, get_current_active_user
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, User as UserSchema, UserBrief

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    使用用户名和密码获取 JWT 访问令牌
    """
    user = authenticate_user(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户不活跃")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.add(user)
    db.commit()
    
    # 创建令牌
    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/register", response_model=UserSchema)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    注册新用户
    """
    # 检查用户名是否已存在
    user = db.query(User).filter(User.username == user_in.username).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="用户名已被使用",
        )
    
    # 检查邮箱是否已存在
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="邮箱已被使用",
        )
    
    # 创建新用户
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=True,
        is_private=False,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.get("/oauth/github", summary="GitHub OAuth登录")
async def github_oauth_login():
    """
    重定向到GitHub进行OAuth认证
    注意：这是一个简化的示例，真实实现需要使用GitHub OAuth API
    """
    github_auth_url = f"https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&redirect_uri={settings.GITHUB_REDIRECT_URI}"
    
    return {"auth_url": github_auth_url}

@router.get("/oauth/github/callback", response_model=Token)
async def github_oauth_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """
    处理GitHub OAuth回调
    注意：这是一个简化的示例，真实实现需要调用GitHub API获取用户信息
    """
    # 在实际实现中，这里会用code换取access_token，然后获取用户信息
    # 这里使用模拟数据作为示例
    mock_github_user = {
        "id": "12345",
        "login": "github_user",
        "email": "github_user@example.com",
        "name": "GitHub User"
    }
    
    # 检查用户是否已存在
    user = db.query(User).filter(User.github_id == mock_github_user["id"]).first()
    
    if not user:
        # 创建新用户
        username = mock_github_user["login"]
        email = mock_github_user["email"]
        
        # 检查用户名和邮箱是否被占用
        if db.query(User).filter(User.username == username).first():
            username = f"{username}_{mock_github_user['id']}"
        
        if db.query(User).filter(User.email == email).first():
            email = f"github_{mock_github_user['id']}@example.com"
        
        user = User(
            github_id=mock_github_user["id"],
            username=username,
            email=email,
            hashed_password=get_password_hash(f"github_{mock_github_user['id']}"),  # 创建随机密码
            full_name=mock_github_user["name"],
            is_active=True,
            is_private=False,
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.add(user)
    db.commit()
    
    # 创建令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/oauth/google", summary="Google OAuth登录")
async def google_oauth_login():
    """
    重定向到Google进行OAuth认证
    注意：这是一个简化的示例，真实实现需要使用Google OAuth API
    """
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={settings.GOOGLE_CLIENT_ID}&response_type=code&scope=email%20profile&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
    
    return {"auth_url": google_auth_url}

@router.get("/oauth/google/callback", response_model=Token)
async def google_oauth_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """
    处理Google OAuth回调
    注意：这是一个简化的示例，真实实现需要调用Google API获取用户信息
    """
    # 在实际实现中，这里会用code换取access_token，然后获取用户信息
    # 这里使用模拟数据作为示例
    mock_google_user = {
        "id": "67890",
        "email": "google_user@example.com",
        "name": "Google User"
    }
    
    # 检查用户是否已存在
    user = db.query(User).filter(User.google_id == mock_google_user["id"]).first()
    
    if not user:
        # 创建新用户
        username = mock_google_user["email"].split("@")[0]
        email = mock_google_user["email"]
        
        # 检查用户名和邮箱是否被占用
        if db.query(User).filter(User.username == username).first():
            username = f"{username}_{mock_google_user['id']}"
        
        if db.query(User).filter(User.email == email).first():
            email = f"google_{mock_google_user['id']}@example.com"
        
        user = User(
            google_id=mock_google_user["id"],
            username=username,
            email=email,
            hashed_password=get_password_hash(f"google_{mock_google_user['id']}"),  # 创建随机密码
            full_name=mock_google_user["name"],
            is_active=True,
            is_private=False,
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.add(user)
    db.commit()
    
    # 创建令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/logout")
def logout(
    response: Response,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    用户登出
    
    注意：由于JWT是无状态的，真正的登出需要客户端删除令牌或使用令牌黑名单
    这里仅作为示例
    """
    return {"detail": "成功登出"}

@router.post("/refresh-token", response_model=Token)
def refresh_access_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    刷新访问令牌
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 创建新令牌
    access_token = create_access_token(
        current_user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": current_user
    }