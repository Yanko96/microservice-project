from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, validator, HttpUrl

from app.models.user import Gender

# 共享属性
class UserBase(BaseModel):
    username: str
    email: EmailStr
    
    
# 创建用户时的输入模型
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('用户名必须是字母和数字的组合')
        return v


# 更新用户基本信息时的输入模型
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


# 更新用户详细资料的输入模型
class UserProfileUpdate(BaseModel):
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[HttpUrl] = None
    gender: Optional[Gender] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    is_private: Optional[bool] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError('电话号码必须只包含数字')
        return v


# 用于数据库操作的用户模型基类
class UserInDBBase(UserBase):
    id: int
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    # 基本资料
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[HttpUrl] = None
    gender: Optional[Gender] = None
    is_private: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # 替代 orm_mode=True (Pydantic v2)


# 返回给前端的用户精简模型（用于列表展示）
class UserBrief(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True


# 返回给前端的用户模型（不包含敏感信息）
class User(UserInDBBase):
    pass


# 在检索其他用户资料时返回的模型（考虑隐私）
class UserPublic(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[HttpUrl] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# 数据库中存储的用户模型（包含密码哈希）
class UserInDB(UserInDBBase):
    hashed_password: str


# 登录请求模型
class UserLogin(BaseModel):
    username: str
    password: str


# 令牌模型
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserBrief


# 令牌载荷
class TokenPayload(BaseModel):
    sub: Optional[int] = None
    exp: Optional[int] = None